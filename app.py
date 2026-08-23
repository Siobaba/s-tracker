from flask import Flask, render_template, request, redirect, url_for
import database
import datetime

app = Flask(__name__)
database.create_tables()


# ==========================================
# 1. ГЛАВНАЯ СТРАНИЦА (ДАШБОРД)
# ==========================================
@app.route('/')
def index():
    conn = database.get_connection()
    incomes = conn.execute('SELECT * FROM income ORDER BY date DESC LIMIT 5').fetchall()

    received_val = conn.execute('SELECT SUM(amount) FROM income WHERE status = "received"').fetchone()[0]
    expected_val = conn.execute('SELECT SUM(amount) FROM income WHERE status = "expected"').fetchone()[0]
    expenses_val = conn.execute('SELECT SUM(amount) FROM expenses').fetchone()[0]

    received = received_val if received_val is not None else 0.0
    expected = expected_val if expected_val is not None else 0.0
    expenses = expenses_val if expenses_val is not None else 0.0

    conn.close()
    return render_template('index.html', incomes=incomes, received=received, expected=expected, expenses=expenses)


# ==========================================
# 2. РАЗДЕЛ "ДОХОДЫ"
# ==========================================
@app.route('/incomes')
def incomes_page():
    status_filter = request.args.get('status', 'all')
    query = 'SELECT * FROM income WHERE 1=1'
    params = []

    if status_filter != 'all':
        query += ' AND status = ?'
        params.append(status_filter)

    query += ' ORDER BY date DESC'

    conn = database.get_connection()
    incomes = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('incomes.html', incomes=incomes, current_status=status_filter)


@app.route('/add_income', methods=['POST'])
def add_income():
    source = request.form.get('source')
    amount = float(request.form.get('amount', 0))
    date = request.form.get('date') or datetime.datetime.now().strftime("%Y-%m-%d")
    status = request.form.get('status')
    comment = request.form.get('comment', '')

    conn = database.get_connection()
    conn.execute('INSERT INTO income (source, amount, date, status, comment) VALUES (?, ?, ?, ?, ?)',
                 (source, amount, date, status, comment))
    conn.commit()
    conn.close()
    return redirect(url_for('incomes_page'))


@app.route('/delete_income/<int:item_id>')
def delete_income(item_id):
    conn = database.get_connection()
    conn.execute('DELETE FROM income WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('incomes_page'))


@app.route('/mark_received/<int:item_id>')
def mark_received(item_id):
    conn = database.get_connection()
    conn.execute('UPDATE income SET status = "received" WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('incomes_page'))


# ==========================================
# 3. РАЗДЕЛ "РАСХОДЫ"
# ==========================================
@app.route('/expenses')
def expenses_page():
    conn = database.get_connection()
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    total_expenses = conn.execute('SELECT SUM(amount) FROM expenses').fetchone()[0] or 0.0
    conn.close()
    return render_template('expenses.html', expenses=expenses, total_expenses=total_expenses)


@app.route('/add_expense', methods=['POST'])
def add_expense():
    category = request.form.get('category')
    amount = float(request.form.get('amount', 0))
    date = request.form.get('date') or datetime.datetime.now().strftime("%Y-%m-%d")
    comment = request.form.get('comment', '')

    conn = database.get_connection()
    conn.execute('INSERT INTO expenses (category, amount, date, comment) VALUES (?, ?, ?, ?)',
                 (category, amount, date, comment))
    conn.commit()
    conn.close()
    return redirect(url_for('expenses_page'))


@app.route('/delete_expense/<int:item_id>')
def delete_expense(item_id):
    conn = database.get_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('expenses_page'))


# ==========================================
# 4. РАЗДЕЛ "ЦЕЛИ"
# ==========================================
@app.route('/goals')
def goals_page():
    conn = database.get_connection()
    goals = conn.execute('SELECT * FROM goals ORDER BY deadline ASC').fetchall()
    conn.close()
    return render_template('goals.html', goals=goals)


@app.route('/add_goal', methods=['POST'])
def add_goal():
    title = request.form.get('title')
    target_amount = float(request.form.get('target_amount', 0))
    deadline = request.form.get('deadline')

    conn = database.get_connection()
    conn.execute('INSERT INTO goals (title, target_amount, deadline) VALUES (?, ?, ?)',
                 (title, target_amount, deadline))
    conn.commit()
    conn.close()
    return redirect(url_for('goals_page'))


@app.route('/contribute_goal/<int:goal_id>', methods=['POST'])
def contribute_goal(goal_id):
    sum_add = float(request.form.get('sum_add', 0))
    conn = database.get_connection()
    conn.execute('UPDATE goals SET current_amount = current_amount + ? WHERE id = ?', (sum_add, goal_id))
    conn.commit()
    conn.close()
    return redirect(url_for('goals_page'))


@app.route('/delete_goal/<int:goal_id>')
def delete_goal(goal_id):
    conn = database.get_connection()
    conn.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('goals_page'))


# ==========================================
# 5. АНАЛИТИКА
# ==========================================
@app.route('/analytics')
def analytics_page():
    conn = database.get_connection()
    total_received = conn.execute('SELECT SUM(amount) FROM income WHERE status = "received"').fetchone()[0] or 0.0
    total_expenses = conn.execute('SELECT SUM(amount) FROM expenses').fetchone()[0] or 0.0
    net_profit = total_received - total_expenses

    max_income = conn.execute('SELECT MAX(amount) FROM income WHERE status = "received"').fetchone()[0] or 0.0
    avg_income = conn.execute('SELECT AVG(amount) FROM income WHERE status = "received"').fetchone()[0] or 0.0

    sources_stat = conn.execute('''
        SELECT source, SUM(amount) as total, COUNT(id) as count 
        FROM income WHERE status = "received" GROUP BY source ORDER BY total DESC
    ''').fetchall()

    conn.close()
    return render_template('analytics.html',
                           total_received=total_received,
                           total_expenses=total_expenses,
                           net_profit=net_profit,
                           max_income=max_income,
                           avg_income=avg_income,
                           sources_stat=sources_stat)


# ==========================================
# 6. ТЕСТОВЫЕ ДАННЫЕ
# ==========================================
@app.route('/add_test')
def add_test():
    conn = database.get_connection()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn.execute('INSERT INTO income (source, amount, date, status, comment) VALUES (?, ?, ?, ?, ?)',
                 ('Партнерка Mysor', 30.0, today, 'expected', 'За ролик на 416k'))
    conn.execute('INSERT INTO income (source, amount, date, status, comment) VALUES (?, ?, ?, ?, ?)',
                 ('TikTok аккаунт', 15.5, today, 'received', 'Продажа старого профиля'))
    conn.execute('INSERT INTO expenses (category, amount, date, comment) VALUES (?, ?, ?, ?)',
                 ('Сервер (Kamatera)', 12.0, today, 'Оплата хостинга бота'))
    conn.execute('INSERT INTO goals (title, target_amount, current_amount, deadline) VALUES (?, ?, ?, ?)',
                 ('Новый ПК для монтажа', 1200.0, 450.0, '2026-12-31'))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
