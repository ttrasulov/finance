import telebot
from config import TOKEN
from database import *
from datetime import datetime

bot = telebot.TeleBot(TOKEN)

# Инициализация БД при запуске
init_db()

# ================= ОСНОВНЫЕ КОМАНДЫ =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    bot.reply_to(message,
        "💰 Добро пожаловать в Финансовый Бот!\n\n"
        "Команды:\n"
        "/salary <сумма> — установить зарплату\n"
        "/add <категория> <сумма> — добавить расход\n"
        "/balance — показать остаток\n"
        "/list — показать все расходы\n"
        "/stats — отчет за текущий месяц\n"
        "/today — расходы за сегодня\n"
        "/clear — сбросить все данные"
    )

@bot.message_handler(commands=['salary'])
def set_salary_command(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ Используй: /salary 5000000")
            return
        amount = int(parts[1])
        set_salary(user_id, amount)
        bot.reply_to(message, f"✅ Зарплата установлена: {amount:,} сум")
    except ValueError:
        bot.reply_to(message, "❌ Введи корректную сумму (число)")

@bot.message_handler(commands=['add'])
def add_expense_command(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) != 3:
            bot.reply_to(message, "❌ Используй: /add еда 150000")
            return
        category = parts[1]
        amount = int(parts[2])
        add_expense(user_id, category, amount)
        bot.reply_to(message, f"✅ Расход добавлен:\nКатегория: {category}\nСумма: {amount:,} сум")
    except ValueError:
        bot.reply_to(message, "❌ Введи корректную сумму (число)")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = message.from_user.id
    salary = get_salary(user_id)
    total_exp = get_total_expenses(user_id)
    balance = salary - total_exp
    bot.reply_to(message,
        f"💰 БАЛАНС\n"
        f"Зарплата: {salary:,} сум\n"
        f"Расходы: {total_exp:,} сум\n"
        f"Остаток: {balance:,} сум"
    )

@bot.message_handler(commands=['list'])
def list_expenses_command(message):
    user_id = message.from_user.id
    expenses = get_expenses(user_id)
    if not expenses:
        bot.reply_to(message, "📭 Расходов пока нет")
        return
    text = "📋 ПОСЛЕДНИЕ РАСХОДЫ:\n\n"
    for cat, amt, date in expenses[:10]:
        text += f"• {cat}: {amt:,} сум ({date})\n"
    bot.reply_to(message, text)

# ================= НОВЫЕ КОМАНДЫ =================

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Отчет за текущий месяц"""
    user_id = message.from_user.id
    current_month = datetime.now().strftime("%Y-%m")
    
    # Получаем расходы по категориям за месяц
    expenses = get_expenses_by_month(user_id, current_month)
    
    if not expenses:
        bot.reply_to(message, "📊 За этот месяц трат пока нет.")
        return
    
    # Считаем общую сумму
    total = sum(amt for _, amt, _ in expenses)
    
    text = f"📊 **ОТЧЕТ ЗА {current_month}:**\n\n"
    for cat, amt, _ in expenses:
        text += f"• {cat}: {amt:,} сум\n"
    text += f"\n💰 **ИТОГО: {total:,} сум**"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=['today'])
def today_command(message):
    """Расходы за сегодня"""
    user_id = message.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    expenses = get_expenses_by_date(user_id, today)
    
    if not expenses:
        bot.reply_to(message, "📭 За сегодня расходов нет")
        return
    
    total = sum(amt for _, amt, _ in expenses)
    
    text = f"📊 **РАСХОДЫ ЗА СЕГОДНЯ ({today}):**\n\n"
    for cat, amt, _ in expenses:
        text += f"• {cat}: {amt:,} сум\n"
    text += f"\n💰 **ИТОГО: {total:,} сум**"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=['delete'])
def delete_last_command(message):
    """Удалить последний расход"""
    user_id = message.from_user.id
    result = delete_last_expense(user_id)
    
    if result:
        cat, amt, date = result
        bot.reply_to(message, 
            f"✅ Последний расход удален:\n"
            f"Категория: {cat}\n"
            f"Сумма: {amt:,} сум\n"
            f"Дата: {date}"
        )
    else:
        bot.reply_to(message, "❌ У вас нет расходов для удаления")

@bot.message_handler(commands=['clear'])
def clear_command(message):
    user_id = message.from_user.id
    clear_data(user_id)
    bot.reply_to(message, "🗑️ Все данные сброшены")

# ================= ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =================

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обработка текстовых сообщений"""
    text = message.text.strip()
    
    # Проверяем, является ли сообщение числом (суммой)
    try:
        # Убираем пробелы и запятые
        clean_text = text.replace(' ', '').replace(',', '')
        amount = int(clean_text)
        
        if amount <= 0:
            bot.reply_to(message, "❌ Сумма должна быть больше 0")
            return
        
        # Сохраняем сумму в состоянии пользователя (временное хранилище)
        # Для простоты используем словарь в памяти
        if not hasattr(bot, 'user_states'):
            bot.user_states = {}
        
        bot.user_states[message.from_user.id] = {'amount': amount}
        
        # Предлагаем ввести категорию
        bot.reply_to(message,
            f"💰 Сумма: {amount:,} сум\n\n"
            "📝 Введите категорию расхода текстом\n"
            "Например: Продукты, Транспорт, Кафе и т.д.\n\n"
            "Или используйте /cancel для отмены"
        )
        
    except ValueError:
        # Если это не число, проверяем состояние пользователя
        if hasattr(bot, 'user_states') and message.from_user.id in bot.user_states:
            # Это категория для сохраненной суммы
            category = text
            user_id = message.from_user.id
            amount = bot.user_states[user_id]['amount']
            
            # Сохраняем расход
            add_expense(user_id, category, amount)
            
            # Удаляем состояние
            del bot.user_states[user_id]
            
            bot.reply_to(message,
                f"✅ Расход добавлен:\n"
                f"Категория: {category}\n"
                f"Сумма: {amount:,} сум"
            )
        else:
            bot.reply_to(message,
                "❓ Я понимаю только суммы и команды.\n\n"
                "📝 Отправьте мне сумму, например:\n"
                "• 50000\n"
                "• 150000\n\n"
                "Или используйте команды:\n"
                "/stats — отчет за месяц\n"
                "/today — расходы за сегодня\n"
                "/delete — удалить последний расход"
            )

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    """Отмена текущей операции"""
    if hasattr(bot, 'user_states') and message.from_user.id in bot.user_states:
        del bot.user_states[message.from_user.id]
        bot.reply_to(message, "❌ Операция отменена")
    else:
        bot.reply_to(message, "❌ Нет активной операции для отмены")

if __name__ == "__main__":
    print("🤖 Бот запущен...")
    print("📊 База данных: finance_bot.db")
    print("📝 Команды: /start для справки")
    bot.polling(none_stop=True)