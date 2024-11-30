import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# OpenWeatherMap API kaliti
API_KEY = '5af718916f321b457560be9c34e12301'  # OpenWeatherMap'dan olingan API kaliti
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

# O'rta Osiyo davlatlari va viloyatlari ro'yxati
CENTRAL_ASIA = {
    "🇺🇿 O'zbekiston": [
        "Toshkent", "Andijon", "Buxoro", "Farg'ona", "Jizzax",
        "Qoraqalpog'iston", "Xorazm", "Namangan", "Navoiy", "Samarqand",
        "Sirdaryo", "Surxandaryo", "Qashqadaryo"
    ],
    "🇰🇿 Qozog'iston": [
        "Almaty", "Nur-Sultan", "Shimkent", "Karaganda", "Aktobe",
        "Pavlodar", "Qostanay", "Taraz", "Atyrau", "Qizilorda"
    ],
    "🇰🇬 Qirg'iziston": [
        "Bishkek", "Osh", "Jalol-Abad", "Karakol", "Naryn",
        "Talas", "Batken"
    ],
    "🇹🇯 Tojikiston": [
        "Dushanbe", "Xo'jand", "Kulob", "Bokhtar", "Istaravshan"
    ],
    "🇹🇲 Turkmaniston": [
        "Ashxobod", "Turkmenabad", "Mary", "Balkanabat", "Dashoguz"
    ]
}

# --- SQLite Bazasini sozlash ---
def setup_database():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_date TEXT
        )
    """)
    conn.commit()
    conn.close()

# Foydalanuvchini bazaga qo'shish funksiyasi
def add_user_to_database(user_id, username, first_name):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, first_name, joined_date)
        VALUES (?, ?, ?, datetime('now'))
    """, (user_id, username, first_name))
    conn.commit()
    conn.close()

# Foydalanuvchilar sonini olish
def get_user_count():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# /start komandasini ishlov beruvchi funksiya
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user if update.message else update.callback_query.from_user
    add_user_to_database(user.id, user.username, user.first_name)  # Foydalanuvchini bazaga qo'shish

    # Davlatlar uchun tugmalarni ikki ustunda yaratish
    keyboard = [
        [InlineKeyboardButton(country, callback_data=country) for country in list(CENTRAL_ASIA.keys())[i:i + 2]]
        for i in range(0, len(CENTRAL_ASIA.keys()), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Xabarni tugmalar bilan yuborish
    if update.message:
        await update.message.reply_text(
            "🌏 <b>Assalomu alaykum!</b> O'rta Osiyo davlatlaridan birini tanlang:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.callback_query.edit_message_text(
            "🌏 <b>Assalomu alaykum!</b> O'rta Osiyo davlatlaridan birini tanlang:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

# Statistika buyruqni ishlovchi funksiya
async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = 123456789  # Adminning Telegram ID'sini kiriting
    if update.effective_user.id == admin_id:  # Faqat admin ko'ra oladi
        user_count = get_user_count()
        await update.message.reply_text(f"Botda hozirda {user_count} foydalanuvchi bor.")
    else:
        await update.message.reply_text("Bu buyruq faqat admin uchun.")

# Tugmalarga javob beruvchi funksiya (Davlat → Viloyatlar)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Callbackni javobini berish
    selected = query.data  # Foydalanuvchi tanlagan davlat yoki viloyat

    if selected in CENTRAL_ASIA:  # Agar davlat tanlansa
        # Tanlangan davlatning viloyatlari uchun tugmalarni ikki ustunda yaratish
        regions = CENTRAL_ASIA[selected]
        keyboard = [
            [InlineKeyboardButton(region, callback_data=region) for region in regions[i:i + 2]]
            for i in range(0, len(regions), 2)
        ]
        # Boshqa davlat tanlash tugmasi
        keyboard.append([InlineKeyboardButton("⬅️ Boshqa davlat tanlash", callback_data='restart')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Xabarni yangilash va viloyatlarni ko'rsatish
        await query.edit_message_text(
            f"🌍 <b>{selected}</b> davlatini tanladingiz. 🌟 Endi viloyatni tanlang:",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif selected in sum(CENTRAL_ASIA.values(), []):  # Agar viloyat tanlansa
        # Ob-havo ma'lumotini olish
        response = requests.get(BASE_URL, params={'q': selected, 'appid': API_KEY, 'units': 'metric'})

        if response.status_code == 200:
            data = response.json()
            weather_info = (
                f"📍 <b>Viloyat:</b> {data['name']}\n"
                f"🌡️ <b>Temperatura:</b> {data['main']['temp']}°C\n"
                f"🌥️ <b>Ob-havo:</b> {data['weather'][0]['description']}\n"
                f"💧 <b>Namlik:</b> {data['main']['humidity']}%\n"
                f"🌬️ <b>Shamol tezligi:</b> {data['wind']['speed']} m/s"
            )

            # "Boshqa davlat" tugmasini qo'shish
            keyboard = [
                [InlineKeyboardButton("⬅️ Boshqa davlat tanlash", callback_data='restart')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Xabarni yangilash va tugmani ko'rsatish
            await query.edit_message_text(weather_info, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await query.edit_message_text("❌ Xatolik yuz berdi yoki viloyat topilmadi.")
    elif selected == 'restart':  # Boshqa davlatni tanlash
        await query.answer()  # Callbackni javobini berish
        await start(update, context)  # Yangi davlatlarni tanlash uchun start() funksiyasini chaqirish

# Botni ishga tushurish
def main():
    setup_database()  # Bazani sozlash

    # Bot tokenini kiritish
    application = Application.builder().token("7873776007:AAHDFbgSu3wCBS2NGTdUfglyS6xKZttMSR4").build()

    # /start komandasi va tugmalarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("statistics", statistics))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Botni ishga tushurish
    application.run_polling()

if __name__ == '__main__':
    main()
