from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from database import init_db, get_db

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    db = get_db()
    transactions = db.execute('SELECT * FROM transactions ORDER BY date DESC, id DESC').fetchall()
    goals = db.execute('SELECT * FROM goals ORDER BY id DESC').fetchall()
    db.close()
    
    # Подсчет балансов (в рублях, как на скрине)
    net_income = 0.0
    pending_income = 0.0
    
    for tx in transactions:
        if tx['type'] == 'income':
            if tx['status'] == 'received':
                net_income += tx['amount']
            elif tx['status'] == 'pending':
                pending_income += tx['amount']
        elif tx['type'] == 'expense':
            if tx['status'] == 'received': # У расходов 'received' значит 'потрачено'
                net_income -= tx['amount']

    return render_template('index.html', 
                           transactions=transactions,
                           goals=goals,
                           net_income=net_income,
                           pending_income=pending_income)

@app.route('/add_tx', methods=['POST'])
def add_tx():
    tx_type = request.form.get('type')
    title = request.form.get('title')
    amount = float(request.form.get('amount', 0))
    status = request.form.get('status', 'received')
    comment = request.form.get('comment', '')
    date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    db = get_db()
    db.execute('''INSERT INTO transactions (type, title, amount, date, status, comment) 
                  VALUES (?, ?, ?, ?, ?, ?)''', 
               (tx_type, title, amount, date, status, comment))
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/add_goal', methods=['POST'])
def add_goal():
    title = request.form.get('title')
    target = float(request.form.get('target', 0))
    
    db = get_db()
    db.execute('INSERT INTO goals (title, target_amount, current_amount) VALUES (?, ?, 0)', 
               (title, target))
    db.commit()
    db.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
