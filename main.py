
 import telebot
from flask import Flask
from threading import Thread

# 1. SOZLAMALAR
TOKEN = '8794780288:AAEwpwNo2Ytxm9dd7VehGFY1xdvqOKsQXmw'
ADMIN_ID = 6971227691 
KINO_KANAL_ID = -1003168624222  

bot = telebot.TeleBot(TOKEN)
CHANNELS = ["@polatkino_uz"]

# 2. RENDER UCHUN
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 3. OBUNA TEKSHIRISH
def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['creator', 'administrator', 'member']:
                return False
        except:
            continue
    return True

# 4. ADMIN PANEL (ENG TEPAGA QO'YDIK)
@bot.message_handler(commands=['panel'])
def send_panel(message):
    if message.from_user.id == ADMIN_ID:
        text = "⚙️ ADMIN PANEL\n\nMajburiy kanallar:\n"
        for ch in CHANNELS:
            text += f"🔹 {ch}\n"
        text += "\n➕ Qo'shish: /add @kanal\n➖ O'chirish: /del @kanal"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, f"Siz admin emassiz. ID: {message.from_user.id}")

@bot.message_handler(commands=['add'])
def add_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            new_ch = message.text.split()[1]
            CHANNELS.append(new_ch)
            bot.reply_to(message, f"✅ {new_ch} qo'shildi")
        except:
            bot.reply_to(message, "Xato yozdingiz")

@bot.message_handler(commands=['del'])
def del_ch(message):
    if message.from_user.id == ADMIN_ID:
        try:
            old_ch = message.text.split()[1]
            if old_ch in CHANNELS:
                CHANNELS.remove(old_ch)
                bot.reply_to(message, f"❌ {old_ch} o'chirildi")
        except:
            bot.reply_to(message, "Xato yozdingiz")

# 5. BOSHQALAR
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "🎬 Salom! Kino kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def get_movie(message):
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Kanallarga a'zo bo'ling: " + ", ".join(CHANNELS))
        return

    if message.text.isdigit():
        try:
            bot.forward_message(message.chat.id, KINO_KANAL_ID, int(message.text))
        except:
            bot.send_message(message.chat.id, "Kino topilmadi.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
