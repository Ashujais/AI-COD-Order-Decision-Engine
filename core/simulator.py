"""
Batch Simulation and Historical Backtesting Engine.
Evaluates the decision engine against historical order datasets (e.g. orders_sample.csv).
Computes exact business outcomes, confusion matrices, avoided RTO costs, preserved sales,
and net rupees saved.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from pathlib import Path

from .decision_engine import DecisionEngine
from .financial_model import BusinessEconomics

class BatchSimulator:
    def __init__(self, engine: DecisionEngine = None):
        self.engine = engine or DecisionEngine()
        self.economics = self.engine.economics

    def run_simulation(self, csv_path: str = "orders_sample.csv") -> Dict[str, Any]:
        df = pd.read_csv(csv_path)
        df["clean_status"] = df["final_status"].astype(str).str.strip().str.upper()

        records = df.to_dict(orient="records")
        results = []

        for rec in records:
            res = self.engine.evaluate_order(rec)
            # Flatten for reporting
            results.append({
                "order_id": rec.get("order_id"),
                "order_datetime": rec.get("order_datetime"),
                "customer_name": rec.get("customer_name"),
                "phone": rec.get("phone"),
                "address": rec.get("address"),
                "city": rec.get("city"),
                "state": rec.get("state"),
                "pincode": rec.get("pincode"),
                "order_value": rec.get("order_value"),
                "customer_prior_orders": rec.get("customer_prior_orders"),
                "customer_prior_rto": rec.get("customer_prior_rto"),
                "actual_status": rec.get("clean_status"),
                "recommended_action": res["action"],
                "risk_score": res["risk_score"],
                "reason": res["reason"],
                "address_type": res["llm_evaluation"]["address_type"],
                "is_fake_name": res["llm_evaluation"]["is_fake_name"],
                "rto_cost_avoided": res["financial_impact"]["rto_cost_avoided"],
                "margin_lost_false_cancel": res["financial_impact"]["margin_lost_false_cancel"],
                "prepaid_discount_cost": res["financial_impact"]["prepaid_discount_cost"],
                "net_financial_gain": res["financial_impact"]["net_financial_gain"]
            })

        sim_df = pd.DataFrame(results)

        # Compute Summary Statistics
        total_orders = len(sim_df)
        action_counts = sim_df["recommended_action"].value_counts().to_dict()
        action_pcts = (sim_df["recommended_action"].value_counts(normalize=True) * 100).round(1).to_dict()

        total_rto_avoided = sim_df["rto_cost_avoided"].sum()
        total_margin_lost = sim_df["margin_lost_false_cancel"].sum()
        total_prepaid_discount = sim_df["prepaid_discount_cost"].sum()
        net_financial_impact = sim_df["net_financial_gain"].sum()

        # Action Breakdown vs Historical Status
        crosstab = pd.crosstab(
            sim_df["recommended_action"],
            sim_df["actual_status"],
            margins=True
        ).to_dict()

        # Detailed bucket metrics
        bucket_stats = {}
        for action in ["Ship as-is", "Ship after confirmation", "Nudge to prepaid", "Hold / cancel"]:
            sub = sim_df[sim_df["recommended_action"] == action]
            n = len(sub)
            if n > 0:
                hist_rto_rate = (sub["actual_status"] == "RTO").mean() if "RTO" in sub["actual_status"].values else 0.0
                bucket_stats[action] = {
                    "count": n,
                    "percentage": round(n / total_orders * 100, 1),
                    "historical_rto_rate": round(hist_rto_rate * 100, 1),
                    "avg_order_value": round(sub["order_value"].mean(), 2),
                    "net_rupees": round(sub["net_financial_gain"].sum(), 2)
                }
            else:
                bucket_stats[action] = {"count": 0, "percentage": 0.0, "historical_rto_rate": 0.0, "avg_order_value": 0.0, "net_rupees": 0.0}

        return {
            "total_orders": total_orders,
            "action_counts": action_counts,
            "action_pcts": action_pcts,
            "bucket_stats": bucket_stats,
            "financial_summary": {
                "total_rto_saved_inr": round(total_rto_avoided, 2),
                "total_margin_lost_inr": round(total_margin_lost, 2),
                "total_prepaid_discounts_inr": round(total_prepaid_discount, 2),
                "net_profit_impact_inr": round(net_financial_impact, 2),
                "avg_impact_per_order_inr": round(net_financial_impact / total_orders, 2)
            },
            "crosstab": crosstab,
            "simulated_df": sim_df
        }
