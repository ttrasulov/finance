import telebot
from config import TOKEN
from database import *

bot = telebot.TeleBot(TOKEN)

# Инициализация БД при запуске
init_db()

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

@bot.message_handler(commands=['clear'])
def clear_command(message):
    user_id = message.from_user.id
    clear_data(user_id)
    bot.reply_to(message, "🗑️ Все данные сброшены")

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)