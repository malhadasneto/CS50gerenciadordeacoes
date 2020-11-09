import requests
import re
import psycopg2
from tax_calculator import tax_for_html, calculate_tax

DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"

# second, now we have to think in months, not sales. and include daytrade = -1 (daytrade_a and b)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
daytrade = daytrade_a = daytrade_b = 1
id = 2

cur.execute("SELECT transacted, expenses FROM expenses WHERE id = %s", (id,))
transacted = cur.fetchall()
for t in range(len(transacted)):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    expenses = transacted[t][1]
    total_op = 0
    cur.execute("SELECT price, shares, control FROM history WHERE id=%s AND transacted = %s", (id, transacted[t][0]))
    _price_shares = cur.fetchall()
    for x in range(len(_price_shares)):
        total_op += _price_shares[x][0] * abs(_price_shares[x][1])
    per_share = expenses/total_op
    cur.execute("UPDATE expenses SET per_share = %s WHERE id = %s AND transacted = %s",
                (per_share, id, transacted[t][0]))
    conn.commit()
    conn.close()

    #update each share in that date (expenses and total)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT control, shares, price FROM history WHERE id = %s AND transacted = %s",
                (id, transacted[t][0]))
    shares_to_update = cur.fetchall()
    for x in range(len(shares_to_update)):
        control = shares_to_update[x][0]
        shares = shares_to_update[x][1]
        price = shares_to_update[x][2]
        expenses = abs(per_share * shares * price)
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("UPDATE history SET expenses = %s, total = %s WHERE control = %s",
                    (-1 * expenses, -1 * ((price * shares) + expenses), control))
        print('exp, total:', -1 * expenses, -1 * ((price * shares) + expenses))
        conn.commit()
        conn.close()