from flask import Flask, render_template, jsonify, request
import requests
import os

app = Flask(__name__)

# SETU AA API CREDENTIALS (Sign up at setu.co for Sandbox Keys)
SETU_CLIENT_ID = os.getenv('SETU_CLIENT_ID', 'your_setu_client_id')
SETU_CLIENT_SECRET = os.getenv('SETU_CLIENT_SECRET', 'your_setu_secret')
SETU_PRODUCT_INSTANCE_ID = os.getenv('SETU_PRODUCT_INSTANCE_ID', 'your_product_instance_id')

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    """
    Simulates / Creates an Indian Account Aggregator consent link
    using Setu or direct OTP bank linking flow.
    """
    try:
        # For testing/demo without live keys, we send a success status 
        # to trigger Indian Bank Phone Verification in the UI.
        return jsonify({
            'success': True,
            'provider': 'Setu_AA_India',
            'message': 'Account Aggregator session initiated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)