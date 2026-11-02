"""
Core Decision Engine for COD Orders.
Combines deterministic business rules, unit economics, and LLM-evaluated address/name signals.
Produces one of four actions:
1. Ship as-is
2. Ship after confirmation
3. Nudge to prepaid
4. Hold / cancel
Each decision includes an actionable, plain-English explanation for operations staff.
Thresholds are dynamically loaded from config.json.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

from .llm_evaluator import LLMEvaluator
from .financial_model import BusinessEconomics

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

class DecisionEngine:
    def __init__(self, config_path: Optional[str] = None, llm_api_key: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self.economics = BusinessEconomics(**self.config.get("financials", {}))
        self.llm = LLMEvaluator(api_key=llm_api_key)

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def reload_config(self, new_config: Optional[Dict[str, Any]] = None):
        if new_config:
            self.config = new_config
        else:
            self.config = self._load_config()
        self.economics = BusinessEconomics(**self.config.get("financials", {}))

    def evaluate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single order dictionary and return decision, risk score, and plain-English reason.
        """
        thresholds = self.config.get("decision_thresholds", {})
        cancel_cutoff = thresholds.get("cancel_risk_cutoff", 0.75)
        nudge_cutoff = thresholds.get("nudge_prepaid_risk_cutoff", 0.45)
        confirm_cutoff = thresholds.get("whatsapp_confirm_risk_cutoff", 0.25)
        max_prior_rto = thresholds.get("max_allowed_prior_rto", 1)
        high_val_threshold = thresholds.get("high_order_value_threshold", 1500.0)
        high_risk_states = set(thresholds.get("high_risk_states", ["Bihar", "Uttar Pradesh", "Madhya Pradesh"]))

        # Extract features
        order_id = str(order.get("order_id", "UNKNOWN"))
        customer_name = str(order.get("customer_name", "")).strip()
        phone = str(order.get("phone", "")).strip()
        address = str(order.get("address", "")).strip()
        city = str(order.get("city", "")).strip() if order.get("city") is not None else ""
        state = str(order.get("state", "")).strip() if order.get("state") is not None else ""
        pincode = order.get("pincode")
        order_val = float(order.get("order_value", self.economics.aov))
        prior_orders = int(order.get("customer_prior_orders", 0))
        prior_rto = int(order.get("customer_prior_rto", 0))
        utm_source = str(order.get("utm_source", "direct")).lower()

        # Step 1: LLM Evaluation of Address & Name
        llm_eval = self.llm.evaluate_order(customer_name, address, city, state, pincode)
        addr_score = llm_eval["address_quality_score"]
        addr_type = llm_eval["address_type"]
        is_fake_name = llm_eval["is_fake_name"]

        # Phone Number Format Validation (Code/Maths)
        digits_phone = re.sub(r'[^0-9]', '', phone)
        if len(digits_phone) == 12 and digits_phone.startswith('91'):
            digits_phone = digits_phone[2:]
        has_invalid_phone = (len(digits_phone) != 10) or (len(set(digits_phone)) <= 2)

        # Baseline COD RTO risk is ~28%
        risk_score = 0.28
        risk_factors = []
        positive_factors = []

        # Customer History Heuristics
        if prior_rto > max_prior_rto:
            risk_score += 0.45
            risk_factors.append(f"Repeat customer with {prior_rto} prior RTOs (empirical 76.5% failure rate)")
        elif prior_orders > 0 and prior_rto == 0:
            risk_score -= 0.16
            positive_factors.append(f"Loyal repeat buyer with {prior_orders} delivered orders and zero returns")
        elif prior_orders == 0:
            risk_score += 0.04
            risk_factors.append("First-time buyer")

        # Address Quality (from LLM)
        if addr_type == "dummy":
            risk_score += 0.45
            risk_factors.append(f"Placeholder/incomplete address ('{address}')")
        elif addr_type == "vague":
            risk_score += 0.20
            risk_factors.append("Vague address missing house or colony details")
        elif addr_type == "hinglish_landmark":
            risk_score += 0.04
            positive_factors.append("Colloquial Hinglish directions with local landmark")
        elif addr_type == "structured":
            risk_score -= 0.08
            positive_factors.append("Complete structured address")

        # Name Authenticity (from LLM)
        if is_fake_name:
            risk_score += 0.35
            risk_factors.append(f"Suspicious bot/test name ('{customer_name}')")

        # Geography
        if state in high_risk_states:
            risk_score += 0.14
            risk_factors.append(f"High-RTO geographic region ({state})")
        elif state in ["Maharashtra", "Tamil Nadu", "Delhi"]:
            risk_score -= 0.08
            positive_factors.append(f"Low-RTO metro region ({state})")

        # Order Value
        if order_val >= high_val_threshold:
            risk_score += 0.12
            risk_factors.append(f"High order value of ₹{order_val:,.0f} (elevated COD default risk)")

        if has_invalid_phone:
            risk_score += 0.20
            risk_factors.append(f"Invalid or repeated-digit phone number ('{phone}')")

        # Bound risk score between 0.02 and 0.98
        risk_score = max(0.02, min(0.98, risk_score))

        # Action Decision Logic & Operational Explanation
        # Action 4: Hold / cancel
        # STRICT CRITERIA: Serial RTO abusers (>=2) OR Bot/Test orders (fake name + dummy address)
        if (prior_rto > max_prior_rto) or (is_fake_name and (addr_type == "dummy" or has_invalid_phone)):
            action = "Hold / cancel"
            if prior_rto > max_prior_rto:
                reason = f"Cancelled: Customer has {prior_rto} prior return history (76.5% RTO rate). COD suspended to stop serial returns."
            else:
                reason = f"Cancelled: Bot/test order detected with fake name ('{customer_name}') and unusable address ('{address}'). Avoiding ₹{self.economics.rto_cost_per_order:.0f} wasted shipping & return costs."

        # Action 3: Nudge to prepaid
        # High value orders (> ₹1,500) OR high-risk state with order value >= ₹1,000 OR prior RTO == 1
        elif (order_val >= high_val_threshold) or (state in high_risk_states and order_val >= 900.0) or (prior_rto == 1 and order_val >= 600.0):
            action = "Nudge to prepaid"
            discount = self.config.get("prepaid_incentive", {}).get("discount_amount", 50.0)
            reason = f"Nudge to prepaid: High value COD risk (₹{order_val:,.0f} in {state}). Offering ₹{discount:.0f} discount to convert to prepaid (4% RTO) and protect gross margin."

        # Action 2: Ship after confirmation
        # Incomplete/dummy addresses with genuine names, Hinglish landmark addresses, vague addresses, or first-time buyers in high-risk states
        elif addr_type in ["dummy", "vague", "hinglish_landmark"] or has_invalid_phone or (prior_orders == 0 and state in high_risk_states) or risk_score >= confirm_cutoff:
            action = "Ship after confirmation"
            if addr_type == "dummy":
                reason = f"Ship after confirmation: Incomplete address ('{address}') from potential genuine buyer. WhatsApp prompt sent to collect full address before shipping."
            elif addr_type == "hinglish_landmark":
                reason = f"Ship after confirmation: Colloquial Hinglish landmark address. WhatsApp confirmation requested to ensure delivery availability."
            elif has_invalid_phone:
                reason = f"Ship after confirmation: Phone number format anomaly ('{phone}'). Verifying active WhatsApp contact before dispatch."
            else:
                reason = f"Ship after confirmation: First-time COD buyer in {state}. Automated WhatsApp check confirms buyer intent and availability."

        # Action 1: Ship as-is
        # Low risk, verified address, repeat customer or clean first-timer in low/medium risk states
        else:
            action = "Ship as-is"
            if prior_orders > 0 and prior_rto == 0:
                reason = f"Ship as-is: Verified repeat buyer ({prior_orders} prior orders, 0 returns). Fast-tracked for immediate dispatch."
            else:
                reason = f"Ship as-is: Low risk profile ({risk_score:.0%}), complete residential address in {state}. Standard dispatch."

        return {
            "order_id": order_id,
            "action": action,
            "risk_score": round(risk_score, 3),
            "reason": reason,
            "llm_evaluation": {
                "address_quality_score": addr_score,
                "address_type": addr_type,
                "address_reason": llm_eval["address_reason"],
                "is_fake_name": is_fake_name,
                "name_reason": llm_eval["name_reason"]
            },
            "financial_impact": self.economics.calculate_order_economics(
                order_value=order_val,
                action=action,
                predicted_rto_prob=risk_score,
                actual_status=order.get("clean_status") or order.get("final_status")
            )
        }
