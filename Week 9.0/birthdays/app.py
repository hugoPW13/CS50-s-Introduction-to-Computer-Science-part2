from cs50 import SQL
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Connect to database
db = SQL("sqlite:///birthdays.db")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        month = request.form.get("month")
        day = request.form.get("day")

        # Validate input
        if not name or not month or not day:
            return redirect("/")
        try:
            month = int(month)
            day = int(day)
        except ValueError:
            return redirect("/")
        if month < 1 or month > 12 or day < 1 or day > 31:
            return redirect("/")

        # Insert new entry
        db.execute(
            "INSERT INTO birthdays (name, month, day) VALUES (?, ?, ?)",
            name, month, day
        )

        return redirect("/")

    else:
        # Query database for all birthdays
        birthdays = db.execute("SELECT * FROM birthdays")
        return render_template("index.html", birthdays=birthdays)
