"""
Mock WhatsApp Cloud API Service & Webhook Handler.
Emulates WhatsApp Business Cloud API webhooks (Meta Graph API).
"""

from typing import Dict, Any
from .flow_manager import WhatsAppFlowManager

class MockWhatsAppService:
    def __init__(self, flow_manager: WhatsAppFlowManager = None):
        self.flow_manager = flow_manager or WhatsAppFlowManager()

    def send_initial_outreach(self, order: Dict[str, Any], action: str) -> Dict[str, Any]:
        """
        Trigger initial template message via WhatsApp API.
        """
        conv = self.flow_manager.start_flow(order, action)
        return {
            "status": "success",
            "message_id": f"wamid.{order.get('order_id')}.init",
            "recipient_phone": order.get("phone"),
            "flow_state": conv["state"],
            "sent_template": conv["last_template"]
        }

    def receive_webhook_payload(self, order_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receives simulated Meta WhatsApp webhook payload.
        Example payload:
        { "type": "button_reply", "button_id": "btn_confirm" }
        or
        { "type": "text", "body": "yes" }
        """
        text = payload.get("body") or payload.get("button_id") or ""
        res = self.flow_manager.process_incoming_message(order_id, text)
        return res

    def get_conversation_history(self, order_id: str) -> Dict[str, Any]:
        conv = self.flow_manager.conversations.get(order_id, {})
        return {
            "order_id": order_id,
            "state": conv.get("state"),
            "history": conv.get("history", [])
        }
