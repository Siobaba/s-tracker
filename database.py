import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    
    # Таблица для системных настроек (например, хранение общего баланса и месяца)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    
    # Инициализируем общий баланс, если его нет
    cursor.execute("SELECT value FROM settings WHERE key = 'all_time_balance'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('all_time_balance', '0')")
        
    # Инициализируем текущий месяц
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute("SELECT value FROM settings WHERE key = 'last_recorded_month'")
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO settings (key, value) VALUES ('last_recorded_month', ?)", (current_month,))
    else:
        # Проверяем, сменился ли месяц
        last_month = row[0]
        if last_month != current_month:
            # Месяц сменился! Переносим доходы прошлого месяца в общий баланс
            # Считаем сумму доходов за прошлый месяц из транзакций
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE date LIKE ?", (f"{last_month}%",))
            res = cursor.fetchone()
            last_month_earnings = res[0] if res and res[0] else 0.0
            
            if last_month_earnings > 0:
                cursor.execute("SELECT value FROM settings WHERE key = 'all_time_balance'")
                current_all_time = float(cursor.fetchone()[0])
                new_all_time = current_all_time + last_month_earnings
                cursor.execute("UPDATE settings SET value = ? WHERE key = 'all_time_balance'", (str(new_all_time),))
            
            # Обновляем месяц на текущий
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'last_recorded_month'", (current_month,))
            
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_time_balance():
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = 'all_time_balance'").fetchone()
    db.close()
    return float(row['value']) if row else 0.0
