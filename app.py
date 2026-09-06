from flask import Flask, render_template, request, redirect, flash, url_for, session
import database as db
from datetime import datetime
import math
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        
        return function(*args, **kwargs)

    return wrapper

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
        
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_input = request.form.get("amount", "").strip()
        
        amount, error = validate_expense(category, amount_input)
        
        if error:
           flash(error, "error")
           return redirect(url_for("index"))
           
        db.add_expense(session["user_id"],category, amount)

        flash("Expense added successfully!")

        return redirect(url_for("index"))
    
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort","newest")
    month = request.args.get("month","")
    
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    if page < 1:
        page = 1
    
    limit = 10
    offset = (page - 1) * limit
    
    expenses = db.get_expenses(session["user_id"], search, sort, month, limit, offset)
    
    filtered_count = db.get_expense_count(session["user_id"],month, search)
    
    total_pages = math.ceil(filtered_count / limit)
     
    spending_by_category = db.get_spending_by_category(session["user_id"],month)
    
    chart_categories = []
    chart_totals = [] 
    for row in spending_by_category:
        chart_categories.append(row[0])
        chart_totals.append(row[1]) 
    
    formatted_expenses = []
    for expense in expenses:
        date_object = datetime.strptime(expense[3],
                      "%Y-%m-%d %H:%M:%S")
        
        formatted_date = date_object.strftime(
                       "%b %d, %Y at %I:%M %p")
    
        updated_expense= (expense[0], expense[1], 
                          expense[2], formatted_date)
        
        formatted_expenses.append(updated_expense)
        
    total = db.get_total(session["user_id"], month)
    expense_count = db.get_expense_count(session["user_id"], month)
    largest_expense = db.get_largest_expense(session["user_id"], month)
    average_expense = db.get_average_expense(session["user_id"], month)
    highest_category = db.get_highest_spending_category(session["user_id"], month)
    
    return render_template("index.html",  expenses = formatted_expenses,
                chart_categories=chart_categories,chart_totals=chart_totals,
                total=total,expense_count=expense_count,
                filtered_count = filtered_count,total_pages = total_pages,
                largest_expense=largest_expense,
                average_expense = average_expense,
                highest_category = highest_category,
                search = search, sort =sort,page = page)
 
@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required 
def delete_expense(expense_id):
    
    deleted = db.delete_expense(expense_id, session["user_id"])
    
    if deleted == 1:
        flash("Expense deleted successfully!")
    else:
        flash("Expense not found.")
    return redirect(url_for("index"))

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required 
def edit_expense(expense_id):
    
    expense = db.get_expense_by_id(expense_id, session["user_id"])

    if expense is None:
        flash("Expense not found.","error")
        return redirect(url_for("index"))

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_input = request.form.get("amount", "").strip()
        date = request.form.get("date", "").strip()
        
        amount, error = validate_expense(category, amount_input)

        if error:
            flash(error, "error")
            return redirect(url_for("edit_expense", expense_id=expense_id))
        
        if date == "":
            flash("Date cannot be empty.","error")
            return redirect(url_for("edit_expense", expense_id=expense[0]))
        
        db.edit_expense(expense_id, session["user_id"], category, amount, date)
        
        flash("Expense updated successfully!")

        return redirect(url_for("index"))

    return render_template("edit.html", expense=expense)

@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method =="POST":
        username= request.form.get("username","").strip()
        password= request.form.get("password","").strip()
        confirm_password= request.form.get("confirm_password","").strip()
    
        if not username:
            flash("Username cannot be empty.", "error")
            return redirect(url_for("register"))
        if not password:
            flash("Password cannot be empty.", "error")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        
        password_hash = generate_password_hash(password)    
        
        try:
            db.register_user(username, password_hash)
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
            return redirect(url_for("register"))
        
        flash("Registration successful!", "success")
        return redirect(url_for("login"))
    
    return  render_template("register.html")   
    
@app.route("/login", methods= ["GET", "POST"])  
def login():
    
    if request.method =="POST":
        username= request.form.get("username","").strip()  
        password= request.form.get("password","").strip()
        
        if not username:
            flash("Username cannot be empty.", "error")
            return redirect(url_for("login"))

        if not password:
            flash("Password cannot be empty.", "error")
            return redirect(url_for("login"))
        
        user = db.get_user_by_username(username)

        if user is None:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))
        
        password_check = check_password_hash(user[2], password)
        
        if not password_check:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))
        
        session["user_id"] = user[0]
           
        return redirect(url_for("index"))
    
    return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login")) 
  
  
def validate_expense(category, amount_input):
    
    if category == "":
        return None, "Category cannot be empty."

    try:
        amount = float(amount_input)
    except ValueError:
        return None, "Invalid amount"

    if amount <= 0:
        return None, "Amount must be greater than zero."
    
    return amount, None
    