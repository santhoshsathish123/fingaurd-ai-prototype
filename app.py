from flask import Flask, render_template, jsonify, request
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
import os

app = Flask(__name__)

# Configure Plaid Environment
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        request_data = LinkTokenCreateRequest(
            products=[Products('auth'), Products('transactions')],
            client_name="FinGuard AI",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='user_finguard_1')
        )
        response = client.link_token_create(request_data)
        return jsonify({'link_token': response['link_token']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)