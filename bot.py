import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ===== ТОВАРЫ И ОСТАТКИ =====
products = {
    "1": {
        "name": "Skeleton Dinosaurs",
        "price": "145 000 сум",
        "photo": "https://images.uzum.uz/d5l47ht2lln7rsu1vmag/t_product_540_high.jpg",
        "stock": 0
    },
    "2": {
        "name": "Luminous Dinosaurs",
        "price": "95 000 сум",
        "photo": "https://images.uzum.uz/d4a0gk5sp2tr82i3ufng/t_product_540_high.jpg",
        "stock": 0
    },
    "3": {
        "name": "Dino Park",
        "price": "95 000 сум",
        "photo": "https://images.uzum.uz/d5fudkbtqdhodfdkl0rg/t_product_540_high.jpg",
        "stock": 15
    },
}

# ===== СТАРТ =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🦖 Добро пожаловать в магазин BY_Croods!\nВыберите товар:")

    for key, item in products.items():
        markup = types.InlineKeyboardMarkup()

        if item["stock"] > 0:
            markup.add(types.InlineKeyboardButton(
                f"🛒 Заказать (в наличии {item['stock']} шт)",
                callback_data=f"order_{key}"
            ))
        else:
            markup.add(types.InlineKeyboardButton(
                "📦 Узнать о поступлении",
                callback_data=f"wait_{key}"
            ))

        bot.send_photo(
            message.chat.id,
            item["photo"],
            caption=f"{item['name']}\nЦена: {item['price']}",
            reply_markup=markup
        )

# ===== НЕТ В НАЛИЧИИ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("wait_"))
def wait_product(call):
    product_id = call.data.split("_")[1]
    product_name = products[product_id]["name"]

    bot.send_message(
        GROUP_ID,
        f"📦 Клиент хочет узнать о поступлении:\n{product_name}\n@{call.from_user.username}"
    )

    bot.send_message(
        call.message.chat.id,
        "Мы уведомим вас, когда товар появится 🙌"
    )

# ===== НАЖАЛ ЗАКАЗАТЬ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def start_order(call):
    product_id = call.data.split("_")[1]

    user_data[call.from_user.id] = {
        "product_id": product_id,
        "product": products[product_id]["name"]
    }

    msg = bot.send_message(
        call.message.chat.id,
        f"Сколько штук вам нужно? (Доступно: {products[product_id]['stock']})"
    )
    bot.register_next_step_handler(msg, get_quantity)

# ===== КОЛИЧЕСТВО =====
def get_quantity(message):
    try:
        qty = int(message.text)
    except:
        msg = bot.send_message(message.chat.id, "Введите число:")
        bot.register_next_step_handler(msg, get_quantity)
        return

    product_id = user_data[message.from_user.id]["product_id"]

    if qty > products[product_id]["stock"]:
        msg = bot.send_message(message.chat.id, "Столько нет. Введите меньше:")
        bot.register_next_step_handler(msg, get_quantity)
        return

    user_data[message.from_user.id]["qty"] = qty

    msg = bot.send_message(message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, get_name)

# ===== ИМЯ =====
def get_name(message):
    user_data[message.from_user.id]["name"] = message.text
    msg = bot.send_message(message.chat.id, "Введите телефон:")
    bot.register_next_step_handler(msg, get_phone)

# ===== ТЕЛЕФОН =====
def get_phone(message):
    user_data[message.from_user.id]["phone"] = message.text
    msg = bot.send_message(message.chat.id, "Введите город:")
    bot.register_next_step_handler(msg, get_city)

# ===== ГОРОД =====
def get_city(message):
    user_data[message.from_user.id]["city"] = message.text
    msg = bot.send_message(message.chat.id, "Введите адрес:")
    bot.register_next_step_handler(msg, finish_order)

# ===== ЗАВЕРШЕНИЕ ЗАКАЗА =====
def finish_order(message):
    user = user_data[message.from_user.id]
    user["address"] = message.text

    product_id = user["product_id"]
    qty = user["qty"]

    # уменьшаем остаток
    products[product_id]["stock"] -= qty

    text = f"""
🛒 Новый заказ BY_Croods

Товар: {user['product']}
Количество: {qty} шт

Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
"""

    bot.send_message(GROUP_ID, text)
    bot.send_message(message.chat.id, "✅ Заказ отправлен! Мы свяжемся с вами.")

# ===== ЗАПУСК =====
bot.polling(none_stop=True)
