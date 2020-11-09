import requests
import re
import psycopg2
from helpers import brl
from tax_calculator import tax_for_html, calculate_tax

DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"

# second, now we have to think in months, not sales. and include daytrade = -1 (daytrade_a and b)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
daytrade = daytrade_a = daytrade_b = 1
id = 1

def tax_for_html(id):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("SELECT month, daytrade, tax FROM tax WHERE id = %s ORDER BY month", (id,))
    tax = cur.fetchall()
    # exemple tax_list: {'2020-09': [rt,dt,total, 20klimit]}
    tax_list = {}  # one list for each month
    for x in range(len(tax)):
        total_tax = 0
        month, daytrade, current_tax = tax[x]

        if month not in tax_list.keys():
            tax_list[month] = [0, 0, 0, 0, 0]

        # if credit (positive) insert in index 0 if regular trade, 1 if dt
        if not current_tax:
            current_tax = 0

        if current_tax > 0:
            tax_list[month][daytrade] = current_tax
        else:
            tax_list[month][2] = tax_list[month][2] + current_tax

    # inserting profit/loss:
    for transacted in tax_list.keys():
        cur.execute("SELECT sum(profit) FROM history WHERE transacted BETWEEN %s AND %s AND id = %s",
                    (transacted + "-01", transacted + "-31", id))
        profit = cur.fetchall()
        if not profit[0][0]:
            profit = 0
        else:
            profit = profit[0][0]
            if tax_list[transacted][2] < 0:
                profit += tax_list[transacted][2]
        tax_list[transacted][3] = profit

        # R$20k limit
        cur.execute(
            "SELECT sum(total) FROM history WHERE id=%s AND shares<0 AND daytrade !=1 AND transacted BETWEEN %s AND %s",
            (id, transacted + "-01", transacted + "-31"))
        check_exemption = cur.fetchall()
        tax_list[transacted][4] = check_exemption[0][0]

    conn.close()

    # convert to list
    tax_list_final = []

    for t in tax_list:
        _temp_tax_list_final = [t, brl(tax_list[t][3]), brl(tax_list[t][0]), brl(tax_list[t][1]), brl(tax_list[t][4]), brl(tax_list[t][2])]
        tax_list_final.append(_temp_tax_list_final)

    return tax_list_final

a=tax_for_html(1)
print(a)