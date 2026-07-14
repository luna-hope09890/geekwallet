import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import func

from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from GeekWallet.models import (
    db,
    User,
    Category,
    Transaction,
    Recurring,
    Budget,
)

import re
import calendar
import pymysql

#app = Flask(__name__)
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
#app.secret_key = "expense_tracker_secret"
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "expense_tracker_secret",
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db = SQLAlchemy(app)
db.init_app(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:Test%401234@localhost/geek_db",
)

# login required
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return route_function(*args, **kwargs)

    return wrapper


# default categories
def insert_default_categories():
    categories = [
        (1, "Salary", "Income", "💵"),
        (2, "Freelance", "Income", "💻"),
        (3, "Investments", "Income", "📈"),
        (4, "Bonus", "Income", "🪙"),
        (5, "Allowance", "Income", "💰"),
        (6, "Business", "Income", "👩‍💼"),
        (7, "Pocket Money", "Income", "🧧"),
        (8, "Other Income", "Income", "💳"),
        (9, "Food", "Expense", "🍽"),
        (10, "Clothing", "Expense", "👗"),
        (11, "Shopping", "Expense", "🛒"),
        (12, "Transportation", "Expense", "🚌"),
        (13, "Education", "Expense", "🎓"),
        (14, "Healthcare", "Expense", "👩‍⚕️"),
        (15, "Entertainment", "Expense", "🎭"),
        (16, "Personal Care", "Expense", "💇‍♀️"),
        (17, "Travel", "Expense", "✈️"),
        (18, "Savings", "Expense", "💰"),
        (19, "Gifts", "Expense", "🎁"),
        (20, "Donations", "Expense", "❤️"),
        (21, "Snacks", "Expense", "🍟"),
        (22, "Stationery", "Expense", "📚"),
        (23, "Rent & Housing", "Expense", "🏠"),
        (24, "Bills & Payments", "Expense", "💲"),
        (25, "Fitness", "Expense", "💪"),
        (26, "Loans", "Expense", "💵"),
        (27, "Other Expenses", "Expense", "💴"),
    ]
    for ctg_id, name, ctg_type, icon in categories:
        existing = Category.query.filter_by(ctg_id=ctg_id).first()
        if existing is None:
            category = Category(
                ctg_id=ctg_id, ctg_name=name, ctg_type=ctg_type, ctg_icon=icon
            )
            db.session.add(category)
    db.session.commit()


@app.route("/signup", methods=["GET", "POST"])
def signup():

    message = None
    redirect_to_login = False
    name = ""
    email = ""
    password = ""
    confirm = ""

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        # INVALID EMAIL
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            message = {
                "type": "error",
                "title": "Please enter a valid email address.",
                "detail": "",
            }
            return render_template("signup.html", message=message)

        if (
            len(password) < 8
            or not re.search(r"[A-Z]", password)
            or not re.search(r"[a-z]", password)
            or not re.search(r"[0-9]", password)
        ):
            message = None
            return render_template("signup.html", message=message)

        # 29-May-2026 luna rearranged this"
        existing_user = User.query.filter_by(email=email).first()

        # CHECK EXISTING EMAIL
        if existing_user:
            message = {
                "type": "error",
                "title": "Account already exists.",
                "detail": "An account with this email already exists.",
            }
            return render_template("signup.html", message=message)

        # PASSWORD NOT MATCH
        if password != confirm:
            message = {
                "type": "error",
                "title": "Passwords do not match.",
                "detail": "",
            }
            return render_template("signup.html", message=message)

        # HASH PASSWORD
        hashed_password = generate_password_hash(password)

        # CREATE USER
        new_user = User(name=name, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        message = {
            "type": "success",
            "title": "Account created successfully!",
            "detail": "Redirecting to Login...",
        }
        redirect_to_login = True
    return render_template(
        "signup.html",
        message=message,
        redirect=redirect_to_login,
        name=name if redirect_to_login else "",
        email=email if redirect_to_login else "",
        password=password if redirect_to_login else "",
        confirm=confirm if redirect_to_login else "",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    redirect_to_dashboard = False
    email = ""  # Luna added this on 6/23/2026
    password = ""  # Luna added this on 6/23/2026
    login_success = False  # Luna added this on 6/23/2026

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        # CHECK USER
        user = User.query.filter_by(email=email).first()

        # LOGIN SUCCESS
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.user_id
            message = {
                "type": "success",
                "title": "Login successful!",
                "detail": "Redirecting to Dashboard...",
            }
            redirect_to_dashboard = True
            login_success = True

        # WRONG PASSWORD
        elif user:
            message = {
                "type": "error",
                "title": "Invalid Password",
                "detail": "Please try again.",
            }

        # UNREGISTERED EMAIL
        else:
            message = {
                "type": "error",
                "title": "Invalid Credentials",
                "detail": "No account found with this email.",
            }
    return render_template(  # Luna added this on 6/23/2026
        "login.html",
        message=message,
        redirect=redirect_to_dashboard,
        email=email,
        password=password,
        login_success=login_success,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    message = None
    reset_link = None

    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()

        if user:
            reset_link = f"/reset?email={email}"
            message = {
                "type": "success",
                "title": "Password Reset",
                "detail": "Password reset link generated.",
            }
        else:
            message = {
                "type": "error",
                "title": "Invalid Credentials",
                "detail": "No account found with this email.",
            }
    return render_template(
        "forgot.html",
        message=message,
        link=reset_link,
        email=email if request.method == "POST" else "",
        reset_success=True if reset_link else False,
    )


@app.route("/reset", methods=["GET", "POST"])
def reset_password():
    email = request.args.get("email")
    message = None
    redirect_to_login = False
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["password"]
        confirm = request.form["confirm"]

        if new_password != confirm:
            message = None
            return render_template("reset.html", message=message, email=email)

        user = User.query.filter_by(email=email).first()
        if user:
            hashed = generate_password_hash(new_password)
            user.password = hashed
            db.session.commit()
            message = {
                "type": "success",
                "title": "Password Updated!",
                "detail": "Redirecting to Login...",
            }
            redirect_to_login = True
        else:
            message = {
                "type": "error",
                "title": "Invalid Credentials",
                "detail": "No account found with this email.",
            }
        return render_template(
            "reset.html",
            message=message,
            redirect=redirect_to_login,
            email=email,
            password=new_password,
            confirm=confirm,
        )
    return render_template("reset.html", email=email)


@app.route("/dashboard")
@login_required
def dashboard():
    # CURRENT DATE
    today = datetime.today()

    # GET MONTH/YEAR FROM URL
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    # FIRST DAY OF MONTH
    start_date = datetime(year, month, 1)

    # NEXT MONTH
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # category
    categories = Category.query.all()

    # filter transations
    recent_transactions = (
        Transaction.query.filter(
            Transaction.user_id == session["user_id"],
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .order_by(func.date(Transaction.date).desc(), Transaction.trans_id.desc())
        .limit(5)
        .all()
    )
    all_transactions = Transaction.query.filter(
        Transaction.user_id == session["user_id"],
        Transaction.date >= start_date,
        Transaction.date < end_date,
    ).all()

    # total
    total_income = 0
    total_expense = 0

    for transaction in all_transactions:
        if transaction.category.ctg_type == "Income":
            total_income += transaction.amount
        else:
            total_expense += transaction.amount

    total_balance = total_income - total_expense
    # Luna added this on 6/23/2026 -- ET5 + 6 Integration (START)
    raw_budgets = (
        db.session.query(Budget, Category.ctg_name, Category.ctg_icon)
        .join(Category, Budget.ctg_id == Category.ctg_id)
        .filter(
            Budget.user_id == session["user_id"],
            func.extract("month", Budget.start_date) == month,
            func.extract("year", Budget.start_date) == year,
        )
        # Dashboard : should be desc because if we use "asc", the oldest will be shown but it's ok
        .order_by(Budget.budget_id.asc())
        .limit(2)
        .all()
    )

    dashboard_budgets = []

    for budget, ctg_name, ctg_icon in raw_budgets:
        spent_amount = (
            db.session.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == session["user_id"],
                Transaction.ctg_id == budget.ctg_id,
                Transaction.date >= budget.start_date,
                Transaction.date <= budget.end_date,
                Transaction.exclude_budget == False,
            )
            .scalar()
            or 0
        )

        dashboard_budgets.append(
            {
                "id": budget.budget_id,
                "category": ctg_name,
                "icon": ctg_icon,
                "amount": budget.amt_limit,
                "spent": spent_amount,
                "note": budget.budget_note,
                "startDate": budget.start_date.strftime("%d.%m.%Y"),
                "endDate": budget.end_date.strftime("%d.%m.%Y"),
            }
        )
    # Luna added this on 6/23/2026 -- ET5 + 6 Integration (END)

    # PREVIOUS MONTH
    prev_month = month - 1
    prev_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    # NEXT MONTH
    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    user = db.session.get(User, session["user_id"])
    return render_template(
        "dashboard.html",
        user=user,
        categories=categories,
        transactions=recent_transactions,
        total_income=total_income,
        total_expense=total_expense,
        total_balance=total_balance,
        dashboard_budgets=dashboard_budgets,
        month=month,
        year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


@app.route("/add_record", methods=["POST"])
@login_required
def add_record():
    date_text = request.form.get("date")
    if date_text:
        record_date = datetime.strptime(date_text, "%Y-%m-%d")
    else:
        record_date = datetime.today()

    be_recurring = True if request.form.get("be_recurring") else False

    frequency = request.form.get("frequency")
    end_date_text = request.form.get("end_date")

    if be_recurring and (not frequency or not end_date_text):
        flash(
            "Please select frequency and end date for recurring transaction.", "danger"
        )
        return redirect(request.form.get("next_url", "/dashboard"))

    ctg_id = request.form.get("ctg_id")
    amount = request.form.get("amount")

    if not ctg_id:
        flash("Please select a category.", "danger")
        return redirect("/dashboard")

    if not amount:
        flash("Please enter an amount.", "danger")
        return redirect("/dashboard")

    transaction = Transaction(
        user_id=session["user_id"],
        ctg_id=request.form["ctg_id"],
        amount=request.form["amount"],
        note=request.form["note"],
        date=record_date,
        exclude_budget=True if request.form.get("exclude_budget") else False,
        be_recurring=be_recurring,
        source_recur_id=None,
    )

    db.session.add(transaction)
    db.session.commit()

    if be_recurring:
        if frequency and end_date_text:
            end_date = datetime.strptime(end_date_text, "%Y-%m-%d").date()

            recurring = Recurring(
                trans_id=transaction.trans_id,
                frequency=frequency,
                start_date=record_date.date(),
                end_date=end_date,
                next_date=calculate_next_date(record_date.date(), frequency),
                status="Active",
            )

            db.session.add(recurring)
            db.session.flush()

            backfill_recurring_transactions(recurring, transaction)

            db.session.commit()

    next_url = request.form.get("next_url", "/dashboard")
    return redirect(next_url)


# Recurring Engine Library - func 1
def get_next_occurrence(current_date, frequency):
    if frequency == "Daily":
        return current_date + timedelta(days=1)

    if frequency == "Weekly":
        return current_date + timedelta(weeks=1)

    if frequency == "Monthly":
        next_month = current_date.month + 1
        next_year = current_date.year

        if next_month == 13:
            next_month = 1
            next_year += 1

        day = current_date.day
        last_day = calendar.monthrange(next_year, next_month)[1]

        if day > last_day:
            day = last_day

        return current_date.replace(year=next_year, month=next_month, day=day)

    return current_date


# Recurring Engine Library - func 2
def is_duplicate_transaction(source_recur_id, transaction_date):
    return (
        Transaction.query.filter_by(
            source_recur_id=source_recur_id, date=transaction_date
        ).first()
        is not None
    )


# Recurring Engine Library - func 3
def calculate_next_date(start_date, frequency):
    today = date.today()

    next_date = start_date

    while next_date <= today:
        next_date = get_next_occurrence(next_date, frequency)

    return next_date


# Recurring Engine Library - func 4
def generate_recurring_transaction(
    recurring_plan, master_transaction, transaction_date
):
    """
    Create one generated recurring transaction.
    It copies the latest data from the master transaction.
    """
    new_transaction = Transaction(
        user_id=master_transaction.user_id,
        ctg_id=master_transaction.ctg_id,
        amount=master_transaction.amount,
        note=master_transaction.note,
        date=transaction_date,
        exclude_budget=master_transaction.exclude_budget,
        be_recurring=False,
        source_recur_id=recurring_plan.recur_id,
    )
    db.session.add(new_transaction)


# Donut Chart - setting rule to show category items function 1
def limit_chart_categories(labels, amounts, max_items=8):
    combined = sorted(zip(labels, amounts), key=lambda item: item[1], reverse=True)

    if len(combined) <= max_items:
        return labels, amounts

    top_items = combined[: max_items - 1]
    other_items = combined[max_items - 1 :]

    new_labels = [item[0] for item in top_items]
    new_amounts = [item[1] for item in top_items]

    new_labels.append("Other…")
    new_amounts.append(sum(item[1] for item in other_items))

    return new_labels, new_amounts


# backfill/auto generate transaction function
def backfill_recurring_transactions(recurring_plan, master_transaction):
    """
    Generate missing recurring transactions from the recurring start date
    up to today, without creating duplicate records.

    This function will be completed step by step.
    """
    today = date.today()

    current_date = get_next_occurrence(
        recurring_plan.start_date, recurring_plan.frequency
    )
    frequency = recurring_plan.frequency
    end_date = recurring_plan.end_date

    while current_date <= today and current_date <= end_date:
        if not is_duplicate_transaction(recurring_plan.recur_id, current_date):
            generate_recurring_transaction(
                recurring_plan, master_transaction, current_date
            )
        current_date = get_next_occurrence(current_date, frequency)

    db.session.commit()


def get_next_recurring_date(start_date, frequency):
    today = datetime.today().date()

    next_date = start_date

    if frequency == "Daily":
        while next_date <= today:
            next_date = next_date + timedelta(days=1)

    elif frequency == "Weekly":
        while next_date <= today:
            next_date = next_date + timedelta(days=7)

    elif frequency == "Monthly":
        while next_date <= today:
            next_month = next_date.month + 1
            next_year = next_date.year

            if next_month == 13:
                next_month = 1
                next_year += 1

            day = start_date.day
            last_day = calendar.monthrange(next_year, next_month)[1]

            if day > last_day:
                day = last_day

            next_date = datetime(next_year, next_month, day).date()

    return next_date


def process_recurring_transactions():
    plans = Recurring.query.filter_by(status="Active").all()
    today = datetime.today().date()

    for plan in plans:

        if plan.next_date and plan.next_date <= today:

            if plan.next_date > plan.end_date:
                plan.status = "Completed"
                continue

            existing = Transaction.query.filter_by(
                source_recur_id=plan.recur_id,
                date=plan.next_date,
            ).first()

            if existing:
                plan.next_date = get_next_occurrence(plan.next_date, plan.frequency)
                continue

            transaction = Transaction(
                user_id=plan.transaction.user_id,
                ctg_id=plan.transaction.ctg_id,
                amount=plan.transaction.amount,
                note=plan.transaction.note,
                date=plan.next_date,
                exclude_budget=plan.transaction.exclude_budget,
                be_recurring=False,
                source_recur_id=plan.recur_id,
            )

            db.session.add(transaction)

            plan.next_date = get_next_occurrence(plan.next_date, plan.frequency)

            if plan.next_date > plan.end_date:
                plan.status = "Completed"

    db.session.commit()


@app.route("/edit_recurring", methods=["POST"])
@login_required
def edit_recurring():
    recur_id = request.form["recur_id"]

    recurring = (
        Recurring.query.join(Transaction)
        .filter(
            Recurring.recur_id == recur_id, Transaction.user_id == session["user_id"]
        )
        .first_or_404()
    )

    transaction = recurring.transaction

    transaction.ctg_id = request.form["ctg_id"]
    transaction.amount = request.form["amount"]
    transaction.note = request.form["note"]

    recurring.frequency = request.form["frequency"]
    recurring.end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()

    recurring.next_date = calculate_next_date(recurring.start_date, recurring.frequency)

    if recurring.next_date > recurring.end_date:
        recurring.status = "Completed"
    else:
        recurring.status = "Active"

    db.session.commit()

    return redirect("/drecords?view=recurring")


@app.route("/delete_recurring/<int:recur_id>")
@login_required
def delete_recurring(recur_id):
    plan = (
        Recurring.query.join(Transaction)
        .filter(
            Recurring.recur_id == recur_id, Transaction.user_id == session["user_id"]
        )
        .first_or_404()
    )
    plan.status = "Deleted"
    plan.transaction.be_recurring = False

    db.session.commit()
    return redirect("/drecords?view=recurring")


@app.route("/drecords")
@login_required
def drecords():
    process_recurring_transactions()
    today = datetime.today()

    view = request.args.get("view", "history")

    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    prev_month = month - 1
    prev_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    user = db.session.get(User, session["user_id"])
    categories = Category.query.all()

    transactions = (
        Transaction.query.filter(
            Transaction.user_id == session["user_id"],
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .order_by(func.date(Transaction.date).desc(), Transaction.trans_id.desc())
        .all()
    )
    recurring_plans = (
        Recurring.query.join(Transaction)
        .filter(
            Transaction.user_id == session["user_id"], Recurring.status != "Deleted"
        )
        .order_by(Recurring.start_date.desc())
        .all()
    )

    filtered_recurring_plans = []

    for plan in recurring_plans:
        plan.next_date = get_next_recurring_date(plan.start_date, plan.frequency)

        if plan.next_date.month == month and plan.next_date.year == year:
            filtered_recurring_plans.append(plan)

    recurring_plans = filtered_recurring_plans

    return render_template(
        "drecords.html",
        user=user,
        categories=categories,
        transactions=transactions,
        recurring_plans=recurring_plans,
        view=view,
        month=month,
        year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


# Edit : only amount and note editable
@app.route("/edit_record", methods=["POST"])
@login_required
def edit_record():
    trans_id = request.form["trans_id"]
    transaction = Transaction.query.filter_by(
        trans_id=trans_id, user_id=session["user_id"]
    ).first_or_404()
    transaction.ctg_id = request.form["ctg_id"]
    transaction.amount = request.form["amount"]
    transaction.note = request.form["note"]

    db.session.commit()

    next_url = request.form.get("next_url", "/drecords")
    return redirect(next_url)


@app.route("/delete_record/<int:trans_id>")
@login_required
def delete_record(trans_id):
    transaction = Transaction.query.get_or_404(trans_id)

    db.session.delete(transaction)

    db.session.commit()

    return redirect("/drecords")


@app.route("/dreports")
@login_required
def dreports():
    # Setup the date boundary variables (e.g., looking back 4 weeks / 28 days)
    today = datetime.today()

    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    start_date = datetime(year, month, 1)

    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    user = db.session.get(User, session["user_id"])
    categories = Category.query.all()
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")  # Security redirect if the user isn't logged in

    # doughnut chart(spending)
    expense_results = (
        db.session.query(
            Category.ctg_name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.ctg_id == Category.ctg_id)
        .filter(
            Transaction.user_id == user_id,
            Category.ctg_type == "Expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .group_by(Category.ctg_id, Category.ctg_name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    # for int() argument error
    spending_labels = []
    spending_amounts = []

    for row in expense_results:
        spending_labels.append(row[0])  # Category Name

        # Safe fallback check if database column is empty
        if row[1] is not None:
            spending_amounts.append(int(row[1]))
        else:
            spending_amounts.append(0)

    spending_labels, spending_amounts = limit_chart_categories(
        spending_labels, spending_amounts
    )
    spending_categories = {"labels": spending_labels, "amounts": spending_amounts}

    # doughnut chart(income)
    # Doughnut chart: Income Sources
    income_src_results = (
        db.session.query(
            Category.ctg_name,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.ctg_id == Category.ctg_id)
        .filter(
            Transaction.user_id == user_id,
            Category.ctg_type == "Income",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .group_by(Category.ctg_id, Category.ctg_name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    income_labels = []
    income_amounts = []
    for row in income_src_results:
        income_labels.append(row[0])
        if row[1] is not None:
            income_amounts.append(float(row[1]))
        else:
            income_amounts.append(0)

    income_labels, income_amounts = limit_chart_categories(
        income_labels, income_amounts
    )

    income_sources = {"labels": income_labels, "amounts": income_amounts}

    # bar chart(category)

    # The doughnut chart needs two separate lists: one for labels, one for numbers
    category_summary = {
        "labels": [row[0] for row in expense_results],
        "amounts": [float(row[1]) for row in expense_results],
    }

    # Line chart: Income vs. Expenses by week
    week_number = (
        func.floor(func.datediff(Transaction.date, start_date) / 7) + 1
    ).label("week_no")

    query_results = (
        db.session.query(
            week_number,
            Category.ctg_type,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.ctg_id == Category.ctg_id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .group_by(week_number, Category.ctg_type)
        .order_by(week_number)
        .all()
    )

    # Create empty baseline arrays for 4 weeks of data
    weekly_income = [0, 0, 0, 0]
    weekly_expenses = [0, 0, 0, 0]
    weeks_labels = ["1-7", "8-14", "15-21", "22-31"]

    # Loop through the query results and sort values into the right week slot
    for row in query_results:
        week_idx = (
            int(row[0]) - 1
        )  # Shifts week numbers 1-4 to array index positions 0-3
        ctg_type = row[1]
        total_amount = float(row[2])

        # Safely assign values to the arrays based on type string match
        if 0 <= week_idx < 4:
            if ctg_type == "Income":
                weekly_income[week_idx] = total_amount
            elif ctg_type == "Expense":
                weekly_expenses[week_idx] = total_amount

    # Group the line chart data into the unified 'tracker' dictionary structure
    income_vs_expenses = {
        "months": weeks_labels,
        "income": weekly_income,
        "expenses": weekly_expenses,
    }

    # PREVIOUS MONTH
    prev_month = month - 1
    prev_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    # NEXT MONTH
    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    return render_template(
        "dreports.html",
        time=weeks_labels,
        spending=spending_categories,
        income=income_sources,
        summary=category_summary,
        tracker=income_vs_expenses,  # type_total
        categories=categories,
        user=user,
        start_date=start_date,
        end_date=end_date,
        month=month,
        year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


@app.route("/dbudget", methods=["GET", "POST"])
@login_required
def dbudget():
    categories = Category.query.all()
    budget_categories = Category.query.filter_by(ctg_type="Expense").all()

    if request.method == "POST":
        budget_id = request.form.get("budget_id")
        ctg_id = request.form.get("ctg_id")
        amount = request.form.get("amount")
        period = request.form.get("period")
        budget_note = request.form.get("budget_note")
        start_date = request.form.get("start_date")
        end_date = request.form.get(
            "end_date"
        )  # Luna added this on 6/23/2026 -- ET5 + 6 Integration

        parsed_date = (
            datetime.strptime(start_date, "%Y-%m-%d").date()
            if start_date
            else datetime.today().date()
        )

        parsed_end_date = (
            datetime.strptime(end_date, "%Y-%m-%d").date()
            if end_date
            else datetime.today().date()
        )

        if budget_id:
            budget = Budget.query.filter_by(
                budget_id=budget_id, user_id=session["user_id"]
            ).first()
            if budget:
                budget.amt_limit = amount
                budget.budget_note = budget_note
                db.session.commit()
                return redirect(url_for("dbudget"))

        new_budget = Budget(
            user_id=session["user_id"],
            ctg_id=ctg_id,
            amt_limit=amount,  #  amt_limit changing
            frequency=period,  #  frequency changing
            start_date=(
                datetime.strptime(start_date, "%Y-%m-%d").date()
                if start_date
                else datetime.today().date()
            ),
            end_date=parsed_end_date,
            budget_note=budget_note,
            budget_noti=True,
        )

        db.session.add(new_budget)
        db.session.commit()
        return redirect(url_for("dbudget"))

    raw_budgets = (
        Budget.query.filter_by(user_id=session["user_id"])
        .order_by(Budget.budget_id.desc())
        .all()
    )

    budgets_list = []
    for b in raw_budgets:
        ctg = Category.query.get(b.ctg_id)
        spent_sum = (
            db.session.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == session["user_id"],
                Transaction.ctg_id == b.ctg_id,
                Transaction.exclude_budget == False,
                Transaction.date >= b.start_date,
                Transaction.date <= b.end_date,
            )
            .scalar()
            or 0
        )

        budgets_list.append(
            {
                "id": b.budget_id,
                "budget_id": b.budget_id,
                "ctg_id": b.ctg_id,
                "category": ctg.ctg_name if ctg else "Unknown",
                "icon": ctg.ctg_icon if ctg else "💰",
                "amount": b.amt_limit,
                "spent": int(spent_sum),
                "note": b.budget_note,
                "startDate": b.start_date.strftime("%Y-%m-%d") if b.start_date else "",
                "endDate": b.end_date.strftime("%Y-%m-%d") if b.end_date else "",
                "period": b.frequency,
            }
        )

    return render_template(
        "dbudget.html",
        budgets=budgets_list,
        categories=categories,
        budget_categories=budget_categories,
        user=db.session.get(User, session["user_id"]),
    )


# for delete
@app.route("/dbudget/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(
        budget_id=budget_id, user_id=session["user_id"]
    ).first()
    if budget:
        db.session.delete(budget)
        db.session.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Budget Not Found"}, 404


@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dabout")
@login_required
def dabout():
    categories = Category.query.all()
    user = db.session.get(User, session["user_id"])

    return render_template("dabout.html", categories=categories, user=user)


@app.route("/support")
def support():
    return render_template("support.html")


@app.route("/dsupport")
@login_required
def dsupport():
    categories = Category.query.all()
    user = db.session.get(User, session["user_id"])

    return render_template("dsupport.html", categories=categories, user=user)


@app.route("/category_list")
@login_required
def category_list():
    categories = Category.query.all()

    user = db.session.get(User, session["user_id"])

    income_categories = Category.query.filter_by(ctg_type="Income").all()
    expense_categories = Category.query.filter_by(ctg_type="Expense").all()

    return render_template(
        "category_list.html",
        user=user,
        categories=categories,
        income_categories=income_categories,
        expense_categories=expense_categories,
    )


@app.route("/setting")
@login_required
def setting():
    categories = Category.query.all()
    user = db.session.get(User, session["user_id"])

    password_message = session.pop("password_message", None)
    password_success = session.pop("password_success", False)
    current_password = session.pop("current_password", "")
    new_password = session.pop("new_password", "")
    confirm_password = session.pop("confirm_password", "")

    return render_template(
        "setting.html",
        categories=categories,
        user=user,
        password_message=password_message,
        password_success=password_success,
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
    )


@app.route("/change_name", methods=["POST"])
@login_required
def change_name():
    user = db.session.get(User, session["user_id"])

    new_name = request.form["new_name"].strip()

    if new_name:
        user.name = new_name
        db.session.commit()

    return redirect("/setting")


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    user = db.session.get(User, session["user_id"])

    current_password = request.form["current_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if not check_password_hash(user.password, current_password):
        session["password_message"] = {
            "type": "error",
            "detail": "Current password is incorrect.",
        }
        return redirect("/setting")

    if check_password_hash(user.password, new_password):
        session["password_message"] = {
            "type": "error",
            "detail": "New password must be different.",
        }
        return redirect("/setting")

    if new_password != confirm_password:
        session["password_message"] = {
            "type": "error",
            "detail": "Passwords do not match.",
        }
        return redirect("/setting")

    user.password = generate_password_hash(new_password)
    db.session.commit()

    session["password_message"] = {
        "type": "success",
        "detail": "Password changed successfully.",
    }
    session["password_success"] = True
    session["current_password"] = current_password
    session["new_password"] = new_password
    session["confirm_password"] = confirm_password

    return redirect("/setting")


@app.route("/financial_tips")
@login_required
def financial_tips():
    user = db.session.get(User, session["user_id"])
    categories = Category.query.all()
    today_date = datetime.today().strftime("%Y-%m-%d")

    return render_template(
        "financial_tips.html", user=user, categories=categories, today_date=today_date
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


# Global connection error (database error)
@app.errorhandler(SQLAlchemyError)
def handle_database_error(error):
    db.session.rollback()
    return render_template("connection_error.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        insert_default_categories()  # this one is for insert default categories
    app.run(debug=True)
