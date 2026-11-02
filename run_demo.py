"""
Comprehensive CLI Demo & Batch Simulation Runner.
Run: python run_demo.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pandas as pd

from core.decision_engine import DecisionEngine
from core.simulator import BatchSimulator
from whatsapp.flow_manager import WhatsAppFlowManager
from core.financial_model import BusinessEconomics

def main():
    print("=" * 75)
    print("   COD GUARDIAN: AI-POWERED RTO PREDICTION & DECISION ENGINE")
    print("   Take-Home Assignment Evaluation & Live Demonstration")
    print("=" * 75)

    engine = DecisionEngine()
    simulator = BatchSimulator(engine)

    print("\n[Step 1/4] Running Batch Simulation on 'orders_sample.csv' (2,018 past COD orders)...")
    res = simulator.run_simulation("orders_sample.csv")
    fin = res["financial_summary"]
    buckets = res["bucket_stats"]

    print("\n" + "=" * 75)
    print("☀️ FOUNDER'S MORNING BRIEF SUMMARY")
    print("=" * 75)
    print(f"Total Orders Evaluated:                 {res['total_orders']:,}")
    print(f"Estimated ₹ Saved from Avoided RTOs:    ₹{fin['total_rto_saved_inr']:,.2f}")
    print(f"Estimated ₹ Lost from False Cancels:    ₹{fin['total_margin_lost_inr']:,.2f}")
    print(f"Prepaid Discounts Invested:             ₹{fin['total_prepaid_discounts_inr']:,.2f}")
    print(f"---------------------------------------------------------------------------")
    print(f"🚀 NET FINANCIAL IMPACT:                +₹{fin['net_profit_impact_inr']:,.2f}")
    print(f"   Average Net Gain Per Order:          +₹{fin['avg_impact_per_order_inr']:.2f}")
    print("=" * 75)

    print("\n[Step 2/4] Breakdown Across the 4 Buckets:")
    print("-" * 75)
    print(f"{'Action Bucket':<28} | {'Orders':<8} | {'% Total':<8} | {'Hist RTO %':<10} | {'Avg Value':<10} | {'Net Impact (₹)'}")
    print("-" * 75)
    for action, s in buckets.items():
        print(f"{action:<28} | {s['count']:<8} | {s['percentage']:<7.1f}% | {s['historical_rto_rate']:<9.1f}% | ₹{s['avg_order_value']:<9.0f} | ₹{s['net_rupees']:>10,.0f}")
    print("-" * 75)

    print("\n[Step 3/4] Sample Decisions with Operations-Friendly Plain-English Explanations:")
    sim_df = res["simulated_df"]
    sample_picks = [
        sim_df[sim_df["recommended_action"] == "Ship as-is"].iloc[0],
        sim_df[sim_df["recommended_action"] == "Ship after confirmation"].iloc[0],
        sim_df[sim_df["recommended_action"] == "Nudge to prepaid"].iloc[0],
        sim_df[sim_df["recommended_action"] == "Hold / cancel"].iloc[0]
    ]

    for row in sample_picks:
        print(f"\nOrder ID:    {row['order_id']} | Value: ₹{row['order_value']} | State: {row['state']}")
        print(f"Customer:    {row['customer_name']} (Phone: {row['phone']})")
        print(f"Address:     {row['address']}, {row['city']}")
        print(f"Prior Stats: {row['customer_prior_orders']} orders, {row['customer_prior_rto']} RTOs")
        print(f"--> Action:  [{row['recommended_action'].upper()}] (Risk: {row['risk_score']:.1%})")
        print(f"--> Reason:  {row['reason']}")

    print("\n" + "=" * 75)
    print("[Step 4/4] WhatsApp Flow & Prepaid Discount Verification:")
    print("=" * 75)
    flow = WhatsAppFlowManager()
    order_sample = sample_picks[1].to_dict()
    conv = flow.start_flow(order_sample, "Ship after confirmation")
    print(f"\n1. Outbound WhatsApp Message (Triggered 5m post-order):")
    print(f"{conv['history'][0]['message']}")

    print("\n2. Customer replies 'Yes, confirm dispatch':")
    reply1 = flow.process_incoming_message(order_sample["order_id"], "Yes, confirm dispatch")
    print(f"Status: {reply1['state']}")
    print(f"Bot: {reply1['reply_text']}")

    print("\n3. Testing 24-Hour Inaction Timeout on another order:")
    timeout_order = sample_picks[2].to_dict()
    flow.start_flow(timeout_order, "Ship after confirmation")
    timeout_res = flow.simulate_timeout(timeout_order["order_id"], 24)
    print(f"Status after 24h: {timeout_res['state']}")
    print(f"Bot Notification: {timeout_res['template']['body']}")

    econ = BusinessEconomics()
    proof = econ.compute_prepaid_discount_justification()
    print("\n4. Mathematical Proof for ₹50 Prepaid Discount:")
    print(f"   - Expected RTO Cost on Risky COD (35% RTO):  ₹{proof['expected_rto_cost_cod']}")
    print(f"   - Expected RTO Cost on Prepaid (4% RTO):     ₹{proof['expected_rto_cost_prepaid']}")
    print(f"   - Direct RTO Shipping Savings Delta:         ₹{proof['rto_savings_delta']}")
    print(f"   - Proposed Upfront Discount:                 ₹{proof['proposed_discount']}")
    print(f"   - Net Profit on Prepaid with Discount:       ₹{proof['expected_profit_prepaid_with_discount']}")
    print(f"   - Net Profit on Risky COD:                   ₹{proof['expected_profit_risky_cod']}")
    print(f"   --> NET GAIN PER CONVERTED ORDER:            +₹{proof['net_gain_to_brand_per_conversion']:.2f}")

    print("\n" + "=" * 75)
    print("✅ All systems operational. To launch the visual UI dashboard, run:")
    print("   python run_dashboard.py   (or: streamlit run dashboard/app.py)")
    print("=" * 75)

if __name__ == "__main__":
    main()
