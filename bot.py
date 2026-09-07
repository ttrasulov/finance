import telebot
from config import TOKEN
from database import *
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

bot = telebot.TeleBot(TOKEN)

# Инициализация БД при запуске
init_db()

# Хранилище состояний пользователей
user_states = {}

# ================= КЛАВИАТУРЫ =================

def get_main_keyboard():
    """Главная клавиатура с командами"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("💰 Баланс"),
        KeyboardButton("📊 Статистика"),
        KeyboardButton("📝 Добавить расход"),
        KeyboardButton("📋 Все расходы"),
        KeyboardButton("📅 Расходы за сегодня"),
        KeyboardButton("🗑️ Сбросить данные")
    )
    return keyboard

def get_months_keyboard():
    """Клавиатура с выбором месяца"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Получаем список месяцев, в которых есть расходы
    months = get_available_months()
    
    if months:
        # Добавляем кнопки с месяцами (по 2 в ряд)
        row = []
        for month in months:
            year, month_num = month.split('-')
            month_name = datetime(int(year), int(month_num), 1).strftime("%B %Y")
            row.append(KeyboardButton(f"📅 {month_name}"))
            if len(row) == 2:
                keyboard.add(*row)
                row = []
        if row:
            keyboard.add(*row)
    else:
        keyboard.add(KeyboardButton("📭 Нет расходов"))
    
    # Всегда добавляем кнопку "Все расходы" и "Назад"
    keyboard.add(
        KeyboardButton("📋 Все расходы"),
        KeyboardButton("🔙 Назад")
    )
    
    return keyboard

def get_previous_month():
    """Возвращает предыдущий месяц в формате YYYY-MM"""
    from datetime import datetime, timedelta
    today = datetime.now()
    first_day_of_month = today.replace(day=1)
    previous_month = first_day_of_month - timedelta(days=1)
    return previous_month.strftime("%Y-%m")

def get_categories_keyboard():
    """Клавиатура с категориями расходов (без эмодзи)"""
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    categories = [
        "Продукты", "Мясо", "Бытовая химия", "Заправка",
        "Жене на кофе", "Садик", "Свет", "Газ", "Вода",
        "Телефон", "Интернет", "ЖЭК", "Мусор", "Аптека", 
        "Одежда", "Прочее"
    ]
    
    # Добавляем категории по 2 в ряд
    row = []
    for cat in categories:
        row.append(KeyboardButton(cat))
        if len(row) == 2:
            keyboard.add(*row)
            row = []
    if row:
        keyboard.add(*row)
    
    # Добавляем кнопку отмены
    keyboard.add(KeyboardButton("❌ Отмена"))
    
    return keyboard

def get_undo_inline_keyboard(record_id):
    """Инлайн клавиатура для отмены записи"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Отменить запись", callback_data=f"undo_{record_id}"))
    return keyboard

# ================= ОБРАБОТКА КОМАНД =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "💰 **Добро пожаловать в Финансовый Бот!**\n\n"
        "📌 Используй кнопки ниже для управления финансами:\n\n"
        "💳 **Основные функции:**\n"
        "💰 Баланс - посмотреть остаток\n"
        "📊 Статистика - отчет по месяцам\n"
        "📝 Добавить расход - записать трату\n"
        "📋 Все расходы - список всех трат\n"
        "📅 Расходы за сегодня - траты за день\n\n"
        "⚙️ **Управление:**\n"
        "🗑️ Сбросить данные - очистить все данные",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ================= ОБРАБОТКА КНОПОК ГЛАВНОГО МЕНЮ =================

@bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def balance_command(message):
    user_id = message.from_user.id
    total_exp = get_total_expenses(user_id)
    
    bot.reply_to(
        message,
        f"💰 **БАЛАНС**\n\n"
        f"📉 Расходы: {total_exp:,} сум",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def stats_command(message):
    user_id = message.from_user.id
    current_month = datetime.now().strftime("%Y-%m")
    month_name = datetime.now().strftime("%B %Y")
    
    expenses = get_expenses_by_month(user_id, current_month)
    
    if not expenses:
        bot.reply_to(
            message,
            f"📊 За {month_name} трат пока нет.",
            reply_markup=get_main_keyboard()
        )
        return
    
    total = sum(amt for _, amt, _ in expenses)
    
    text = f"📊 **ОТЧЕТ ЗА {month_name.upper()}**\n\n"
    
    # Сортируем по убыванию суммы
    sorted_expenses = sorted(expenses, key=lambda x: x[1], reverse=True)
    
    for cat, amt, _ in sorted_expenses:
        text += f"• {cat}: {amt:,} сум\n"
    
    text += f"\n💰 **ИТОГО: {total:,} сум**"
    
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ================= ВЫБОР МЕСЯЦА ДЛЯ РАСХОДОВ =================

def get_available_months():
    """Возвращает список месяцев, в которых есть расходы"""
    import sqlite3
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT strftime('%Y-%m', date) as month
        FROM expenses
        ORDER BY month DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

@bot.message_handler(func=lambda message: message.text == "📋 Все расходы")
def list_expenses_command(message):
    user_id = message.from_user.id
    
    # Проверяем, есть ли вообще расходы
    expenses = get_expenses(user_id)
    if not expenses:
        bot.reply_to(
            message,
            "📭 У вас пока нет расходов.\n"
            "Нажмите '📝 Добавить расход' чтобы добавить.",
            reply_markup=get_main_keyboard()
        )
        return
    
    bot.reply_to(
        message,
        "📋 **Выберите месяц:**\n\n"
        "Нажмите на месяц, чтобы посмотреть расходы за него.\n"
        "📋 Все расходы - показать все записи.",
        parse_mode="Markdown",
        reply_markup=get_months_keyboard()
    )

@bot.message_handler(func=lambda message: message.text.startswith("📅 ") and message.text != "📅 Расходы за сегодня")
def handle_month_selection(message):
    """Обработка выбора месяца из списка"""
    user_id = message.from_user.id
    
    # Извлекаем название месяца из кнопки
    month_text = message.text.replace("📅 ", "")
    
    # Парсим месяц (формат: "January 2025")
    try:
        month_date = datetime.strptime(month_text, "%B %Y")
        month = month_date.strftime("%Y-%m")
        month_name = month_text
    except ValueError:
        bot.reply_to(
            message,
            "❌ Не удалось распознать месяц. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем расходы за выбранный месяц
    show_expenses_by_month(message, user_id, month, month_name)

@bot.message_handler(func=lambda message: message.text == "📋 Все расходы")
def show_all_expenses_from_menu(message):
    user_id = message.from_user.id
    expenses = get_expenses(user_id)
    
    if not expenses:
        bot.reply_to(
            message,
            "📭 У вас пока нет расходов.",
            reply_markup=get_main_keyboard()
        )
        return
    
    text = "📋 **ВСЕ РАСХОДЫ:**\n\n"
    total = 0
    
    for cat, amt, date in expenses[:20]:
        total += amt
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        date_str = date_obj.strftime("%d.%m.%Y %H:%M")
        text += f"• {cat}: {amt:,} сум ({date_str})\n"
    
    if len(expenses) > 20:
        text += f"\n... и еще {len(expenses) - 20} записей"
    
    text += f"\n💰 **ВСЕГО РАСХОДОВ: {total:,} сум**"
    
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📅 Расходы за сегодня")
def today_command(message):
    user_id = message.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    today_str = datetime.now().strftime("%d.%m.%Y")
    
    expenses = get_expenses_by_date(user_id, today)
    
    if not expenses:
        bot.reply_to(
            message,
            f"📭 За сегодня ({today_str}) расходов нет",
            reply_markup=get_main_keyboard()
        )
        return
    
    total = sum(amt for _, amt, _ in expenses)
    
    text = f"📅 **РАСХОДЫ ЗА СЕГОДНЯ ({today_str})**\n\n"
    for cat, amt, date in expenses:
        time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
        text += f"• {cat}: {amt:,} сум ({time})\n"
    
    text += f"\n💰 **ИТОГО ЗА ДЕНЬ: {total:,} сум**"
    
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить последний")
def delete_last_command(message):
    user_id = message.from_user.id
    result = delete_last_expense(user_id)
    
    if result:
        cat, amt, date = result
        bot.reply_to(
            message,
            f"✅ **Последний расход удален:**\n\n"
            f"📂 {cat}\n"
            f"💰 {amt:,} сум\n"
            f"🕐 {date}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.reply_to(
            message,
            "❌ У вас нет расходов для удаления",
            reply_markup=get_main_keyboard()
        )

@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_to_main(message):
    bot.reply_to(
        message,
        "📌 Главное меню:",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🗑️ Сбросить данные")
def clear_command(message):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("✅ Да, сбросить всё"),
        KeyboardButton("❌ Нет, отмена")
    )
    bot.reply_to(
        message,
        "⚠️ **ВНИМАНИЕ!**\n\n"
        "Вы уверены, что хотите сбросить ВСЕ данные?\n"
        "Это действие нельзя отменить!",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == "✅ Да, сбросить всё")
def confirm_clear(message):
    user_id = message.from_user.id
    clear_data(user_id)
    bot.reply_to(
        message,
        "🗑️ **Все данные успешно сброшены!**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "❌ Нет, отмена")
def cancel_clear(message):
    bot.reply_to(
        message,
        "✅ Операция отменена",
        reply_markup=get_main_keyboard()
    )

# ================= ДОБАВЛЕНИЕ РАСХОДА =================

@bot.message_handler(func=lambda message: message.text == "📝 Добавить расход")
def add_expense_start(message):
    user_id = message.from_user.id
    
    # Сохраняем состояние - ожидание ввода суммы
    user_states[user_id] = {'step': 'waiting_amount'}
    
    bot.reply_to(
        message,
        "💰 **Введите сумму расхода**\n\n"
        "Напишите число, например: 150000",
        parse_mode="Markdown",
        reply_markup=get_categories_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def cancel_operation(message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    bot.reply_to(
        message,
        "❌ Операция отменена",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка всех текстовых сообщений"""
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем, есть ли состояние пользователя
    if user_id in user_states:
        step = user_states[user_id].get('step')
        
        # ========== ОБРАБОТКА ДОБАВЛЕНИЯ РАСХОДА ==========
        if step == 'waiting_amount':
            # Пробуем распарсить сумму
            try:
                clean_text = text.replace(' ', '').replace(',', '').replace('.', '')
                amount = int(clean_text)
                
                if amount <= 0:
                    bot.reply_to(
                        message, 
                        "❌ Сумма должна быть больше 0\n\nПопробуйте снова:",
                        reply_markup=get_categories_keyboard()
                    )
                    return
                
                # Сохраняем сумму в состоянии
                user_states[user_id]['amount'] = amount
                user_states[user_id]['step'] = 'waiting_category'
                
                bot.reply_to(
                    message,
                    f"✅ Сумма: {amount:,} сум\n\n"
                    "📂 **Теперь выберите категорию расхода:**",
                    parse_mode="Markdown",
                    reply_markup=get_categories_keyboard()
                )
                
            except ValueError:
                if text in get_categories_list():
                    bot.reply_to(
                        message,
                        "❌ Сначала введите сумму!\n\n"
                        "Напишите число, например: 150000",
                        reply_markup=get_categories_keyboard()
                    )
                else:
                    bot.reply_to(
                        message,
                        "❌ Введите корректную сумму (число)\n\n"
                        "Пример: 150000",
                        reply_markup=get_categories_keyboard()
                    )
        
        # Если ожидаем категорию
        elif step == 'waiting_category':
            # Проверяем, является ли текст категорией
            if text in get_categories_list():
                category = text
                amount = user_states[user_id]['amount']
                
                # Сохраняем расход
                add_expense(user_id, category, amount)
                
                # Получаем ID последней записи
                record_id = get_last_expense_id(user_id)
                
                # Удаляем состояние
                del user_states[user_id]
                
                # Отправляем подтверждение
                bot.reply_to(
                    message,
                    f"✅ **Расход добавлен!**\n\n"
                    f"📂 Категория: {category}\n"
                    f"💰 Сумма: {amount:,} сум\n"
                    f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"📊 Всего расходов: {get_total_expenses(user_id):,} сум",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                
                # Отправляем кнопку отмены отдельным сообщением
                if record_id:
                    bot.send_message(
                        message.chat.id,
                        "💡 Если ошиблись, можете отменить запись:",
                        reply_markup=get_undo_inline_keyboard(record_id)
                    )
            else:
                bot.reply_to(
                    message,
                    "❌ Пожалуйста, выберите категорию из списка кнопок.",
                    reply_markup=get_categories_keyboard()
                )
    
    else:
        # Если нет состояния, проверяем специальные кнопки
        if text not in ["💰 Баланс", "📊 Статистика", "📝 Добавить расход", 
                        "📋 Все расходы", "📅 Расходы за сегодня", "🗑️ Сбросить данные",
                        "🔙 Назад", "🗑️ Удалить последний"]:
            bot.reply_to(
                message,
                "❓ Используйте кнопки меню для управления ботом.\n\n"
                "📌 Нажмите '📝 Добавить расход' чтобы записать трату.",
                reply_markup=get_main_keyboard()
            )

# ================= ИНЛАЙН ОБРАБОТЧИКИ =================

@bot.callback_query_handler(func=lambda call: call.data.startswith('undo_'))
def handle_undo(callback_query):
    record_id = int(callback_query.data.replace('undo_', ''))
    user_id = callback_query.from_user.id
    
    if delete_expense_by_id(record_id, user_id):
        bot.answer_callback_query(callback_query.id, "✅ Запись удалена!")
        bot.edit_message_text(
            "✅ **Запись успешно удалена!**\n\n"
            "Вы можете продолжить работу с ботом.",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(
            callback_query.id, 
            "❌ Запись не найдена или уже удалена",
            show_alert=True
        )

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================

def get_categories_list():
    """Возвращает список категорий"""
    return [
        "Продукты", "Мясо", "Бытовая химия", "Заправка",
        "Жене на кофе", "Садик", "Свет", "Газ", "Вода",
        "Телефон", "Интернет", "ЖЭК", "Мусор", "Аптека",
        "Одежда", "Прочее"
    ]

def get_last_expense_id(user_id):
    """Получить ID последнего расхода"""
    import sqlite3
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM expenses 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT 1
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def delete_expense_by_id(record_id, user_id):
    """Удалить расход по ID"""
    import sqlite3
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM expenses 
        WHERE id = ? AND user_id = ?
    ''', (record_id, user_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def show_expenses_by_month(message, user_id, month, month_name):
    """Показывает расходы за конкретный месяц"""
    expenses = get_expenses_by_month(user_id, month)
    
    if not expenses:
        bot.reply_to(
            message,
            f"📭 За {month_name} расходов нет.",
            reply_markup=get_main_keyboard()
        )
        return
    
    total = sum(amt for _, amt, _ in expenses)
    
    text = f"📋 **РАСХОДЫ ЗА {month_name.upper()}**\n\n"
    
    sorted_expenses = sorted(expenses, key=lambda x: x[2])
    
    for cat, amt, date in sorted_expenses:
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        date_str = date_obj.strftime("%d.%m")
        text += f"• {cat}: {amt:,} сум ({date_str})\n"
    
    text += f"\n💰 **ИТОГО ЗА МЕСЯЦ: {total:,} сум**"
    
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# ================= ЗАПУСК БОТА =================

if __name__ == "__main__":
    print("🤖 Бот запущен...")
    print("📊 База данных: finance_bot.db")
    print("📌 Бот работает с ручным вводом суммы!")
    bot.polling(none_stop=True)