import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    
    # Get the transaction portfolio of the users
    portfolio = db.execute("SELECT symbol, name, SUM(shares_number) AS num_shares FROM stock WHERE user_id = ? GROUP BY symbol HAVING (num_shares) > 0", session["user_id"])

    # Get the Price = lookup(request.form.get("symbol"))["price"]

    # Check how much cash the user has in the account
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

    # Find the Total $
    total_value = cash 

    # Add up the value to find new total
    for stock in portfolio:
        stock["price"] = lookup(stock["symbol"])["price"] 
        total_value += stock["price"] * stock["num_shares"]

    # view the stocks that the user holds
    return render_template("index.html", portfolio=portfolio, cash=cash, total_value=total_value)

# Allow users to add more cash into their account


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add cash value"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure that the user inputs an amount to be added
        if not request.form.get("amount"):
            return apology("missing cash amount", 400)

        # Check that the amount is a valid
        # Ensure that amount is a number
        try: 
            float_amount = float(request.form.get("amount"))
        except ValueError:
            return apology("invalid amount", 400)

        # Check that the amount doesn't have more than 2 decimal places
        if round(float_amount, 2) != float_amount:
            return apology("invalid amount", 400)

        # Ensure that the amount is positive
        elif float_amount < 0:
            return apology("invalid amount", 400)

        # Check how much cash the user has in the account
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

        # Update cash from account to reflect the amount added
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + float_amount, session["user_id"])

        # Display the index HTML page to show updated cash amount 
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure that the user inputs a symbol
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Ensure that the symbol is valid
        elif lookup(request.form.get("symbol")) == None:
            return apology("invalid symbol", 400)
        
        # Ensure that user inputs a number of shares to buy
        elif not request.form.get("shares"):
            return apology("missing shares", 400)

        # Ensure that shares is valid number
        elif not request.form.get("shares").isdigit():
            return apology("invalid shares", 400)
        
        # Find price of shares
        price = lookup(request.form.get("symbol"))["price"]

        # store the number of shares
        shares = int(request.form.get("shares"))
            
        # Ensure that at least one share is purchased
        if shares < 1:
            return apology("invalid shares", 400)

        # Calculate the total price
        total_cost = shares * price
        
        # Check how much cash the user has in the account
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

        # Ensure that the user has enough cash for the transaction
        if total_cost > cash:
            return apology("not enough cash", 400)

        # Sucessful purchase
        # Update cash from account to reflect purchased stock
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - total_cost, session["user_id"])

        # Record the transaction 
        db.execute("INSERT INTO stock (user_id, symbol, name, shares_number, shares_price, shares_cost) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], request.form.get("symbol"), lookup(request.form.get("symbol"))["name"], shares, price, total_cost)
        
        # Display the index HTML page to view stocks
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Show the information from the SQL table where the transactions were stored
    history = db.execute("SELECT * FROM stock WHERE user_id = ?", session["user_id"])

    # Display the history HTML page
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure that the user inputs a symbol
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Ensure that the symbol is valid
        elif lookup(request.form.get("symbol")) == None:
            return apology("invalid symbol", 400)

        # Display the quoted page
        return render_template("quoted.html", stock=lookup(request.form.get("symbol")))

    # User reached route via GET
    else: 
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Query database for username
    list = db.execute("SELECT username FROM users WHERE username = ?", request.form.get("username"))
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check that username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)
        
        # Check that password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Check that passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Check that username is new
        elif len(list) != 0:
            return apology("Username is already taken", 400)

        # remember successful registrants 
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
            
        # redirect to main page
        return redirect("/")
        
    # User reached route via GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure that the user inputs a symbol
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)
        
        # Ensure that user inputs a number of shares to buy
        elif not request.form.get("shares"):
            return apology("missing shares", 400)

        # Ensure that shares is valid number
        elif not request.form.get("shares").isdigit():
            return apology("invalid shares", 400)
        
        # Find price of shares
        price = lookup(request.form.get("symbol"))["price"]

        # store the number of shares
        shares = int(request.form.get("shares"))

        # Ensure that at least one share is sold
        if shares < 1:
            return apology("invalid shares", 400)

        # Get the transaction portfolio of the users
        shares_owned = db.execute("SELECT SUM(shares_number) AS num_shares FROM stock WHERE user_id = ? AND symbol = ?", session["user_id"], request.form.get("symbol"))[0]["num_shares"]
            
        # Ensure that user isn't selling more shares than they have
        if shares > shares_owned:
            return apology("invalid shares", 400)

         # Calculate the total price
        total_cost = shares * price
        
        # Check how much cash the user has in the account
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

        # Successful sell 
        # Update cash from account to reflect sold stock
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + total_cost, session["user_id"])

        # Record the transaction 
        db.execute("INSERT INTO stock (user_id, symbol, name, shares_number, shares_price, shares_cost) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], request.form.get("symbol"), lookup(request.form.get("symbol"))["name"], shares * -1, price, total_cost)
        
        # View current/updated stocks
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        symbol = db.execute("SELECT DISTINCT(symbol) FROM stock WHERE user_id = ?", session["user_id"])
        return render_template("sell.html", symbol=symbol)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
