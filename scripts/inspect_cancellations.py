import pandas as pd
from core.decision_engine import DecisionEngine
from core.simulator import BatchSimulator

# Let's inspect orders that got "Hold / cancel"
engine = DecisionEngine()
sim = BatchSimulator(engine)
res = sim.run_simulation('orders_sample.csv')
sim_df = res['simulated_df']

cancelled = sim_df[sim_df['recommended_action'] == 'Hold / cancel']
print("Cancelled orders count:", len(cancelled))
print("Cancelled delivered count:", (cancelled['actual_status'] == 'DELIVERED').sum())
print("Cancelled RTO count:", (cancelled['actual_status'] == 'RTO').sum())
print("\nSample cancelled that were delivered:")
print(cancelled[cancelled['actual_status'] == 'DELIVERED'][['customer_name', 'phone', 'address', 'city', 'state', 'order_value', 'reason']].head(10).to_string())
