import telebot
from flask import Flask
from threading import Thread
import os

# 1. SOZLAMALAR
# Token va ID'larni o'zingizniki bilan tekshiring
TOKEN = '8113580026:AAGDr8Cd6jT0-m7XoRZNIEt9qUHfCRD62qw'
ADMIN_ID = 6971227691
KINO_KANAL_ID = -1003168624222 # Kinolar yuklangan kanal IDsi

bot = telebot.TeleBot(TOKEN)
CHANNELS = ["@polatkino_uz"] # Boshlang'ich kanal

# 2. WEB SERVER (Render uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot 24/7 rejimida ishlayapti!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 3. FOYDALANUVCHILAR BAZASI BILAN ISHLASH
def save_user(user_id):
    user_id = str(user_id)
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f:
            f.write("")
    
    with open("users.txt", "r") as f:
        users = f.read().splitlines()
    
    if user_id not in users:
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")

# 4. OBUNA TEKSHIRISH
def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ['left', 'kicked']:
                return False
        except:
            # Agar bot kanal admini bo'lmasa yoki kanal topilmasa
            return False
    return True

# 5. ADMIN PANEL (KOMANDALAR)
@bot.message_handler(commands=['panel'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        text = "⚙️ **ADMIN PANELIGA XUSH KELIBSIZ**\n\n"
        text += "📢 **Hozirgi kanallar:**\n"
        for ch in CHANNELS:
            text += f"🔹 {ch}\n"
        text += "\n➕ Qo'shish: `/add @kanal`"
        text += "\n➖ O'chirish: `/del @kanal`"
        text += "\n✉️ Reklama yuborish: `/send`"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            new_ch = message.text.split()[1]
            if new_ch.startswith('@'):
                if new_ch not in CHANNELS:
                    CHANNELS.append(new_ch)
                    bot.reply_to(message, f"✅ {new_ch} ro'yxatga qo'shildi!")
                else:
                    bot.reply_to(message, "Bu kanal allaqachon mavjud.")
            else:
                bot.reply_to(message, "Xato! Kanal nomi @ bilan boshlanishi kerak.")
        except:
            bot.reply_to(message, "Format: `/add @kanal`")

@bot.message_handler(commands=['del'])
def del_channel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            ch = message.text.split()[1]
            if ch in CHANNELS:
                CHANNELS.remove(ch)
                bot.reply_to(message, f"❌ {ch} o'chirildi!")
            else:
                bot.reply_to(message, "Kanal topilmadi.")
        except:
            bot.reply_to(message, "Format: `/del @kanal`")

# 6. REKLAMA TARQATISH (FAQAT ADMIN UCHUN)
@bot.message_handler(commands=['send'])
def send_ad_request(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Barcha foydalanuvchilarga yuboriladigan xabarni yuboring (Rasm, matn, video yoki post):")
        bot.register_next_step_handler(msg, start_broadcasting)
    else:
        bot.reply_to(message, "❌ Bu buyruq faqat bot admini uchun!")

def start_broadcasting(message):
    if not os.path.exists("users.txt"):
        bot.send_message(ADMIN_ID, "Baza bo'sh!")
        return

    with open("users.txt", "r") as f:
        users = f.read().splitlines()

    bot.send_message(ADMIN_ID, f"🚀 Tarqatish boshlandi (Jami: {len(users)} ta)...")
    
    count = 0
    error = 0
    for user in users:
        try:
            bot.copy_message(user, message.chat.id, message.message_id)
            count += 1
        except:
            error += 1
    
    bot.send_message(ADMIN_ID, f"📢 **Xabar tarqatish tugadi!**\n\n✅ Yetkazildi: {count}\n❌ Bloklaganlar: {error}")

# 7. FOYDALANUVCHI QISMI
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    bot.send_message(
        message.chat.id, 
        f"🎬 Salom {message.from_user.first_name}!\nKino kodini yuboring, men sizga kinoni topib beraman."
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Tasdiqlandi! Kino kodini yuboring:")
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanallarga a'zo bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    # Har doim foydalanuvchini bazaga tekshirib qo'shamiz
    save_user(message.from_user.id)

    # Obunani tekshirish
    if not check_sub(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            markup.add(telebot.types.InlineKeyboardButton(text=f"A'zo bo'lish ({ch})", url=f"https://t.me/{ch[1:]}"))
        markup.add(telebot.types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_sub"))
        
        bot.send_message(
            message.chat.id, 
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart:", 
            reply_markup=markup
        )
        return

    # Kino kodini tekshirish
    if message.text.isdigit():
        try:
            # Kinoni forward emas, COPY qilish (chiroyli chiqadi)
            bot.copy_message(message.chat.id, KINO_KANAL_ID, int(message.text))
        except:
            bot.send_message(message.chat.id, "😔 Afsuski, bu kod bo'yicha kino topilmadi.")
    else:
        bot.send_message(message.chat.id, "🔢 Iltimos, faqat kino kodini (raqam) yuboring.")

# 8. ISHGA TUSHIRISH
if __name__ == "__main__":
    # Web serverni alohida thread'da boshlaymiz
    t = Thread(target=run)
    t.start()
    
    print("Bot muvaffaqiyatli ishga tushdi!")
    bot.infinity_polling()
