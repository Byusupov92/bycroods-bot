import telebot
from telebot import types
import os
import base64
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

products = {
    "1": {"name": "Skeleton Dinosaurs", "price": 145000, "stock": 0},
    "2": {"name": "Luminous Dinosaurs", "price": 96000, "stock": 0},
    "3": {"name": "Dino Park", "price": 95000, "stock": 15},
}

# ================== САЙТ ШЛЁТ СЮДА ЗАКАЗ ==================
@app.route("/site_order", methods=["POST"])
def site_order():
    data = request.json

    encoded = base64.b64encode(
        f"{data['product']}|{data['name']}|{data['phone']}|{data['city']}|{data['address']}|{data['qty']}".encode()
    ).decode()

    link = f"https://t.me/MyNotebekBot?start={encoded}"
    return {"telegram_link": link}


# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()

    # Пришёл с сайта
    if len(args) > 1:
        decoded = base64.b64decode(args[1]).decode("utf-8")
        product, name, phone, city, address, qty = decoded.split("|")

        for key, item in products.items():
            if item["name"] == product:
                user_data[message.from_user.id] = {
                    "product_id": key,
                    "product": product,
                    "price": item["price"],
                    "qty": int(qty),
                    "name": name,
                    "phone": phone,
                    "city": city,
                    "address": address
                }

        choose_payment(message)
        return

    bot.send_message(message.chat.id, "🦖 Витрина BY_Croods")

    for key, item in products.items():
        markup = types.InlineKeyboardMarkup()

        if item["stock"] > 0:
            markup.add(types.InlineKeyboardButton(
                f"🛒 Заказать (осталось {item['stock']})",
                callback_data=f"order_{key}"
            ))
        else:
            markup.add(types.InlineKeyboardButton(
                "📦 Узнать о поступлении",
                callback_data=f"wait_{key}"
            ))

        bot.send_message(
            message.chat.id,
            f"{item['name']}\nЦена: {item['price']} сум",
            reply_markup=markup
        )


# ================== ОПЛАТА ==================
def choose_payment(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💵 Наличными", callback_data="cash"),
        types.InlineKeyboardButton("💳 QR", callback_data="qr")
    )
    bot.send_message(message.chat.id, "Выберите способ оплаты:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["cash", "qr"])
def payment_handler(call):
    user = user_data[call.from_user.id]

    if call.data == "cash":
        finish_order(call.from_user.id, "Наличными")
        bot.send_message(call.message.chat.id, "✅ Заказ принят!")

    if call.data == "qr":
        user["waiting_receipt"] = True
        bot.send_photo(
            call.message.chat.id,
            open("qr.jpg", "rb"),
            caption="Оплатите и отправьте скрин чека"
        )


@bot.message_handler(content_types=['photo'])
def get_receipt(message):
    user = user_data.get(message.from_user.id)
    if user and user.get("waiting_receipt"):
        finish_order(message.from_user.id, "QR")
        bot.forward_message(GROUP_ID, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "✅ Чек получен!")


def finish_order(user_id, payment):
    user = user_data[user_id]
    products[user["product_id"]]["stock"] -= user["qty"]

    text = f"""
🛒 Новый заказ С САЙТА

Товар: {user['product']}
Количество: {user['qty']}
Сумма: {user['price'] * user['qty']} сум
Оплата: {payment}

Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
"""
    bot.send_message(GROUP_ID, text)


# ================== ЗАПУСК ==================
import threading

def run_bot():
    bot.polling(none_stop=True)

threading.Thread(target=run_bot).start()

app.run(host="0.0.0.0", port=8080)
