import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)

user_data = {}
user_state = {}

products = {
    "1": {
        "name": "Skeleton Dinosaurs",
        "price": "145 000 сум",
        "photo": "https://images.uzum.uz/d5l47ht2lln7rsu1vmag/t_product_540_high.jpg",
    },
    "2": {
        "name": "Luminous Dinosaurs",
        "price": "96 000 сум",
        "photo": "https://images.uzum.uz/d4a0gk5sp2tr82i3ufng/t_product_540_high.jpg",
    },
    "3": {
        "name": "Dino Park",
        "price": "95 000 сум",
        "photo": "https://images.uzum.uz/d5fudkbtqdhodfdkl0rg/t_product_540_high.jpg",
    },
}

# ===== СТАРТ =====
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

# ===== ВЫБОР ТОВАРА =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def start_order(call):
    user_id = call.from_user.id
    product_id = call.data.split("_")[1]

    user_data[user_id] = {"product": products[product_id]["name"]}
    user_state[user_id] = "name"

    bot.send_message(call.message.chat.id, "Введите ваше имя:")

# ===== ОБРАБОТКА ШАГОВ =====
@bot.message_handler(content_types=['text', 'photo'])
def handle_steps(message):
    user_id = message.from_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if state == "name":
        user_data[user_id]["name"] = message.text
        user_state[user_id] = "phone"
        bot.send_message(message.chat.id, "Введите телефон:")

    elif state == "phone":
        user_data[user_id]["phone"] = message.text
        user_state[user_id] = "city"
        bot.send_message(message.chat.id, "Введите город:")

    elif state == "city":
        user_data[user_id]["city"] = message.text
        user_state[user_id] = "address"
        bot.send_message(message.chat.id, "Введите адрес:")

    elif state == "address":
        user_data[user_id]["address"] = message.text
        user_state[user_id] = "payment"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Click / Payme / Paynet", callback_data="pay_qr"))
        markup.add(types.InlineKeyboardButton("💵 Наличными при получении", callback_data="pay_cash"))

        bot.send_message(message.chat.id, "Выберите способ оплаты:", reply_markup=markup)

# ===== ВЫБОР ОПЛАТЫ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def payment_choice(call):
    user_id = call.from_user.id

    if call.data == "pay_cash":
        send_order_to_group(user_id, "Наличными")
        bot.send_message(call.message.chat.id, "✅ Заказ принят! Мы скоро свяжемся с вами.")
        user_state.pop(user_id)
        user_data.pop(user_id)

    elif call.data == "pay_qr":
        user_state[user_id] = "receipt"

        qr = open("qr.jpg", "rb")
        bot.send_photo(
            call.message.chat.id,
            qr,
            caption="Отсканируйте QR для оплаты.\nПосле оплаты отправьте фото чека."
        )

# ===== ПРИЁМ ЧЕКА =====
@bot.message_handler(content_types=['photo'])
def get_receipt(message):
    user_id = message.from_user.id

    if user_id in user_state and user_state[user_id] == "receipt":
        bot.forward_message(GROUP_ID, message.chat.id, message.message_id)
        send_order_to_group(user_id, "Оплачено по QR")

        bot.send_message(message.chat.id, "✅ Чек получен! Мы скоро свяжемся с вами.")
        user_state.pop(user_id)
        user_data.pop(user_id)

# ===== ОТПРАВКА ЗАКАЗА =====
def send_order_to_group(user_id, payment_type):
    user = user_data[user_id]

    text = f"""
🛒 Новый заказ BY_Croods

Товар: {user['product']}
Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
Оплата: {payment_type}
"""
    bot.send_message(GROUP_ID, text)

# ===== ЗАПУСК =====
bot.polling(none_stop=True)
