import os
import telebot
import sqlite3
from datetime import datetime, timedelta

API_TOKEN = '7628466810:AAHIiGViWOH3W6C7FbxQd0KZzqzFWcy3zKA'
OWNER_USERNAME = 'RYBBKA_MACO'

bot = telebot.TeleBot(API_TOKEN)

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 10, -- Начальный баланс 10 Драго
        last_earn TEXT,
        is_owner INTEGER DEFAULT 0,
        registered_date TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER,
        from_username TEXT,
        to_user_id INTEGER,
        to_username TEXT,
        amount INTEGER,
        transfer_date TEXT,
        FOREIGN KEY (from_user_id) REFERENCES users (user_id),
        FOREIGN KEY (to_user_id) REFERENCES users (user_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bans (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        banned_by TEXT,
        ban_reason TEXT,
        ban_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        appointed_by TEXT,
        appointed_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')
conn.commit()

# Add columns if they don't exist (migration)
try:
    cursor.execute('ALTER TABLE users ADD COLUMN is_owner INTEGER DEFAULT 0')
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    cursor.execute('ALTER TABLE users ADD COLUMN registered_date TEXT DEFAULT CURRENT_TIMESTAMP')
    conn.commit()
except sqlite3.OperationalError:
    pass

# Helper functions
def is_owner(user_id):
    cursor.execute('SELECT is_owner FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

def is_main_admin(user_id, username):
    return username == OWNER_USERNAME

def is_admin(user_id, username):
    if username == OWNER_USERNAME:
        return True
    cursor.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None

def is_banned(user_id):
    cursor.execute('SELECT * FROM bans WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None

def ban_user(user_id, username, banned_by, reason="Не указана"):
    cursor.execute('''
        INSERT OR REPLACE INTO bans (user_id, username, banned_by, ban_reason, ban_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, banned_by, reason, datetime.now().isoformat()))
    conn.commit()

def unban_user(user_id):
    cursor.execute('DELETE FROM bans WHERE user_id = ?', (user_id,))
    conn.commit()

def add_admin(user_id, username, appointed_by):
    cursor.execute('''
        INSERT OR REPLACE INTO admins (user_id, username, appointed_by, appointed_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, appointed_by, datetime.now().isoformat()))
    conn.commit()

def remove_admin(user_id):
    cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
    conn.commit()

def get_balance(user_id):
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

def add_user(user_id, username):
    is_owner_flag = 1 if username == OWNER_USERNAME else 0
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, balance, is_owner) VALUES (?, ?, 10, ?)', 
                   (user_id, username, is_owner_flag))
    if username == OWNER_USERNAME:
        cursor.execute('UPDATE users SET is_owner = 1 WHERE user_id = ?', (user_id,))
    conn.commit()

# Command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
        
    add_user(user_id, username)
    
    if username == OWNER_USERNAME:
        bot.reply_to(message, f"Привет, {message.from_user.first_name}! 👑 Ты владелец бота с бесконечным балансом Драго!\nИспользуй /help для списка команд.")
    else:
        bot.reply_to(message, f"Привет, {message.from_user.first_name}! 👋 Добро пожаловать в  бота ролевой! 🪙\nТвой стартовый баланс: 10 Драго.\nИспользуй /help для списка команд.")

@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    help_text = """
💫 **ДОСТУПНЫЕ КОМАНДЫ:**

💰 **Экономика:**
/balance - Мой баланс
/checkbalance @username - Баланс другого пользователя
/earn - Заработать 10 Драго (раз в 10 часов)
/transfer @username сумма - Перевести Драго

📊 **Статистика:**
/stats - Общая статистика системы
/top - Топ-10 самых богатых
/stats_day - Статистика переводов за день
/stats_week - Статистика переводов за неделю
/stats_month - Статистика переводов за месяц

Примеры:
/transfer @ivanov 50
/checkbalance @petr
"""
    
    if is_admin(user_id, username):
        help_text += """
🔧 **Команды администратора:**
/ban @username [причина] - Забанить пользователя
/unban @username - Разбанить пользователя
/banlist - Список забаненных
/adminlist - Список администраторов
/myadmin - Мои права доступа
"""
    
    if is_main_admin(user_id, username):
        help_text += """
👑 **Команды главного администратора:**
/addadmin @username - Назначить администратора
/removeadmin @username - Снять администратора
"""
    
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['balance'])
def show_balance(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
        
    balance = get_balance(user_id)
    
    if balance is not None:
        if is_owner(user_id):
            bot.reply_to(message, f"💰 Твой баланс: ∞ Драго (владелец)")
        else:
            bot.reply_to(message, f"💰 Твой баланс: {balance} Драго.")
    else:
        bot.reply_to(message, "Сначала напиши /start.")

@bot.message_handler(commands=['checkbalance', 'userbalance', 'balanceof'])
def check_user_balance(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
    
    parts = message.text.split()
    
    if len(parts) != 2:
        bot.reply_to(message, "❌ Неправильный формат. Используй: /checkbalance @username\nПример: /checkbalance @ivanov")
        return
    
    target_username = parts[1].lstrip('@')
    
    cursor.execute('SELECT balance, user_id, is_owner FROM users WHERE username = ?', (target_username,))
    result = cursor.fetchone()
    
    if not result:
        bot.reply_to(message, f"❌ Пользователь @{target_username} не найден.\nВозможно, он еще не запускал бота через /start.")
        return
    
    balance, user_id, is_owner_flag = result
    
    if message.from_user.id == user_id:
        bot.reply_to(message, f"🤔 Для просмотра своего баланса используй просто /balance")
        return
    
    if is_owner_flag == 1:
        bot.reply_to(message, f"📊 Баланс пользователя @{target_username}: ∞ Драго 👑 (владелец)")
    else:
        bot.reply_to(message, f"📊 Баланс пользователя @{target_username}: {balance} Драго 🪙")

@bot.message_handler(commands=['earn'])
def earn_coins(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
        
    add_user(user_id, username)

    if is_owner(user_id):
        bot.reply_to(message, "👑 У тебя уже бесконечный баланс!")
        return

    cursor.execute('SELECT last_earn FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    now = datetime.now().isoformat()

    if result and result[0]:
        last_earn = datetime.fromisoformat(result[0])
        if datetime.now() - last_earn < timedelta(hours=10):
            bot.reply_to(message, "❌ Слишком рано! Зарабатывать Драго можно раз в 10 часов.")
            return

    cursor.execute('UPDATE users SET balance = balance + 10, last_earn = ? WHERE user_id = ?', (now, user_id))
    conn.commit()
    bot.reply_to(message, "✅ Ты заработал 10 Драго! 🪙")

@bot.message_handler(commands=['transfer'])
def transfer_coins(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
        
    parts = message.text.split()

    if len(parts) != 3:
        bot.reply_to(message, "❌ Неправильный формат. Используй: /transfer @username количество")
        return

    target_username = parts[1].lstrip('@')
    
    try:
        amount = int(parts[2])
    except ValueError:
        bot.reply_to(message, "❌ Количество должно быть числом.")
        return

    if amount <= 0:
        bot.reply_to(message, "❌ Можно переводить только положительную сумму.")
        return
    
    MAX_AMOUNT = 2147483647
    if amount > MAX_AMOUNT:
        bot.reply_to(message, f"❌ Максимальная сумма перевода: {MAX_AMOUNT} Драго.")
        return

    if not is_owner(user_id):
        sender_balance = get_balance(user_id)
        if sender_balance is None or sender_balance < amount:
            bot.reply_to(message, "❌ Недостаточно Драго для перевода.")
            return

    cursor.execute('SELECT user_id FROM users WHERE username = ?', (target_username,))
    result = cursor.fetchone()

    if not result:
        bot.reply_to(message, f"❌ Пользователь @{target_username} не найден. Он должен был хотя бы раз написать боту /start.")
        return

    target_user_id = result[0]
    
    if is_banned(target_user_id):
        bot.reply_to(message, f"❌ Нельзя переводить Драго забаненному пользователю.")
        return

    if user_id == target_user_id:
        bot.reply_to(message, "❌ Нельзя переводить самому себе.")
        return

    if not is_owner(user_id):
        cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, target_user_id))
    
    transfer_time = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO transfers (from_user_id, from_username, to_user_id, to_username, amount, transfer_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, message.from_user.username, target_user_id, target_username, amount, transfer_time))
    
    conn.commit()

    bot.reply_to(message, f"✅ Успешно переведено {amount} Драго пользователю @{target_username}!")
    try:
        bot.send_message(target_user_id, f"💸 Тебе перевели {amount} Драго от @{message.from_user.username}!")
    except:
        pass

@bot.message_handler(commands=['stats', 'statistics'])
def show_stats(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
    
    cursor.execute('SELECT COUNT(*) as total_users, SUM(balance) as total_coins FROM users')
    user_stats = cursor.fetchone()
    total_users, total_coins = user_stats
    total_coins = total_coins or 0
    
    cursor.execute('SELECT username, balance FROM users WHERE is_owner = 0 ORDER BY balance DESC LIMIT 1')
    richest_user = cursor.fetchone()
    richest_username, richest_balance = richest_user if richest_user else ("Нет данных", 0)
    
    cursor.execute('SELECT COUNT(*) FROM transfers')
    total_transfers = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(amount) FROM transfers')
    total_transferred = cursor.fetchone()[0] or 0
    
    stats_text = f"""
📊 **ОБЩАЯ СТАТИСТИКА СИСТЕМЫ**

👥 Всего пользователей: {total_users}
💰 Всего Драго в системе: {total_coins} 🪙
🏆 Самый богатый: @{richest_username} ({richest_balance} Драго)
📤 Всего переводов: {total_transfers}
💸 Всего переведено: {total_transferred} Драго

Для детальной статистики переводов:
/stats_day - за сегодня
/stats_week - за неделю
/stats_month - за месяц
"""
    bot.reply_to(message, stats_text)

@bot.message_handler(commands=['stats_day'])
def show_stats_day(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
    
    today = datetime.now().date().isoformat()
    
    cursor.execute('''
        SELECT COUNT(*) as transfers_count, SUM(amount) as total_amount 
        FROM transfers 
        WHERE date(transfer_date) = date(?)
    ''', (today,))
    
    stats = cursor.fetchone()
    transfers_count, total_amount = stats
    total_amount = total_amount or 0
    
    cursor.execute('''
        SELECT from_username, to_username, amount 
        FROM transfers 
        WHERE date(transfer_date) = date(?)
        ORDER BY amount DESC LIMIT 1
    ''', (today,))
    
    largest_transfer = cursor.fetchone()
    
    stats_text = f"""
📊 **СТАТИСТИКА ЗА СЕГОДНЯ** ({today})

🔄 Количество переводов: {transfers_count}
💰 Сумма переводов: {total_amount} Драго
"""
    
    if largest_transfer:
        from_user, to_user, amount = largest_transfer
        stats_text += f"🏆 Крупнейший перевод: {amount} Драго от @{from_user} к @{to_user}"
    
    bot.reply_to(message, stats_text)

@bot.message_handler(commands=['stats_week'])
def show_stats_week(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
    
    week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
    
    cursor.execute('''
        SELECT COUNT(*) as transfers_count, SUM(amount) as total_amount 
        FROM transfers 
        WHERE date(transfer_date) >= date(?)
    ''', (week_ago,))
    
    stats = cursor.fetchone()
    transfers_count, total_amount = stats
    total_amount = total_amount or 0
    
    cursor.execute('''
        SELECT from_username, COUNT(*) as transfer_count
        FROM transfers 
        WHERE date(transfer_date) >= date(?)
        GROUP BY from_user_id 
        ORDER BY transfer_count DESC 
        LIMIT 1
    ''', (week_ago,))
    
    active_sender = cursor.fetchone()
    
    stats_text = f"""
📊 **СТАТИСТИКА ЗА НЕДЕЛЮ** (с {week_ago})

🔄 Количество переводов: {transfers_count}
💰 Сумма переводов: {total_amount} Драго
"""
    
    if active_sender:
        sender_username, transfer_count = active_sender
        stats_text += f"🎯 Самый активный: @{sender_username} ({transfer_count} переводов)"
    
    bot.reply_to(message, stats_text)

@bot.message_handler(commands=['stats_month'])
def show_stats_month(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
    
    month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    
    cursor.execute('''
        SELECT COUNT(*) as transfers_count, SUM(amount) as total_amount 
        FROM transfers 
        WHERE date(transfer_date) >= date(?)
    ''', (month_ago,))
    
    stats = cursor.fetchone()
    transfers_count, total_amount = stats
    total_amount = total_amount or 0
    
    cursor.execute('''
        SELECT to_username, SUM(amount) as received 
        FROM transfers 
        WHERE date(transfer_date) >= date(?)
        GROUP BY to_user_id 
        ORDER BY received DESC 
        LIMIT 3
    ''', (month_ago,))
    
    top_receivers = cursor.fetchall()
    
    stats_text = f"""
📊 **СТАТИСТИКА ЗА МЕСЯЦ** (последние 30 дней)

🔄 Количество переводов: {transfers_count}
💰 Сумма переводов: {total_amount} Драго
"""
    
    if top_receivers:
        stats_text += "\n🏆 Топ-3 получателей:\n"
        for i, (username, amount) in enumerate(top_receivers, 1):
            stats_text += f"{i}. @{username} - {amount} Драго\n"
    
    bot.reply_to(message, stats_text)

@bot.message_handler(commands=['top', 'rich'])
def show_top_users(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Вы забанены и не можете использовать бота.")
        return
    
    cursor.execute('''
        SELECT username, balance, is_owner
        FROM users 
        WHERE username IS NOT NULL 
        ORDER BY balance DESC 
        LIMIT 10
    ''')
    
    top_users = cursor.fetchall()
    
    top_text = "🏆 **ТОП-10 САМЫХ БОГАТЫХ ПОЛЬЗОВАТЕЛЕЙ**\n\n"
    
    for i, (username, balance, is_owner_flag) in enumerate(top_users, 1):
        medal = ""
        if i == 1: medal = "🥇"
        elif i == 2: medal = "🥈" 
        elif i == 3: medal = "🥉"
        else: medal = f"{i}."
        
        if is_owner_flag == 1:
            top_text += f"{medal} @{username} - ∞ Драго 👑 (владелец)\n"
        else:
            top_text += f"{medal} @{username} - {balance} Драго 🪙\n"
    
    bot.reply_to(message, top_text)

# Admin commands
@bot.message_handler(commands=['ban'])
def ban_user_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_admin(user_id, username):
        bot.reply_to(message, "❌ У вас нет прав для использования этой команды.")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.reply_to(message, "❌ Неправильный формат. Используй: /ban @username [причина]\nПример: /ban @username Спам")
        return
    
    target_username = parts[1].lstrip('@')
    ban_reason = " ".join(parts[2:]) if len(parts) > 2 else "Не указана"
    
    cursor.execute('SELECT user_id FROM users WHERE username = ?', (target_username,))
    result = cursor.fetchone()
    
    if not result:
        bot.reply_to(message, f"❌ Пользователь @{target_username} не найден.")
        return
    
    target_user_id = result[0]
    
    if is_admin(target_user_id, target_username) and not is_main_admin(user_id, username):
        bot.reply_to(message, f"❌ Нельзя забанить другого администратора.")
        return
    
    if target_user_id == user_id:
        bot.reply_to(message, "❌ Нельзя забанить самого себя.")
        return
    
    if is_banned(target_user_id):
        bot.reply_to(message, f"❌ Пользователь @{target_username} уже забанен.")
        return
    
    ban_user(target_user_id, target_username, username, ban_reason)
    
    try:
        bot.send_message(target_user_id, f"🚫 Вы были забанены администратором @{username}.\nПричина: {ban_reason}")
    except:
        pass
    
    bot.reply_to(message, f"✅ Пользователь @{target_username} забанен.\nПричина: {ban_reason}")

@bot.message_handler(commands=['unban'])
def unban_user_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_admin(user_id, username):
        bot.reply_to(message, "❌ У вас нет прав для использования этой команды.")
        return
    
    parts = message.text.split()
    
    if len(parts) != 2:
        bot.reply_to(message, "❌ Неправильный формат. Используй: /unban @username\nПример: /unban @username")
        return
    
    target_username = parts[1].lstrip('@')
    
    cursor.execute('SELECT user_id FROM bans WHERE username = ?', (target_username,))
    result = cursor.fetchone()
    
    if not result:
        bot.reply_to(message, f"❌ Пользователь @{target_username} не найден в списке забаненных.")
        return
    
    target_user_id = result[0]
    
    unban_user(target_user_id)
    
    try:
        bot.send_message(target_user_id, f"✅ Вы были разбанены администратором @{username}.")
    except:
        pass
    
    bot.reply_to(message, f"✅ Пользователь @{target_username} разбанен.")

@bot.message_handler(commands=['banlist', 'bans'])
def show_banlist(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_admin(user_id, username):
        bot.reply_to(message, "❌ У вас нет прав для использования этой команды.")
        return
    
    cursor.execute('''
        SELECT username, banned_by, ban_reason, ban_date 
        FROM bans 
        ORDER BY ban_date DESC
    ''')
    
    banned_users = cursor.fetchall()
    
    if not banned_users:
        bot.reply_to(message, "📋 Список забаненных пользователей пуст.")
        return
    
    banlist_text = "📋 **СПИСОК ЗАБАНЕННЫХ ПОЛЬЗОВАТЕЛЕЙ**\n\n"
    
    for i, (banned_username, banned_by, reason, ban_date) in enumerate(banned_users, 1):
        ban_date_formatted = datetime.fromisoformat(ban_date).strftime("%d.%m.%Y %H:%M")
        banlist_text += f"{i}. @{banned_username}\n"
        banlist_text += f"   👮 Забанен: @{banned_by}\n"
        banlist_text += f"   📅 Дата: {ban_date_formatted}\n"
        banlist_text += f"   📝 Причина: {reason}\n\n"
    
    bot.reply_to(message, banlist_text)

@bot.message_handler(commands=['addadmin', 'appoint'])
def add_admin_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_main_admin(user_id, username):
        bot.reply_to(message, "❌ Только @RYBBKA_MACO может назначать администраторов.")
        return
    
    parts = message.text.split()
    
    if len(parts) != 2:
        bot.reply_to(message, "❌ Неправильный формат. Используй: /addadmin @username\nПример: /addadmin @ivanov")
        return
    
    target_username = parts[1].lstrip('@')
    
    cursor.execute('SELECT user_id FROM users WHERE username = ?', (target_username,))
    result = cursor.fetchone()
    
    if not result:
        bot.reply_to(message, f"❌ Пользователь @{target_username} не найден.")
        return
    
    target_user_id = result[0]
    
    if is_admin(target_user_id, target_username):
        bot.reply_to(message, f"❌ Пользователь @{target_username} уже является администратором.")
        return
    
    if target_user_id == user_id:
        bot.reply_to(message, "❌ Вы уже являетесь главным администратором.")
        return
    
    add_admin(target_user_id, target_username, username)
    
    try:
        bot.send_message(target_user_id, f"🎉 Поздравляем! Вас назначили администратором бота пользователем @{username}.\nТеперь вам доступны команды модерации.")
    except:
        pass
    
    bot.reply_to(message, f"✅ Пользователь @{target_username} назначен администратором.")

@bot.message_handler(commands=['removeadmin', 'demote'])
def remove_admin_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_main_admin(user_id, username):
        bot.reply_to(message, "❌ Только @RYBBKA_MACO может снимать администраторов.")
        return
    
    parts = message.text.split()
    
    if len(parts) != 2:
        bot.reply_to(message, "❌ Неправильный формат. Используй: /removeadmin @username\nПример: /removeadmin @ivanov")
        return
    
    target_username = parts[1].lstrip('@')
    
    cursor.execute('SELECT user_id FROM admins WHERE username = ?', (target_username,))
    result = cursor.fetchone()
    
    if not result:
        bot.reply_to(message, f"❌ Пользователь @{target_username} не является администратором.")
        return
    
    target_user_id = result[0]
    
    remove_admin(target_user_id)
    
    try:
        bot.send_message(target_user_id, f"ℹ️ Вы больше не являетесь администратором бота. Права снял пользователь @{username}.")
    except:
        pass
    
    bot.reply_to(message, f"✅ Пользователь @{target_username} снят с должности администратора.")

@bot.message_handler(commands=['adminlist', 'admins'])
def show_admin_list(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_admin(user_id, username):
        bot.reply_to(message, "❌ У вас нет прав для просмотра списка администраторов.")
        return
    
    cursor.execute('''
        SELECT username, appointed_by, appointed_date 
        FROM admins 
        ORDER BY appointed_date
    ''')
    admin_list = cursor.fetchall()
    
    admin_text = "👑 **СПИСОК АДМИНИСТРАТОРОВ**\n\n"
    
    admin_text += "👑 **Главный администратор:**\n"
    admin_text += f"• @RYBBKA_MACO (создатель)\n\n"
    
    if admin_list:
        admin_text += "🔧 **Назначенные администраторы:**\n"
        for i, (admin_username, appointed_by, appointed_date) in enumerate(admin_list, 1):
            date_formatted = datetime.fromisoformat(appointed_date).strftime("%d.%m.%Y")
            admin_text += f"{i}. @{admin_username}\n"
            admin_text += f"   📅 Назначен: {date_formatted}\n"
            admin_text += f"   👤 Назначил: @{appointed_by}\n\n"
    else:
        admin_text += "📝 Назначенных администраторов нет.\n\n"
    
    if is_main_admin(user_id, username):
        admin_text += "💡 Используйте:\n/addadmin @username - назначить админа\n/removeadmin @username - снять админа"
    
    bot.reply_to(message, admin_text)

@bot.message_handler(commands=['myadmin', 'myrights'])
def show_my_rights(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    rights_text = "👤 **ВАШИ ПРАВА ДОСТУПА**\n\n"
    
    if is_main_admin(user_id, username):
        rights_text += "👑 **Главный администратор**\n"
        rights_text += "• Полный доступ ко всем командам\n"
        rights_text += "• Назначение и снятие администраторов\n"
        rights_text += "• Бан и разбан пользователей\n"
        rights_text += "• Бесконечный баланс Драго\n"
        rights_text += "• Просмотр всей статистики\n"
    elif is_admin(user_id, username):
        rights_text += "🔧 **Администратор**\n"
        rights_text += "• Бан и разбан пользователей\n"
        rights_text += "• Просмотр списка банов\n"
        rights_text += "• Просмотр списка администраторов\n"
        rights_text += "• Просмотр всей статистики\n"
    else:
        rights_text += "👤 **Пользователь**\n"
        rights_text += "• Основные команды экономики\n"
        rights_text += "• Просмотр общей статистики\n"
    
    bot.reply_to(message, rights_text)

print("Бот запущен и слушает сообщения...")
bot.infinity_polling()

