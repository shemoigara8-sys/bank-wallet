
import os
import qrcode

from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    send_file
)

from werkzeug.utils import secure_filename

from models import db, User, Transaction
from config import Config


wallet_bp = Blueprint("wallet", __name__)


# =====================================
# Balance
# =====================================

@wallet_bp.route("/balance")
def balance():

    if "account" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.filter_by(
        account=session["account"]
    ).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    sent = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.sender == user.account
    ).scalar() or 0

    received = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.receiver == user.account
    ).scalar() or 0

    return jsonify({
        "username": user.username,
        "account": user.account,
        "balance": user.balance,
        "sent": sent,
        "received": received,
        "photo": user.photo
    })


# =====================================
# Send Money
# =====================================

@wallet_bp.route("/send", methods=["POST"])
def send():

    if "account" not in session:
        return jsonify({"error": "Login first"}), 401

    data = request.json

    receiver = User.query.filter_by(
        account=data["receiver"]
    ).first()

    sender = User.query.filter_by(
        account=session["account"]
    ).first()

    if not receiver:
        return jsonify({"error": "Receiver not found"}), 404

    amount = float(data["amount"])

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    if sender.balance < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    sender.balance -= amount
    receiver.balance += amount

    transaction = Transaction(
        sender=sender.account,
        receiver=receiver.account,
        amount=amount
    )

    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "message": f"KES {amount:.2f} sent successfully"
    })


# =====================================
# Transaction History
# =====================================

@wallet_bp.route("/history")
def history():

    if "account" not in session:
        return jsonify([])

    transactions = Transaction.query.filter(
        (Transaction.sender == session["account"]) |
        (Transaction.receiver == session["account"])
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    history = []

    for tx in transactions:

        history.append({

            "from": tx.sender,
            "to": tx.receiver,
            "amount": tx.amount,
            "date": tx.created_at.strftime("%d %b %Y %H:%M")

        })

    return jsonify(history)


# =====================================
# Upload Profile Photo
# =====================================

@wallet_bp.route("/upload_photo", methods=["POST"])
def upload_photo():

    if "account" not in session:
        return jsonify({"error": "Login first"}), 401

    if "photo" not in request.files:
        return jsonify({"error": "No photo selected"}), 400

    file = request.files["photo"]

    if file.filename == "":
        return jsonify({"error": "No photo selected"}), 400

    user = User.query.filter_by(
        account=session["account"]
    ).first()

    filename = secure_filename(
        f"{user.account}_{file.filename}"
    )

    filepath = os.path.join(
        Config.UPLOAD_FOLDER,
        filename
    )

    file.save(filepath)

    user.photo = filename

    db.session.commit()

    return jsonify({
        "message": "Photo uploaded",
        "filename": filename
    })


# =====================================
# QR Code
# =====================================

@wallet_bp.route("/qr")
def qr():

    if "account" not in session:
        return "Login first"

    account = session["account"]

    os.makedirs(
        Config.QR_FOLDER,
        exist_ok=True
    )

    filename = os.path.join(
        Config.QR_FOLDER,
        f"{account}.png"
    )

    img = qrcode.make(account)

    img.save(filename)

    return send_file(
        filename,
        mimetype="image/png"
    )

