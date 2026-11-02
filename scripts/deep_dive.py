import pandas as pd
import numpy as np

df = pd.read_csv('orders_sample.csv')
df['clean_status'] = df['final_status'].astype(str).str.strip().str.upper()
df = df[df['clean_status'].isin(['DELIVERED', 'RTO'])].copy()
df['is_rto'] = (df['clean_status'] == 'RTO').astype(int)

print("=== DEEP DATA DIVE ===")
# 1. Prior RTO count
print("\n--- Prior RTO Breakdown ---")
for rto_cnt in sorted(df['customer_prior_rto'].unique()):
    sub = df[df['customer_prior_rto'] == rto_cnt]
    print(f"Prior RTO = {rto_cnt}: {len(sub)} orders, RTO rate = {sub['is_rto'].mean():.2%}")

# 2. Prior orders == 0 vs > 0
print("\n--- First time vs Repeat Customers ---")
first_timers = df[df['customer_prior_orders'] == 0]
repeat = df[df['customer_prior_orders'] > 0]
print(f"First-time buyers: {len(first_timers)} orders ({len(first_timers)/len(df):.1%}), RTO rate = {first_timers['is_rto'].mean():.2%}")
print(f"Repeat buyers: {len(repeat)} orders ({len(repeat)/len(df):.1%}), RTO rate = {repeat['is_rto'].mean():.2%}")

repeat_no_rto = repeat[repeat['customer_prior_rto'] == 0]
repeat_with_rto = repeat[repeat['customer_prior_rto'] > 0]
print(f"  Repeat with 0 prior RTO: {len(repeat_no_rto)} orders, RTO rate = {repeat_no_rto['is_rto'].mean():.2%}")
print(f"  Repeat with >=1 prior RTO: {len(repeat_with_rto)} orders, RTO rate = {repeat_with_rto['is_rto'].mean():.2%}")

# 3. State-level RTO
print("\n--- State-Level RTO ---")
state_df = df.groupby('state').agg(
    orders=('is_rto', 'count'),
    rto_cnt=('is_rto', 'sum'),
    rto_rate=('is_rto', 'mean')
).sort_values('rto_rate', ascending=False)
print(state_df)

# 4. Courier-level RTO within same state
print("\n--- Courier performance ---")
print(df.groupby('courier').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

# 5. Order Value distribution and RTO
print("\n--- High vs Low Order Value ---")
print(df.groupby(pd.cut(df['order_value'], [0, 500, 1000, 1500, 2000, 3500])).agg(
    orders=('is_rto', 'count'),
    rto_rate=('is_rto', 'mean')
))

# 6. Combined Risk factors
print("\n--- Fake names vs Real names ---")
fake_names = ['test', 'asdf', 'qwerty', 'xyz', 'admin', 'na', 'aaa', 'abc', 'test order']
df['is_fake_name'] = df['customer_name'].str.lower().str.strip().isin(fake_names) | df['customer_name'].str.lower().str.contains(r'test|asdf|qwerty', regex=True)
print(df.groupby('is_fake_name').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

# 7. Dummy Address vs Real
dummy_addrs = ['.', 'xyz', 'home', 'call me', 'near station']
df['is_dummy_addr'] = df['address'].str.lower().str.strip().isin(dummy_addrs) | (df['address'].str.strip().str.len() <= 3) | (df['address'].str.strip().str.lower() == df['city'].str.strip().str.lower())
print(df.groupby('is_dummy_addr').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

# 8. Both fake name and dummy address
print("\n--- Both fake name and dummy address ---")
print(pd.crosstab(df['is_fake_name'], df['is_dummy_addr'], values=df['is_rto'], aggfunc=['count', 'mean']))

# 9. Phone number issues
df['phone_clean'] = df['phone'].astype(str).str.replace(r'[^0-9]', '', regex=True)
df['phone_len'] = df['phone_clean'].str.len()
print("\n--- Phone length issues ---")
print(df.groupby('phone_len').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))
