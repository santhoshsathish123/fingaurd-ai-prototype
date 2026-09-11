from flask import Flask, render_template, jsonify, request
import requests
import random

app = Flask(__name__)

# Fast2SMS Dev API Key
FAST2SMS_API_KEY = "iaLPf76dmB2vQRIKCobOJyqH5w13WjTxUZnge4AlEMDku80zVFoZyJeKpgnQAGbt2k5D4hExRIXLwmdW"

# In-memory session/OTP store
otp_store = {}

@app.route('/')
def home():
    # Directs directly to the main application interface
    return render_template('dashboard.html')

@app.route('/send_otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json() or {}
        phone = str(data.get('phone', '')).strip()

        if len(phone) != 10 or not phone.isdigit():
            return jsonify({'success': False, 'error': 'Please enter a valid 10-digit mobile number.'}), 400

        # Generate a 4-digit OTP
        generated_otp = str(random.randint(1000, 9999))
        otp_store[phone] = generated_otp

        # Call Fast2SMS API using the Quick SMS / OTP endpoint
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

        # If Fast2SMS sends the message successfully
        if response.status_code == 200 and res_data.get('return') == True:
            return jsonify({'success': True, 'message': f'OTP sent to +91-{phone}'})
        else:
            # Fallback: Print OTP to terminal/logs so you are never locked out during testing
            print(f"[TESTING FALLBACK] OTP for {phone} is: {generated_otp}")
            return jsonify({
                'success': True, 
                'message': f'SMS Gateway Notice: Use test OTP {generated_otp} if SMS is delayed.'
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json() or {}
        otp = str(data.get('otp', '')).strip()
        phone = str(data.get('phone', '')).strip()

        saved_otp = otp_store.get(phone)

        # Accepts generated OTP or universal master code '1234'
        if (saved_otp and otp == saved_otp) or otp == '1234':
            return jsonify({'success': True, 'message': 'Authentication successful!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid OTP code. Please try again.'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)