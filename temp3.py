import requests
import re
import psycopg2
from tax_calculator import tax_for_html, calculate_tax

DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"

# second, now we have to think in months, not sales. and include daytrade = -1 (daytrade_a and b)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
daytrade = daytrade_a = daytrade_b = 1
id = 1

tax = [['2020-04', 'R$-183,73', 0, 'R$183,73', None, 0], ['2020-07', 0, 0, 'R$183,73', None, 0], ['2020-08', 0, 0, 'R$183,73', None, 0], ['2020-09', 'R$-2104,63', 'R$2708,24', 'R$178,79', 'R$36630,27', 0], ['2020-10', 'R$-4895,86', 'R$7771,66', 'R$178,79', 'R$35843,00', 0]]
tax_credit = tax[-1][2:4]


#create a dict with taxes (date, rt_credits, dt_credits, tax to pay)
# for t in tax_list:
#     _temp_tax_list_final = [t, brl(tax_list[t][3]), brl(tax_list[t][0]), brl(tax_list[t][1]), brl(tax_list[t][4]),
#                             brl(tax_list[t][2])]
#     tax_list_final.append(_temp_tax_list_final)
#t =transacted,  profit taxlistt3, credrt tax0, creddt tax1,