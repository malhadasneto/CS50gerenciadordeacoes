import sqlite3
from helpers import brl

def update_expenses_regular_trade(id):
    conn = sqlite3.connect("stocks.db")
    transacted = conn.execute("SELECT transacted, expenses FROM expenses WHERE id = ?", (id, )).fetchall()
    for t in range(len(transacted)):
        sum_shares = conn.execute("SELECT SUM(abs(shares)) FROM history WHERE id=? AND transacted = ?",(id, transacted[t][0])).fetchall()
        per_share = transacted[t][1]/sum_shares[0][0]
        conn.execute("UPDATE expenses SET per_share = ? WHERE id = ? AND transacted = ?",(per_share, id, transacted[t][0])).fetchall()
        conn.commit()

        #update each share in that date (expenses and total)
        shares_to_update = conn.execute("SELECT control, shares, price FROM history WHERE id = ? AND transacted = ?", (id, transacted[t][0])).fetchall()
        for x in range(len(shares_to_update)):
            control = shares_to_update[x][0]
            shares = shares_to_update[x][1]
            price = shares_to_update[x][2]
            expenses = abs(per_share * shares)
            conn.execute("UPDATE history SET expenses = ?, total = ? WHERE control = ?",
                         (-1*expenses, -1*((price * shares) + expenses), control))
            conn.commit()

    conn.close()


def history_avg_price(id):
    conn = sqlite3.connect("stocks.db")

    #first, special case shortsell daytrade=-1
    special_cases = conn.execute("SELECT price, control FROM history WHERE shares > 0 AND id=? AND daytrade=-1",(id,)).fetchall()
    for x in range(len(special_cases)):
        avg_price = special_cases[x][0]
        control = special_cases[x][1]
        conn.execute("UPDATE history SET avg_price = ? WHERE control=?", (avg_price, control))

    # take information to calc avg_price for regular trade (x==0) and daytrade (x==1)
    for x in range(2):
        # for daytrade logic is different:
        if x == 1:
            transactions = conn.execute(
                "SELECT DISTINCT transacted FROM history WHERE id = ? AND daytrade = 1",
                (id,)).fetchall()

            for transacted in transactions:
                list_symbols = conn.execute(
                    "SELECT DISTINCT symbol FROM history WHERE id = ? AND daytrade = 1 AND transacted=?",
                    (id, transacted[0])).fetchall()

                for symbol in list_symbols:
                    last_loop = conn.execute(
                        "SELECT shares, total, control from history WHERE id=? AND symbol = ? AND daytrade = 1 AND transacted=? AND shares > 0",
                        (id, symbol[0], transacted[0])).fetchall()

                    _temp_prices = [0, 0.0, 0.0, []]  # shares, total, avg_price, control
                    for trade in last_loop:
                        _temp_prices[0] = trade[0] + _temp_prices[0]
                        _temp_prices[1] = trade[1] + _temp_prices[1]
                        _temp_prices[3].append(trade[2])

                    # finally...
                    avg_price = _temp_prices[1] / _temp_prices[0]
                    for each_control in _temp_prices[3]:
                        conn.execute("UPDATE history SET avg_price = ? WHERE control = ?",
                                     (avg_price * -1, each_control))
                        conn.commit()

        # RT only: for each stock, get prices
        else:
            list_symbols = conn.execute(
                "SELECT DISTINCT symbol FROM history WHERE id = ? AND daytrade <= 0",
                (id,)).fetchall()
            for symbol in list_symbols:
                _temp_prices = [0, 0.0, 0.0, []]  # shares, total, avg_price, control
                list_stocks = conn.execute(
                    "SELECT shares, total, control from history WHERE id=? AND symbol = ? AND daytrade <= 0 ORDER BY transacted, control",
                    (id, symbol[0],)).fetchall()

                # loop through each symbol to get avg_price. sum all until "share" is zero or less.
                for j in range(len(list_stocks)):
                    control = list_stocks[j][2]
                    _temp_prices[0] = list_stocks[j][0] + _temp_prices[0]

                    # avg_price only changes when stocks are purchased
                    if list_stocks[j][0] > 0:
                        _temp_prices[1] = (list_stocks[j][1] + _temp_prices[1])
                        _temp_prices[3].append(control)
                        _temp_prices[2] = _temp_prices[1] / _temp_prices[0]

                    # every time stock == 0 or negative, we need to fix the avg_price for all purchases, store in DB and start a new serie
                    if _temp_prices[0] <= 0:
                        for each_control in _temp_prices[3]:
                            conn.execute("UPDATE history SET avg_price = ? WHERE control = ?",
                                         (_temp_prices[2] * -1, each_control))
                            conn.commit()

                        # reset current_stock as well if needed (todo: se for short sell tem q inserir no current_stocks em vez de só atualizar)
                        conn.execute("UPDATE current_stocks SET shares = ? WHERE id = ?", (_temp_prices[0], id))
                        conn.commit()

                        _temp_prices = [0, 0.0, 0.0, []]  # reset shares, total, avg_price, control

                # if loop is over and stock is still positive:
                if _temp_prices[0] > 0:
                    for each_control in _temp_prices[3]:
                        conn.execute("UPDATE history SET avg_price = ? WHERE control = ?",
                                     (_temp_prices[2] * -1, each_control))
                        conn.commit()

                    # updating my_wallet
                    conn.execute("UPDATE current_stocks SET avg_price=?, current_value=? WHERE symbol=? AND id=?",
                                 (_temp_prices[2] * -1, _temp_prices[0], symbol[0], id))
                    conn.commit()

    conn.close()


def calculate_tax(id):
    conn = sqlite3.connect("stocks.db")

    # first loop, daytrade == 0 (regular) and daytrade == 1
    for i in range(2):
        daytrade = i
        daytrade_a = 0
        daytrade_b = -1
        tax_rate = 0.15
        if daytrade == 1:
            tax_rate = 0.20
            daytrade_a = daytrade_b = 1
        # first, let´s calculate the tax for each sale.
        all_trades = conn.execute(
            "SELECT symbol, shares, total, control, daytrade, transacted, avg_price FROM history WHERE id = ? AND daytrade = ? ORDER BY transacted, control",
            (id, daytrade)).fetchall()
        # dict legend: {symbol: current avg_price}
        _temp_avg_price = {}

        for trades in all_trades:
            symbol, shares, total, control, daytrade, transacted, avg_price = trades

            if symbol not in _temp_avg_price.keys():
                _temp_avg_price[symbol] = 0.0

            if total < 0:
                _temp_avg_price[symbol] = avg_price

            elif total > 0 and daytrade != -1:
                to_tax = total + (shares * _temp_avg_price[symbol])

                #update profit/loss column
                conn.execute("UPDATE history SET profit = ? WHERE control = ?", (to_tax, control))
                conn.commit()

                # check profit/loss to calculate tax or keep as a credit
                if to_tax > 0:
                    to_tax = to_tax * tax_rate
                conn.execute("UPDATE history SET tax = ? WHERE control = ?", (-1 * to_tax, control))
                conn.commit()

        # special case - shortsell - becaise we need to consider purchase date not selling date
        # first list symbols daytrade -1
        shortsell_symbols = conn.execute("SELECT DISTINCT symbol FROM history WHERE id=? AND daytrade=-1",
                                         (id,)).fetchall()

        # second, get all trades for each symbol, create a selling list with index to avoid repetition if there´s more than one purchase
        for x in range(len(shortsell_symbols)):
            shortsell_trades = conn.execute(
                "SELECT symbol,shares,total,transacted, control,avg_price,price FROM history WHERE id=? AND daytrade=-1 AND symbol=? ORDER BY transacted, control",
                (id, shortsell_symbols[x][0])).fetchall()
            short_sell_indexes = [i for i, j in enumerate(shortsell_trades) if j[1] <= 0]
            short_sell_sold = short_sell_total = 0

            # third, find first purchase
            for y in range(len(shortsell_trades)):
                if shortsell_trades[y][1] > 0:
                    symbol, shares, total, transacted, control, avg_price, price = shortsell_trades[y]
                    total = price * shares * -1

                    # forth, find first sell. check if it´s enough, otherwise, take next. in the end, remove items from list to avoid repetition
                    for z in short_sell_indexes:
                        short_sell_sold += shortsell_trades[z][1]
                        short_sell_total += shortsell_trades[z][2]

                        # if buy = sell, calculate tax, update DB
                        if short_sell_sold == shares * -1:
                            profit = total + short_sell_total
                            if profit > 0:
                                tax = profit * 0.15 * -1
                            else:
                                tax = profit * -1
                            conn.execute("UPDATE history SET tax=?, profit=? WHERE control=?", (tax, profit, control))
                            conn.commit()
                            del short_sell_indexes[0:z + 1]
                            break

        # second, now we have to think in months, not sales. and include daytrade = -1 (daytrade_a and b)
        transactions = conn.execute(
            "SELECT DISTINCT transacted FROM history WHERE id = ? AND (daytrade = ? OR daytrade = ?) ORDER BY transacted, control",
            (id, daytrade_a, daytrade_b)).fetchall()

        for t in range(len(transactions)):
            transacted = transactions[t][0]
            # first, get tax from the last month, if it´s positive, it´s a credit. if not, = 0
            last_tax_trade = ""
            last_tax_year = transacted[0:4]
            last_tax_month = transacted[5:7]
            # last month adjustment (january - 1 = december):
            if last_tax_month == "01":
                last_tax_year = str(int(last_tax_year) - 1)
                last_tax_month = str(12)
            else:
                last_tax_month = str(int(last_tax_month) - 1)
                if int(last_tax_month) < 10:
                    last_tax_month = "0" + last_tax_month
            last_tax_date = last_tax_year + "-" + last_tax_month

            last_tax_trade = conn.execute("SELECT tax FROM tax WHERE month = ? AND id = ? AND (daytrade = ? OR daytrade=?) ",
                                          (last_tax_date, id, daytrade_a, daytrade_b)).fetchall()

            # "negative" tax = you have to pay; "positive" = credit to use.
            if len(last_tax_trade) == 0 or last_tax_trade[0][0] < 0:
                last_tax = 0
            else:
                last_tax = last_tax_trade[0][0]

            # third, create a row for the current month if there isn´t one:
            row_current_table = conn.execute("SELECT * FROM tax WHERE month = ? AND id = ? AND (daytrade = ? or daytrade = ?)",
                                             (transacted[:-3], id, daytrade_a, daytrade_b)).fetchall()

            if len(row_current_table) == 0:
                conn.execute("INSERT INTO tax (id, Month, Daytrade) VALUES (?, ?, ?)", (id, transacted[:-3], daytrade))
                conn.commit()

            # forth, add current profit/loss AND tax to db
            current_tax = 0
            temp_current_tax = conn.execute(
                "SELECT SUM(tax) FROM history WHERE (daytrade = ? or daytrade = ?) AND transacted BETWEEN ? AND ? AND id = ?",
                (daytrade_a, daytrade_b, transacted[:-2] + "01", transacted[:-3] + "31", id)).fetchall()

            if temp_current_tax[0][0]:
                current_tax = temp_current_tax[0][0]
            current_tax += last_tax

            #brazilian law: up to R$20.000 in sales, investor is exempt from payment of tax, except for daytrade
            if daytrade !=1 and current_tax < 0:
                check_exemption = conn.execute("SELECT sum(total) FROM history WHERE id=? AND shares<0 AND daytrade !=1 AND transacted BETWEEN ? AND ?",
                (id, transacted[:-2] + "01", transacted[:-3] + "31")).fetchall()
                if check_exemption[0][0] < 20000:
                    current_tax = 0

            conn.execute("UPDATE tax SET tax = ? WHERE month = ? AND id = ? AND daytrade = ?",
                         (current_tax, transacted[:-3], id, daytrade))
            conn.commit()

    conn.close()

#create a dict with taxes (date, rt_credits, dt_credits, tax to pay)
def tax_for_html(id):
    conn = sqlite3.connect("stocks.db")
    tax = conn.execute("SELECT month, daytrade, tax FROM tax WHERE id = ? ORDER BY month", (id,)).fetchall()
    # exemple tax_list: {'2020-09': [rt,dt,total, 20klimit]}
    tax_list = {}  # one list for each month
    for x in range(len(tax)):
        total_tax = 0
        month, daytrade, current_tax = tax[x]

        if month not in tax_list.keys():
            tax_list[month] = [0, 0, 0, 0, 0]

        # if credit (positive) insert in index 0 if regular trade, 1 if dt
        if current_tax > 0:
            tax_list[month][daytrade] = current_tax
        else:
            tax_list[month][2] = tax_list[month][2] + current_tax

    # inserting profit/loss:
    for transacted in tax_list.keys():
        profit = conn.execute("SELECT sum(profit) FROM history WHERE transacted BETWEEN ? AND ? AND id = ?",
                              (transacted + "-01", transacted + "-31", id)).fetchall()
        if not profit[0][0]:
            profit = 0
        else:
            profit = profit[0][0]
            if tax_list[transacted][2] < 0:
                profit += tax_list[transacted][2]
        tax_list[transacted][3] = profit

        # R$20k limit
        check_exemption = conn.execute(
            "SELECT sum(total) FROM history WHERE id=? AND shares<0 AND daytrade !=1 AND transacted BETWEEN ? AND ?",
            (id, transacted + "-01", transacted + "-31")).fetchall()
        tax_list[transacted][4] = check_exemption[0][0]

    conn.close()

    # convert to list
    tax_list_final = []

    for t in tax_list:
        _temp_tax_list_final = [t, brl(tax_list[t][3]), brl(tax_list[t][0]), brl(tax_list[t][1]), brl(tax_list[t][4]), brl(tax_list[t][2])]
        tax_list_final.append(_temp_tax_list_final)

    return tax_list_final