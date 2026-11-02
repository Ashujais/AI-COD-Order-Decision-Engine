import pandas as pd
import numpy as np
from core.decision_engine import DecisionEngine
from core.simulator import BatchSimulator

# Let's test different configurations
df = pd.read_csv('orders_sample.csv')
df['clean_status'] = df['final_status'].astype(str).str.strip().str.upper()

print("Testing refined rules...")
engine = DecisionEngine()
sim = BatchSimulator(engine)
res = sim.run_simulation('orders_sample.csv')
print("Action Counts:", res['action_counts'])
print("Action %:", res['action_pcts'])
print("Financials:", res['financial_summary'])
for action, stats in res['bucket_stats'].items():
    print(f"{action}: Count={stats['count']}, Hist RTO={stats['historical_rto_rate']}%, Net ₹={stats['net_rupees']}")
