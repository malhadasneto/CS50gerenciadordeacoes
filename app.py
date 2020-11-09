import re
import os
import psycopg2
import sqlite3
import secrets
from send_mail import send_mail
from db_schema import config_db
from datetime import datetime
from tax_calculator import calculate_tax, update_expenses_regular_trade, history_avg_price, tax_for_html
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, reload_symbols, add_symbol, get_quote, build_my_wallet, update_current_stocks

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ul!H(QLNP=kr("VFL'
app.config['SQLALCHEMY_DATABASE_URL'] = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true&sslfactory=org.postgresql.ssl.NonValidatingFactory"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database, create .db if it doesn't exist
DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"
conn = psycopg2.connect(DATABASE_URL)
config_db(conn)

# Load symbols
symbols = reload_symbols()

# Routes
@app.route("/")
@app.route("/my_wallet")
@login_required
def my_wallet():
    id = session["user_id"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    #update expenses
    update_expenses_regular_trade(id)

    #update history average prices
    history_avg_price(id)

    #update taxes
    calculate_tax(id)

    #show tax > month credito_rt credito_dt total a pagar
    tax = tax_for_html(id)

    # adjusting for better view
    if len(tax) > 0:
        tax_credit= tax[-1][2:4]
    else:
        tax_credit = None
    for x in range(len(tax)):
        print(tax[x])
        del tax[x][2:4]

    cur.execute("SELECT SUM(shares) FROM history WHERE id = %s AND daytrade = 1", (id,))
    check_missing_daytrades = cur.fetchall()
    if check_missing_daytrades[0][0] and check_missing_daytrades[0][0] != 0:
        flash(f"Atenção: você possui operações de Daytrade não finalizadas", "warning")

    #update current_stocks
    update_current_stocks(id)

    #building wallet
    _wallet = build_my_wallet(id)

    conn.close()
    return render_template("my_wallet.html", _wallet = _wallet, tax = tax, tax_credit=tax_credit)

@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Show history of transactions"""
    id = session["user_id"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    #if user ordered to delete something
    if request.method == "POST":

        if request.form.get("deletehistory"):
            delete = int(request.form.get("deletehistory"))
            cur.execute("SELECT transacted FROM history WHERE control=%s", (delete,))
            transacted = cur.fetchall()
            cur.execute("DELETE FROM history WHERE control=%s", (delete, ))
            conn.commit()

            #check if transacted(expenses) still have transacted(history), otherwise delete transacted(expenses)
            cur.execute("SELECT transacted FROM history WHERE id=%s AND transacted=%s", (id, transacted[0][0]))
            transacted_history = cur.fetchall()
            if not transacted_history:
                try:
                    cur.execute("DELETE from expenses WHERE id=%s and transacted=%s", (id, transacted[0][0])).fetchall()
                    conn.commit()
                except:
                    pass

        elif request.form.get("deleteexpense"):
            delete = int(request.form.get("deleteexpense"))
            cur.execute("DELETE FROM expenses WHERE control=%s", (delete, ))
            conn.commit()

        #If user deletes anything, we have to drop all tax rows
        cur.execute("DELETE from tax WHERE id=%s", (id, ))
        conn.commit()

    cur.execute(
        "SELECT name, symbol, shares, price, total, transacted, daytrade, control FROM history WHERE id = %s ORDER BY transacted DESC, control DESC",
        (id,))
    history = cur.fetchall()
    cur.execute(
        "SELECT transacted, expenses, control FROM expenses WHERE id = %s ORDER BY transacted DESC, control DESC",
        (id,))
    expenses = cur.fetchall()
    conn.close()
    return render_template("history.html", history=history, expenses=expenses)


@app.route("/sell", methods=["GET", "POST"])
@app.route("/buy", methods=["GET", "POST"])
@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    id = session["user_id"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    global symbols
    expenses = 0.00

    if request.method == "POST":
        if request.form.get("buyorsell"):
            buyorsell = int(request.form.get("buyorsell"))
            trade_type = int(request.form.get("trade_type"))
            transacted = request.form.get("transacted_quote")
            symbol = (request.form.get("symbol")).upper()
            shares = int(request.form.get("shares"))
            price = request.form.get("price")

            #check date
            if transacted > datetime.today().strftime('%Y-%m-%d'):
                flash("Data inválida. Verifique e tente novamente", "danger")
                return render_template("update.html")

            #check daytrade

            if trade_type != 1:
                conn = psycopg2.connect(DATABASE_URL)
                cur.execute("SELECT shares FROM history WHERE id = %s AND symbol = %s AND transacted = %s",
                            (id, symbol, transacted))
                check_daytrade = cur.fetchall()
                for i in range(len(check_daytrade)):
                    if shares * buyorsell * check_daytrade[i][0] < 0:
                        flash("Atenção! Você já adicionou uma negociação para o mesmo dia marcada como 'Operação Comum'. Verifique se está correto para evitar erro de cálculo de imposto", "warning")

            #check if symbol is current negative, if yes, purchasing must be exactly same units
            if buyorsell == 1:
                cur.execute("SELECT sum(shares) FROM current_stocks WHERE id = %s AND symbol = %s",
                            (id, symbol))
                check_shortsell = cur.fetchall()
                # check if it´s exactly value to cover short sell
                if trade_type == -1:
                    if not check_shortsell[0][0]:
                        flash(f"""Erro! Você não está vendido em {symbol}. Para a opção "Operação Descoberta" é preciso registrar primeiro a venda""",
                              "danger")
                        return render_template("update.html")
                else:
                    if check_shortsell[0][0] and check_shortsell[0][0] < 0:
                        flash(
                            f"""Erro! Você está vendido em {symbol} em {check_shortsell[0][0]}. Selecione a opção "Compra" e "Operação Descoberta". A quantidade de "Venda" deve ser a mesma da "Compra". Pode ser necessário recadastrar "compra" ou "venda" em duas operações. Para conferir, clique no link Histórico""",
                            "danger")
                        return render_template("update.html")

                if check_shortsell[0][0] and check_shortsell[0][0] < 0 and check_shortsell[0][0] != (shares * -1):
                    flash(f"""Erro! Você está vendido em {symbol} em {check_shortsell[0][0]} unidades.\n
                          É preciso que COMPRA e VENDA sejam iguais. \n
                        Caso necessário, divida a negociação. (Ex.: uma compra de 200un vira 2 de 100un).\n
                        Lembre-se de marcar a opção "Operação Descoberta" tanto para Compra quanto para Venda""", "danger")
                    return render_template("update.html")

            cur.execute("SELECT SUM(shares) FROM history WHERE id = %s AND symbol = %s AND transacted <= %s",
                        (id, symbol, transacted))
            check_temp = cur.fetchall()

            #regular case, you cant´sell more than you already have
            if trade_type != -1 and buyorsell == -1:
                if not check_temp[0][0] or check_temp[0][0] < shares:
                    flash("Erro! Não há ações suficientes para essa venda. Se necessário, a diferença deve ser cadastrada na opção Venda Descoberta", "danger")
                    return render_template("update.html")

            if trade_type == -1 and buyorsell == -1:
                #special case: check if there´s stock. you can´t "shortsell" if you still have stock.
                if check_temp[0][0] and check_temp[0][0] > 0:
                    flash(f"""Erro! Para Venda Descoberta você não pode ter o papel em carteira. A diferença deve ser cadastrada como Operação Regular primeiro.
No momento, você tem {check_temp[0][0]} un. de {symbol}:""", "danger")
                    return render_template("update.html")

            #check if symbol exist b4 return error
            if symbol not in symbols:
                    _temp = get_quote(symbol)
                    if _temp == "ERROR_02":
                        flash("Código não encontrado. Verifique e tente novamente", "danger")
                        return render_template("update.html")
                    else:
                        name = (_temp[0])
                        add_symbol(_temp[0], symbol)
                        symbols = reload_symbols()

            else:
                name = symbols[symbol]

            #changing "," for "." - foom brazilian currency to acceptable DB float.
            try:
                price = float(convert_to_intl_cents(price))
                shares = int(shares)*buyorsell
                total = price * shares * -1
            except:
                print("ERRO03")
                flash("Erro! Utilize apenas número ou número + vírgula (0,00)", "danger")
                return render_template("update.html")

            if price > 0.0 and shares != 0:
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()

                cur.execute("""INSERT INTO HISTORY (name, symbol, shares, price, total, transacted, daytrade, id) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (name, symbol, shares, price, total, transacted,
                                                                   trade_type, id))
                conn.commit()

                flash("Registrado com sucesso!", "success")

            elif price <= 0 or shares <= 0:
                flash("Valores inválidos. Verifique e tente novamente", "danger")
                return render_template("update.html")

        #2nd form was answered
        else:
            #check date
            transacted = request.form.get("transacted")
            if transacted > datetime.today().strftime('%Y-%m-%d'):
                flash("Data inválida. Verifique e tente novamente", "danger")
                return render_template("update.html")

            #check if in this day there is expenses registered; or if zero stocks traded
            cur.execute("SELECT transacted FROM history WHERE id = %s AND transacted = %s", (id, transacted))
            check_history = cur.fetchall()
            cur.execute("SELECT transacted, expenses FROM expenses WHERE id = %s AND transacted = %s", (id, transacted))
            check_expenses = cur.fetchall()

            if len(check_history) < 1:
                flash("Erro! Não há nenhum trade registrado nesse dia", "danger")
                return render_template("update.html")
            elif len(check_expenses) != 0:
                flash("Erro! Já há registro de despesas para esse dia. Delete acessando a aba 'histórico'", "danger")
                return render_template("update.html")

            #sum expenses
            for n in range (1,7):
                _expenses = request.form.get("custos"+str(n))

                if _expenses:
                    try:
                        expenses += float(convert_to_intl_cents(_expenses))
                    except:
                        print("ERRO04")
                        flash("Erro! Utilize apenas número ou número + vírgula (0,00)", "danger")
                        return render_template("update.html")

            cur.execute("""INSERT INTO expenses (transacted, expenses, id) 
                          VALUES (%s, %s, %s)""", (transacted, expenses, id))
            conn.commit()
            flash("Registrado com sucesso!", "success")

    #check daytrade not finished
    cur.execute("SELECT DISTINCT symbol FROM history WHERE id = %s AND daytrade = 1",
                (id,))
    get_dt_symbols = cur.fetchall()
    for i in range(len(get_dt_symbols)):
        symbol = get_dt_symbols[i][0]
        cur.execute("SELECT SUM(shares) FROM history WHERE id = %s AND symbol = %s AND daytrade = 1",
                    (id, symbol))
        check_dt_not_finished = cur.fetchall()
        if check_dt_not_finished and check_dt_not_finished[0][0] != 0:
            flash(f"Operação de daytrade de {symbol} ainda não foi concluída", "warning")
            break

    conn.close()
    return render_template("update.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        cur.execute("SELECT * FROM users WHERE username = %s", ([request.form.get("username").lower()]))
        rows = cur.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            flash ("Erro! E-mail não cadastrado ou senha inválida. Verifique e tente novamente", "danger")
            conn.close()
            return render_template('login.html')

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        conn.close()

    # Redirect user to history
        flash ("Seja bem-vindo(a)! Boa sorte!", "success")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        conn.close()
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    if request.method == "POST":
        # Query database for username
        username = (request.form.get("username")).lower()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        rows = cur.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 0:
            flash("Email já cadastrado","danger")
            conn.close()
            return render_template("register.html")

        password = request.form.get("password")
        hash_password = generate_password_hash(password)
        cur.execute("INSERT INTO USERS (username, hash) VALUES (%s,%s)", (username, hash_password))
        conn.commit()
        conn.close()

        # Redirect user to home page
        flash ("Cadastro confirmado!","success")
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        conn.close()
        return render_template("register.html")



@app.route("/reset", methods=["GET", "POST"])
def reset():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    if request.method == "POST":
        conn = psycopg2.connect(DATABASE_URL)
        if request.form.get("reset_token") and request.form.get("reset_username"):
            reset_key = cur.execute("SELECT reset_key FROM users WHERE username = %s", ([request.form.get("reset_username")])).fetchall()
            if reset_key[0][0] == request.form.get("reset_token"):
                cur.execute("UPDATE users SET reset_key = %s WHERE username = %s", ("", request.form.get("reset_username")))
                cur.execute("UPDATE users SET hash = %s WHERE username = %s", (generate_password_hash(request.form.get("password")), request.form.get("reset_username")))
                conn.commit()
                conn.close()
                flash("Redefinição de senha concluída com sucesso!", "success")
                return render_template("login.html")
            else:
                flash("Erro! Código inválido. Verifique e tente novamente", "danger")
                conn.close()
                return render_template("reset.html", reset = "true")

        else:
            rows = cur.execute("SELECT * FROM users WHERE username = %s", ([request.form.get("username").lower()])).fetchall()
            if len(rows) != 1:
                conn.close()
                flash ("Erro! E-mail não cadastrado. Verifique e tente novamente", "danger")
                return render_template('reset.html')
            else:
                token = secrets.token_urlsafe(8)
                mail = send_mail(request.form.get("username").lower(), token)
                if mail == 1:
                    cur.execute("UPDATE users SET reset_key = %s WHERE username = %s", (token, request.form.get("username").lower()))
                    conn.commit()
                    conn.close()
                    flash ("Em alguns instantes, verifique seu e-mail e copie/cole o código", "success")
                    return render_template("reset.html", reset = "true") #sopraverseéesseologin
                else:
                    conn.close()
                    flash("Ocorreu um erro. Tente de novo. Persistindo o erro, entre em contato", "alert")
    else:
        return render_template("reset.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/aboutme")
def aboutme():
    return render_template("aboutme.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def convert_to_intl_cents(value):
    value = value.strip()
    if re.match(r'(^\d+$)', value):
        return float(value)
    elif re.match(r'(^\d+),(\d\d$)', value):
        _value = list(value)
        _value[-3] = "."
        return "".join(_value)
    else:
        return None

@app.template_filter()
def convert_to_br_cents(value):
    return (f"R${value:.2f}").replace(".", ",")


if __name__ == '__main__':
    app.run(debug=True)

