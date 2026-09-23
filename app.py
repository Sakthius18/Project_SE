from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = "smart-expenses-tracker-secret-key"

DATA_DIR = "data"

TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.csv")
BUDGETS_FILE = os.path.join(DATA_DIR, "budgets.csv")


# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------
TRANSACTIONS_FILE = "data/transactions.csv"
CATEGORIES_FILE = "data/categories.csv"
BUDGETS_FILE = "data/budgets.csv"
USERS_FILE = "data/users.csv"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def read_users():
    if not os.path.exists(USERS_FILE):
        return []

    with open(USERS_FILE, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def save_user(user):
    file_exists = os.path.exists(USERS_FILE)

    with open(USERS_FILE, "a", newline="", encoding="utf-8") as file:
        fieldnames = ["id", "name", "email", "password"]

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists or os.path.getsize(USERS_FILE) == 0:
            writer.writeheader()

        writer.writerow(user)

def initialize_files():

    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "id",
                "user_id",
                "type",
                "amount",
                "category",
                "date",
                "description",
                "payment_method"
            ])

    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "user_id", "name", "type"])

            default_categories = [
                [1, "Food", "expense"],
                [2, "Transport", "expense"],
                [3, "Shopping", "expense"],
                [4, "Bills", "expense"],
                [5, "Entertainment", "expense"],
                [6, "Health", "expense"],
                [7, "Education", "expense"],
                [8, "Salary", "income"],
                [9, "Other", "income"]
            ]

            # Default categories are created per user when they sign up.
            # Keep the file empty initially so one user's categories
            # cannot automatically appear for another user.

    if not os.path.exists(BUDGETS_FILE):
        with open(BUDGETS_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "id",
                "user_id",
                "category",
                "amount",
                "month"
            ])


# --------------------------------------------------
# CSV HELPERS
# --------------------------------------------------

def read_csv(filename):

    with open(filename, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(filename, fieldnames, rows):

    with open(filename, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)


def get_next_id(filename):

    rows = read_csv(filename)

    if not rows:
        return 1

    return max(int(row["id"]) for row in rows) + 1


def login_required():
    """Return the current user's ID or redirect to login."""
    return session.get("user_id")


def user_rows(filename):
    """Return only rows belonging to the logged-in user."""
    user_id = login_required()
    if user_id is None:
        return []
    return [
        row for row in read_csv(filename)
        if row.get("user_id") == str(user_id)
    ]


def get_next_user_id(filename, user_id):
    """Generate an ID that is unique within the user's records."""
    rows = user_rows(filename)
    if not rows:
        return 1
    return max(int(row["id"]) for row in rows) + 1


def create_default_categories(user_id):
    """Create the default categories for a newly registered user."""
    rows = read_csv(CATEGORIES_FILE)

    defaults = [
        ("Food", "expense"),
        ("Transport", "expense"),
        ("Shopping", "expense"),
        ("Bills", "expense"),
        ("Entertainment", "expense"),
        ("Health", "expense"),
        ("Education", "expense"),
        ("Salary", "income"),
        ("Other", "income")
    ]

    next_id = get_next_user_id(CATEGORIES_FILE, user_id)

    for name, category_type in defaults:
        rows.append({
            "id": str(next_id),
            "user_id": str(user_id),
            "name": name,
            "type": category_type
        })
        next_id += 1

    write_csv(
        CATEGORIES_FILE,
        ["id", "user_id", "name", "type"],
        rows
    )


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    transactions = user_rows(TRANSACTIONS_FILE)

    total_income = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "income"
    )

    total_expenses = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "expense"
    )

    balance = total_income - total_expenses

    current_month = datetime.now().strftime("%Y-%m")

    monthly_expenses = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "expense"
        and t["date"].startswith(current_month)
    )

    recent_transactions = sorted(
        transactions,
        key=lambda x: x["date"],
        reverse=True
    )[:5]

    category_totals = {}

    for transaction in transactions:

        if transaction["type"] == "expense":

            category = transaction["category"]

            category_totals[category] = (
                category_totals.get(category, 0)
                + float(transaction["amount"])
            )

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        monthly_expenses=monthly_expenses,
        recent_transactions=recent_transactions,
        category_totals=category_totals
    )


# --------------------------------------------------
# TRANSACTIONS
# --------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("signup"))

        users = read_users()

        for user in users:
            if user["email"].lower() == email:
                flash("An account with this email already exists.", "error")
                return redirect(url_for("signup"))

        new_id = str(len(users) + 1)

        save_user({
            "id": new_id,
            "name": name,
            "email": email,
            "password": hash_password(password)
        })

        # Every user gets their own independent default categories.
        create_default_categories(new_id)

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        users = read_users()

        for user in users:

            if (
                user["email"].lower() == email
                and user["password"] == hash_password(password)
            ):

                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]

                flash("Login successful.", "success")

                return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))

@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    rows = user_rows(TRANSACTIONS_FILE)

    search = request.args.get("search", "").lower()
    transaction_type = request.args.get("type", "")
    category = request.args.get("category", "")

    filtered = []

    for row in rows:

        matches_search = (
            search in row["description"].lower()
            or search in row["category"].lower()
        )

        matches_type = (
            not transaction_type
            or row["type"] == transaction_type
        )

        matches_category = (
            not category
            or row["category"] == category
        )

        if matches_search and matches_type and matches_category:
            filtered.append(row)

    filtered.reverse()

    categories = user_rows(CATEGORIES_FILE)

    return render_template(
        "transactions.html",
        transactions=filtered,
        categories=categories
    )


# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

@app.route("/transactions/add", methods=["GET", "POST"])
def add_transaction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    categories = user_rows(CATEGORIES_FILE)

    if request.method == "POST":

        transaction = {
            "id": str(get_next_user_id(TRANSACTIONS_FILE, session["user_id"])),
            "user_id": str(session["user_id"]),
            "type": request.form["type"],
            "amount": request.form["amount"],
            "category": request.form["category"],
            "date": request.form["date"],
            "description": request.form["description"],
            "payment_method": request.form["payment_method"]
        }

        rows = read_csv(TRANSACTIONS_FILE)

        rows.append(transaction)

        write_csv(
            TRANSACTIONS_FILE,
            [
                "id",
                "user_id",
                "type",
                "amount",
                "category",
                "date",
                "description",
                "payment_method"
            ],
            rows
        )

        return redirect(url_for("transactions"))

    return render_template(
        "add_transaction.html",
        categories=categories
    )


# --------------------------------------------------
# EDIT TRANSACTION
# --------------------------------------------------

@app.route("/transactions/edit/<int:id>", methods=["GET", "POST"])
def edit_transaction(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    rows = read_csv(TRANSACTIONS_FILE)

    transaction = next(
        (
            row for row in rows
            if int(row["id"]) == id
            and row.get("user_id") == str(session["user_id"])
        ),
        None
    )

    if transaction is None:
        return "Transaction not found", 404

    categories = user_rows(CATEGORIES_FILE)

    if request.method == "POST":

        transaction["type"] = request.form["type"]
        transaction["amount"] = request.form["amount"]
        transaction["category"] = request.form["category"]
        transaction["date"] = request.form["date"]
        transaction["description"] = request.form["description"]
        transaction["payment_method"] = request.form["payment_method"]

        write_csv(
            TRANSACTIONS_FILE,
            [
                "id",
                "user_id",
                "type",
                "amount",
                "category",
                "date",
                "description",
                "payment_method"
            ],
            rows
        )

        return redirect(url_for("transactions"))

    return render_template(
        "edit_transaction.html",
        transaction=transaction,
        categories=categories
    )


# --------------------------------------------------
# DELETE TRANSACTION
# --------------------------------------------------

@app.route("/transactions/delete/<int:id>")
def delete_transaction(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    rows = read_csv(TRANSACTIONS_FILE)

    rows = [
        row for row in rows
        if not (
            int(row["id"]) == id
            and row.get("user_id") == str(session["user_id"])
        )
    ]

    write_csv(
        TRANSACTIONS_FILE,
        [
            "id",
            "user_id",
            "type",
            "amount",
            "category",
            "date",
            "description",
            "payment_method"
        ],
        rows
    )

    return redirect(url_for("transactions"))


# --------------------------------------------------
# BUDGETS
# --------------------------------------------------

@app.route("/budgets", methods=["GET", "POST"])
def budgets():

    if "user_id" not in session:
        return redirect(url_for("login"))

    budgets_data = user_rows(BUDGETS_FILE)
    categories = user_rows(CATEGORIES_FILE)

    if request.method == "POST":

        budget = {
            "id": str(get_next_user_id(BUDGETS_FILE, session["user_id"])),
            "user_id": str(session["user_id"]),
            "category": request.form["category"],
            "amount": request.form["amount"],
            "month": request.form["month"]
        }

        budgets_data.append(budget)

        write_csv(
            BUDGETS_FILE,
            ["id", "user_id", "category", "amount", "month"],
            budgets_data
        )

        return redirect(url_for("budgets"))

    transactions = user_rows(TRANSACTIONS_FILE)

    for budget in budgets_data:

        spent = 0

        for transaction in transactions:

            if (
                transaction["type"] == "expense"
                and transaction["category"] == budget["category"]
                and transaction["date"].startswith(budget["month"])
            ):

                spent += float(transaction["amount"])

        budget["spent"] = spent

        budget["remaining"] = (
            float(budget["amount"]) - spent
        )

        if float(budget["amount"]) > 0:

            budget["percentage"] = min(
                100,
                round(
                    (spent / float(budget["amount"])) * 100,
                    2
                )
            )

        else:
            budget["percentage"] = 0

    return render_template(
        "budgets.html",
        budgets=budgets_data,
        categories=categories
    )


@app.route("/budgets/delete/<int:id>")
def delete_budget(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    rows = read_csv(BUDGETS_FILE)

    rows = [
        row for row in rows
        if not (
            int(row["id"]) == id
            and row.get("user_id") == str(session["user_id"])
        )
    ]

    write_csv(
        BUDGETS_FILE,
        ["id", "user_id", "category", "amount", "month"],
        rows
    )

    return redirect(url_for("budgets"))


# --------------------------------------------------
# REPORTS
# --------------------------------------------------

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    transactions = user_rows(TRANSACTIONS_FILE)

    monthly_data = {}

    category_data = {}

    for transaction in transactions:

        month = transaction["date"][:7]

        if month not in monthly_data:
            monthly_data[month] = {
                "income": 0,
                "expense": 0
            }

        amount = float(transaction["amount"])

        if transaction["type"] == "income":

            monthly_data[month]["income"] += amount

        else:

            monthly_data[month]["expense"] += amount

            category = transaction["category"]

            category_data[category] = (
                category_data.get(category, 0)
                + amount
            )

    return render_template(
        "reports.html",
        monthly_data=monthly_data,
        category_data=category_data
    )

# --------------------------------------------------
# NOTIFICATIONS
# --------------------------------------------------


# --------------------------------------------------
# NOTIFICATION HELPER
# --------------------------------------------------

def generate_notifications():
    notifications = []

    transactions = read_csv(TRANSACTIONS_FILE)

    # ----------------------------------------------
    # No transactions
    # ----------------------------------------------

    if not transactions:

        notifications.append({
            "type": "info",
            "title": "Welcome to Smart Expense Tracker",
            "message": "Start by adding your first income or expense.",
            "date": "Today"
        })

        return notifications


    # ----------------------------------------------
    # Latest transaction
    # ----------------------------------------------

    latest = transactions[-1]

    latest_amount = float(latest["amount"])

    if latest["type"] == "expense":

        notifications.append({
            "type": "expense",
            "title": "Expense Added",
            "message": (
                f"₹{latest_amount:,.2f} spent on "
                f"{latest['category']}."
            ),
            "date": latest["date"]
        })

    else:

        notifications.append({
            "type": "income",
            "title": "Income Added",
            "message": (
                f"₹{latest_amount:,.2f} income received."
            ),
            "date": latest["date"]
        })


    # ----------------------------------------------
    # Calculate totals
    # ----------------------------------------------

    total_income = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "income"
    )

    total_expenses = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "expense"
    )


    balance = total_income - total_expenses


    # ----------------------------------------------
    # Balance notification
    # ----------------------------------------------

    if balance < 0:

        notifications.append({
            "type": "warning",
            "title": "Negative Balance",
            "message": (
                "Your total expenses are currently "
                "higher than your total income."
            ),
            "date": "Today"
        })

    else:

        notifications.append({
            "type": "balance",
            "title": "Current Balance",
            "message": (
                f"Your current balance is "
                f"₹{balance:,.2f}."
            ),
            "date": "Today"
        })


    # ----------------------------------------------
    # Monthly expense notification
    # ----------------------------------------------

    current_month = datetime.now().strftime("%Y-%m")

    monthly_expenses = sum(
        float(t["amount"])
        for t in transactions
        if (
            t["type"] == "expense"
            and t["date"].startswith(current_month)
        )
    )


    if monthly_expenses > 0:

        notifications.append({
            "type": "expense",
            "title": "Monthly Spending",
            "message": (
                f"You have spent "
                f"₹{monthly_expenses:,.2f} "
                f"this month."
            ),
            "date": "This month"
        })


    # ----------------------------------------------
    # High spending notification
    # ----------------------------------------------

    if monthly_expenses >= 10000:

        notifications.append({
            "type": "warning",
            "title": "High Monthly Spending",
            "message":( "Your monthly expenses have "
                "crossed ₹10,000."),
            "date": "This month"
        })


    return notifications

@app.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    notifications_data = generate_notifications()

    return render_template(
        "notifications.html",
        notifications=notifications_data
    )

@app.context_processor
def inject_notifications():

    if "user_id" not in session:
        return {
            "notification_count": 0
        }

    notifications = generate_notifications()

    return {
        "notification_count": len(notifications)
    }
# --------------------------------------------------
# CATEGORIES
# --------------------------------------------------

@app.route("/categories", methods=["GET", "POST"])
def categories():

    if "user_id" not in session:
        return redirect(url_for("login"))

    rows = user_rows(CATEGORIES_FILE)

    if request.method == "POST":

        category = {
            "id": str(get_next_user_id(CATEGORIES_FILE, session["user_id"])),
            "user_id": str(session["user_id"]),
            "name": request.form["name"],
            "type": request.form["type"]
        }

        rows.append(category)

        write_csv(
            CATEGORIES_FILE,
            ["id", "user_id", "name", "type"],
            rows
        )

        return redirect(url_for("categories"))

    return render_template(
        "categories.html",
        categories=rows
    )


@app.route("/categories/delete/<int:id>")
def delete_category(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    rows = read_csv(CATEGORIES_FILE)

    rows = [
        row for row in rows
        if not (
            int(row["id"]) == id
            and row.get("user_id") == str(session["user_id"])
        )
    ]

    write_csv(
        CATEGORIES_FILE,
        ["id", "user_id", "name", "type"],
        rows
    )

    return redirect(url_for("categories"))




def migrate_csv_files():
    """Add user_id columns to old CSV files without losing existing data."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Existing transactions/budgets/categories created by the old version
    # have no owner. They are intentionally not assigned to a user because
    # there is no reliable way to know which account owns them.
    migrations = [
        (TRANSACTIONS_FILE,
         ["id", "user_id", "type", "amount", "category", "date", "description", "payment_method"]),
        (CATEGORIES_FILE,
         ["id", "user_id", "name", "type"]),
        (BUDGETS_FILE,
         ["id", "user_id", "category", "amount", "month"])
    ]

    for filename, new_fields in migrations:
        if not os.path.exists(filename):
            continue

        with open(filename, "r", newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        if not rows and not os.path.getsize(filename):
            write_csv(filename, new_fields, [])
            continue

        old_fields = rows[0].keys() if rows else []
        if "user_id" not in old_fields:
            migrated = []
            for row in rows:
                new_row = dict(row)
                new_row["user_id"] = ""
                migrated.append({
                    field: new_row.get(field, "")
                    for field in new_fields
                })
            write_csv(filename, new_fields, migrated)


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    initialize_files()
    migrate_csv_files()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )