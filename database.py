import sqlite3
from datetime import datetime

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
            date TEXT DEFAULT CURRENT_TIMESTAMP,
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
    """Получить список расходов (последние 50)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, amount, datetime(date, 'localtime') 
        FROM expenses 
        WHERE user_id = ? 
        ORDER BY date DESC
        LIMIT 50
    ''', (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_expenses_by_month(user_id, year_month):
    """Получить расходы за конкретный месяц по категориям"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, SUM(amount), date
        FROM expenses 
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        GROUP BY category
        ORDER BY date DESC
    ''', (user_id, year_month))
    result = cursor.fetchall()
    conn.close()
    return result

def get_expenses_by_date(user_id, date_str):
    """Получить расходы за конкретную дату"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, amount, date
        FROM expenses 
        WHERE user_id = ? AND date LIKE ?
        ORDER BY date DESC
    ''', (user_id, f"{date_str}%"))
    result = cursor.fetchall()
    conn.close()
    return result

def delete_last_expense(user_id):
    """Удалить последний расход пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Находим последний расход
    cursor.execute('''
        SELECT id, category, amount, date
        FROM expenses 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT 1
    ''', (user_id,))
    result = cursor.fetchone()
    
    if result:
        expense_id = result[0]
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()
        return result[1:]  # Возвращаем category, amount, date
    else:
        conn.close()
        return None

def clear_data(user_id):
    """Очистить все данные пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()