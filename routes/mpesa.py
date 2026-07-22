"""M-Pesa integration routes (DEMO VERSION)"""
from flask import Blueprint, render_template, request, jsonify, session, redirect
from models import db, User, MpesaTransaction
import uuid
from datetime import datetime

mpesa_bp = Blueprint("mpesa", __name__)

# Configuration (DEMO - Replace with real credentials)
MPESA_CONSUMER_KEY = "DEMO_KEY"
MPESA_CONSUMER_SECRET = "DEMO_SECRET"
MPESA_SHORTCODE = "174379"
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd1a503b6015d86422d466f35664"


# =====================================
# M-Pesa Pages
# =====================================

@mpesa_bp.route("/mpesa")
def mpesa_page():
    """M-Pesa main page"""
    if "account" not in session:
        return redirect("/login-page")
    return render_template("mpesa.html")


@mpesa_bp.route("/mpesa-transactions")
def mpesa_transactions():
    """M-Pesa transactions history"""
    if "account" not in session:
        return redirect("/login-page")
    return render_template("mpesa_transactions.html")


# =====================================
# M-Pesa API Endpoints
# =====================================

@mpesa_bp.route("/api/mpesa/deposit", methods=["POST"])
def mpesa_deposit():
    """Initiate M-Pesa deposit (STK Push)"""
    if "account" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    phone_number = data.get("phone_number")
    amount = float(data.get("amount", 0))

    # Validation
    if not phone_number or amount <= 0:
        return jsonify({"error": "Invalid phone number or amount"}), 400

    if amount > 150000:
        return jsonify({"error": "Amount exceeds M-Pesa limit (KES 150,000)"}), 400

    user = User.query.filter_by(account=session["account"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Create M-Pesa transaction record
    mpesa_tx = MpesaTransaction(
        user_account=user.account,
        phone_number=phone_number,
        transaction_type="deposit",
        amount=amount,
        status="pending",
        mpesa_reference=f"DEMO-{uuid.uuid4().hex[:12].upper()}",
        description=f"Deposit KES {amount} to {user.account}"
    )

    db.session.add(mpesa_tx)
    db.session.commit()

    # DEMO: Return simulated STK push response
    return jsonify({
        "message": "STK Push sent to your phone",
        "reference": mpesa_tx.mpesa_reference,
        "phone_number": phone_number,
        "amount": amount,
        "status": "pending",
        "transaction_id": mpesa_tx.id,
        "demo_note": "This is a DEMO - In production, you'll receive an STK prompt on your phone"
    })


@mpesa_bp.route("/api/mpesa/confirm/<int:transaction_id>", methods=["POST"])
def mpesa_confirm_deposit(transaction_id):
    """Confirm M-Pesa deposit (DEMO - Simulates successful payment)"""
    if "account" not in session:
        return jsonify({"error": "Not logged in"}), 401

    mpesa_tx = MpesaTransaction.query.get(transaction_id)
    if not mpesa_tx:
        return jsonify({"error": "Transaction not found"}), 404

    if mpesa_tx.user_account != session["account"]:
        return jsonify({"error": "Unauthorized"}), 403

    # Update transaction status
    mpesa_tx.status = "success"
    mpesa_tx.mpesa_receipt = f"LLK221V6ZK"
    mpesa_tx.updated_at = datetime.utcnow()

    # Add money to user's K Wallet balance
    user = User.query.filter_by(account=session["account"]).first()
    user.balance += mpesa_tx.amount

    db.session.commit()

    return jsonify({
        "message": f"Successfully deposited KES {mpesa_tx.amount} to your K Wallet",
        "new_balance": user.balance,
        "receipt": mpesa_tx.mpesa_receipt
    })


@mpesa_bp.route("/api/mpesa/withdraw", methods=["POST"])
def mpesa_withdraw():
    """Initiate M-Pesa withdrawal"""
    if "account" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    phone_number = data.get("phone_number")
    amount = float(data.get("amount", 0))

    # Validation
    if not phone_number or amount <= 0:
        return jsonify({"error": "Invalid phone number or amount"}), 400

    user = User.query.filter_by(account=session["account"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.balance < amount:
        return jsonify({"error": "Insufficient balance"}), 400

    if amount > 150000:
        return jsonify({"error": "Amount exceeds M-Pesa limit (KES 150,000)"}), 400

    # Create M-Pesa transaction record
    mpesa_tx = MpesaTransaction(
        user_account=user.account,
        phone_number=phone_number,
        transaction_type="withdraw",
        amount=amount,
        status="pending",
        mpesa_reference=f"DEMO-{uuid.uuid4().hex[:12].upper()}",
        description=f"Withdraw KES {amount} from {user.account}"
    )

    db.session.add(mpesa_tx)
    db.session.commit()

    return jsonify({
        "message": "Withdrawal initiated",
        "reference": mpesa_tx.mpesa_reference,
        "phone_number": phone_number,
        "amount": amount,
        "status": "pending",
        "transaction_id": mpesa_tx.id,
        "demo_note": "This is a DEMO - In production, money will be sent to your M-Pesa account"
    })


@mpesa_bp.route("/api/mpesa/confirm-withdraw/<int:transaction_id>", methods=["POST"])
def mpesa_confirm_withdraw(transaction_id):
    """Confirm M-Pesa withdrawal (DEMO - Simulates successful payout)"""
    if "account" not in session:
        return jsonify({"error": "Not logged in"}), 401

    mpesa_tx = MpesaTransaction.query.get(transaction_id)
    if not mpesa_tx:
        return jsonify({"error": "Transaction not found"}), 404

    if mpesa_tx.user_account != session["account"]:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.filter_by(account=session["account"]).first()

    # Deduct from balance
    user.balance -= mpesa_tx.amount

    # Update transaction status
    mpesa_tx.status = "success"
    mpesa_tx.mpesa_receipt = f"LLK221V6ZK"
    mpesa_tx.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": f"Successfully withdrew KES {mpesa_tx.amount} to {mpesa_tx.phone_number}",
        "new_balance": user.balance,
        "receipt": mpesa_tx.mpesa_receipt
    })


@mpesa_bp.route("/api/mpesa/transactions")
def get_mpesa_transactions():
    """Get user's M-Pesa transactions"""
    if "account" not in session:
        return jsonify({"error": "Not logged in"}), 401

    transactions = MpesaTransaction.query.filter_by(
        user_account=session["account"]
    ).order_by(MpesaTransaction.created_at.desc()).all()

    return jsonify([
        {
            "id": tx.id,
            "type": tx.transaction_type,
            "amount": tx.amount,
            "phone": tx.phone_number,
            "status": tx.status,
            "reference": tx.mpesa_reference,
            "receipt": tx.mpesa_receipt,
            "date": tx.created_at.strftime("%d %b %Y %H:%M"),
            "description": tx.description
        }
        for tx in transactions
    ])


@mpesa_bp.route("/admin/mpesa-stats")
def admin_mpesa_stats():
    """Admin: Get M-Pesa statistics"""
    if "admin" not in session:
        return jsonify({"error": "Not authorized"}), 401

    total_deposits = db.session.query(db.func.sum(MpesaTransaction.amount)).filter(
        MpesaTransaction.transaction_type == "deposit",
        MpesaTransaction.status == "success"
    ).scalar() or 0

    total_withdrawals = db.session.query(db.func.sum(MpesaTransaction.amount)).filter(
        MpesaTransaction.transaction_type == "withdraw",
        MpesaTransaction.status == "success"
    ).scalar() or 0

    total_transactions = MpesaTransaction.query.count()

    return jsonify({
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "total_transactions": total_transactions,
        "net_flow": total_deposits - total_withdrawals
    })


@mpesa_bp.route("/admin/mpesa-transactions")
def admin_mpesa_transactions():
    """Admin: Get all M-Pesa transactions"""
    if "admin" not in session:
        return jsonify({"error": "Not authorized"}), 401

    transactions = MpesaTransaction.query.order_by(
        MpesaTransaction.created_at.desc()
    ).limit(100).all()

    return jsonify([
        {
            "user_account": tx.user_account,
            "type": tx.transaction_type,
            "amount": tx.amount,
            "phone": tx.phone_number,
            "status": tx.status,
            "reference": tx.mpesa_reference,
            "date": tx.created_at.strftime("%d %b %Y %H:%M")
        }
        for tx in transactions
    ])
