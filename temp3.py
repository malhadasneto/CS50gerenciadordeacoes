import psycopg2
DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"


conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
name = 'Banco BTG Pactual SA Brazilian Units'
symbol = 'BPAC11'
shares = 100
price = 79.95
total = -7995.0
transacted = '2020-07-06'
trade_type = 0
id = 1

cur.execute("""INSERT INTO HISTORY (name, symbol, shares, price, total, transacted, daytrade, id) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (name, symbol, shares, price, total, transacted,
                                                                   trade_type, id))
conn.commit()


conn.close()

