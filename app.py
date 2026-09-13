import os
from flask import Flask, jsonify, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# --- SETU SANDBOX CREDENTIALS ---
SETU_CLIENT_ID = "5901ff92-35f8-4c4a-be07-32e6793ed4b1"
SETU_CLIENT_SECRET = "n2QLcqjYxOfiuudkO8Ryk9PqEi4DZqU3"
SETU_BASE_URL = "https://aabridge.setu.co"

linked_accounts_db = {}

# 1. Login Page
@app.route("/")
def home():
    return render_template("login.html")

# 2. Link Bank Account Page (After Login)
@app.route("/link-account")
def link_account_page():
    return render_template("link_account.html")

# 3. Main Interactive App Dashboard (After Linking Bank)
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# API Route to handle linking bank account
@app.route("/link_bank_account", methods=["POST"])
def link_bank_account():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    phone = str(data.get("phone", "")).strip()

    if phone.startswith("+91"):
        phone = phone[3:]

    if len(phone) != 10 or not phone.isdigit():
        return jsonify({
            "success": False,
            "message": "Please enter a valid 10-digit mobile number."
        }), 400

    simulated_bank_data = {
        "bank_name": "HDFC Bank",
        "account_number": f"XXXX-XXXX-{phone[-4:]}",
        "account_type": "Savings Account",
        "balance": 48520.50,
        "currency": "INR",
        "status": "LINKED"
    }

    linked_accounts_db[phone] = simulated_bank_data

    return jsonify({
        "success": True,
        "redirect_url": "/dashboard",
        "account": simulated_bank_data
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)