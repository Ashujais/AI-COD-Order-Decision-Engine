import pandas as pd
import re

df = pd.read_csv('orders_sample.csv')
df['clean_status'] = df['final_status'].astype(str).str.strip().str.upper()
df = df[df['clean_status'].isin(['DELIVERED', 'RTO'])].copy()
df['is_rto'] = (df['clean_status'] == 'RTO').astype(int)

# Check customer names
print("Unique customer names with test/weird patterns:")
print(df[df['customer_name'].str.contains(r'test|asdf|qwerty|xyz|admin', case=False)]['customer_name'].value_counts())

print("\nLet's check other weird names:")
print(df[df['customer_name'].str.split().str.len() == 1]['customer_name'].value_counts())

print("\nAddress types:")
# Categorize address types
def categorize_address(addr):
    a = str(addr).strip()
    if a == '.': return 'Dummy: dot'
    if a.lower() == 'xyz': return 'Dummy: xyz'
    if a.lower() == 'call me': return 'Dummy: call me'
    if a.lower() == 'home': return 'Dummy: home'
    if a.lower() == 'near station': return 'Incomplete: near station'
    if len(a.split()) == 1: return 'Single word / city only'
    if len(a) < 20: return 'Very short (<20)'
    if re.search(r'ke paas|ke saamne|ke andar|se left|ph krke aana|ghar ka naam', a, re.I):
        return 'Hinglish / Landmark colloquial'
    if re.search(r'flat|apartment|house no|sector|nagar|road|mandir|school|opp\.|near', a, re.I):
        return 'Structured standard address'
    return 'Other'

df['addr_category'] = df['address'].apply(categorize_address)
print(df.groupby('addr_category').agg(orders=('is_rto', 'count'), rto_rate=('is_rto', 'mean'), rto_count=('is_rto', 'sum')).sort_values('orders', ascending=False))
