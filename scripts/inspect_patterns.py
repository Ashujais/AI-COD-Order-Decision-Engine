import pandas as pd
import re

df = pd.read_csv('orders_sample.csv')
df['clean_status'] = df['final_status'].astype(str).str.strip().str.upper()
df = df[df['clean_status'].isin(['DELIVERED', 'RTO'])].copy()
df['is_rto'] = (df['clean_status'] == 'RTO').astype(int)

# Let's inspect addresses for RTO vs Delivered
print("Sample RTO addresses (short or suspicious):")
rto_samples = df[df['is_rto'] == 1][['customer_name', 'phone', 'address', 'city', 'state', 'pincode', 'customer_prior_orders', 'customer_prior_rto', 'order_value']].head(20)
print(rto_samples.to_string())

print("\nSample short addresses:")
print(df[df['address'].str.len() <= 20][['address', 'clean_status', 'customer_name']].head(15))

print("\nSample suspicious names:")
suspicious_names = df[df['customer_name'].str.lower().str.contains('test|asdf|qwerty|xyz|admin|user|fake|null', regex=True)]
print(suspicious_names[['customer_name', 'address', 'clean_status']].head(15))

print("\nCheck address patterns (e.g. keywords like 'near', 'behind', 'opp', 'flat', 'house', 'road', Hinglish terms like 'ke samne', 'ke pass', 'gali', 'ward'):")
keywords = ['near', 'behind', 'opp', 'opposite', 'flat', 'house', 'floor', 'room', 'road', 'gali', 'nagar', 'colony', 'ke pass', 'ke samne', 'mandir', 'school', 'hospital']
for kw in keywords:
    has_kw = df['address'].str.lower().str.contains(kw)
    cnt = has_kw.sum()
    rto = df[has_kw]['is_rto'].mean() if cnt > 0 else 0
    print(f"Keyword '{kw}': count={cnt}, RTO rate={rto:.2%}")

print("\nCheck address length distribution details:")
print(df['address'].str.len().describe())

print("\nCheck phone formats:")
print("Non-10 digit phones:")
print(df[df['phone'].str.len() != 10][['phone', 'clean_status']].head(10))

print("\nCheck items column:")
print(df['items'].value_counts().head(15))
print("\nItems vs RTO:")
print(df.groupby('items').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean')).sort_values('orders', ascending=False).head(15))
