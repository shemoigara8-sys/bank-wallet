"""M-Pesa integration routes with REAL API support"""
from flask import Blueprint, render_template, request, jsonify, session, redirect
from models import db, User, MpesaTransaction
import uuid
from datetime import datetime
import requests
import os
import base64
from requests.auth import HTTPBasicAuth

mpesa_bp = Blueprint("mpesa", __name__)

# M-Pesa Configuration from Environment Variables
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', 'DEMO_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', 'DEMO_SECRET')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd1a503b6015d86422d466f35664')
MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', 'http://localhost:5000/api/mpesa/callback')

# M-Pesa API URLs
if MPESA_ENVIRONMENT == 'production':
    MPESA_BASE_URL = 'https://api.safaricom.co.ke'
else:
    MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke'

MPESA_AUTH_URL = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
MPESA_STK_PUSH_URL = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
MPESA_QUERY_URL = f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query"
MPESA_B2C_URL = f"{MPESA_BASE_URL}/mpesa/b2c/v1/paymentrequest"

# Access token cache
_access_token_cache = {}


def get_mpesa_access_token():
    """Get M-Pesa access token"""
    try:
        response = requests.get(
            MPESA_AUTH_URL,
            auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            _access_token_cache['token'] = data['access_token']
            return data['access_token']
        else:
            print(f"M-Pesa Auth Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting M-Pesa token: {str(e)}")
        return None


def get_cached_token():
    """Get cached access token or fetch new one"""
    return _access_token_cache.get('token') or get_mpesa_access_token()


def get_timestamp():
    """Get timestamp in format: YYYYMMDDHHmmss"""
    return datetime.now().strftime('%Y%m%d%H%M%S')


def get_password(shortcode, passkey, timestamp):
    """Generate M-Pesa password"""
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    encoded_bytes = base64.b64encode(data_to_encode.encode('utf-8'))
    return encoded_bytes.decode('utf-8')


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
# M-Pesa API Endpoints (REAL)
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
        mpesa_reference=f"DEP-{uuid.uuid4().hex[:12].upper()}",
        description=f"Deposit KES {amount} to {user.account}"
    )

    db.session.add(mpesa_tx)
    db.session.commit()

    # Call real M-Pesa API
    access_token = get_cached_token()
    if not access_token:
        mpesa_tx.status = "failed"
        mpesa_tx.description = "Failed to authenticate with M-Pesa"
        db.session.commit()
        return jsonify({"error": "M-Pesa service unavailable"}), 503

    try:
        timestamp = get_timestamp()
        password = get_password(MPESA_SHORTCODE, MPESA_PASSKEY, timestamp)

        # Prepare STK Push request
        stk_push_payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone_number,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": mpesa_tx.mpesa_reference,
            "TransactionDesc": "K Wallet Deposit"
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            MPESA_STK_PUSH_URL,
            json=stk_push_payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('ResponseCode') == '0':
                mpesa_tx.mpesa_reference = response_data.get('CheckoutRequestID')
                db.session.commit()
                
                return jsonify({
                    "message": "STK Push sent to your phone",
                    "reference": response_data.get('CheckoutRequestID'),
                    "phone_number": phone_number,
                    "amount": amount,
                    "status": "pending",
                    "transaction_id": mpesa_tx.id
                })
            else:
                mpesa_tx.status = "failed"
                mpesa_tx.description = response_data.get('ResponseDescription')
                db.session.commit()
                return jsonify({"error": response_data.get('ResponseDescription')}), 400
        else:
            mpesa_tx.status = "failed"
            mpesa_tx.description = f"M-Pesa API error: {response.status_code}"
            db.session.commit()
            return jsonify({"error": "M-Pesa service error"}), 503

    except Exception as e:
        mpesa_tx.status = "failed"
        mpesa_tx.description = str(e)
        db.session.commit()
        print(f"M-Pesa STK Push Error: {str(e)}")
        return jsonify({"error": "Failed to initiate payment"}), 500


@mpesa_bp.route("/api/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """Handle M-Pesa payment callback"""
    try:
        data = request.json
        result = data.get('Body', {}).get('stkCallback', {})
        
        checkout_request_id = result.get('CheckoutRequestID')
        result_code = result.get('ResultCode')
        result_desc = result.get('ResultDesc')
        
        # Find transaction by reference
        mpesa_tx = MpesaTransaction.query.filter_by(
            mpesa_reference=checkout_request_id
        ).first()
        
        if mpesa_tx:
            if result_code == 0:  # Success
                mpesa_tx.status = "success"
                mpesa_tx.mpesa_receipt = result.get('CallbackMetadata', {}).get('Item', [{}])[1].get('Value')
                
                # Add money to user's K Wallet balance
                user = User.query.filter_by(account=mpesa_tx.user_account).first()
                if user:
                    user.balance += mpesa_tx.amount
            else:
                mpesa_tx.status = "failed"
                mpesa_tx.description = result_desc
            
            mpesa_tx.updated_at = datetime.utcnow()
            db.session.commit()
        
        # Always return success to M-Pesa
        return jsonify({"ResultCode": 0, "ResultDesc": "Success"}), 200
    
    except Exception as e:
        print(f"M-Pesa Callback Error: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Failed"}), 200


@mpesa_bp.route("/api/mpesa/withdraw", methods=["POST"])
def mpesa_withdraw():
    """Initiate M-Pesa withdrawal (B2C)"""
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
        mpesa_reference=f"WDR-{uuid.uuid4().hex[:12].upper()}",
        description=f"Withdraw KES {amount} from {user.account}"
    )

    db.session.add(mpesa_tx)
    db.session.commit()

    # Call real M-Pesa API
    access_token = get_cached_token()
    if not access_token:
        mpesa_tx.status = "failed"
        mpesa_tx.description = "Failed to authenticate with M-Pesa"
        db.session.commit()
        return jsonify({"error": "M-Pesa service unavailable"}), 503

    try:
        # Prepare B2C request
        b2c_payload = {
            "InitiatorName": "K Wallet",
            "SecurityCredential": "YOUR_SECURITY_CREDENTIAL",  # Requires encryption
            "CommandID": "BusinessPayment",
            "Amount": int(amount),
            "PartyA": MPESA_SHORTCODE,
            "PartyB": phone_number,
            "Remarks": "K Wallet Withdrawal",
            "QueueTimeOutURL": MPESA_CALLBACK_URL,
            "ResultURL": MPESA_CALLBACK_URL
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            MPESA_B2C_URL,
            json=b2c_payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('ResponseCode') == '0':
                mpesa_tx.mpesa_reference = response_data.get('ConversationID')
                mpesa_tx.status = "success"  # In real scenario, wait for callback
                user.balance -= amount  # Deduct immediately
                db.session.commit()
                
                return jsonify({
                    "message": f"Successfully withdrew KES {amount} to {phone_number}",
                    "reference": response_data.get('ConversationID'),
                    "new_balance": user.balance,
                    "transaction_id": mpesa_tx.id
                })
            else:
                mpesa_tx.status = "failed"
                mpesa_tx.description = response_data.get('ResponseDescription')
                db.session.commit()
                return jsonify({"error": response_data.get('ResponseDescription')}), 400
        else:
            mpesa_tx.status = "failed"
            mpesa_tx.description = f"M-Pesa API error: {response.status_code}"
            db.session.commit()
            return jsonify({"error": "M-Pesa service error"}), 503

    except Exception as e:
        mpesa_tx.status = "failed"
        mpesa_tx.description = str(e)
        db.session.commit()
        print(f"M-Pesa B2C Error: {str(e)}")
        return jsonify({"error": "Failed to process withdrawal"}), 500


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
        "net_flow": total_deposits - total_withdrawals,
        "environment": MPESA_ENVIRONMENT
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
