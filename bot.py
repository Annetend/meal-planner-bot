import telebot
import os
import json
import random

# Получаем токен ТОЛЬКО из переменных окружения (НЕ из .env!)
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ ОШИБКА: Переменная BOT_TOKEN не найдена")
    print("💡 Совет: Добавьте в Railway → Variables → Key: BOT_TOKEN, Value: ваш_токен")
    exit(1)

print(f"✅ Бот запущен с токеном: {BOT_TOKEN[:10]}...")

bot = telebot.TeleBot(BOT_TOKEN)

# Загружаем базы данных
with open('products.json', 'r', encoding='utf-8') as f:
    products_data = json.load(f)

with open('recipes.json', 'r', encoding='utf-8') as f:
    recipes_data = json.load(f)

products = {p['id']: p for p in products_data['products']}
recipes = {r['id']: r for r in recipes_data['recipes']}
allergens_list = products_data['allergens_list']

user_data = {}

main_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("🍽️ Составить меню")
main_menu.add("⚖️ Рассчитать ИМТ")
main_menu.add("🔥 Рассчитать калории")
main_menu.add("ℹ️ О боте")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "🍽️ Добро пожаловать в Планировщик Питания!\n\n"
        "Выберите действие:",
        reply_markup=main_menu
    )

# ... остальной код без изменений ...

@bot.message_handler(func=lambda message: message.text == "🍽️ Составить меню")
def start_menu_planning(message):
    type_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    type_menu.add("👤 Для себя")
    type_menu.add("👨‍👩‍👧‍👦 Для семьи")
    type_menu.add("↩️ Назад")
    msg = bot.reply_to(message, "👥 Для кого составляем меню?", reply_markup=type_menu)
    bot.register_next_step_handler(msg, process_person_type)

def process_person_type(message):
    if message.text == "↩️ Назад":
        bot.reply_to(message, "Возврат в главное меню", reply_markup=main_menu)
        return
    if message.text not in ["👤 Для себя", "👨‍👩‍👧‍👦 Для семьи"]:
        msg = bot.reply_to(message, "Выберите из меню:")
        bot.register_next_step_handler(msg, process_person_type)
        return
    user_data[message.chat.id] = {'person_type': message.text}
    if message.text == "👤 Для себя":
        gender_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        gender_menu.add("Мужчина 👨")
        gender_menu.add("Женщина 👩")
        gender_menu.add("↩️ Назад")
        msg = bot.reply_to(message, "👤 Выберите ваш пол:", reply_markup=gender_menu)
        bot.register_next_step_handler(msg, process_gender_for_menu)
    else:
        msg = bot.reply_to(message, "👨‍👩‍👧‍👦 Сколько человек в семье?")
        bot.register_next_step_handler(msg, process_family_size)

def process_gender_for_menu(message):
    if message.text == "↩️ Назад":
        start_menu_planning(message)
        return
    if message.text not in ["Мужчина 👨", "Женщина 👩"]:
        msg = bot.reply_to(message, "Выберите пол:")
        bot.register_next_step_handler(msg, process_gender_for_menu)
        return
    user_data[message.chat.id]['gender'] = message.text
    msg = bot.reply_to(message, "🎯 Введите желаемую калорийность в день (например: 2000):")
    bot.register_next_step_handler(msg, process_calories_for_menu)

def process_family_size(message):
    try:
        size = int(message.text)
        if size < 1 or size > 20:
            raise ValueError
        user_data[message.chat.id]['family_size'] = size
        msg = bot.reply_to(message, f"👨‍👩‍👧‍👦 Семья: {size} человек. Введите калорийность на человека в день:")
        bot.register_next_step_handler(msg, process_calories_for_menu)
    except ValueError:
        msg = bot.reply_to(message, "❌ Введите число от 1 до 20:")
        bot.register_next_step_handler(msg, process_family_size)

def process_calories_for_menu(message):
    try:
        calories = int(message.text)
        if calories < 800 or calories > 5000:
            raise ValueError
        user_data[message.chat.id]['calories'] = calories
        msg = bot.reply_to(message, f"🎯 Калорийность: {calories} ккал/день. Введите бюджет в день (в рублях, например: 500):")
        bot.register_next_step_handler(msg, process_budget_for_menu)
    except ValueError:
        msg = bot.reply_to(message, "❌ Введите число от 800 до 5000:")
        bot.register_next_step_handler(msg, process_calories_for_menu)

def process_budget_for_menu(message):
    try:
        budget = int(message.text)
        if budget < 100 or budget > 5000:
            raise ValueError
        user_data[message.chat.id]['budget'] = budget
        period_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        period_menu.add("📅 На день")
        period_menu.add("📆 На неделю")
        period_menu.add("↩️ Назад")
        msg = bot.reply_to(message, f"💰 Бюджет: {budget}₽/день. На какой период?", reply_markup=period_menu)
        bot.register_next_step_handler(msg, process_period)
    except ValueError:
        msg = bot.reply_to(message, "❌ Введите число от 100 до 5000:")
        bot.register_next_step_handler(msg, process_budget_for_menu)

def process_period(message):
    if message.text == "↩️ Назад":
        start_menu_planning(message)
        return
    if message.text not in ["📅 На день", "📆 На неделю"]:
        msg = bot.reply_to(message, "Выберите период:")
        bot.register_next_step_handler(msg, process_period)
        return
    user_data[message.chat.id]['period'] = message.text
    allergen_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    allergen_menu.add("Нет аллергий ✅")
    allergen_menu.add("Выбрать аллергены")
    allergen_menu.add("↩️ Назад")
    msg = bot.reply_to(message, "🚫 Есть ли аллергии?", reply_markup=allergen_menu)
    bot.register_next_step_handler(msg, process_allergens_choice)

def process_allergens_choice(message):
    if message.text == "↩️ Назад":
        process_period(message)
        return
    chat_id = message.chat.id
    user_data[chat_id]['allergens'] = []
    if message.text == "Нет аллергий ✅":
        generate_menu(message)
    else:
        allergen_buttons = telebot.types.InlineKeyboardMarkup()
        for allergen in allergens_list:
            btn = telebot.types.InlineKeyboardButton(text=allergen, callback_data=f"allergen_{allergen}")
            allergen_buttons.add(btn)
        done_btn = telebot.types.InlineKeyboardButton(text="✅ Готово", callback_data="allergens_done")
        allergen_buttons.add(done_btn)
        bot.reply_to(message, "Выберите аллергены (нажмите на аллерген, чтобы добавить/убрать):", reply_markup=allergen_buttons)

@bot.callback_query_handler(func=lambda call: call.data.startswith('allergen_') or call.data == 'allergens_done')
def callback_allergens(call):
    chat_id = call.message.chat.id
    if call.data == 'allergens_done':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="✅ Аллергены сохранены!")
        generate_menu(call.message)
        return
    allergen = call.data.replace('allergen_', '')
    if 'allergens' not in user_data.get(chat_id, {}):
        user_data[chat_id]['allergens'] = []
    if allergen in user_data[chat_id]['allergens']:
        user_data[chat_id]['allergens'].remove(allergen)
    else:
        user_data[chat_id]['allergens'].append(allergen)
    allergen_buttons = telebot.types.InlineKeyboardMarkup()
    for a in allergens_list:
        mark = "✅ " if a in user_data[chat_id]['allergens'] else ""
        btn = telebot.types.InlineKeyboardButton(text=f"{mark}{a}", callback_data=f"allergen_{a}")
        allergen_buttons.add(btn)
    done_btn = telebot.types.InlineKeyboardButton(text="✅ Готово", callback_data="allergens_done")
    allergen_buttons.add(done_btn)
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=allergen_buttons)

def generate_menu(message):
    chat_id = message.chat.id
    user = user_data[chat_id]
    calories = user['calories']
    budget = user['budget']
    allergens = user.get('allergens', [])
    suitable_recipes = {'завтрак': [], 'обед': [], 'ужин': [], 'перекус': []}
    for recipe in recipes.values():
        if recipe['calories'] > calories * 0.5 or recipe['calories'] < 200:
            continue
        if recipe['price'] > budget * 0.4:
            continue
        if any(a in allergens for a in recipe['allergens']):
            continue
        suitable_recipes[recipe['category']].append(recipe)
    menu = {}
    total_calories = 0
    total_cost = 0
    for category in ['завтрак', 'обед', 'ужин', 'перекус']:
        if suitable_recipes[category]:
            menu[category] = random.choice(suitable_recipes[category])
            total_calories += menu[category]['calories']
            total_cost += menu[category]['price']
        else:
            menu[category] = None
    period = user['period']
    if period == "📅 На день":
        result = f"""
🍽️ *МЕНЮ НА ДЕНЬ*

🎯 Калорийность: {calories} ккал
💰 Бюджет: {budget}₽/день
🚫 Аллергены: {', '.join(allergens) if allergens else 'нет'}

"""
        emojis = {'завтрак': '🌅', 'обед': '☀️', 'ужин': '🌙', 'перекус': '🍎'}
        for cat, recipe in menu.items():
            if recipe:
                result += f"{emojis[cat]} *{cat.capitalize()}*:\n"
                result += f"  {recipe['name']}\n"
                result += f"  🔥 {recipe['calories']} ккал | 💰 {recipe['price']}₽\n"
                result += f"  🥗 Б: {recipe['protein']}г Ж: {recipe['fat']}г У: {recipe['carbs']}г\n"
                result += f"  ⏱️ {recipe['prep_time']} мин\n"
                result += f"  📝 Ингредиенты:\n"
                for ing in recipe['ingredients']:
                    product = products.get(ing['product_id'])
                    if product:
                        result += f"    • {product['name']} ({ing['amount']}г)\n"
                result += "\n"
            else:
                result += f"{emojis[cat]} *{cat.capitalize()}*: не найден подходящий рецепт\n\n"
        result += f"📊 *Итого:* {total_calories} ккал, {total_cost}₽"
        bot.reply_to(message, result, parse_mode="Markdown", reply_markup=main_menu)
    elif period == "📆 На неделю":
        result = "🍽️ *МЕНЮ НА НЕДЕЛЮ*\n\n"
        result += f"🎯 Калорийность: {calories} ккал/день | 💰 Бюджет: {budget}₽/день"
        if allergens:
            result += f"\n🚫 Аллергены: {', '.join(allergens)}"
        result += "\n\n"
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for day in days:
            result += f"*{day}:*\n"
            for category in ['завтрак', 'обед', 'ужин']:
                if suitable_recipes[category]:
                    recipe = random.choice(suitable_recipes[category])
                    result += f"  • {recipe['name']} ({recipe['calories']} ккал)\n"
            result += "\n"
        bot.reply_to(message, result, parse_mode="Markdown", reply_markup=main_menu)
    del user_data[chat_id]

@bot.message_handler(func=lambda message: message.text == "⚖️ Рассчитать ИМТ")
def start_bmi_calculation(message):
    msg = bot.reply_to(message, "📊 Введите ваш вес в килограммах:")
    bot.register_next_step_handler(msg, process_weight_step)

def process_weight_step(message):
    try:
        weight = float(message.text.replace(',', '.'))
        if weight < 30 or weight > 300:
            raise ValueError
        user_data[message.chat.id] = {'weight': weight}
        msg = bot.reply_to(message, "📏 Введите ваш рост в сантиметрах:")
        bot.register_next_step_handler(msg, process_height_step)
    except ValueError:
        msg = bot.reply_to(message, "❌ Неверный формат. Введите число от 30 до 300:")
        bot.register_next_step_handler(msg, process_weight_step)

def process_height_step(message):
    try:
        height = float(message.text.replace(',', '.'))
        if height < 100 or height > 250:
            raise ValueError
        chat_id = message.chat.id
        user_data[chat_id]['height'] = height
        weight = user_data[chat_id]['weight']
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        if bmi < 18.5:
            category = "Недостаточный вес"
            emoji = "⚠️"
            recommendation = "Рекомендуется увеличить калорийность питания"
        elif 18.5 <= bmi < 25:
            category = "Нормальный вес"
            emoji = "✅"
            recommendation = "Поддерживайте текущий уровень питания"
        elif 25 <= bmi < 30:
            category = "Избыточный вес"
            emoji = "⚠️"
            recommendation = "Рекомендуется снизить калорийность на 15-20%"
        else:
            category = "Ожирение"
            emoji = "⚠️"
            recommendation = "Рекомендуется консультация с врачом"
        result = f"""
📊 *РЕЗУЛЬТАТЫ РАСЧЁТА ИМТ*

Вес: {weight} кг
Рост: {height} см

{emoji} *Ваш ИМТ:* {bmi:.1f}
*Категория:* {category}

💡 *Рекомендация:*
{recommendation}
        """
        bot.reply_to(message, result, parse_mode="Markdown", reply_markup=main_menu)
        del user_data[chat_id]
    except ValueError:
        msg = bot.reply_to(message, "❌ Неверный формат. Введите число от 100 до 250:")
        bot.register_next_step_handler(msg, process_height_step)

@bot.message_handler(func=lambda message: message.text == "🔥 Рассчитать калории")
def start_calories_calculation(message):
    gender_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    gender_menu.add("Мужчина 👨")
    gender_menu.add("Женщина 👩")
    gender_menu.add("↩️ Назад")
    msg = bot.reply_to(message, "👤 Выберите ваш пол:", reply_markup=gender_menu)
    bot.register_next_step_handler(msg, process_gender_step)

def process_gender_step(message):
    if message.text == "↩️ Назад":
        bot.reply_to(message, "Возврат в главное меню", reply_markup=main_menu)
        return
    gender = message.text
    if gender not in ["Мужчина 👨", "Женщина 👩"]:
        msg = bot.reply_to(message, "Выберите пол из меню:")
        bot.register_next_step_handler(msg, process_gender_step)
        return
    user_data[message.chat.id] = {'gender': gender}
    msg = bot.reply_to(message, "⚖️ Введите ваш вес в килограммах:")
    bot.register_next_step_handler(msg, process_calories_weight_step)

def process_calories_weight_step(message):
    try:
        weight = float(message.text.replace(',', '.'))
        if weight < 30 or weight > 300:
            raise ValueError
        user_data[message.chat.id]['weight'] = weight
        msg = bot.reply_to(message, "📏 Введите ваш рост в сантиметрах:")
        bot.register_next_step_handler(msg, process_calories_height_step)
    except ValueError:
        msg = bot.reply_to(message, "❌ Неверный формат. Введите число от 30 до 300:")
        bot.register_next_step_handler(msg, process_calories_weight_step)

def process_calories_height_step(message):
    try:
        height = float(message.text.replace(',', '.'))
        if height < 100 or height > 250:
            raise ValueError
        user_data[message.chat.id]['height'] = height
        msg = bot.reply_to(message, "🎂 Введите ваш возраст:")
        bot.register_next_step_handler(msg, process_age_step)
    except ValueError:
        msg = bot.reply_to(message, "❌ Неверный формат. Введите число от 100 до 250:")
        bot.register_next_step_handler(msg, process_calories_height_step)

def process_age_step(message):
    try:
        age = int(message.text)
        if age < 14 or age > 100:
            raise ValueError
        user_data[message.chat.id]['age'] = age
        activity_menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        activity_menu.add("Низкая (сидячая работа)")
        activity_menu.add("Умеренная (лёгкие тренировки)")
        activity_menu.add("Высокая (интенсивные тренировки)")
        activity_menu.add("↩️ Назад")
        msg = bot.reply_to(message, "🏃 Выберите уровень активности:", reply_markup=activity_menu)
        bot.register_next_step_handler(msg, process_activity_step)
    except ValueError:
        msg = bot.reply_to(message, "❌ Неверный формат. Введите число от 14 до 100:")
        bot.register_next_step_handler(msg, process_age_step)

def process_activity_step(message):
    if message.text == "↩️ Назад":
        bot.reply_to(message, "Возврат в главное меню", reply_markup=main_menu)
        return
    activity_levels = {
        "Низкая (сидячая работа)": 1.2,
        "Умеренная (лёгкие тренировки)": 1.375,
        "Высокая (интенсивные тренировки)": 1.55
    }
    if message.text not in activity_levels:
        msg = bot.reply_to(message, "Выберите уровень активности из меню:")
        bot.register_next_step_handler(msg, process_activity_step)
        return
    chat_id = message.chat.id
    user = user_data[chat_id]
    gender = user['gender']
    weight = user['weight']
    height = user['height']
    age = user['age']
    activity = activity_levels[message.text]
    if gender == "Мужчина 👨":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    daily_calories = bmr * activity
    result = f"""
🔥 *РАСЧЁТ СУТОЧНОЙ НОРМЫ КАЛОРИЙ*

{gender}
Вес: {weight} кг
Рост: {height} см
Возраст: {age} лет
Активность: {message.text}

📊 *Базовый метаболизм (BMR):* {int(bmr)} ккал
🎯 *Суточная норма:* {int(daily_calories)} ккал
        """
    bot.reply_to(message, result, parse_mode="Markdown", reply_markup=main_menu)
    del user_data[chat_id]

@bot.message_handler(func=lambda message: message.text == "ℹ️ О боте")
def about_handler(message):
    bot.reply_to(message,
        "🤖 *Планировщик Питания*\n"
        "Ваш персональный помощник!\n\n"
        "✨ *Возможности:*\n"
        "• Составление меню на день/неделю 🍽️\n"
        "• Учёт калорийности и бюджета 💰\n"
        "• Исключение аллергенов 🚫\n"
        "• Расчёт ИМТ и нормы калорий ⚖️🔥\n\n"
        "Разработано с ❤️",
        parse_mode="Markdown",
        reply_markup=main_menu
    )

if __name__ == "__main__":
    print("✅ Бот успешно запущен!")
    print("📱 Откройте Telegram и напишите /start")
    bot.infinity_polling()
