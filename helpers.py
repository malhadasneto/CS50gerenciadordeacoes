import re
import requests
import psycopg2
from flask import redirect, render_template, request, session
from functools import wraps


DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("%s", "~q"),
                         ("%s", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def brl(value):
    """Format value as BRL."""
    if value:
        return (f"R${value:.2f}").replace(".", ",")
    else:
        return value


def reload_symbols():
    symbols = {}
    with open('symbols_bvmf.txt', 'r') as file:
        for lines in file.readlines():
            _temp = lines.split(";")
            symbols[_temp[1][:-1]] = _temp[0]
    return symbols

def add_symbol(name, symbol):
    with open('symbols_bvmf.txt', 'a') as file:
        text = str(name + ";" + symbol + "\n")
        file.write(text)


def get_quote(stock):
    url = "https://www.google.com/search?q=bvmf:"+stock
    info = []
    with requests.Session() as s:
        try:
            content = str(s.get(url).content)
            name_start = content.find('<div class="ZINbbc xpd O9g5cc uUPGi"><div class="kCrYT"><span><span class="BNeawe tAd8D AP7Wnd">')+96
            name_end = content.find('</span></span><span class="BNeawe s3v9rd AP7Wnd"> /')
            print(content[name_start:name_end])
            if name_end - name_start > 100:
                return "ERROR_01"
            info.append(content[name_start:name_end])
            stock_quotation = re.findall('\d\d*,\d\d <', content)
            print("stockquotation", stock_quotation, info, "info")
            info.append(stock_quotation[0][:-2])
        except Exception as e:
            print(e)
            print(stock, "stock", info, name_start, name_end)
            return "ERROR_02"

        return info


def build_my_wallet(id):
    """For each symbol in current_stock,
    create a list with: name, symbol, shares, avg_price, current_value, performance"""
    wallet = []
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        "SELECT symbol, shares, avg_price, current_value FROM current_stocks WHERE id = %s ORDER BY symbol",
        (id,))
    _temp_wallet = cur.fetchall()

    for x in range(len(_temp_wallet)):
        symbol = _temp_wallet[x][0]
        avg_price = brl(_temp_wallet[x][2])
        current_value = brl(_temp_wallet[x][3])
        cur.execute("SELECT name FROM history WHERE symbol = %s", (symbol,))
        name = cur.fetchone()[0]
        conn.close()

        # protection against web search errors:
        try:
            current_price = get_quote(_temp_wallet[x][0])[1]
            float_current_price = float(current_price[:-3] + "." + current_price[-2:])
            current_price = brl(float_current_price)
        except:
            current_price = None
            float_current_price = None
            print("ERROR 10 - Getting quote")

        # calculate performance
        float_avg_price = _temp_wallet[x][2]

        # protection against any fault in websearch (function "get_quote)
        if current_price and float_avg_price:
            performance = round(100 * ((float_current_price - float_avg_price) / float_avg_price), 2)
            #if special case, invert
            if _temp_wallet[x][1] < 0:
                performance = round(-100*(_temp_wallet[x][3] - (float_current_price * _temp_wallet[x][1])) / (float_current_price * _temp_wallet[x][1]),2)

            performance = (str(performance) + "%").replace(".", ",")
        else:
            performance = None
        _temp_list = [name, symbol, str(_temp_wallet[x][1]), avg_price, current_value, current_price, performance]
        wallet.append(_temp_list)

    return wallet

def update_current_stocks(id):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM current_stocks WHERE id=%s", (id,))
    conn.commit()
    cur.execute(
        "SELECT symbol, SUM(shares) FROM history WHERE id=%s AND DAYTRADE!=1 GROUP BY symbol ORDER BY symbol",
        (id,))
    current_stocks = cur.fetchall()
    for x in range(len(current_stocks)):
        if current_stocks[x][1] != 0:
            symbol = current_stocks[x][0]
            shares = current_stocks[x][1]

            if shares > 0:
                cur.execute(
                    "SELECT avg_price, total FROM history WHERE id=%s AND symbol=%s AND shares>0 ORDER BY transacted DESC, control DESC",
                    (id, symbol))
                stock_info = cur.fetchall()
            #special case short sell
            else:
                cur.execute(
                    "SELECT avg_price, total FROM history WHERE id=%s AND symbol=%s AND shares<0 ORDER BY transacted DESC, control DESC",
                    (id, symbol))
                stock_info = cur.fetchall()

            # for regular case:
            if shares > 0:
                avg_price = stock_info[0][0]
                current_value = stock_info[0][0] * shares * -1
            # special case, shortsell
            elif shares < 0:
                #if there´s more than 1 row with shortselling, we have to sum
                total = 0
                for x in range(len(stock_info)):
                    if stock_info[x][1] > 0:
                        total += stock_info[x][1]
                    else:
                        break
                avg_price = total / shares * -1
                current_value = total

            cur.execute("INSERT INTO current_stocks (symbol, shares, id, avg_price, current_value) VALUES (%s,%s,%s,%s,%s)",
                         (symbol, shares, id, avg_price, current_value))
            conn.commit()
    conn.close()