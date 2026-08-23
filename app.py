from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from database import init_db, get_db, get_all_time_balance

app = Flask(__name__)
init_db()

RANKS = [
    (0, "Стажёр (0₽)"), (500, "Новичок (500₽)"), (1500, "Фрилансер"), (3000, "Первые деньги"),
    (5000, "Студент-скриптер"), (7500, "Мелкий барыга"), (10000, "Десятка (10k)"),
    (15000, "Мастер авито"), (20000, "Уверенный тип"), (30000, "Серый кардинал"),
    (50000, "Полтинник (50k)"), (75000, "Магнат микробизнеса"), (100000, "Сотка (100k)"),
    (150000, "Тир-2 Стример"), (200000, "Оптовик"), (300000, "Владелец сетей"),
    (500000, "Полумиллионер"), (1000000, "Миллионер (1M)"), (5000000, "Рыночный хищник"),
    (10000000, "Босс Уолл-Стрит")
]

QUOTES = [
    "«Деньги не спят. И твой баланс тоже не должен.»",
    "«SEC следит за каждым твоим шагом. Будь умнее.»",
    "«Каждая ошибка на рынке — это просто платная лекция.»",
    "«Риск — это плата за успех на Уолл-стрит.»",
    "«Хочешь разбогатеть — перестань слушать советы тех, кто беднее тебя.»"
]

BUSINESS_IDEAS = [
    {"title": "Telegram-боты под ключ", "potential": "Высокий", "desc": "Разработка кастомных ботов для автоматизации продаж."},
    {"title": "Арбитраж (Playerok/FunPay)", "potential": "Средний", "desc": "Перепродажа аккаунтов, валюты и ключей с наценкой."},
    {"title": "Локальные AI-ассистенты", "potential": "Топ", "desc": "Интеграция ИИ с CRM системами компаний."}
]

def get_rank(amount):
    current_rank = RANKS[0][1]
    for threshold, rank_name in RANKS:
        if amount >= threshold: current_rank = rank_name
        else: break
    return current_rank

@app.route('/')
def index():
    db = get_db()
    transactions = db.execute('SELECT * FROM transactions ORDER BY date DESC, id DESC').fetchall()
    goals = db.execute('SELECT * FROM goals ORDER BY id DESC').fetchall()
    all_time_balance = get_all_time_balance()
    db.close()
    
    current_month_str = datetime.now().strftime('%Y-%m')
    net_income = 0.0
    pending_income = 0.0
    
    for tx in transactions:
        if tx['type'] == 'income' and tx['date'].startswith(current_month_str):
            if tx['status'] == 'received': net_income += tx['amount']
            elif tx['status'] == 'pending': pending_income += tx['amount']
            
    current_rank = get_rank(net_income)

    return render_template('index.html', 
                           transactions=transactions, goals=goals,
                           net_income=net_income, pending_income=pending_income,
                           all_time_balance=all_time_balance, current_rank=current_rank,
                           quotes=QUOTES, ideas=BUSINESS_IDEAS)

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
                  VALUES (?, ?, ?, ?, ?, ?)''', (tx_type, title, amount, date, status, comment))
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/add_goal', methods=['POST'])
def add_goal():
    title = request.form.get('title')
    target = float(request.form.get('target', 0))
    db = get_db()
    db.execute('INSERT INTO goals (title, target_amount, current_amount) VALUES (?, ?, 0)', (title, target))
    db.commit()
    db.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
