
from flask import Blueprint, render_template, request, jsonify, session, redirect

from models import db, User, Admin
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)


# =====================================
# Helpers
# =====================================

def generate_account():

    count = User.query.count()

    return f"KW{count + 1:06}"


# =====================================
# Pages
# =====================================

@auth_bp.route("/")
def home():

    return render_template("index.html")


@auth_bp.route("/login-page")
def login_page():

    return render_template("login.html")


@auth_bp.route("/register-page")
def register_page():

    return render_template("register.html")


@auth_bp.route("/dashboard")
def dashboard():

    if "account" not in session:

        return redirect("/login-page")

    return render_template("dashboard.html")


@auth_bp.route("/admin")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin-login")

    return render_template("admin.html")


@auth_bp.route("/admin-login")
def admin_login_page():

    return render_template("admin_login.html")


# =====================================
# User Authentication
# =====================================

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.json

    if not data:

        return jsonify({"error": "Invalid request"}), 400

    username = data.get("username")
    pin = data.get("pin")

    if not username or not pin:

        return jsonify({"error": "All fields are required"}), 400

    user = User(
    username=username,
    account=generate_account(),
    pin=generate_password_hash(pin)
)

    db.session.add(user)

    db.session.commit()

    return jsonify({

        "message": "Account Created",

        "account": user.account

    })



@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.json

    if not data:
        return jsonify({"error": "Invalid request"}), 400

    user = User.query.filter_by(
        account=data.get("account")
    ).first()

    if not user:
        return jsonify({
            "error": "Account not found"
        }), 404

    if not check_password_hash(
        user.pin,
        data.get("pin")
    ):
        return jsonify({
            "error": "Wrong PIN"
        }), 401

    session["account"] = user.account

    return jsonify({
        "message": "Login Successful",
        "username": user.username,
        "balance": user.balance
    })




@auth_bp.route("/admin-login", methods=["POST"])
def admin_login():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Invalid request"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    admin = Admin.query.filter_by(
        username=username
    ).first()

    # Create default admin if doesn't exist
    if not admin and username == "admin" and password == "admin123":
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        session["admin"] = admin.username
        return jsonify({
            "message": "Admin login successful"
        })

    if admin is None:
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if not admin.check_password(password):
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    session.clear()
    session["admin"] = admin.username

    return jsonify({
        "message": "Admin login successful"
    })

# =====================================
# Logout
# =====================================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")

