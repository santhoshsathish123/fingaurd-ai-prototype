import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Plaid API Imports
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

app = Flask(__name__)
app.secret_key = 'finguard_v3_login_force_key'

# Versioned SQLite instance to prevent schema locks
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'finguard_v3.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Plaid API Client Setup (Sandbox Mode)
PLAID_CLIENT_ID = '6aa2ee36fc5c77000c6a89b8'
PLAID_SECRET = '8d25970b467626c1db1e25adf26bcb'

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False)
    account_nickname = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    plaid_access_token = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    next_due_date = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Session Security Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- AUTHENTICATION ROUTES ---

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return render_template('login.html', error="Invalid username or password.")

        session['user_id'] = user.id
        session['user_name'] = user.username
        return redirect(url_for('dashboard'))

    session.clear()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('register.html', error="Please fill out all fields.")

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Username already taken.")

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.username
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- BANK LINKING & PLAID API ENDPOINTS ---

@app.route('/create_link_token', methods=['POST'])
@login_required
def create_link_token():
    try:
        plaid_request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=str(session['user_id'])),
            client_name="FinGuard AI",
            products=[Products('auth'), Products('transactions')],
            country_codes=[CountryCode('US')],
            language='en'
        )
        response = plaid_client.link_token_create(plaid_request)
        return jsonify({'link_token': response['link_token']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/exchange_public_token', methods=['POST'])
@login_required
def exchange_public_token():
    data = request.get_json()
    public_token = data.get('public_token')

    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = plaid_client.item_public_token_exchange(exchange_request)
        access_token = exchange_response['access_token']

        # Fetch live balance from Plaid Sandbox
        balance_request = AccountsBalanceGetRequest(access_token=access_token)
        balance_response = plaid_client.accounts_balance_get(balance_request)

        # Save linked accounts to SQLite
        for account in balance_response['accounts']:
            new_acc = BankAccount(
                bank_name=account['name'],
                account_nickname=account['official_name'] or account['name'],
                account_number=f"•••• {account['mask']}",
                balance=float(account['balances']['current'] or 0.0),
                plaid_access_token=access_token,
                user_id=session['user_id']
            )
            db.session.add(new_acc)

        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- CORE APPLICATION ROUTES ---

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    accounts = BankAccount.query.filter_by(user_id=user_id).all()
    transactions = Transaction.query.filter_by(user_id=user_id).all()

    total_balance = sum(acc.balance for acc in accounts)
    total_expense = sum(tx.amount for tx in transactions)

    category_totals = {}
    for tx in transactions:
        category_totals[tx.category] = category_totals.get(tx.category, 0.0) + tx.amount

    return render_template('dashboard.html', 
                           accounts=accounts, 
                           total_balance=total_balance, 
                           total_expense=total_expense, 
                           category_totals=category_totals)

@app.route('/categorization')
@login_required
def categorization():
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.date.desc()).all()
    return render_template('categorization.html', transactions=transactions)

@app.route('/subscriptions')
@login_required
def subscriptions():
    subs = Subscription.query.filter_by(user_id=session['user_id']).all()
    top_sub = subs[0] if subs else None
    return render_template('subscriptions.html', subscriptions=subs, top_sub=top_sub)

@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        bank_name = request.form.get('bank_name')
        account_nickname = request.form.get('account_nickname')
        account_number = request.form.get('account_number')
        balance = float(request.form.get('balance', 0.0))

        new_acc = BankAccount(
            bank_name=bank_name,
            account_nickname=account_nickname,
            account_number=account_number,
            balance=balance,
            user_id=session['user_id']
        )
        db.session.add(new_acc)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_account.html')

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        category = request.form.get('category')
        account_id = request.form.get('account_id')

        if not account_id:
            return "Please select a bank account", 400

        account = BankAccount.query.filter_by(id=int(account_id), user_id=session['user_id']).first()
        if not account:
            return "Unauthorized or invalid account", 403

        new_tx = Transaction(
            amount=amount,
            description=description,
            category=category,
            account_id=account.id,
            user_id=session['user_id'],
            date=datetime.utcnow()
        )

        account.balance -= amount

        db.session.add(new_tx)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_transaction.html', accounts=accounts)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)