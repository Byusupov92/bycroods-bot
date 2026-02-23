import telebot
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import base64
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)
CORS(app)  # ← ВАЖНО


# ===== ТОВАРЫ =====
products = {
    "1": {
        "name": "Skeleton Dinosaurs",
        "price": 145000,
        "photo": "https://images.uzum.uz/d5l47ht2lln7rsu1vmag/t_product_540_high.jpg",
        "stock": 0
    },
    "2": {
        "name": "Luminous Dinosaurs",
        "price": 96000,
        "photo": "https://images.uzum.uz/d4a0gk5sp2tr82i3ufng/t_product_540_high.jpg",
        "stock": 0
    },
    "3": {
        "name": "Dino Park",
        "price": 95000,
        "photo": "https://images.uzum.uz/d5fudkbtqdhodfdkl0rg/t_product_540_high.jpg",
        "stock": 15
    },
}

# ===== СТАРТ =====
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()

    if len(args) > 1:
        decoded = base64.b64decode(args[1]).decode("utf-8")
        product, name, phone, city, address, qty = decoded.split("|")

        user_data[message.from_user.id] = {
            "product": product,
            "name": name,
            "phone": phone,
            "city": city,
            "address": address,
            "qty": int(qty),
            "price": 0
        }

        # ищем товар в списке
        for key, item in products.items():
            if item["name"] == product:
                user_data[message.from_user.id]["product_id"] = key
                user_data[message.from_user.id]["price"] = item["price"]

        choose_payment(message)
        return

    bot.send_message(message.chat.id, "🦖 Добро пожаловать в магазин BY_Croods!")


    for key, item in products.items():
        markup = types.InlineKeyboardMarkup()

        if item["stock"] > 0:
            btn = f"🛒 Заказать (в наличии {item['stock']} шт)"
            markup.add(types.InlineKeyboardButton(btn, callback_data=f"order_{key}"))
        else:
            markup.add(types.InlineKeyboardButton(
                "📦 Узнать о поступлении",
                callback_data=f"wait_{key}"
            ))

        bot.send_photo(
            message.chat.id,
            item["photo"],
            caption=f"{item['name']}\nЦена: {item['price']} сум",
            reply_markup=markup
        )

def choose_payment(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💵 Наличными", callback_data="cash"),
        types.InlineKeyboardButton("💳 Оплатить по QR", callback_data="qr")
    )

    bot.send_message(message.chat.id, "Выберите способ оплаты:", reply_markup=markup)



# ===== НЕТ В НАЛИЧИИ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("wait_"))
def wait_product(call):
    product_id = call.data.split("_")[1]
    bot.send_message(
        GROUP_ID,
        f"📦 Запрос о поступлении: {products[product_id]['name']}"
    )
    bot.send_message(call.message.chat.id, "Мы уведомим вас о поступлении 🙌")

# ===== НАЖАЛ ЗАКАЗАТЬ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def start_order(call):
    product_id = call.data.split("_")[1]

    user_data[call.from_user.id] = {
        "product_id": product_id,
        "product": products[product_id]["name"],
        "price": products[product_id]["price"]
    }

    msg = bot.send_message(
        call.message.chat.id,
        f"Сколько штук нужно? (Доступно {products[product_id]['stock']})"
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

# ===== ДАННЫЕ КЛИЕНТА =====
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
        types.InlineKeyboardButton("💳 Оплатить по QR", callback_data="qr")
    )

    bot.send_message(message.chat.id, "Выберите способ оплаты:", reply_markup=markup)

# ===== ОБРАБОТКА ОПЛАТЫ =====
@bot.callback_query_handler(func=lambda call: call.data in ["cash", "qr"])
def payment_handler(call):
    user = user_data.get(call.from_user.id)

    if not user:
        return

    # НАЛИЧНЫЕ
    if call.data == "cash":
        finish_order(call.from_user.id, paid=True, payment_type="Наличными")
        bot.send_message(call.message.chat.id, "✅ Заказ принят!")

    # QR
    if call.data == "qr":
        user["waiting_receipt"] = True
        qr = open("qr.jpg", "rb")
        bot.send_photo(
            call.message.chat.id,
            qr,
            caption="Оплатите по QR. https://indoor.click.uz/pay?id=0068348&t=0\nПосле оплаты отправьте скрин чека."
        )

# ===== ПОЛУЧЕНИЕ ЧЕКА =====
@bot.message_handler(content_types=['photo'])
def get_receipt(message):
    user = user_data.get(message.from_user.id)

    if user and user.get("waiting_receipt"):
        finish_order(message.from_user.id, paid=True, payment_type="QR")
        bot.forward_message(GROUP_ID, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "✅ Чек получен!")
        user["waiting_receipt"] = False

# ===== ФИНАЛИЗАЦИЯ ЗАКАЗА =====
def finish_order(user_id, paid, payment_type):
    user = user_data[user_id]
    product_id = user["product_id"]
    qty = user["qty"]

    # уменьшаем остаток
    products[product_id]["stock"] -= qty

    text = f"""
🛒 Новый заказ Телеграм BY_Croods

Товар: {user['product']}
Количество: {qty} шт
Сумма: {user['price'] * qty} сум
Оплата: {payment_type}

Имя: {user['name']}
Телефон: {user['phone']}
Город: {user['city']}
Адрес: {user['address']}
"""

    bot.send_message(GROUP_ID, text)



# ===== ТОВАРЫ =====
products = {
    "Skeleton Dinosaurs": {"price": 145000, "stock": 6},
    "Luminous Dinosaurs": {"price": 96000, "stock": 0},
    "Dino Park": {"price": 95000, "stock": 15},
    "Jurassic Discovery Triceratops": {"price": 199000, "stock": 3},
    "Jurassic Discovery Mammoth": {"price": 199000, "stock": 2},
    "Jurassic Discovery Velociraptor": {"price": 199000, "stock": 2},
    "Jurassic Discovery Spinosaurus": {"price": 199000, "stock": 2},
    "Jurassic Discovery Pterodactyl ": {"price": 199000, "stock": 2},
    
    
    
}

# ===== САЙТ ОТПРАВЛЯЕТ ЗАКАЗ =====
@app.route('/site_order', methods=['POST'])
def site_order():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Нет данных"}), 400

        product = data.get("product")
        name = data.get("name")
        phone = data.get("phone")
        city = data.get("city")
        address = data.get("address")
        qty = int(data.get("qty", 1))

        if product not in products:
            return jsonify({"success": False, "error": "Товар не найден"}), 400

        text = f"""
🛒 Новый заказ с сайта BY_Croods

📦 Товар: {product}
🔢 Количество: {qty}

👤 Имя: {name}
📞 Телефон: {phone}
🏙 Город: {city}
🏠 Адрес: {address}
"""

        bot.send_message(GROUP_ID, text)

        return jsonify({"success": True})

    except Exception as e:
        print("Ошибка:", e)
        return jsonify({"success": False, "error": "Ошибка сервера"}), 500


# ===== ЗАПУСК БОТА И СЕРВЕРА =====
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()




