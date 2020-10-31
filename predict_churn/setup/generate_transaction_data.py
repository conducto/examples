"""
We didn't have real
Generate artificial transaction data from the customer data, in order to show
how to do a join in Conducto.
"""

import pandas as pd
import random


df = pd.read_csv("../data/customer_data.csv")

transactions = []
for idx, row in df.iterrows():
    for i in range(1 + int(random.expovariate(1/3))):
        transactions.append({
            "TransactionId": 100000 + len(transactions),
            "CustomerId": row.CustomerId,
            "Amount": random.gauss(0, 200)
        })

df2 = pd.DataFrame.from_records(transactions)
df2.to_csv("../data/transaction_data.csv", index=False)