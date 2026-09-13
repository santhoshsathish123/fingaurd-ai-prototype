from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/link-account")
def link_account_page():
    return render_template("link_account.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

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

    return jsonify({
        "success": True,
        "redirect_url": "/dashboard",
        "account": simulated_bank_data
    })

if __name__ == "__main__":
    app.run(debug=True)