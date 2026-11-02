import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv('orders_sample.csv')
df['clean_status'] = df['final_status'].astype(str).str.strip().str.upper()

# Let's inspect serial RTOs and test orders
print("--- Repeat RTO >= 2 ---")
rto2 = df[df['customer_prior_rto'] >= 2]
print(f"Total: {len(rto2)}, Delivered: {(rto2['clean_status']=='DELIVERED').sum()}, RTO: {(rto2['clean_status']=='RTO').sum()}, RTO Rate: {(rto2['clean_status']=='RTO').mean():.1%}")

print("\n--- Fake name + dummy address ---")
fake_names = ['test', 'test order', 'asdf', 'qwerty', 'xyz', 'admin', 'user', 'na', 'aaa', 'abc']
is_fake_name = df['customer_name'].str.lower().str.strip().isin(fake_names) | df['customer_name'].str.lower().str.contains(r'test|asdf|qwerty', regex=True)
is_dummy_addr = df['address'].str.lower().str.strip().isin(['.', 'xyz', 'home', 'call me', 'near station']) | (df['address'].str.strip().str.len() <= 2)

both = df[is_fake_name & is_dummy_addr]
print(f"Total both: {len(both)}, Delivered: {(both['clean_status']=='DELIVERED').sum()}, RTO: {(both['clean_status']=='RTO').sum()}, RTO Rate: {(both['clean_status']=='RTO').mean():.1%}")

print("\n--- Fake name alone ---")
fake_only = df[is_fake_name & ~is_dummy_addr]
print(f"Total: {len(fake_only)}, Delivered: {(fake_only['clean_status']=='DELIVERED').sum()}, RTO: {(fake_only['clean_status']=='RTO').sum()}, RTO Rate: {(fake_only['clean_status']=='RTO').mean():.1%}")

print("\n--- Dummy address alone (with real name) ---")
dummy_only = df[~is_fake_name & is_dummy_addr]
print(f"Total: {len(dummy_only)}, Delivered: {(dummy_only['clean_status']=='DELIVERED').sum()}, RTO: {(dummy_only['clean_status']=='RTO').sum()}, RTO Rate: {(dummy_only['clean_status']=='RTO').mean():.1%}")
