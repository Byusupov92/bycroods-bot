import telebot
from telebot import types
import os
from flask import Flask, request, jsonify
import threading

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}

# ===== ТОВАРЫ =====
products = {
    "Skeleton Dinosaurs": {"price": 145000, "stock": 0},
    "Luminous Dinosaurs": {"price": 96000, "stock": 0},
    "Dino Park": {"price": 95000, "stock": 15},
}

# ===== САЙТ ОТПРАВЛЯЕТ ЗАКАЗ СЮДА =====
@app.route("/site_order", methods=["POST"])
def site_order():
    data = request.json

    product = data.get("product")
    name = data.get("name")
    phone = data.get("phone")
    city = data.get("city")
    address = data.get("address")
    qty = int(data.get("qty"))

    if product not in products:
        return jsonify({"error": "Товар не найден"}), 400

    if qty > products[product]["stock"]:
        return jsonify({"error": "Нет столько в наличии"}), 400

    total = products[product]["price"] * qty

    # уменьшаем остаток
    products[product]["stock"] -= qty

    text = f"""
🛒 Новый заказ САЙТ BY_Croods

Товар: {product}
Количество: {qty}
Сумма: {total} сум

Имя: {name}
Телефон: {phone}
Город: {city}
Адрес: {address}
"""

    bot.send_message(GROUP_ID, text)

    return jsonify({"success": True})

# ===== ЗАПУСК БОТА И ВЕБ-СЕРВЕРА =====
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
