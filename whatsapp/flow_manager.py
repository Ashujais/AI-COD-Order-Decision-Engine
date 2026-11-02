"""
WhatsApp State Machine and Conversation Flow Manager.
Handles all customer interaction states:
- "yes" / confirm -> Marks order CONFIRMED, moves to DISPATCH.
- "no" / cancel -> Marks CANCELLED_BY_CUSTOMER, prevents forward + return shipping waste.
- "change address" -> Prompts customer for updated address details, then confirms.
- Random replies ("kab milega", "is it safe?", gibberish) -> AI helper replies and re-prompts buttons.
- 12h / 24h timeouts -> Automated reminder and graceful auto-hold.
"""

import re
from enum import Enum
from typing import Dict, Any, Tuple
from datetime import datetime

class FlowState(str, Enum):
    INIT = "INIT"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    AWAITING_PREPAID_DECISION = "AWAITING_PREPAID_DECISION"
    AWAITING_ADDRESS_UPDATE = "AWAITING_ADDRESS_UPDATE"
    CONFIRMED = "CONFIRMED"
    CONVERTED_TO_PREPAID = "CONVERTED_TO_PREPAID"
    CANCELLED_BY_CUSTOMER = "CANCELLED_BY_CUSTOMER"
    HELD_ON_TIMEOUT = "HELD_ON_TIMEOUT"

class WhatsAppFlowManager:
    def __init__(self):
        # In-memory store for active conversations (in production, stored in Redis/Postgres)
        self.conversations: Dict[str, Dict[str, Any]] = {}

    def start_flow(self, order: Dict[str, Any], initial_action: str) -> Dict[str, Any]:
        """
        Initialize flow for an order based on recommended decision engine action.
        """
        order_id = str(order.get("order_id"))
        from .templates import get_confirmation_template, get_nudge_prepaid_template

        if initial_action == "Nudge to prepaid":
            state = FlowState.AWAITING_PREPAID_DECISION
            template = get_nudge_prepaid_template(order)
        elif initial_action == "Ship after confirmation":
            state = FlowState.AWAITING_CONFIRMATION
            template = get_confirmation_template(order)
        else:
            state = FlowState.CONFIRMED
            template = {"body": "Order approved for direct shipping.", "buttons": []}

        conv = {
            "order_id": order_id,
            "order": order,
            "state": state,
            "initial_action": initial_action,
            "history": [
                {"sender": "system", "message": template["body"], "timestamp": datetime.now().isoformat()}
            ],
            "last_template": template,
            "updated_address": None
        }
        self.conversations[order_id] = conv
        return conv

    def process_incoming_message(self, order_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process customer response (text message or quick reply button ID).
        """
        conv = self.conversations.get(order_id)
        if not conv:
            return {"error": f"No active conversation for order {order_id}"}

        msg = str(user_message).strip()
        msg_lower = msg.lower()
        curr_state = conv["state"]

        # Record incoming message
        conv["history"].append({"sender": "customer", "message": msg, "timestamp": datetime.now().isoformat()})

        reply_text = ""
        reply_buttons = []
        new_state = curr_state

        # Helper for word boundary matching
        def contains_word(text: str, words: list) -> bool:
            pattern = r'\b(' + '|'.join(re.escape(w) for w in words) + r')\b'
            return bool(re.search(pattern, text, re.IGNORECASE))

        # Check for Cancellation first! (Priority check)
        is_cancel = (
            "btn_cancel" in msg_lower
            or contains_word(msg_lower, [
                "cancel", "cancelled", "cancle", "nahi", "mat", "no",
                "mat bhejna", "don't send", "dont send", "stop"
            ])
            or "nahi chahiye" in msg_lower
        )

        # State 1: Awaiting Address Update
        if curr_state == FlowState.AWAITING_ADDRESS_UPDATE:
            if is_cancel:
                new_state = FlowState.CANCELLED_BY_CUSTOMER
                reply_text = f"🛑 Order #{order_id} has been cancelled upon your request."
            elif len(msg) >= 10:
                conv["updated_address"] = msg
                new_state = FlowState.CONFIRMED
                reply_text = (
                    f"✅ *Address Updated Successfully!*\n\n"
                    f"Updated Address: {msg}\n"
                    f"Your order #{order_id} is now confirmed and sent to warehouse packing! 🚀"
                )
            else:
                reply_text = "Please provide your full address including house number, street, and landmark so delivery is smooth:"

        # State 2: Awaiting Prepaid Nudge Decision
        elif curr_state == FlowState.AWAITING_PREPAID_DECISION:
            if is_cancel:
                new_state = FlowState.CANCELLED_BY_CUSTOMER
                reply_text = f"🛑 Your order #{order_id} has been cancelled upon your request. No amount will be charged."
            elif any(k in msg_lower for k in ["btn_pay_online", "pay online", "online", "upi", "card", "pay"]) and not contains_word(msg_lower, ["no", "not"]):
                new_state = FlowState.CONVERTED_TO_PREPAID
                reply_text = (
                    f"🎉 *Payment Link Generated!*\n\n"
                    f"Tap to complete payment with ₹50 discount: https://pay.example.com/checkout/{order_id}\n\n"
                    f"Once paid, your order gets express priority dispatch! ⚡"
                )
            elif any(k in msg_lower for k in ["btn_keep_cod", "cod", "cash", "cod hi rakho", "keep cod"]):
                new_state = FlowState.AWAITING_CONFIRMATION
                reply_text = (
                    f"No problem! We have kept your order on Cash on Delivery.\n\n"
                    f"Please confirm your delivery address to dispatch:"
                )
                reply_buttons = [
                    {"id": "btn_confirm", "title": "Confirm Order ✅"},
                    {"id": "btn_cancel", "title": "Cancel Order ❌"}
                ]
            else:
                reply_text = (
                    f"Would you like to pay online to save ₹50, or proceed with COD?\n"
                    f"Tap an option below:"
                )
                reply_buttons = [
                    {"id": "btn_pay_online", "title": "Pay Online & Save ₹50 💳"},
                    {"id": "btn_keep_cod", "title": "Continue with COD 🚚"}
                ]

        # State 3: Awaiting Standard Confirmation
        elif curr_state in [FlowState.AWAITING_CONFIRMATION, FlowState.HELD_ON_TIMEOUT]:
            if is_cancel:
                new_state = FlowState.CANCELLED_BY_CUSTOMER
                reply_text = (
                    f"🛑 *Order #{order_id} Cancelled*\n\n"
                    f"We have cancelled your order. If you change your mind, you can reorder anytime on our store!"
                )

            elif any(k in msg_lower for k in ["btn_update_addr", "change address", "new address", "address", "pata badalna"]):
                new_state = FlowState.AWAITING_ADDRESS_UPDATE
                reply_text = "Please reply with your updated complete address (House/Flat No, Building, Landmark, City, Pincode):"

            elif "btn_confirm" in msg_lower or "btn_unpause" in msg_lower or contains_word(msg_lower, ["yes", "ha", "haan", "confirm", "ok", "bhejo", "dispatch", "sure"]) or "bhej do" in msg_lower:
                new_state = FlowState.CONFIRMED
                reply_text = (
                    f"✅ *Order #{order_id} Confirmed!*\n\n"
                    f"Thank you! Your order is being packed and will be handed over to courier shortly. "
                    f"You will receive tracking details via SMS/WhatsApp once dispatched! 📦✨"
                )

            # Conversational / Random queries
            elif contains_word(msg_lower, ["kab", "when", "time", "din"]):
                reply_text = (
                    f"🕒 Expected delivery time is *3 to 4 business days* from dispatch.\n\n"
                    f"Would you like to confirm your order now?"
                )
                reply_buttons = [
                    {"id": "btn_confirm", "title": "Confirm Order ✅"},
                    {"id": "btn_cancel", "title": "Cancel Order ❌"}
                ]
            elif contains_word(msg_lower, ["original", "genuine", "hair", "safe", "quality"]):
                reply_text = (
                    f"🌿 Yes! All our haircare formulas are 100% genuine, paraben-free, and dermatologically tested.\n\n"
                    f"Please confirm to proceed with dispatch:"
                )
                reply_buttons = [
                    {"id": "btn_confirm", "title": "Confirm Order ✅"},
                    {"id": "btn_cancel", "title": "Cancel Order ❌"}
                ]
            else:
                reply_text = (
                    f"We received your message: \"{msg}\".\n\n"
                    f"To ensure quick shipping of order #{order_id}, please select an option below:"
                )
                reply_buttons = [
                    {"id": "btn_confirm", "title": "Confirm Order ✅"},
                    {"id": "btn_update_addr", "title": "Change Address 📍"},
                    {"id": "btn_cancel", "title": "Cancel Order ❌"}
                ]

        conv["state"] = new_state
        conv["history"].append({"sender": "system", "message": reply_text, "timestamp": datetime.now().isoformat()})

        return {
            "order_id": order_id,
            "state": new_state,
            "reply_text": reply_text,
            "reply_buttons": reply_buttons,
            "history": conv["history"]
        }

    def simulate_timeout(self, order_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Simulate what happens when 12 hours or 24 hours pass without a reply.
        """
        conv = self.conversations.get(order_id)
        if not conv:
            return {"error": "Order not found"}

        from .templates import get_timeout_template

        if hours == 12:
            tmpl = get_timeout_template(order_id, reminder_level=1)
            conv["history"].append({"sender": "system", "message": tmpl["body"], "timestamp": datetime.now().isoformat()})
            return {"order_id": order_id, "state": conv["state"], "action": "12h_reminder_sent", "template": tmpl}
        else:
            # 24 hours: Auto Hold
            conv["state"] = FlowState.HELD_ON_TIMEOUT
            tmpl = get_timeout_template(order_id, reminder_level=2)
            conv["history"].append({"sender": "system", "message": tmpl["body"], "timestamp": datetime.now().isoformat()})
            return {"order_id": order_id, "state": FlowState.HELD_ON_TIMEOUT, "action": "order_auto_held_prevented_rto", "template": tmpl}
