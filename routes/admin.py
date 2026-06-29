from flask import Blueprint, jsonify, render_template, session, redirect
from sqlalchemy import func

from models import db, User, Transaction

admin_bp = Blueprint("admin", __name__)


# ==========================
# Admin Dashboard
# ==========================

@admin_bp.route("/admin")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin-login")

    return render_template("admin.html")


# ==========================
# Statistics
# ==========================

@admin_bp.route("/admin/stats")
def admin_stats():

    total_users = User.query.count()

    total_transactions = Transaction.query.count()

    total_money = db.session.query(
        func.sum(Transaction.amount)
    ).scalar() or 0

    return jsonify({
        "users": total_users,
        "transactions": total_transactions,
        "money": total_money
    })


# ==========================
# Registered Users
# ==========================

@admin_bp.route("/admin/users")
def admin_users():

    users = User.query.order_by(
        User.username
    ).all()

    return jsonify([
        {
            "username": user.username,
            "account": user.account,
            "balance": user.balance
        }
        for user in users
    ])


# ==========================
# Recent Transactions
# ==========================

@admin_bp.route("/admin/transactions")
def admin_transactions():

    transactions = Transaction.query.order_by(
        Transaction.created_at.desc()
    ).limit(50).all()

    return jsonify([
        {
            "from": tx.sender,
            "to": tx.receiver,
            "amount": tx.amount,
            "date": tx.created_at.strftime("%d %b %Y %H:%M")
        }
        for tx in transactions
    ])


# ==========================
# Line Chart
# ==========================

@admin_bp.route("/admin/chart")
def admin_chart():

    transactions = Transaction.query.order_by(
        Transaction.created_at
    ).all()

    daily = {}

    for tx in transactions:

        day = tx.created_at.strftime("%d %b")

        daily[day] = daily.get(day, 0) + tx.amount

    return jsonify({
        "labels": list(daily.keys()),
        "values": list(daily.values())
    })


# ==========================
# Pie Chart
# ==========================

@admin_bp.route("/admin/pie")
def admin_pie():

    total_sent = db.session.query(
        func.sum(Transaction.amount)
    ).scalar() or 0

    current_wallet_money = db.session.query(
        func.sum(User.balance)
    ).scalar() or 0

    return jsonify({
        "sent": total_sent,
        "wallets": current_wallet_money
    })


# ==========================
# Top Wallet Balances
# ==========================

@admin_bp.route("/admin/top-users")
def admin_top_users():

    users = User.query.order_by(
        User.balance.desc()
    ).limit(10).all()

    return jsonify({
        "labels": [u.username for u in users],
        "balances": [u.balance for u in users]
    })