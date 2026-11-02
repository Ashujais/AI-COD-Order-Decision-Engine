"""
WhatsApp Message Templates and Discount Formulas.
Supports English, Hinglish, Quick Reply Buttons, and Mathematical Verification.
"""

from typing import Dict, Any

def get_confirmation_template(order: Dict[str, Any], lang: str = "hinglish") -> Dict[str, Any]:
    """
    Template for 'Ship after confirmation'.
    """
    customer_name = order.get("customer_name", "Customer").split()[0]
    order_id = order.get("order_id", "KT000000")
    order_value = order.get("order_value", 649)
    items = order.get("items", "Haircare Bundle").replace("|", ", ")
    address = order.get("address", "Address on file")
    city = order.get("city", "")
    pincode = str(order.get("pincode", "")).replace(".0", "")

    if lang == "hinglish":
        body = (
            f"✨ *Hi {customer_name}!* Thank you for shopping with us! 🌿\n\n"
            f"Aapka Cash on Delivery order *#{order_id}* dispatch ke liye ready hai:\n"
            f"📦 *Items:* {items}\n"
            f"💵 *Total COD Amount:* ₹{order_value:,.0f}\n"
            f"📍 *Delivery Address:* {address}, {city} - {pincode}\n\n"
            f"⚠️ Delivery partner ko delay na ho, please apna order confirm karein:"
        )
    else:
        body = (
            f"✨ *Hi {customer_name}!* Thank you for your order! 🌿\n\n"
            f"Your Cash on Delivery order *#{order_id}* is ready for dispatch:\n"
            f"📦 *Items:* {items}\n"
            f"💵 *COD Amount to Pay:* ₹{order_value:,.0f}\n"
            f"📍 *Shipping Address:* {address}, {city} - {pincode}\n\n"
            f"Please confirm your order to avoid shipping delays:"
        )

    buttons = [
        {"id": "btn_confirm", "title": "Confirm Order ✅"},
        {"id": "btn_update_addr", "title": "Change Address 📍"},
        {"id": "btn_cancel", "title": "Cancel Order ❌"}
    ]

    return {
        "type": "button_template",
        "order_id": order_id,
        "language": lang,
        "body": body,
        "buttons": buttons,
        "trigger_timing": "5 minutes post-order"
    }

def get_nudge_prepaid_template(order: Dict[str, Any], discount: float = 50.0, lang: str = "hinglish") -> Dict[str, Any]:
    """
    Template for 'Nudge to prepaid'.
    """
    customer_name = order.get("customer_name", "Customer").split()[0]
    order_id = order.get("order_id", "KT000000")
    order_value = float(order.get("order_value", 649.0))
    discounted_value = max(1.0, order_value - discount)

    if lang == "hinglish":
        body = (
            f"🎉 *Special Offer on Order #{order_id}, {customer_name}!* 🎉\n\n"
            f"Abhi online pay karein via UPI/Card aur paayein *Instant ₹{discount:.0f} OFF*! ⚡\n\n"
            f"Original COD Bill: ~₹{order_value:,.0f}~\n"
            f"👉 *New Discounted Price: ₹{discounted_value:,.0f}* (You Save ₹{discount:.0f}!)\n\n"
            f"✨ *Benefits:* Zero cash hassle + Priority express shipping!\n"
            f"Kaise pay karna chahenge?"
        )
    else:
        body = (
            f"🎉 *Exclusive Offer on Order #{order_id}, {customer_name}!* 🎉\n\n"
            f"Pay online right now via UPI / Card & get *Instant ₹{discount:.0f} OFF*! ⚡\n\n"
            f"Original COD Total: ~₹{order_value:,.0f}~\n"
            f"👉 *Pay Online Total: ₹{discounted_value:,.0f}* (Save ₹{discount:.0f}!)\n\n"
            f"Enjoy instant contactless delivery and priority packaging."
        )

    buttons = [
        {"id": "btn_pay_online", "title": f"Pay ₹{discounted_value:,.0f} Online 💳"},
        {"id": "btn_keep_cod", "title": f"Keep COD at ₹{order_value:,.0f} 🚚"}
    ]

    return {
        "type": "button_template",
        "order_id": order_id,
        "language": lang,
        "body": body,
        "buttons": buttons,
        "discount_applied": discount,
        "original_price": order_value,
        "discounted_price": discounted_value,
        "trigger_timing": "2 minutes post-order"
    }

def get_timeout_template(order_id: str, reminder_level: int = 1) -> Dict[str, Any]:
    """
    Automated templates for 12h reminder and 24h timeout hold.
    """
    if reminder_level == 1:
        # 12-hour reminder
        body = (
            f"⏰ *Gentle Reminder for Order #{order_id}!* ⏰\n\n"
            f"Aapka package ready hai! Agar aap chahte hain ki package aaj hi dispatch ho, "
            f"please neeche click karke confirm karein:"
        )
        buttons = [
            {"id": "btn_confirm", "title": "Confirm Dispatch ✅"},
            {"id": "btn_cancel", "title": "Cancel Order ❌"}
        ]
    else:
        # 24-hour timeout auto-hold
        body = (
            f"⏸️ *Order #{order_id} Paused on Hold*\n\n"
            f"Since we didn't receive your confirmation within 24 hours, we have paused "
            f"your order to prevent wrong delivery. "
            f"Aap kabhi bhi 'Unpause' click karke order activate kar sakte hain:"
        )
        buttons = [
            {"id": "btn_unpause", "title": "Unpause My Order 🚀"},
            {"id": "btn_cancel", "title": "Cancel Order ❌"}
        ]

    return {
        "reminder_level": reminder_level,
        "body": body,
        "buttons": buttons
    }
