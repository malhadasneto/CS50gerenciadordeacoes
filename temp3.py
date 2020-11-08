import requests
import re
import psycopg2

DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"

# second, now we have to think in months, not sales. and include daytrade = -1 (daytrade_a and b)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
daytrade = daytrade_a = daytrade_b = 1
id = 1

cur.execute(
    "SELECT DISTINCT transacted, transacted, control FROM history WHERE id = %s AND (daytrade = %s OR daytrade = %s) ORDER BY transacted, control",
    (id, daytrade_a, daytrade_b))
transactions = cur.fetchall()

for t in range(len(transactions)):
    transacted = transactions[t][0][0:7]
    cur.execute(
    "SELECT tax FROM tax WHERE id = %s AND month < %s AND (daytrade = %s OR daytrade = %s) ORDER BY month DESC",
        (id, transacted, daytrade_a, daytrade_b))
    last_tax = cur.fetchall()
    if len(last_tax) > 0 and last_tax[0][0] > 0:
        last_tax = last_tax[0][0]
    else:
         last_tax = 0
