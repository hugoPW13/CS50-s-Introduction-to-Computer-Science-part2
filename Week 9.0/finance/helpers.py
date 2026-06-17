import requests
import os
import urllib.parse
from functools import wraps
from flask import redirect, render_template, request, session

def apology(message, code=400):
    return render_template("apology.html", top=code, bottom=message), code

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def lookup(symbol):
    """Mock stock lookup (replace with real API if needed)"""
    symbol = symbol.upper()
    # Mock prices
    prices = {"AAPL": 150.0, "GOOG": 2800.0, "MSFT": 300.0, "TSLA": 700.0, "NFLX": 500.0}
    if symbol not in prices:
        return None
    return {"name": symbol + " Inc.", "price": prices[symbol], "symbol": symbol}

def usd(value):
    return f"${value:,.2f}"
