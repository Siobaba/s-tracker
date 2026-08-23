import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # 1. Таблица операций (связана с идеями)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'received',
            idea_id INTEGER
        )
    ''')
    
    # 2. Таблица идей заработка
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            potential TEXT,
            difficulty TEXT,
            skills TEXT,
            investments TEXT,
            launch_time TEXT,
            source TEXT,
            status TEXT NOT NULL DEFAULT 'Новая',
            description TEXT,
            notes TEXT
        )
    ''')

    # 3. Таблица истории месяцев
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_history (
            month_key TEXT PRIMARY KEY,
            month_name TEXT,
            earned_amount REAL DEFAULT 0,
            expenses_amount REAL DEFAULT 0,
            net_income REAL DEFAULT 0,
            income_count INTEGER DEFAULT 0,
            expense_count INTEGER DEFAULT 0
        )
    ''')

    # 4. Таблица настроек и общего баланса
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    
    # Инициализация общего баланса
    cursor.execute("SELECT value FROM settings WHERE key = 'all_time_balance'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('all_time_balance', '0.0')")
        
    # Логика проверки и автопереноса закрытых месяцев
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute("SELECT value FROM settings WHERE key = 'last_checked_month'")
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO settings (key, value) VALUES ('last_checked_month', ?)", (current_month,))
    else:
        last_month = row[0]
        if last_month != current_month:
            # Считаем заработок за закрытый месяц
            cursor.execute("SELECT amount, category, status FROM transactions WHERE date LIKE ?", (f"{last_month}%",))
            past_txs = cursor.fetchall()
            
            inc_sum = sum(tx[0] for tx in past_txs if tx[1] == 'Доход' and tx[2] == 'received')
            exp_sum = sum(tx[0] for tx in past_txs if tx[1] == 'Расход')
            net = inc_sum - exp_sum
            
            # Записываем в архив истории месяцев
            cursor.execute('''
                INSERT OR REPLACE INTO monthly_history 
                (month_key, month_name, earned_amount, expenses_amount, net_income, income_count, expense_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (last_month, last_month, inc_sum, exp_sum, net, 
                  len([tx for tx in past_txs if tx[1] == 'Доход']), 
                  len([tx for tx in past_txs if tx[1] == 'Расход'])))
            
            # Переносим чистый профит в общий накопленный баланс
            if net > 0:
                cursor.execute("SELECT value FROM settings WHERE key = 'all_time_balance'")
                curr_all = float(cursor.fetchone()[0])
                new_all = curr_all + net
                cursor.execute("UPDATE settings SET value = ? WHERE key = 'all_time_balance'", (str(new_all),))
                
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'last_checked_month'", (current_month,))
            
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn
