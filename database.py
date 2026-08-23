import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # Таблица операций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            comment TEXT
        )
    ''')
    
    # Таблица целей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0
        )
    ''')
    
    # Таблица настроек (для автопереноса баланса)
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
        cursor.execute("INSERT INTO settings (key, value) VALUES ('all_time_balance', '0')")
        
    # Логика автопереноса при смене месяца
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute("SELECT value FROM settings WHERE key = 'last_recorded_month'")
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO settings (key, value) VALUES ('last_recorded_month', ?)", (current_month,))
    else:
        last_month = row[0]
        if last_month != current_month:
            # Считаем только ПОЛУЧЕННЫЙ доход за прошлый месяц
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND status='received' AND date LIKE ?", (f"{last_month}%",))
            res = cursor.fetchone()
            last_month_earnings = res[0] if res and res[0] else 0.0
            
            if last_month_earnings > 0:
                cursor.execute("SELECT value FROM settings WHERE key = 'all_time_balance'")
                current_all_time = float(cursor.fetchone()[0])
                new_all_time = current_all_time + last_month_earnings
                cursor.execute("UPDATE settings SET value = ? WHERE key = 'all_time_balance'", (str(new_all_time),))
            
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
