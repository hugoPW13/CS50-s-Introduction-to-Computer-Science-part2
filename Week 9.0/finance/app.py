import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from CS50x.finance.helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    # Fetch user's holdings
    rows = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0", session["user_id"])
    portfolio = []
    total_value = 0
    for row in rows:
        quote = lookup(row["symbol"])
        if quote:
            value = row["total_shares"] * quote["price"]
            total_value += value
            portfolio.append({
                "symbol": row["symbol"],
                "name": quote["name"],
                "shares": row["total_shares"],
                "price": quote["price"],
                "total": value
            })
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    grand_total = cash + total_value
    return render_template("index.html", portfolio=portfolio, cash=cash, grand_total=grand_total)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)

        hash_pw = generate_password_hash(password)
        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_pw)
        except:
            return apology("username already exists", 400)

        session["user_id"] = new_user
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)
        if not password:
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("must provide symbol", 400)
        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol", 400)
        return render_template("quoted.html", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must provide symbol", 400)
        quote = lookup(symbol)
        if not quote:
            return apology("invalid symbol", 400)

        try:
            shares = int(shares)
            if shares <= 0:
                return apology("shares must be positive integer", 400)
        except:
            return apology("shares must be integer", 400)

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        cost = shares * quote["price"]
        if cash < cost:
            return apology("cannot afford", 400)

        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", cost, session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], symbol.upper(), shares, quote["price"])
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    rows = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0", session["user_id"])
    symbols = [row["symbol"] for row in rows]

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not symbol:
            return apology("must select symbol", 400)
        if symbol not in symbols:
            return apology("you do not own this stock", 400)
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("shares must be positive", 400)
        except:
            return apology("shares must be integer", 400)

        owned = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)[0]["total_shares"]
        if shares > owned:
            return apology("not enough shares", 400)

        price = lookup(symbol)["price"]
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", shares*price, session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], symbol, -shares, price)
        return redirect("/")
    else:
        return render_template("sell.html", symbols=symbols)


@app.route("/history")
@login_required
def history():
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY transacted DESC", session["user_id"])
    return render_template("history.html", transactions=transactions)
