import pandas as pd
import numpy as np

df = pd.read_csv('orders_sample.csv')
df['clean_status'] = df['final_status'].astype(str).str.strip().str.upper()
# filter out IN_TRANSIT for analysis
df = df[df['clean_status'].isin(['DELIVERED', 'RTO'])].copy()
df['is_rto'] = (df['clean_status'] == 'RTO').astype(int)

total_orders = len(df)
base_rto_rate = df['is_rto'].mean()
print(f"Total labeled orders: {total_orders}, Overall RTO Rate: {base_rto_rate:.2%}")

print("\n--- 1. PRIOR HISTORY ---")
print("customer_prior_orders value counts:")
print(df.groupby('customer_prior_orders').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\ncustomer_prior_rto value counts:")
print(df.groupby('customer_prior_rto').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\nCross tab prior orders vs prior rto:")
print(pd.crosstab(df['customer_prior_orders'], df['customer_prior_rto'], values=df['is_rto'], aggfunc=['count', 'mean']))

print("\n--- 2. UTM SOURCE ---")
print(df.groupby('utm_source').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')).sort_values('orders', ascending=False))

print("\n--- 3. COURIER ---")
print(df.groupby('courier').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')).sort_values('orders', ascending=False))

print("\n--- 4. ORDER VALUE & NUM ITEMS ---")
print(df.groupby('num_items').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean'), avg_value=('order_value', 'mean')))
df['val_bin'] = pd.qcut(df['order_value'], 5, duplicates='drop')
print(df.groupby('val_bin', observed=False).agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\n--- 5. ORDER DATETIME (HOUR OF DAY) ---")
df['order_datetime'] = pd.to_datetime(df['order_datetime'])
df['hour'] = df['order_datetime'].dt.hour
df['day_name'] = df['order_datetime'].dt.day_name()
print("Hourly RTO:")
hourly = df.groupby('hour').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean'))
print(hourly[hourly['orders'] > 20].to_string())

print("\nLate night (0-5 AM) vs rest:")
df['is_late_night'] = df['hour'].isin([0, 1, 2, 3, 4, 5])
print(df.groupby('is_late_night').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\n--- 6. CUSTOMER NAME ANALYSIS ---")
df['name_len'] = df['customer_name'].astype(str).str.strip().str.len()
df['name_words'] = df['customer_name'].astype(str).str.strip().str.split().str.len()
print("Name word count:")
print(df.groupby('name_words').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

# Check suspicious names (e.g. 'test', 'asdf', numbers, repeated chars)
import re
def is_suspicious_name(name):
    s = str(name).strip().lower()
    if len(s) <= 3:
        return 'Too short (<=3)'
    if re.search(r'(test|asdf|qwerty|xyz|admin|user|fake|null|none)', s):
        return 'Gibberish/Test keyword'
    if re.search(r'[0-9]', s):
        return 'Contains digits'
    if len(set(s.replace(' ', ''))) <= 2:
        return 'Repeated chars'
    if len(s.split()) == 1 and len(s) < 5:
        return 'Single short name'
    return 'Normal'

df['name_check'] = df['customer_name'].apply(is_suspicious_name)
print(df.groupby('name_check').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\n--- 7. ADDRESS ANALYSIS ---")
df['addr_len'] = df['address'].astype(str).str.strip().str.len()
df['addr_words'] = df['address'].astype(str).str.strip().str.split().str.len()
df['addr_has_digits'] = df['address'].astype(str).str.contains(r'[0-9]').astype(int)

df['addr_len_bin'] = pd.cut(df['addr_len'], bins=[0, 15, 30, 50, 100, 300])
print("Address length vs RTO:")
print(df.groupby('addr_len_bin', observed=False).agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\nAddress has numbers (house/flat/street nr) vs RTO:")
print(df.groupby('addr_has_digits').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))

print("\n--- 8. PINCODE ANALYSIS ---")
print("Null pincodes count:", df['pincode'].isna().sum())
if df['pincode'].isna().sum() > 0:
    print("Null pincode RTO rate:", df[df['pincode'].isna()]['is_rto'].mean())

pincode_stats = df.groupby('pincode').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean'))
print(f"Total unique pincodes: {len(pincode_stats)}")
print("Pincodes with >= 5 orders:", (pincode_stats['orders'] >= 5).sum())
print("Top 10 highest volume pincodes:")
print(pincode_stats.sort_values('orders', ascending=False).head(10))

print("\n--- 9. STATE ANALYSIS ---")
state_stats = df.groupby('state').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')).sort_values('orders', ascending=False)
print("Top states by volume:")
print(state_stats.head(15))
print("States with worst RTO (min 10 orders):")
print(state_stats[state_stats['orders'] >= 10].sort_values('rto_rate', ascending=False).head(10))
print("States with best RTO (min 10 orders):")
print(state_stats[state_stats['orders'] >= 10].sort_values('rto_rate', ascending=True).head(10))

print("\n--- 10. PHONE ANALYSIS ---")
def check_phone(p):
    s = re.sub(r'[^0-9]', '', str(p))
    if len(s) == 12 and s.startswith('91'):
        s = s[2:]
    if len(s) != 10:
        return 'Invalid length'
    if s[0] not in ['6', '7', '8', '9']:
        return 'Invalid starting digit'
    if len(set(s)) <= 2:
        return 'Fake repeated digits'
    return 'Valid'

df['phone_check'] = df['phone'].apply(check_phone)
print(df.groupby('phone_check').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')))
