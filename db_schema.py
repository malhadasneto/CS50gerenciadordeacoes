
def config_db(db):
    db.execute("""CREATE TABLE IF NOT EXISTS 'users' 
                ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'reset_key' TEXT)""")

    db.execute("""CREATE TABLE IF NOT EXISTS 'history' 
                ('Name' TEXT NOT NULL,
                 'Symbol' TEXT NOT NULL,
                 'Shares' INTEGER NOT NULL,
                 'Price' REAL NOT NULL, 
                "Expenses"	REAL,
                 'Total' REAL NOT NULL,
                 'Transacted' TEXT NOT NULL,
                 'Daytrade' INTEGER,
                 'id' INTEGER NOT NULL,
                 'CONTROL' INTEGER NOT NULL UNIQUE,
                 'Avg_price' REAL,
                 'Tax'	REAL,
                  'Profit' REAL,
                 PRIMARY KEY("CONTROL" AUTOINCREMENT),
                 FOREIGN KEY('id') REFERENCES users('id'))""")

    db.execute("""CREATE TABLE IF NOT EXISTS 'expenses' 
                ('Transacted' TEXT NOT NULL,
                 'Expenses' REAL,
                 'id' INTEGER NOT NULL,
                 "CONTROL" INTEGER NOT NULL UNIQUE,
                "Per_share"	REAL,
                 PRIMARY KEY("CONTROL" AUTOINCREMENT),
                 FOREIGN KEY('id') REFERENCES users('id'))""")

    db.execute("""CREATE TABLE IF NOT EXISTS 'tax'
                ('id' INTEGER NUT NULL,
                'Month' TEXT NOT NULL,
                'Tax' REAL,
                'Daytrade' INTEGER,
                FOREIGN KEY('id') REFERENCES users('id'))""")

    db.execute("""CREATE TABLE IF NOT EXISTS 'current_stocks' (
                'id'	INTEGER NOT NULL,
                'symbol'	TEXT NOT NULL,
                'shares'	INTEGER,
                'avg_price'	REAL,
                'current_value'	REAL,
                'CONTROL' INTEGER NOT NULL UNIQUE,
                 PRIMARY KEY('CONTROL' AUTOINCREMENT),
                FOREIGN KEY('id') REFERENCES users('id'))""")

    db.commit()
    db.close()