from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/link-account")
def link_account_page():
    return render_template("link_account.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/link_bank_account", methods=["POST"])
def link_bank_account():
    data = request.get_json(silent=True) or {}
    otp = data.get("otp", "")

    if otp == "1899":
        return jsonify({
            "success": True,
            "redirect_url": "/dashboard"
        })
    
    return jsonify({"success": False, "message": "Invalid OTP"}), 400

if __name__ == "__main__":
    app.run(debug=True)