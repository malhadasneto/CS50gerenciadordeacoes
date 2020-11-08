

def config_db(con):
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users 
                (id SERIAL PRIMARY KEY, 
                username TEXT NOT NULL, hash TEXT NOT NULL, reset_key TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS history 
                (Name TEXT NOT NULL,
                 Symbol TEXT NOT NULL,
                 Shares INTEGER NOT NULL,
                 Price REAL NOT NULL, 
                 Expenses	REAL,
                 Total REAL NOT NULL,
                 Transacted TEXT NOT NULL,
                 Daytrade INTEGER,
                 id INTEGER NOT NULL,
                 CONTROL SERIAL PRIMARY KEY,
                 Avg_price REAL,
                 Tax	REAL,
                 Profit REAL) """)

    cur.execute("""CREATE TABLE IF NOT EXISTS expenses 
                (Transacted TEXT NOT NULL,
                 Expenses REAL,
                 id INTEGER NOT NULL,
                 CONTROL SERIAL PRIMARY KEY,
                 Per_share	REAL)  """)

    cur.execute("""CREATE TABLE IF NOT EXISTS tax
                (id INTEGER NOT NULL,
                Month TEXT NOT NULL,
                Tax REAL,
                Daytrade INTEGER) """)

    cur.execute("""CREATE TABLE IF NOT EXISTS current_stocks (
                id	INTEGER NOT NULL,
                symbol	TEXT NOT NULL,
                shares	INTEGER,
                avg_price	REAL,
                current_value	REAL,
                CONTROL SERIAL PRIMARY KEY)""")

    con.commit()
    con.close()