import telebot
from flask import Flask
from threading import Thread
import os
import time
import sqlite3
from datetime import datetime

# 1. SOZLAMALAR
TOKEN = '8113580026:AAGDr8Cd6jT0-m7XoRZNIEt9qUHfCRD62qw'
ADMIN_ID = 6971227691
KINO_KANAL_ID = -1003168624222 

# Botni ko'p tarmoqli (multithreading) rejimida yoqish
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)
CHANNELS = ["@polatkino_uz"]

# 2. MA'LUMOTLAR BAZASI BILAN ISHLASH
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            joined_at DATE
        )
    """)
    conn.commit()
    conn.close()

def save_user(user_id):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("INSERT OR IGNORE INTO users (user_id, joined_at) VALUES (?, ?)", (user_id, today))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Baza xatosi: {e}")

# 3. AVTOMATIK HISOBOT VA BAZA NUSXASI (BACKUP)
def auto_tasks_loop():
    while True:
        now = datetime.now()
        # Har kuni tungi 00:00 da ishlaydi
        if now.hour == 00 and now.minute == 00:
            try:
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
                
                # Jami soni
                cursor.execute("SELECT COUNT(*) FROM users")
                total = cursor.fetchone()[0]
                
                # Bugungi yangi odamlar
                today_str = now.strftime('%Y-%m-%d')
                cursor.execute("SELECT COUNT(*) FROM users WHERE joined_at = ?", (today_str,))
                today_count = cursor.fetchone()[0]
                conn.close()

                # 1. Hisobot yuborish
                report = f"📊 **KUNLIK HISOBOT**\n\n👤 Bugun qo'shildi: {today_count}\n👥 Jami: {total}"
                bot.send_message(ADMIN_ID, report, parse_mode="Markdown")

                # 2. Baza nusxasini yuborish (Render'da o'chib ketish xavfi uchun)
                with open("users.db", "rb") as doc:
                    bot.send_document(ADMIN_ID, doc, caption=f"💾 Baza nusxasi: {today_str}")
                
                time.sleep(65) # Qayta ishlamasligi uchun 1 minut kutish
            except Exception as e:
                print(f"Avto-vazifa xatosi: {e}")
        
        time.sleep(30)

# 4. OBUNA TEKSHIRISH
def check_sub(user_id):
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status in ['left', 'kicked']: return False
        except: return False
    return True

# 5. REKLAMA (ALOHIDA OQIMDA)
def broadcast_worker(message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    bot.send_message(ADMIN_ID, f"🚀 Reklama {len(users)} kishiga yuborilmoqda...")
    c, e = 0, 0
    for (u_id,) in users:
        try:
            bot.copy_message(u_id, message.chat.id, message.message_id)
            c += 1
            time.sleep(0.05) # Telegram limitidan oshmaslik uchun
        except: e += 1
    bot.send_message(ADMIN_ID, f"✅ Reklama tugadi!\n\nYetkazildi: {c}\nBlok: {e}")

# 6. KOMANDALAR VA HANDLERLAR
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    bot.send_message(message.chat.id, f"🎬 Salom {message.from_user.first_name}!\nKino kodini yuboring:")

@bot.message_handler(commands=['stat'])
def get_stat(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        conn.close()
        bot.reply_to(message, f"📊 Bazadagi jami foydalanuvchilar: {total} ta")

@bot.message_handler(commands=['send'])
def send_ad(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Reklama postini yuboring (text, rasm, video):")
        bot.register_next_step_handler(msg, lambda m: Thread(target=broadcast_worker, args=(m,)).start())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Rahmat! Endi kino kodini yuborishingiz mumkin:")
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali a'zo bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    save_user(message.from_user.id)
    if not check_sub(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            markup.add(telebot.types.InlineKeyboardButton(text=f"Kanalga a'zo bo'lish", url=f"https://t.me/{ch[1:]}"))
        markup.add(telebot.types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart:", reply_markup=markup)
        return

    if message.text.isdigit():
        try:
            bot.copy_message(message.chat.id, KINO_KANAL_ID, int(message.text))
        except:
            bot.send_message(message.chat.id, "😔 Bu kodga mos kino topilmadi.")
    else:
        bot.send_message(message.chat.id, "🔢 Iltimos, faqat kino kodini yuboring.")

# 7. RENDER UCHUN WEB SERVER
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    init_db()
    Thread(target=run_web).start()
    Thread(target=auto_tasks_loop).start()
    
    print("Bot muvaffaqiyatli yoqildi!")
    
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Polling xatosi: {e}")
            time.sleep(10)
