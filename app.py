from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'finguard_secret_key'

@app.route('/')
def home():
    # Load white embossed login directly
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        session['user'] = email
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Make sure user is logged in before opening dashboard
    if 'user' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)