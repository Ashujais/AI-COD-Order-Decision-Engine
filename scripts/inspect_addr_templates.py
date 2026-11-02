import pandas as pd
df = pd.read_csv('orders_sample.csv')

# Let's inspect unique addresses with length < 25
print("Addresses with len < 25:")
short_addr = df[df['address'].str.len() < 25]
print(short_addr['address'].value_counts())
print("\nRTO rate for short addresses (<25 chars):")
short_addr_clean = short_addr[short_addr['final_status'].str.strip().str.upper().isin(['DELIVERED', 'RTO'])]
print(short_addr_clean.groupby('address')['final_status'].value_counts(normalize=True))

print("\nAll address length value counts:")
print(df['address'].str.len().value_counts().sort_index())
