import telebot
from flask import Flask
from threading import Thread

# 1. BOT SOZLAMALARI
TOKEN = '8794780288:AAEwpwNo2Ytxm9dd7VehGFY1xdvqOKsQXmw'
ADMIN_ID = 6971227691  
KINO_KANAL_ID = -1003168624222  

bot = telebot.TeleBot(TOKEN)
CHANNELS = ["@polatkino_uz"]

# 2. RENDER UCHUN SAYTCHA
app = Flask('')
@app.route('/')
def home():
    return "Bot ishlayapti!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 3. OBUNANI TEKSHIRISH
def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['creator', 'administrator', 'member']:
                return False
        except:
            continue
    return True

# 4. ADMIN PANEL
@bot.message_handler(commands=['panel'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        text = "⚙️ **ADMIN PANEL**\n\n"
        text += "Hozirgi majburiy kanallar:\n"
        for ch in CHANNELS:
            text += f"🔹 {ch}\n"
        text += "\n➕ Qo'shish: `/add @kanal`"
        text += "\n➖ O'chirish: `/del @kanal`"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            new_ch = message.text.split()[1]
            if new_ch.startswith('@') and new_ch not in CHANNELS:
                CHANNELS.append(new_ch)
                bot.reply_to(message, f"✅ {new_ch} qo'shildi!")
        except:
            bot.reply_to(message, "Xato! `/add @kanal` shaklida yozing.")

@bot.message_handler(commands=['del'])
def del_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            old_ch = message.text.split()[1]
            if old_ch in CHANNELS:
                CHANNELS.remove(old_ch)
                bot.reply_to(message, f"❌ {old_ch} o'chirildi!")
        except:
            bot.reply_to(message, "Xato! `/del @kanal` shaklida yozing.")

# 5. ASOSIY QIDIRUV
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🎬 Salom! Kino kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def get_kino(message):
    if not check_sub(message.from_user.id):
        btn = telebot.types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            btn.add(telebot.types.InlineKeyboardButton(text="A'zo bo'lish", url=f"https://t.me/{ch[1:]}"))
        bot.send_message(message.chat.id, "❌ Kanalga a'zo bo'ling!", reply_markup=btn)
        return

    if message.text.isdigit():
        try:
            bot.forward_message(message.chat.id, KINO_KANAL_ID, int(message.text))
        except:
            bot.send_message(message.chat.id, "😔 Kino topilmadi.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
