import telebot
from telebot import types
import datetime
import sqlite3

# توكن البوت
TOKEN = '7391592516:AAGu93B7HOv1YUTxpn7WPSN3GAxXvhHMfRU'  # هنا التوكن الخاص بك
bot = telebot.TeleBot(TOKEN)

# معلومات المالك
OWNER_PHONE_NUMBER_ZAIN = '07709634185'  # رقم زين كاش
OWNER_PHONE_NUMBER_ASIA = '07709634185'  # رقم أسيا سيل (تم التعديل)
OWNER_USERNAME = "@JU7US"  # يوزر المالك
OWNER_ID = 7146124259  # ID حساب المالك

# قاعدة البيانات
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء الجداول في قاعدة البيانات
def create_tables():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        user_id INTEGER,
        amount REAL,
        points INTEGER,
        package TEXT,
        username TEXT,
        payment_method TEXT,
        status TEXT DEFAULT 'pending',
        timestamp DATETIME
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER PRIMARY KEY,
        referral_code TEXT,
        points INTEGER DEFAULT 0
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        user_id INTEGER,
        rating INTEGER,
        review TEXT,
        timestamp DATETIME
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        user_id INTEGER,
        task TEXT,
        completed BOOLEAN DEFAULT FALSE,
        timestamp DATETIME
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        user_id INTEGER,
        message TEXT,
        timestamp DATETIME
    )
    ''')
    conn.commit()

create_tables()

# دالة لإرسال رسالة للمالك
def notify_owner(user_id, amount, points, package=None, username=None, payment_method=None):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))) # توقيت العراق
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    owner_message = f"📦 طلب جديد من المستخدم: {user_id}\n"
    owner_message += f"💰 المبلغ المحول: {amount} دولار\n"
    owner_message += f"✨ سيتم تحويلها إلى: {points} نقطة\n"
    if package:
        owner_message += f"🎯 طلب: {package}\n"
    if username:
        owner_message += f"👤 يوزر انستجرام: @{username}\n"
    if payment_method:
        owner_message += f"💳 طريقة الدفع: {payment_method}\n"
    owner_message += f"⏰ وقت الطلب: {timestamp}"
    try:
        bot.send_message(OWNER_ID, owner_message)
    except Exception as e:
        print(f"حدث خطأ أثناء إرسال الإشعار للمالك: {e}")

# لوحة إدارة المالك
def owner_panel():
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("عرض الطلبات المعلقة", callback_data="admin_pending_orders")
    button2 = types.InlineKeyboardButton("إرسال رسالة للكل", callback_data="admin_send_all")
    button3 = types.InlineKeyboardButton("تحديث الرصيد", callback_data="admin_update_balance")
    button4 = types.InlineKeyboardButton("عرض الإحصائيات", callback_data="admin_stats")
    markup.add(button1, button2)
    markup.add(button3, button4)
    return markup

# أمر لبدء المحادثة مع رسالة ترحيبية ولوحة إدارة للمالك
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id == OWNER_ID:
        bot.send_message(OWNER_ID, "👋 مرحباً بك في لوحة إدارة البوت:", reply_markup=owner_panel())
    else:
        welcome_message = f"""
مرحباً بك في بوت رشق الوارث! 👋

يمكنك استخدام هذا البوت لطلب زيادة عدد المتابعين لحسابك على انستجرام.

طريقة الدفع:
1.  قم بتحويل المبلغ المطلوب (بالدولار الأمريكي) إلى حسابنا عبر:
    * زين كاش: {OWNER_PHONE_NUMBER_ZAIN}
    * أسيا سيل: {OWNER_PHONE_NUMBER_ASIA}
2.  بعد التحويل، استخدم الأمر /pay وأخبرنا بالمبلغ الذي قمت بتحويله.
3.  اختر عدد المتابعين الذي ترغب في الحصول عليه من الخيارات المتاحة.
4.  أرسل لنا اسم المستخدم الخاص بحسابك على انستجرام.

إذا واجهتك أي مشكلة، يمكنك التواصل مع المالك على {OWNER_USERNAME}.
"""
        bot.reply_to(message, welcome_message)

# أمر الدفع
@bot.message_handler(commands=['pay'])
def ask_amount(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("زين كاش", callback_data="payment_zain")
    button2 = types.InlineKeyboardButton("أسيا سيل", callback_data="payment_asia")
    button3 = types.InlineKeyboardButton("التواصل مع المالك", callback_data="contact_owner")
    markup.add(button1, button2)
    markup.add(button3)
    bot.reply_to(message, "يرجى اختيار طريقة الدفع:", reply_markup=markup)

# معالجة المبلغ المحول
@bot.message_handler(func=lambda message: True)
def process_payment(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text.split()[0])  # المبلغ المحول
        points = amount * 50  # تحويل المبلغ إلى نقاط (1 دولار = 50 نقطة)

        # تخزين المبلغ والنقاط في قاعدة البيانات
        cursor.execute('INSERT INTO orders (user_id, amount, points, timestamp) VALUES (?, ?, ?, ?)',
                       (user_id, amount, points, datetime.datetime.now()))
        conn.commit()

        # إرسال إشعار للمالك
        notify_owner(user_id, amount, points)

        # إرسال رسالة تأكيد للزبون وعرض خيارات المتابعين مباشرة
        confirmation_message = f"تم استلام المبلغ: {amount} دولار. سيتم تحويل {points} نقطة لك قريبًا."
        bot.reply_to(message, confirmation_message)

        # عرض خيارات المتابعين
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("1000 متابع بـ 100 نقطة", callback_data="followers_1000"),
                   types.InlineKeyboardButton("2000 متابع بـ 200 نقطة", callback_data="followers_2000"))
        markup.add(types.InlineKeyboardButton("5000 متابع بـ 500 نقطة", callback_data="followers_5000"),
                   types.InlineKeyboardButton("10000 متابع بـ 1000 نقطة", callback_data="followers_10000"))
        markup.add(types.InlineKeyboardButton("20000 متابع بـ 2000 نقطة", callback_data="followers_20000"),
                   types.InlineKeyboardButton("50000 متابع بـ 5000 نقطة", callback_data="followers_50000"))
        markup.add(types.InlineKeyboardButton("100000 متابع بـ 10000 نقطة", callback_data="followers_100000"))

        bot.send_message(message.chat.id, "اختر عدد المتابعين الذي ترغب في الحصول عليه:", reply_markup=markup)

    except ValueError:
        bot.reply_to(message, "الرجاء إدخال مبلغ صحيح. مثال: 5 دولار.")
    except Exception as e:
        print(f"حدث خطأ أثناء معالجة الدفع: {e}")
        bot.reply_to(message, "حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقًا.")

# معالجة الضغط على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if call.data.startswith("followers_"):
        num_followers = call.data.split('_')[1]
        points_needed = int(num_followers) // 10
        selected_package = f"{num_followers} متابع بـ {points_needed} نقطة"
        bot.answer_callback_query(call.id, f"تم اختيار {selected_package}.")
        bot.send_message(call.message.chat.id, f"الآن، يرجى إرسال اسم المستخدم الخاص بحسابك على انستجرام.")
    elif call.data == "contact_owner":
        bot.send_message(call.message.chat.id, f"يمكنك التواصل مع المالك على {OWNER_USERNAME}.")
    elif call.data.startswith("admin_"):
        if call.data == "admin_pending_orders":
            cursor.execute('SELECT user_id, amount, points, timestamp FROM orders WHERE status = ?', ('pending',))
            pending_orders = cursor.fetchall()
            if pending_orders:
                orders_message = "📋 الطلبات المعلقة:\n"
                for order in pending_orders:
                    user_id, amount, points, timestamp = order
                    orders_message += f"👤 المستخدم: {user_id}\n💰 المبلغ: {amount} دولار\n✨ النقاط: {points}\n⏰ الوقت: {timestamp}\n\n"
                bot.send_message(OWNER_ID, orders_message)
            else:
                bot.send_message(OWNER_ID, "لا توجد طلبات معلقة.")
        elif call.data == "admin_send_all":
            bot.send_message(OWNER_ID, "أدخل الرسالة التي تريد إرسالها للكل:")
            bot.register_next_step_handler(call.message, send_to_all)
        elif call.data == "admin_update_balance":
            bot.send_message(OWNER_ID, "أدخل معرف المستخدم والمبلغ الجديد (مثال: 123456 1000):")
            bot.register_next_step_handler(call.message, update_balance)
        elif call.data == "admin_stats":
            cursor.execute('SELECT COUNT(*) FROM orders WHERE status = ?', ('completed',))
            completed_orders = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM orders WHERE status = ?', ('pending',))
            pending_orders = cursor.fetchone()[0]
            stats_message = f"📊 الإحصائيات:\n✅ الطلبات المكتملة: {completed_orders}\n🕒 الطلبات المعلقة: {pending_orders}"
            bot.send_message(OWNER_ID, stats_message)

# إرسال رسالة للكل
def send_to_all(message):
    text = message.text
    cursor.execute('SELECT DISTINCT user_id FROM orders')
    users = cursor.fetchall()
    for user in users:
        try:
            bot.send_message(user[0], text)
        except Exception as e:
            print(f"حدث خطأ أثناء إرسال الرسالة للمستخدم {user[0]}: {e}")
    bot.send_message(OWNER_ID, "تم إرسال الرسالة للكل بنجاح.")

# تحديث رصيد المستخدم
def update_balance(message):
    try:
        user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = float(amount)
        cursor.execute('UPDATE orders SET points = ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        bot.send_message(OWNER_ID, f"تم تحديث رصيد المستخدم {user_id} إلى {amount} نقطة.")
    except Exception as e:
        bot.send_message(OWNER_ID, f"حدث خطأ أثناء تحديث الرصيد: {e}")

# تشغيل البوت
bot.polling()