import re
import requests
import sqlite3


from flask import redirect, render_template, request, session
from functools import wraps

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
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
    return (f"R${value:.2f}").replace(".", ",")


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
            name_start = content.find(stock.upper() + " (") + len(stock) + 2
            name_end = content.find(") |")
            if name_end - name_start > 30:
                return "ERROR_01"
            info.append(content[name_start:name_end])
            stock_quotation = re.findall('\d\d*,\d\d <', content)
            info.append(stock_quotation[0][:-2])
        except:
            return "ERROR_02"
        return info


def build_my_wallet(id):
    """For each symbol in current_stock,
    create a list with: name, symbol, shares, avg_price, current_value, performance"""
    wallet = []
    conn = sqlite3.connect("stocks.db")

    _temp_wallet = conn.execute(
        "SELECT symbol, shares, avg_price, current_value FROM current_stocks WHERE id = ? ORDER BY symbol",
        (id,)).fetchall()

    for x in range(len(_temp_wallet)):
        symbol = _temp_wallet[x][0]
        avg_price = brl(_temp_wallet[x][2])
        current_value = brl(_temp_wallet[x][3])
        name = (conn.execute("SELECT name FROM history WHERE symbol = ?", (symbol,)).fetchone())[0]

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
    conn = sqlite3.connect("stocks.db")
    conn.execute("DELETE FROM current_stocks WHERE id=?", (id,))
    conn.commit()
    current_stocks = conn.execute(
        "SELECT symbol, SUM(shares) FROM history WHERE id=? AND DAYTRADE!=1 GROUP BY symbol ORDER BY symbol",
        (id,)).fetchall()
    for x in range(len(current_stocks)):
        if current_stocks[x][1] != 0:
            symbol = current_stocks[x][0]
            shares = current_stocks[x][1]

            if shares > 0:
                stock_info = conn.execute("SELECT avg_price, total FROM history WHERE id=? AND symbol=? AND shares>0 ORDER BY transacted DESC, control DESC",
                                      (id, symbol)).fetchall()
            #special case short sell
            else:
                stock_info = conn.execute("SELECT avg_price, total FROM history WHERE id=? AND symbol=? AND shares<0 ORDER BY transacted DESC, control DESC",
                                      (id, symbol)).fetchall()

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

            conn.execute("INSERT INTO current_stocks (symbol, shares, id, avg_price, current_value) VALUES (?,?,?,?,?)",
                         (symbol, shares, id, avg_price, current_value))
            conn.commit()
    conn.close()