import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN")

GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ===== ТОВАРЫ =====
products = {
    "1": {
        "name": "Skeleton Dinosaurs",
        "price": "145 000 сум",
        "photo": "https://images.uzum.uz/d5l47ht2lln7rsu1vmag/t_product_540_high.jpg",
    },
    "2": {
        "name": "Luminous Dinosaurs",
        "price": "95 000 сум",
        "photo": "https://images.uzum.uz/d4a0gk5sp2tr82i3ufng/t_product_540_high.jpg",
    },
    "3": {
        "name": "Dino Park",
        "price": "95 000 сум",
        "photo": "https://images.uzum.uz/d5fudkbtqdhodfdkl0rg/t_product_540_high.jpg",
    },
}

# ===== СТАРТ (витрина с фото) =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🦖 Добро пожаловать в магазин BY_Croods!\nВыберите товар:")

    for key, item in products.items():
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Заказать", callback_data=f"order_{key}"))

        bot.send_photo(
            message.chat.id,
            item["photo"],
            caption=f"{item['name']}\nЦена: {item['price']}",
            reply_markup=markup
        )

# ===== НАЖАЛ ЗАКАЗАТЬ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def start_order(call):
    product_id = call.data.split("_")[1]
    user_data[call.from_user.id] = {"product": products[product_id]["name"]}

    msg = bot.send_message(call.message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    user_data[message.from_user.id]["name"] = message.text
    msg = bot.send_message(message.chat.id, "Введите телефон:")
    bot.register_next_step_handler(msg, get_phone)

def get_phone(message):
    user_data[message.from_user.id]["phone"] = message.text
    msg = bot.send_message(message.chat.id, "Введите город:")
    bot.register_next_step_handler(msg, get_city)

def get_city(message):
    user_data[message.from_user.id]["city"] = message.text
    msg = bot.send_message(message.chat.id, "Введите адрес:")
    bot.register_next_step_handler(msg, finish_order)

def finish_order(message):
    user = user_data[message.from_user.id]
    user["address"] = message.text

    text = f"""
🛒 Новый заказ BY_Croods

Товар: {user['product']}
Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
"""

    bot.send_message(GROUP_ID, text)
    bot.send_message(message.chat.id, "✅ Заказ отправлен! Мы свяжемся с вами.")

# ===== ЗАПУСК =====
bot.polling(none_stop=True)
