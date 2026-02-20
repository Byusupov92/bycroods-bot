import telebot
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -5208779977

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)
CORS(app)  # ← ВАЖНО

# ===== ТОВАРЫ =====
products = {
    "Skeleton Dinosaurs": {"price": 145000, "stock": 0},
    "Luminous Dinosaurs": {"price": 96000, "stock": 0},
    "Dino Park": {"price": 95000, "stock": 15},
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

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
