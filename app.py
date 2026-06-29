from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect
import os
from werkzeug.utils import secure_filename
import qrcode
import os
from flask import send_file


app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.secret_key = "kwallet_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kwallet.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ==========================
# DATABASE MODELS
# ==========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    account = db.Column(db.String(20), unique=True)
    pin = db.Column(db.String(10))
    balance = db.Column(db.Float, default=1000)

    photo = db.Column(
        db.String(200),
        default="default.png"
    )

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20))
    receiver = db.Column(db.String(20))
    amount = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


with app.app_context():
    db.create_all()


# ==========================
# HELPERS
# ==========================

def generate_account():
    count = User.query.count()
    return f"KW{count+1:06}"


# ==========================
# ROUTES
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.json

    user = User(
        username=data["username"],
        pin=data["pin"],
        account=generate_account()
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Account Created",
        "account": user.account
    })


@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(
        account=data["account"]
    ).first()

    if not user:
        return jsonify({"error":"Account not found"}),404

    if user.pin != data["pin"]:
        return jsonify({"error":"Wrong PIN"}),401

    session["account"] = user.account

    return jsonify({
        "message":"Login Successful",
        "username":user.username,
        "balance":user.balance
    })


@app.route("/balance")
def balance():

    if "account" not in session:
        return jsonify({"error":"Not logged in"}),401

    user = User.query.filter_by(
        account=session["account"]
    ).first()

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
        "photo": user.photo,
        "sent": sent,
        "received": received
    })


@app.route("/send", methods=["POST"])
def send():

    if "account" not in session:
        return jsonify({"error":"Login first"}),401

    data = request.json

    sender = User.query.filter_by(
        account=session["account"]
    ).first()

    receiver = User.query.filter_by(
        account=data["receiver"]
    ).first()

    if not receiver:
        return jsonify({"error":"Receiver not found"}),404

    amount = float(data["amount"])

    if sender.balance < amount:
        return jsonify({"error":"Insufficient funds"}),400

    sender.balance -= amount
    receiver.balance += amount

    tx = Transaction(
        sender=sender.account,
        receiver=receiver.account,
        amount=amount
    )

    db.session.add(tx)
    db.session.commit()

    return jsonify({
        "message": f"KES {amount} sent to {receiver.account}"
    })

@app.route("/history")
def history():

    if "account" not in session:
        return jsonify([])

    transactions = Transaction.query.filter(
        (Transaction.sender == session["account"]) |
        (Transaction.receiver == session["account"])
    ).all()

    data = []

    for t in transactions:
        data.append({
            "from": t.sender,
            "to": t.receiver,
            "amount": t.amount,
            "date": t.created_at.strftime("%d %b %Y %H:%M")
        })

    return jsonify(data)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    if "account" not in session:
        return jsonify({"error":"Login first"}), 401

    if "photo" not in request.files:
        return jsonify({"error":"No file selected"}), 400

    file = request.files["photo"]

    if file.filename == "":
        return jsonify({"error":"No file selected"}), 400

    user = User.query.filter_by(
        account=session["account"]
    ).first()

    filename = secure_filename(
        f"{user.account}_{file.filename}"
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    user.photo = filename

    db.session.commit()

    return jsonify({
        "message":"Photo uploaded",
        "filename":filename
    })

@app.route("/qr")
def qr():

    if "account" not in session:
        return "Login first"

    account = session["account"]

    os.makedirs("static/qrcodes", exist_ok=True)

    filename = f"static/qrcodes/{account}.png"

    img = qrcode.make(account)

    img.save(filename)

    return send_file(
        filename,
        mimetype="image/png"
    )




if __name__ == "__main__":
    app.run(debug=True)