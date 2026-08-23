from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from database import init_db, get_db

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    db = get_db()
    transactions = db.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
    
    total_balance = sum(
        tx['amount'] if tx['category'] == 'Доход' else -tx['amount']
        for tx in transactions
    )
    
    db.close()
    return render_template('index.html', transactions=transactions, total_balance=total_balance)

@app.route('/add', methods=['POST'])
def add_transaction():
    title = request.form.get('title')
    amount = float(request.form.get('amount', 0))
    category = request.form.get('category', 'Доход')
    date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    db = get_db()
    db.execute('INSERT INTO transactions (title, amount, category, date) VALUES (?, ?, ?, ?)',
               (title, amount, category, date))
    db.commit()
    db.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
