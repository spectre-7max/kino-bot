import telebot
import os
from flask import Flask
from threading import Thread

# 1. BOT SOZLAMALARI
TOKEN = '8794780288:AAEwpwNo2Ytxm9dd7VehGFY1xdvqOKsQXmw'
KINO_KANAL = -1003168624222
bot = telebot.TeleBot(TOKEN)

# 2. BOT O'CHIB QOLMASLIGI UCHUN KICHIK SAYTCHA (RENDER UCHUN)
app = Flask('')
@app.route('/')
def home():
    return "Bot ishlayapti!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 3. BOT BUYRUQLARI
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Bot Render.com serverida ishga tushdi! 🚀")

@bot.message_handler(func=lambda m: True)
def get_kino(message):
    if message.text.isdigit():
        try:
            bot.forward_message(message.chat.id, KINO_KANAL, int(message.text))
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Kino topilmadi.")

# 4. ISHGA TUSHIRISH
def start_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # Saytni alohida oqimda yoqish
    Thread(target=run).start()
    # Botni yoqish
    start_bot()
