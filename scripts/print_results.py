import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from core.decision_engine import DecisionEngine
from core.simulator import BatchSimulator

engine = DecisionEngine()
sim = BatchSimulator(engine)
res = sim.run_simulation('orders_sample.csv')

print("=== BUCKET SUMMARY ===")
for action, stats in res['bucket_stats'].items():
    print(f"{action}: Count={stats['count']} ({stats['percentage']}%), Hist RTO={stats['historical_rto_rate']}%, Avg Val=₹{stats['avg_order_value']:.0f}, Net Impact=₹{stats['net_rupees']:,.0f}")

print("\n=== OVERALL FINANCIAL IMPACT ===")
for k, v in res['financial_summary'].items():
    print(f"{k}: {v}")

print("\n=== CONFUSION MATRIX (Action vs Actual Status) ===")
sim_df = res['simulated_df']
print(pd.crosstab(sim_df['recommended_action'], sim_df['actual_status'], margins=True))
