from flask import Flask, render_template, jsonify, request
import requests
import random

app = Flask(__name__)

# Fast2SMS Dev API Authorization Key
FAST2SMS_API_KEY = "iaLPf76dmB2vQRIKCobOJyqH5w13WjTxUZnge4AlEMDku80zVFoZyJeKpgnQAGbt2k5D4hExRIXLwmdW"

# In-memory storage for app users & bank verification OTPs
users_db = {}      # Format: {'username': 'password'}
bank_otp_store = {} # Format: {'phone': '1234'}

@app.route('/')
def home():
    return render_template('dashboard.html')

# --- 1. USER AUTHENTICATION (USERNAME & PASSWORD) ---

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        username = str(data.get('username', '')).strip()
        password = str(data.get('password', '')).strip()

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

        if username in users_db:
            return jsonify({'success': False, 'message': 'Username already exists. Please login.'}), 400

        users_db[username] = password
        return jsonify({'success': True, 'message': 'Registration successful! You can now log in.'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = str(data.get('username', '')).strip()
        password = str(data.get('password', '')).strip()

        if users_db.get(username) == password:
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# --- 2. BANK LINKING (MOBILE OTP VIA FAST2SMS) ---

@app.route('/send_bank_otp', methods=['POST'])
def send_bank_otp():
    try:
        data = request.get_json() or {}
        phone = str(data.get('phone', '')).strip()

        if len(phone) != 10 or not phone.isdigit():
            return jsonify({'success': False, 'error': 'Please enter a valid 10-digit mobile number.'}), 400

        # Generate 4-digit OTP
        generated_otp = str(random.randint(1000, 9999))
        bank_otp_store[phone] = generated_otp

        # Send real SMS using Fast2SMS API
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            'authorization': FAST2SMS_API_KEY,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'variables_values': generated_otp,
            'route': 'otp',
            'numbers': phone
        }

        response = requests.post(url, data=payload, headers=headers)
        res_data = response.json()

        if response.status_code == 200 and res_data.get('return') == True:
            return jsonify({'success': True, 'message': f'OTP sent via SMS to +91-{phone}'})
        else:
            # Output fallback code in server console if SMS API fails
            print(f"[FAST2SMS NOTICE] Could not send SMS. Test OTP for {phone}: {generated_otp}")
            return jsonify({
                'success': True, 
                'message': f'Gateway Notice: Use test OTP {generated_otp} if SMS fails to deliver.'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/verify_bank_otp', methods=['POST'])
def verify_bank_otp():
    try:
        data = request.get_json() or {}
        otp = str(data.get('otp', '')).strip()
        phone = str(data.get('phone', '')).strip()

        saved_otp = bank_otp_store.get(phone)

        # Match generated OTP or emergency master OTP '1234'
        if (saved_otp and otp == saved_otp) or otp == '1234':
            return jsonify({'success': True, 'message': 'Bank account linked successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Incorrect OTP entered.'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)