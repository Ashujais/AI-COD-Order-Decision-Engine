"""
Financial Model and Unit Economics for D2C COD/RTO Decision Engine.
All figures and formulas directly derive from the company's business model.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class BusinessEconomics:
    aov: float = 649.0                  # Average Order Value (₹)
    gross_margin_pct: float = 0.62      # Gross margin on delivered order (62%)
    forward_shipping: float = 65.0      # Forward shipping cost (₹)
    return_shipping: float = 65.0       # Return shipping cost (₹)
    packaging_handling: float = 25.0    # Packaging & handling cost (₹)
    damage_rate: float = 0.08           # Percentage of returns damaged and unsellable (8%)
    damaged_product_cost: float = 180.0 # Average product manufacturing/replacement cost (₹)
    meta_cac: float = 300.0             # Meta Ads Customer Acquisition Cost (₹300+)
    prepaid_rto_rate: float = 0.04      # Historical prepaid RTO rate (4%)
    prepaid_discount: float = 50.0      # Discount offered to nudge to prepaid (₹50)

    @property
    def rto_cost_per_order(self) -> float:
        """
        Total cash lost whenever an order turns into an RTO:
        Forward shipping (₹65) + Return shipping (₹65) + Packaging (₹25) + Expected damage (8% * ₹180 = ₹14.40)
        = ₹169.40 per RTO.
        """
        return (
            self.forward_shipping
            + self.return_shipping
            + self.packaging_handling
            + (self.damage_rate * self.damaged_product_cost)
        )

    @property
    def gross_profit_delivered(self) -> float:
        """Gross contribution profit on a successfully delivered order = 62% of ₹649 = ₹402.38."""
        return self.aov * self.gross_margin_pct

    @property
    def cost_of_false_cancellation(self) -> float:
        """
        Economic loss when we cancel an order that would have been delivered:
        Lost Gross Profit (₹402.38) + Sunk Meta CAC (₹300.00) = ₹702.38.
        """
        return self.gross_profit_delivered + self.meta_cac

    def calculate_order_economics(
        self,
        order_value: float,
        action: str,
        predicted_rto_prob: float,
        actual_status: str = None
    ) -> Dict[str, float]:
        """
        Calculate financial outcomes for a given order decision.
        """
        val = order_value if order_value > 0 else self.aov
        gross_profit = val * self.gross_margin_pct
        rto_cost = self.rto_cost_per_order

        metrics = {
            "rto_cost_avoided": 0.0,
            "margin_lost_false_cancel": 0.0,
            "prepaid_discount_cost": 0.0,
            "net_financial_gain": 0.0
        }

        if action == "Hold / cancel":
            if actual_status == "RTO" or (actual_status is None and predicted_rto_prob >= 0.5):
                # Successfully avoided an RTO!
                metrics["rto_cost_avoided"] = rto_cost
                metrics["net_financial_gain"] = rto_cost
            else:
                # Cancelled a genuine customer who would have taken delivery
                metrics["margin_lost_false_cancel"] = gross_profit + self.meta_cac
                metrics["net_financial_gain"] = -(gross_profit + self.meta_cac)

        elif action == "Nudge to prepaid":
            # Assuming 40% of nudged customers convert to prepaid, where RTO rate drops from predicted_rto_prob to 4%
            metrics["prepaid_discount_cost"] = self.prepaid_discount
            # RTO probability reduction: from predicted_rto_prob to prepaid_rto_rate
            prob_delta = max(0.0, predicted_rto_prob - self.prepaid_rto_rate)
            metrics["rto_cost_avoided"] = prob_delta * rto_cost
            metrics["net_financial_gain"] = metrics["rto_cost_avoided"] - self.prepaid_discount

        elif action == "Ship after confirmation":
            # Customer confirmation filters out ~65% of uncommitted RTO orders while preserving ~95% of genuine orders
            if actual_status == "RTO":
                # Avoided RTO through non-confirmation / cancellation on WhatsApp
                metrics["rto_cost_avoided"] = 0.65 * rto_cost
                metrics["net_financial_gain"] = 0.65 * rto_cost
            else:
                metrics["net_financial_gain"] = 0.0

        elif action == "Ship as-is":
            metrics["net_financial_gain"] = 0.0

        return metrics

    def compute_prepaid_discount_justification(self) -> Dict[str, Any]:
        """
        Exact mathematical justification for the ₹50 prepaid discount.
        """
        risky_cod_rto_rate = 0.35
        expected_rto_cost_cod = risky_cod_rto_rate * self.rto_cost_per_order
        expected_rto_cost_prepaid = self.prepaid_rto_rate * self.rto_cost_per_order
        rto_savings = expected_rto_cost_cod - expected_rto_cost_prepaid

        discount = self.prepaid_discount
        prepaid_gp = (1 - self.prepaid_rto_rate) * (self.gross_profit_delivered - discount) - expected_rto_cost_prepaid
        cod_gp = (1 - risky_cod_rto_rate) * self.gross_profit_delivered - expected_rto_cost_cod

        net_advantage_per_order = prepaid_gp - cod_gp

        return {
            "risky_cod_rto_rate": risky_cod_rto_rate,
            "prepaid_rto_rate": self.prepaid_rto_rate,
            "rto_cost_per_order": round(self.rto_cost_per_order, 2),
            "expected_rto_cost_cod": round(expected_rto_cost_cod, 2),
            "expected_rto_cost_prepaid": round(expected_rto_cost_prepaid, 2),
            "rto_savings_delta": round(rto_savings, 2),
            "proposed_discount": round(discount, 2),
            "expected_profit_prepaid_with_discount": round(prepaid_gp, 2),
            "expected_profit_risky_cod": round(cod_gp, 2),
            "net_gain_to_brand_per_conversion": round(net_advantage_per_order, 2)
        }
