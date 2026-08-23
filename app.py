from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import random
from database import init_db, get_db

app = Flask(__name__)
init_db()

RANKS = [
    (1, "Новичок", 50), (2, "Первые шаги", 100), (3, "Стажёр", 200), (4, "Практикант", 350),
    (5, "Студент", 500), (6, "Юниор", 700), (7, "Энтузиаст", 1000), (8, "Фрилансер", 1300),
    (9, "Исполнитель", 1700), (10, "Спекулянт", 2200), (11, "Трейдер", 2800), (12, "Ассистент", 3500),
    (13, "Специалист", 4300), (14, "Мастер сделок", 5200), (15, "Опытный", 6200), (16, "Скриптер", 7300),
    (17, "Продвинутый", 8500), (18, "Оптовик", 10000), (19, "Десятка", 12000), (20, "Профи", 14500),
    (21, "Лидер продаж", 17500), (22, "Теневой игрок", 21000), (23, "Автоматизатор", 25000),
    (24, "Партнёр", 30000), (25, "Четвертак", 36000), (26, "Аналитик", 43000), (27, "Кибер-диллер", 51000),
    (28, "Полтинник", 60000), (29, "Техно-магнат", 70000), (30, "Владелец сетей", 82000),
    (31, "Стратег", 95000), (32, "Сотка", 110000), (33, "Капиталист", 130000), (34, "Инвестор", 155000),
    (35, "Директор", 185000), (36, "Маркетмейкер", 220000), (37, "Архитектор прибыли", 260000),
    (38, "Крипто-босс", 310000), (39, "Теневой банкир", 370000), (40, "Финансовый гуру", 440000),
    (41, "Полумиллионер", 520000), (42, "Властелин сделок", 620000), (43, "Рыночный хищник", 740000),
    (44, "Грандмастер", 880000), (45, "Миллионер", 1050000), (46, "Олигарх", 1300000),
    (47, "Теневой кардинал", 1600000), (48, "Хозяин системы", 2000000), (49, "Легенда S-TRACKER", 2500000),
    (50, "Босс Уолл-Стрит", 3000000)
]

QUOTES = [
    "«Маленькие суммы тоже становятся большими.»",
    "«Главное — продолжать.»",
    "«Сегодня +10 ₽. Завтра +100 ₽.»",
    "«Результат складывается из маленьких действий.»",
    "«Не жди идеального момента.»",
    "«Дисциплина бьёт любой талант.»",
    "«Каждая зафиксированная сделка приближает цель.»",
    "«Рынок платит терпеливым.»"
]

def calculate_rank(month_earnings):
    current = RANKS[0]
    next_rank = RANKS[1]
    
    for i, r in enumerate(RANKS):
        if month_earnings >= r[2]:
            current = r
            next_rank = RANKS[i+1] if i+1 < len(RANKS) else r
        else:
            if i == 0:
                next_rank = r
            break
            
    target = next_rank[2]
    needed = max(0, target - month_earnings)
    pct = min(100, int((month_earnings / target) * 100)) if target > 0 else 100
    
    return {
        "num": current[0],
        "name": current[1],
        "current_val": month_earnings,
        "target_val": target,
        "needed": needed,
        "progress_pct": pct
    }

@app.route('/')
def index():
    db = get_db()
    current_month_str = datetime.now().strftime('%Y-%m')
    
    transactions = db.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
    ideas = db.execute('SELECT id, title FROM ideas').fetchall()
    history = db.execute('SELECT * FROM monthly_history ORDER BY month_key DESC').fetchall()
    
    month_earned = sum(tx['amount'] for tx in transactions if tx['category'] == 'Доход' and tx['status'] == 'received' and tx['date'].startswith(current_month_str))
    month_pending = sum(tx['amount'] for tx in transactions if tx['category'] == 'Доход' and tx['status'] == 'pending' and tx['date'].startswith(current_month_str))
    
    row_all = db.execute("SELECT value FROM settings WHERE key = 'all_time_balance'").fetchone()
    all_time_base = float(row_all['value']) if row_all else 0.0
    all_time_balance = all_time_base + month_earned
    
    rank_info = calculate_rank(month_earned)
    random_quote = random.choice(QUOTES)
    
    db.close()
    return render_template('index.html', 
                           transactions=transactions, 
                           ideas=ideas,
                           history=history,
                           month_earned=month_earned, 
                           month_pending=month_pending,
                           all_time_balance=all_time_balance,
                           rank=rank_info,
                           quote=random_quote)

@app.route('/goals')
def goals_page():
    db = get_db()
    goals = db.execute('SELECT * FROM goals ORDER BY id DESC').fetchall()
    db.close()
    return render_template('goals.html', goals=goals)

@app.route('/calc')
def calc_page():
    return render_template('calc.html')

@app.route('/ideas')
def ideas_page():
    db = get_db()
    ideas = db.execute('SELECT * FROM ideas ORDER BY id DESC').fetchall()
    ideas_data = []
    for idea in ideas:
        earned = db.execute('SELECT SUM(amount) FROM transactions WHERE idea_id = ? AND category = "Доход" AND status = "received"', (idea['id'],)).fetchone()[0] or 0.0
        ideas_data.append({"info": idea, "earned": earned})
    db.close()
    return render_template('ideas.html', ideas=ideas_data)

@app.route('/add', methods=['POST'])
def add_transaction():
    title = request.form.get('title')
    amount = float(request.form.get('amount', 0))
    category = request.form.get('category', 'Доход')
    status = request.form.get('status', 'received')
    idea_id = request.form.get('idea_id')
    idea_id = int(idea_id) if idea_id and idea_id.isdigit() else None
    date = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    db = get_db()
    db.execute('''INSERT INTO transactions (title, amount, category, date, status, idea_id) 
                  VALUES (?, ?, ?, ?, ?, ?)''',
               (title, amount, category, date, status, idea_id))
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/delete_tx/<int:tx_id>', methods=['POST'])
def delete_tx(tx_id):
    db = get_db()
    db.execute('DELETE FROM transactions WHERE id = ?', (tx_id,))
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/add_goal', methods=['POST'])
def add_goal():
    title = request.form.get('title')
    target = float(request.form.get('target', 0))
    current = float(request.form.get('current', 0))
    db = get_db()
    db.execute('INSERT INTO goals (title, target_amount, current_amount) VALUES (?, ?, ?)', (title, target, current))
    db.commit()
    db.close()
    return redirect(url_for('goals_page'))

@app.route('/delete_goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    db = get_db()
    db.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    db.commit()
    db.close()
    return redirect(url_for('goals_page'))

@app.route('/add_idea', methods=['POST'])
def add_idea():
    db = get_db()
    db.execute('''
        INSERT INTO ideas (title, category, potential, difficulty, skills, investments, launch_time, source, status, description, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form.get('title'),
        request.form.get('category', 'Другое'),
        request.form.get('potential'),
        request.form.get('difficulty'),
        request.form.get('skills'),
        request.form.get('investments'),
        request.form.get('launch_time'),
        request.form.get('source'),
        request.form.get('status', 'Новая'),
        request.form.get('description'),
        request.form.get('notes')
    ))
    db.commit()
    db.close()
    return redirect(url_for('ideas_page'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
