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
    product_id = call.data.split("_")[1]
    user_data[call.from_user.id] = {
        "product": products[product_id]["name"],
        "price": products[product_id]["price"]
    }

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
    bot.register_next_step_handler(msg, choose_payment)

# ===== ВЫБОР ОПЛАТЫ =====
def choose_payment(message):
    user_data[message.from_user.id]["address"] = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💵 Наличными", callback_data="cash"),
        types.InlineKeyboardButton("💳 QR Click ", callback_data="qr")
    )

    bot.send_message(message.chat.id, "Выберите способ оплаты:", reply_markup=markup)

# ===== ОБРАБОТКА ВЫБОРА ОПЛАТЫ =====
@bot.callback_query_handler(func=lambda call: call.data in ["cash", "qr"])
def payment_handler(call):
    user = user_data.get(call.from_user.id)

    if not user:
        return

    order_text = f"""
🛒 Новый заказ BY_Croods

Товар: {user['product']}
Цена: {user['price']}
Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
"""

    # ===== НАЛИЧНЫЕ =====
    if call.data == "cash":
        bot.send_message(GROUP_ID, order_text + "\n💵 Оплата: Наличными")
        bot.send_message(call.message.chat.id, "✅ Заказ принят! Мы скоро свяжемся с вами.")

    # ===== QR ОПЛАТА =====
    if call.data == "qr":
        user["waiting_receipt"] = True

        qr = open("qr.jpg", "rb")
        bot.send_photo(
            call.message.chat.id,
            qr,
            caption="💳 Отсканируйте QR для оплаты или по ссылки https://indoor.click.uz/pay?id=0068348&t=0.\nПосле оплаты отправьте сюда скриншот чека."
        )

# ===== ПОЛУЧЕНИЕ ЧЕКА (ФОТО) =====
@bot.message_handler(content_types=['photo'])
def get_receipt(message):
    user = user_data.get(message.from_user.id)

    if user and user.get("waiting_receipt"):
        order_text = f"""
🛒 Новый заказ BY_Croods (QR оплачен)

Товар: {user['product']}
Цена: {user['price']}
Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
"""

        bot.send_message(GROUP_ID, order_text)
        bot.forward_message(GROUP_ID, message.chat.id, message.message_id)

        bot.send_message(message.chat.id, "✅ Чек получен! Мы проверим оплату и свяжемся с вами.")
        user["waiting_receipt"] = False

# ===== ЗАПУСК =====
bot.polling(none_stop=True)
