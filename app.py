from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        # Indian Account Aggregator (AA Framework) session initiation endpoint
        return jsonify({
            'success': True,
            'provider': 'RBI_Account_Aggregator_India',
            'message': 'OTP sent successfully to Indian mobile number'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json() or {}
        otp = data.get('otp')
        phone = data.get('phone')
        
        # Simulating OTP Verification for Indian Banks (HDFC, SBI, ICICI, etc.)
        if otp and len(str(otp)) >= 4:
            return jsonify({
                'success': True, 
                'message': f'Bank account linked successfully for +91-{phone}'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid OTP entered. Please try again.'
            }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)