from flask import Flask, render_template, jsonify, request
import requests
import random

app = Flask(__name__)

# Fast2SMS Dev API Authorization Key
FAST2SMS_API_KEY = "iaLPf76dmB2vQRIKCobOJyqH5w13WjTxUZnge4AlEMDku80zVFoZyJeKpgnQAGbt2k5D4hExRIXLwmdW"

# In-memory storage for generated OTPs
otp_store = {}

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        data = request.get_json() or {}
        phone = data.get('phone')

        if not phone or len(str(phone)) != 10:
            return jsonify({'success': False, 'error': 'Please provide a valid 10-digit mobile number.'}), 400

        # Generate 4-digit OTP
        generated_otp = str(random.randint(1000, 9999))
        
        # Save OTP in memory mapped to phone number
        otp_store[phone] = generated_otp

        # Call Fast2SMS API
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
            return jsonify({
                'success': True,
                'message': f'OTP sent successfully to +91-{phone}'
            })
        else:
            error_msg = res_data.get('message', ['Failed to send SMS'])[0] if isinstance(res_data.get('message'), list) else res_data.get('message', 'Failed to send SMS')
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json() or {}
        otp = str(data.get('otp', '')).strip()
        phone = str(data.get('phone', '')).strip()

        saved_otp = otp_store.get(phone)

        # Check against stored OTP or allow backup test code '1234'
        if (saved_otp and otp == saved_otp) or otp == '1234':
            return jsonify({'success': True, 'message': 'Bank account linked successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Incorrect OTP entered.'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)