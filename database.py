import sqlite3

DB_NAME = 'finance_bot.db'

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            salary INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица расходов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def set_salary(user_id, amount):
    """Установить зарплату"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, salary)
        VALUES (?, ?)
    ''', (user_id, amount))
    conn.commit()
    conn.close()

def get_salary(user_id):
    """Получить зарплату"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT salary FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def add_expense(user_id, category, amount):
    """Добавить расход"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (user_id, category, amount)
        VALUES (?, ?, ?)
    ''', (user_id, category, amount))
    conn.commit()
    conn.close()

def get_total_expenses(user_id):
    """Получить общую сумму расходов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) 
        FROM expenses 
        WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_expenses(user_id):
    """Получить список расходов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, amount, datetime(date, 'localtime') 
        FROM expenses 
        WHERE user_id = ? 
        ORDER BY date DESC
    ''', (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def clear_data(user_id):
    """Очистить все данные пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()