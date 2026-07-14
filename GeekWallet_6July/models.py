from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Models for 5 tables
db = SQLAlchemy()


# geek_user table
class User(db.Model):
    __tablename__ = "geek_user"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now)


# category table
class Category(db.Model):
    __tablename__ = "category"

    ctg_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ctg_name = db.Column(db.String(100), nullable=False)
    ctg_type = db.Column(db.Enum("Income", "Expense"), nullable=False)
    ctg_icon = db.Column(db.String(50))


# transactions table
class Transaction(db.Model):
    __tablename__ = "transactions"

    trans_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("geek_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    ctg_id = db.Column(
        db.Integer, db.ForeignKey("category.ctg_id", ondelete="CASCADE"), nullable=False
    )
    amount = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    exclude_budget = db.Column(db.Boolean, default=False)
    be_recurring = db.Column(db.Boolean, default=False)
    source_recur_id = db.Column(db.Integer, nullable=True)

    category = db.relationship("Category")
    recurring = db.relationship(
        "Recurring", backref="transaction", uselist=False, cascade="all, delete-orphan"
    )


# recurring table
class Recurring(db.Model):
    __tablename__ = "recurring"

    recur_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trans_id = db.Column(
        db.Integer,
        db.ForeignKey("transactions.trans_id", ondelete="CASCADE"),
        nullable=False,
    )
    frequency = db.Column(db.Enum("Daily", "Weekly", "Monthly"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    next_date = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.Enum("Active", "Completed", "Deleted"), nullable=False, default="Active"
    )


# budget table
class Budget(db.Model):
    __tablename__ = "budget"

    budget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("geek_user.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    ctg_id = db.Column(
        db.Integer, db.ForeignKey("category.ctg_id", ondelete="CASCADE"), nullable=False
    )
    amt_limit = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.Enum("Day", "Week", "Month"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    budget_note = db.Column(db.String(255))
    budget_noti = db.Column(db.Boolean, default=True)
    end_date = db.Column(db.Date, nullable=False)
