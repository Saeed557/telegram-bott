# Then put your bot code like this:
# -*- coding: utf-8 -*-
import telebot
from telebot import types
import os
import time
import threading
import requests
from requests import post, get
from rich.console import Console
import concurrent.futures
import json
import random
import sys
import re
import datetime


# Initialize bot
BOT_TOKEN = 8557970225:AAEiKaAJH5vQEndFFNba2-GWDkl4TNxG6Vo
# Subscription system files
SUBSCRIPTION_FILE = "subscribed_users.txt"
ADMINS = [7887268414 , 6634996616]  # Replace with your admin ID 

# Load subscribed users
def load_subscribed_users():
    try:
        with open(SUBSCRIPTION_FILE, "r") as f:
            users = {}
            for line in f:
                user_id, expiry_date = line.strip().split(',')
                users[int(user_id)] = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
            return users
    except FileNotFoundError:
        return {}

# Save subscribed users
def save_subscribed_users(users):
    with open(SUBSCRIPTION_FILE, "w") as f:
        for user_id, expiry_date in users.items():
            f.write(f"{user_id},{expiry_date.strftime('%Y-%m-%d')}\n")

# Initialize subscribed users
subscribed_users = load_subscribed_users()

# Check subscription status
def is_subscribed(user_id):
    return user_id in ADMINS or (user_id in subscribed_users and subscribed_users[user_id] >= datetime.date.today())

# Subscription check background thread
def check_subscriptions():
    while True:
        today = datetime.date.today()

        # Notify users 3 days before expiration
        expiring_soon = [uid for uid, date in subscribed_users.items() 
                        if date == today + datetime.timedelta(days=3)]

        for user_id in expiring_soon:
            try:
                bot.send_message(user_id, "⚠️ Your subscription will expire in 3 days! Please contact the admin to renew.")
            except:
                pass

        # Remove expired users
        expired_users = [uid for uid, date in subscribed_users.items() 
                        if date < today]

        for user_id in expired_users:
            try:
                bot.send_message(user_id, "❌ Your subscription has expired! Please contact the admin to renew.")
                del subscribed_users[user_id]
            except:
                pass

        save_subscribed_users(users)
        time.sleep(86400)  # Check every 24 hours

# Start subscription check thread
threading.Thread(target=check_subscriptions, daemon=True).start()

# Admin commands
@bot.message_handler(commands=['admin'])
def handle_admin(message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        bot.reply_to(message, "❌ You don't have permission to access this!")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add Subscriber", "🗑 Remove Subscriber")
    markup.add("📋 List Subscribers", "🔙 Back")

    bot.send_message(user_id, "👨‍💻 Admin Control Panel:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "➕ Add Subscriber" and message.from_user.id in ADMINS)
def add_user_step1(message):
    msg = bot.send_message(message.chat.id, "📝 Enter the user ID:")
    bot.register_next_step_handler(msg, add_user_step2)

def add_user_step2(message):
    try:
        user_id = int(message.text)
        msg = bot.send_message(message.chat.id, "📅 Enter subscription duration in days:")
        bot.register_next_step_handler(msg, lambda m: add_user_step3(m, user_id))
    except ValueError:
        bot.send_message(message.chat.id, "❌ User ID must be a number!")

def add_user_step3(message, user_id):
    try:
        days = int(message.text)
        expiry_date = datetime.date.today() + datetime.timedelta(days=days)
        subscribed_users[user_id] = expiry_date
        save_subscribed_users(subscribed_users)
        bot.send_message(message.chat.id, f"✅ Subscription activated for user {user_id} until {expiry_date}")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Subscription duration must be a number!")

@bot.message_handler(func=lambda message: message.text == "🗑 Remove Subscriber" and message.from_user.id in ADMINS)
def remove_user_step1(message):
    msg = bot.send_message(message.chat.id, "📝 Enter the user ID to remove:")
    bot.register_next_step_handler(msg, remove_user_step2)

def remove_user_step2(message):
    try:
        user_id = int(message.text)
        if user_id in subscribed_users:
            del subscribed_users[user_id]
            save_subscribed_users(subscribed_users)
            bot.send_message(message.chat.id, f"✅ User {user_id} removed successfully")
        else:
            bot.send_message(message.chat.id, "❌ This user is not in the list!")
    except ValueError:
        bot.send_message(message.chat.id, "❌ User ID must be a number!")

@bot.message_handler(func=lambda message: message.text == "📋 List Subscribers" and message.from_user.id in ADMINS)
def list_users(message):
    if not subscribed_users:
        bot.send_message(message.chat.id, "📭 No subscribers currently!")
        return

    users_list = ["📋 Subscribers List:"]
    today = datetime.date.today()

    for user_id, expiry_date in subscribed_users.items():
        status = "✅ Active" if expiry_date >= today else "❌ Expired"
        users_list.append(f"🔹 {user_id} - Until {expiry_date} ({status})")

    bot.send_message(message.chat.id, "\n".join(users_list))

# Original bot variables and functions
user_states = {}
user_data = {}
session_cache = {}
active_reports = {}

class UserState:
    IDLE = 'idle'
    AWAITING_TARGET_ID = 'awaiting_target_id'
    AWAITING_REPORT_TYPE = 'awaiting_report_type'
    AWAITING_REPORTS_PER_SESSION = 'awaiting_reports_per_session'
    AWAITING_SLEEP_TIME = 'awaiting_sleep_time'
    REPORTING = 'reporting'
    AWAITING_SESSIONS_INPUT = 'awaiting_sessions_input'
    AWAITING_TARGET_IDS_ALL = 'awaiting_target_ids_all'
    AWAITING_REPORT_TYPE_FOR_MULTI_TARGET = 'awaiting_report_type_for_multi_target'
    AWAITING_NEW_REPORT_TYPE_DURING_PROCESS = 'awaiting_new_report_type_during_process'
    AWAITING_REPORT_COUNT_FOR_SELECT = 'awaiting_report_count_for_select'
    AWAITING_MULTIPLE_REPORT_TYPES_SELECTION = 'awaiting_multiple_report_types_selection'
    AWAITING_MULTI_TARGET_REPORT_TYPE_CHANGE = 'awaiting_multi_target_report_type_change'
    AWAITING_MULTI_REPORT_TYPES_CHANGE = 'awaiting_multi_report_types_change'

report_options = {
    1: ("Spam", "Report spam content or behavior"),
    2: ("Self", "Report self-harm content"),
    3: ("Drugs", "Report drug-related content"),
    4: ("Nudity", "Report nudity content"),
    5: ("Violence", "Report violent content"),
    6: ("Hate", "Report hate speech"),
    7: ("Harassment", "Report harassment"),
    8: ("Impersonation", "Report impersonation"),
    11: ("Underage", "User is under 13"),
    12: ("GunSelling", "Selling firearms or weapons"),
}

reason_ids = {
    "Spam": 1,
    "Self": 2,
    "Drugs": 3,
    "Nudity": 4,
    "Violence": 5,
    "Hate": 6,
    "Harassment": 7,
    "Impersonation": 8,
    "Underage": 11,
    "GunSelling": 12,
}

def send_animated_gif(user_id, text):
    try:
        with open("reporting.gif", "rb") as gif_file:
            msg = bot.send_animation(
                user_id,
                gif_file,
                caption=f" {text}",
                parse_mode="HTML"
            )
            return msg.message_id
    except Exception as e:
        console.print(f"[red]Error sending GIF: {e}[/red]")
        return None

def delete_previous_message(user_id, message_id):
    try:
        bot.delete_message(user_id, message_id)
    except Exception as e:
        console.print(f"[red]Error deleting message: {e}[/red]")

def log_user_to_file(user_id, username):
    try:
        with open("users.txt", "a", encoding="utf-8") as f:
            f.write(f"{user_id} - {username}\n")
    except Exception as e:
        console.print(f"[red]Error logging user to file: {str(e)}[/red]")

def get_csrf_token(sessionid):
    try:
        if sessionid in session_cache:
            return session_cache[sessionid]

        r1 = requests.get(
            "https://www.instagram.com/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
            },
            cookies={"sessionid": sessionid},
            timeout=10
        )
        if "csrftoken" in r1.cookies:
            session_cache[sessionid] = r1.cookies["csrftoken"]
            return r1.cookies["csrftoken"]
        else:
            return None
    except Exception as e:
        return None

def validate_session(sessionid):
    try:
        csrf = get_csrf_token(sessionid)
        if csrf:
            test_req = requests.get(
                "https://www.instagram.com/accounts/edit/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
                },
                cookies={"sessionid": sessionid},
                timeout=10,
                allow_redirects=False
            )
            return test_req.status_code == 200, csrf
        return False, None
    except Exception as e:
        return False, None

def filter_sessions(sessions, user_id, callback_message_id):
    valid_sessions = []
    invalid_sessions = []
    total = len(sessions)

    progress_message = bot.send_message(user_id, f"Checking sessions... ({0}/{total})")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_session = {executor.submit(validate_session, session): session for session in sessions}

        completed = 0
        for future in concurrent.futures.as_completed(future_to_session):
            session = future_to_session[future]
            try:
                is_valid, csrf = future.result()
                if is_valid:
                    valid_sessions.append(session)
                    session_cache[session] = csrf
                else:
                    invalid_sessions.append(session)
            except Exception as e:
                invalid_sessions.append(session)

            completed += 1
            try:
                bot.edit_message_text(
                    f"Checking sessions... ({completed}/{total})",
                    user_id,
                    progress_message.message_id
                )
            except:
                pass

    result_message = f"Found {len(valid_sessions)} valid sessions\nExcluded {len(invalid_sessions)} invalid sessions"

    try:
        bot.edit_message_text(result_message, user_id, progress_message.message_id)
    except:
        bot.send_message(user_id, result_message)

    return valid_sessions

def report_instagram(target_id, sessionid, csrftoken, reportType):
    try:
        r3 = requests.post(
            f"https://i.instagram.com/users/{target_id}/flag/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
                "Host": "i.instagram.com",
                "cookie": f"sessionid={sessionid}",
                "X-CSRFToken": csrftoken,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
            data=f'source_name=&reason_id={reportType}&frx_context=',
            allow_redirects=False,
            timeout=15
        )
        return r3.status_code == 200 or r3.status_code == 302
    except Exception as e:
        return False

def get_random_report_type():
    report_type_id = random.choice(list(report_options.keys()))
    report_type, _ = report_options[report_type_id]
    reason_id = reason_ids[report_type]
    return report_type, reason_id

def create_sessions_list(user_id, sessions_text):
    sessions = [s.strip() for s in sessions_text.strip().split('\n') if s.strip()]

    if not sessions:
        bot.send_message(user_id, "No valid sessions provided!")
        return False

    with open("sessions.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sessions))

    bot.send_message(user_id, f"Saved {len(sessions)} sessions to sessions.txt")
    return True

def get_user_identifier(user):
    return f"{user.id} - {user.username or 'Unknown'}"

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    log_user_to_file(user_id, username)

    if user_id in ADMINS:
        handle_admin(message)
        return

    if not is_subscribed(user_id):
        bot.send_message(
            user_id,
            "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin"
        )
        return

    bot.send_message(
        user_id,
        "Welcome to Instagram Report Bot\n\n"
        "Available commands:\n"
        "/report - Start reporting on a single target\n"
        "/reportall - Start reporting on multiple targets\n"
        "/select_reports - Select multiple report types for a single target\n"
        "/create_sessions - Create sessions list\n"
        "/stop - Stop current process\n"
        "/status - Check status\n\n"
        "Send sessions.txt file or use /report to begin"
    )
    user_states[user_id] = UserState.IDLE

@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    help_text = (
        "<b>Help Guide</b>\n\n"
        "1. Send sessions.txt file\n"
        "2. Use /report to start single target reporting\n"
        "3. Use /reportall to start multi-target reporting\n"
        "4. Use /select_reports to choose multiple report types for a single target\n"
        "5. Enter target ID(s)\n"
        "6. Choose report type(s)\n"
        "7. Set reporting parameters\n\n"
        "<b>Report Types:</b>\n"
        "1 - Spam\n2 - Self-harm\n3 - Drugs\n"
        "4 - Nudity\n5 - Violence\n6 - Hate\n"
        "7 - Harassment\n8 - Impersonation\n"
        "11 - Underage\n12 - Gun Selling\n\n"
        "Use /stop to cancel anytime"
    )
    bot.send_message(user_id, help_text, parse_mode="HTML")

@bot.message_handler(commands=['report'])
def handle_report(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if user_id in user_data and 'valid_sessions' in user_data[user_id] and user_data[user_id]['valid_sessions']:
        if user_id in active_reports:
            active_reports.pop(user_id, None)
        user_data[user_id]['good_count'] = 0
        user_data[user_id]['bad_count'] = 0

        bot.send_message(user_id, "Enter target ID:")
        user_states[user_id] = UserState.AWAITING_TARGET_ID
        user_data[user_id]['multi_report_types_mode'] = False
        user_data[user_id]['multi_target_mode'] = False
    else:
        bot.send_message(user_id, "Please send sessions.txt file first!")
        user_states[user_id] = UserState.IDLE

@bot.message_handler(commands=['reportall'])
def handle_report_all(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if user_id in user_data and 'valid_sessions' in user_data[user_id] and user_data[user_id]['valid_sessions']:
        if user_id in active_reports:
            active_reports.pop(user_id, None)
        user_data[user_id]['good_count'] = 0
        user_data[user_id]['bad_count'] = 0

        bot.send_message(user_id, "Please send the list of target IDs, one ID per line:")
        user_states[user_id] = UserState.AWAITING_TARGET_IDS_ALL
        user_data[user_id]['multi_target_mode'] = True
        user_data[user_id]['multi_report_types_mode'] = False
    else:
        bot.send_message(user_id, "Please send sessions.txt file first!")
        user_states[user_id] = UserState.IDLE

@bot.message_handler(commands=['select_reports'])
def handle_select_reports(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if user_id in user_data and 'valid_sessions' in user_data[user_id] and user_data[user_id]['valid_sessions']:
        if user_id in active_reports:
            active_reports.pop(user_id, None)
        user_data[user_id]['good_count'] = 0
        user_data[user_id]['bad_count'] = 0

        bot.send_message(user_id, "Enter target ID:")
        user_states[user_id] = UserState.AWAITING_TARGET_ID
        user_data[user_id]['multi_report_types_mode'] = True
        user_data[user_id]['multi_target_mode'] = False
    else:
        bot.send_message(user_id, "Please send sessions.txt file first!")
        user_states[user_id] = UserState.IDLE

@bot.message_handler(commands=['create_sessions'])
def handle_create_sessions(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    bot.send_message(
        user_id,
        "<b>Create Sessions List</b>\n\n"
        "Enter sessions, one per line:",
        parse_mode="HTML"
    )
    user_states[user_id] = UserState.AWAITING_SESSIONS_INPUT

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if user_id in active_reports and (active_reports[user_id]["running"] or active_reports[user_id].get("paused")):
        active_reports[user_id]["running"] = False
        active_reports[user_id]["paused"] = False
        active_reports[user_id]['pause_event'].set()

        if "gif_message_id" in active_reports[user_id]:
            delete_previous_message(user_id, active_reports[user_id]["gif_message_id"])

        bot.send_message(user_id, "Process stopping...")
    else:
        bot.send_message(user_id, "No active process to stop")

@bot.message_handler(commands=['status'])
def handle_status(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if user_id in active_reports and active_reports[user_id]['running']:
        stats = (
            f"<b>Current Status</b>\n\n"
            f"Successful: <b>{active_reports[user_id]['good_count']}</b>\n"
            f"Failed: <b>{active_reports[user_id]['bad_count']}</b>\n"
            f"Running: <b>Yes</b>\n\n"
            f"<i>Use /stop to cancel</i>"
        )
        bot.send_message(user_id, stats, parse_mode="HTML")
    elif user_id in active_reports and active_reports[user_id].get('paused'):
        stats = (
            f"<b>Current Status</b>\n\n"
            f"Successful: <b>{active_reports[user_id]['good_count']}</b>\n"
            f"Failed: <b>{active_reports[user_id]['bad_count']}</b>\n"
            f"Running: <b>No (Paused)</b>\n\n"
            f"<i>Use /resume to continue or /stop to end completely</i>"
        )
        bot.send_message(user_id, stats, parse_mode="HTML")
    else:
        bot.send_message(user_id, "No active process running")

@bot.message_handler(commands=['resume'])
def handle_resume(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if user_id in active_reports and active_reports[user_id].get('paused'):
        if user_id not in user_data or 'valid_sessions' not in user_data[user_id] or not user_data[user_id]['valid_sessions']:
            bot.send_message(user_id, "Cannot resume. Session data not found or no valid sessions. Please start a new process.")
            if user_id in active_reports:
                active_reports.pop(user_id, None)
            user_states[user_id] = UserState.IDLE
            return

        active_reports[user_id]['running'] = True
        active_reports[user_id]['paused'] = False
        active_reports[user_id]['pause_event'].set()

        threading.Thread(target=reporting_thread, 
                       args=(user_id, 
                            user_data[user_id]['target_ids'], 
                            user_data[user_id]['sleep_time'],
                            user_data[user_id].get('reports_per_session', float('inf')),
                            user_data[user_id]['valid_sessions'],
                            active_reports[user_id]['status_message_id'],
                            active_reports[user_id].get('is_multi_target', False),
                            active_reports[user_id].get('is_multi_report_types', False),
                            active_reports[user_id].get('selected_report_types', []))).start()

        bot.send_message(user_id, "Reporting resumed.")
    else:
        bot.send_message(user_id, "No paused process to resume.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if message.document.file_name.lower() != 'sessions.txt':
        bot.send_message(user_id, "Please send sessions.txt file only")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    sessions = downloaded_file.decode('utf-8').splitlines()

    if not sessions:
        bot.send_message(user_id, "Sessions file is empty!")
        return

    if user_id not in user_data:
        user_data[user_id] = {}

    valid_sessions = filter_sessions(sessions, user_id, 0)

    if not valid_sessions:
        bot.send_message(user_id, "No valid sessions found!")
        return

    user_data[user_id]['valid_sessions'] = valid_sessions
    bot.send_message(user_id, f"Loaded {len(valid_sessions)} valid sessions\nUse /report, /reportall or /select_reports to start")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.AWAITING_SESSIONS_INPUT)
def handle_sessions_input(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    if create_sessions_list(user_id, message.text):
        with open("sessions.txt", "r", encoding="utf-8") as f:
            sessions = [line.strip() for line in f.readlines()]

        valid_sessions = filter_sessions(sessions, user_id, 0)

        if user_id not in user_data:
            user_data[user_id] = {}

        user_data[user_id]['valid_sessions'] = valid_sessions
        user_states[user_id] = UserState.IDLE

        if valid_sessions:
            bot.send_message(user_id, f"Loaded {len(valid_sessions)} valid sessions\nUse /report, /reportall or /select_reports to start")
        else:
            bot.send_message(user_id, "No valid sessions found")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.AWAITING_TARGET_ID)
def handle_target_id_input(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    target_id = message.text.strip()

    if not target_id.isdigit():
        bot.send_message(user_id, "Invalid target ID! Please enter a numeric ID.")
        return

    if user_id not in user_data:
        user_data[user_id] = {}

    user_data[user_id]['target_ids'] = [{'id': target_id, 'report_type': None, 'reason_id': None}]
    user_data[user_id]['current_target_idx'] = 0

    if user_data[user_id].get('multi_report_types_mode', False):
        bot.send_message(user_id, "How many report types do you want to select?")
        user_states[user_id] = UserState.AWAITING_REPORT_COUNT_FOR_SELECT
    else:
        markup = types.InlineKeyboardMarkup()
        for key, (value, desc) in report_options.items():
            markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", callback_data=f"report_type_{key}"))

        markup.add(types.InlineKeyboardButton("Random - Varying report types", callback_data="report_type_random"))

        sent_message = bot.send_message(user_id, "Choose report type:", reply_markup=markup)
        user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later
        user_states[user_id] = UserState.AWAITING_REPORT_TYPE

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.AWAITING_REPORT_COUNT_FOR_SELECT)
def handle_report_count_for_select(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    try:
        count = int(message.text.strip())
        if count <= 0 or count > len(report_options):
            bot.send_message(user_id, f"Please enter a positive number up to {len(report_options)}.")
            return
        user_data[user_id]['selected_report_types_count'] = count
        user_data[user_id]['selected_report_types'] = []
        user_data[user_id]['current_selection_idx'] = 0
        ask_for_next_report_type_selection(user_id)
    except ValueError:
        bot.send_message(user_id, "Invalid input. Please enter a number.")

def ask_for_next_report_type_selection(user_id):
    count_to_select = user_data[user_id]['selected_report_types_count']
    current_selection_idx = user_data[user_id]['current_selection_idx']

    if current_selection_idx < count_to_select:
        markup = types.InlineKeyboardMarkup()
        for key, (value, desc) in report_options.items():
            if {'report_type': value, 'reason_id': key} not in user_data[user_id]['selected_report_types']:
                markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", callback_data=f"select_multi_report_type_{key}"))

        sent_message = bot.send_message(user_id, f"Select report type {current_selection_idx + 1} of {count_to_select}:", reply_markup=markup)
        user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later
        user_states[user_id] = UserState.AWAITING_MULTIPLE_REPORT_TYPES_SELECTION
    else:
        bot.send_message(user_id, "Enter delay between reports (seconds):")
        user_states[user_id] = UserState.AWAITING_SLEEP_TIME

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_multi_report_type_'))
def handle_select_multi_report_type(call):
    user_id = call.from_user.id

    if user_states.get(user_id) not in [UserState.AWAITING_MULTIPLE_REPORT_TYPES_SELECTION, UserState.AWAITING_MULTI_REPORT_TYPES_CHANGE]:
        return

    # Delete the message with the options after selection
    if 'last_options_message_id' in user_data[user_id]:
        delete_previous_message(user_id, user_data[user_id]['last_options_message_id'])
        del user_data[user_id]['last_options_message_id']

    report_id = int(call.data.replace('select_multi_report_type_', ''))
    report_type, _ = report_options[report_id]
    reason_id = report_id

    if user_states.get(user_id) == UserState.AWAITING_MULTI_REPORT_TYPES_CHANGE:
        if 'temp_new_selected_report_types' not in user_data[user_id]:
            user_data[user_id]['temp_new_selected_report_types'] = []

        user_data[user_id]['temp_new_selected_report_types'].append({'report_type': report_type, 'reason_id': reason_id})
        user_data[user_id]['current_selection_idx'] += 1
        bot.answer_callback_query(call.id, f"Selected: {report_type}")
        ask_for_next_report_type_selection_for_change(user_id)
    else:
        user_data[user_id]['selected_report_types'].append({'report_type': report_type, 'reason_id': reason_id})
        user_data[user_id]['current_selection_idx'] += 1
        bot.answer_callback_query(call.id, f"Selected: {report_type}")
        ask_for_next_report_type_selection(user_id)

def ask_for_next_report_type_selection_for_change(user_id):
    count_to_select = user_data[user_id]['selected_report_types_count']
    current_selection_idx = user_data[user_id]['current_selection_idx']

    if current_selection_idx < count_to_select:
        markup = types.InlineKeyboardMarkup()
        for key, (value, desc) in report_options.items():
            if {'report_type': value, 'reason_id': key} not in user_data[user_id]['temp_new_selected_report_types']:
                markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", callback_data=f"select_multi_report_type_{key}"))

        sent_message = bot.send_message(user_id, f"Select new report type {current_selection_idx + 1} of {count_to_select}:", reply_markup=markup)
        user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later
        user_states[user_id] = UserState.AWAITING_MULTI_REPORT_TYPES_CHANGE
    else:
        bot.send_message(user_id, "All report types selected. Resuming reporting...")

        # Update the selected report types
        user_data[user_id]['selected_report_types'] = user_data[user_id]['temp_new_selected_report_types']
        del user_data[user_id]['temp_new_selected_report_types']

        # Resume reporting
        if active_reports[user_id].get('paused'):
            active_reports[user_id]['running'] = True
            active_reports[user_id]['paused'] = False
            active_reports[user_id]['pause_event'].set()

            threading.Thread(target=reporting_thread, 
                           args=(user_id, 
                                user_data[user_id]['target_ids'], 
                                user_data[user_id]['sleep_time'],
                                user_data[user_id].get('reports_per_session', float('inf')),
                                user_data[user_id]['valid_sessions'],
                                active_reports[user_id]['status_message_id'],
                                active_reports[user_id].get('is_multi_target', False),
                                active_reports[user_id].get('is_multi_report_types', False),
                                user_data[user_id]['selected_report_types'])).start()

        user_states[user_id] = UserState.REPORTING

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.AWAITING_TARGET_IDS_ALL)
def handle_target_ids_all_input(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    target_ids_raw = message.text.strip().split('\n')

    target_ids_list = []
    for tid in target_ids_raw:
        tid = tid.strip()
        if tid.isdigit():
            target_ids_list.append({'id': tid, 'report_type': None, 'reason_id': None})

    if not target_ids_list:
        bot.send_message(user_id, "No valid target IDs found. Please enter numeric IDs, one per line.")
        return

    if user_id not in user_data:
        user_data[user_id] = {}

    user_data[user_id]['target_ids'] = target_ids_list
    user_data[user_id]['current_target_idx'] = 0
    user_data[user_id]['multi_target_mode'] = True

    ask_for_next_target_report_type(user_id)

def ask_for_next_target_report_type(user_id):
    current_target_idx = user_data[user_id]['current_target_idx']
    target_ids = user_data[user_id]['target_ids']

    if current_target_idx < len(target_ids):
        target_id = target_ids[current_target_idx]['id']
        markup = types.InlineKeyboardMarkup()
        for key, (value, desc) in report_options.items():
            markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", callback_data=f"report_type_multi_{key}_{target_id}"))

        markup.add(types.InlineKeyboardButton("Random - Varying report types", callback_data="report_type_multi_random"))

        sent_message = bot.send_message(user_id, f"Choose report type for target ID: <b>{target_id}</b>", reply_markup=markup, parse_mode="HTML")
        user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later
        user_states[user_id] = UserState.AWAITING_REPORT_TYPE_FOR_MULTI_TARGET
    else:
        if len(user_data[user_id]['valid_sessions']) > 1:
            bot.send_message(user_id, "Enter reports per session (or 'inf' for unlimited):")
            user_states[user_id] = UserState.AWAITING_REPORTS_PER_SESSION
        else:
            bot.send_message(user_id, "Enter delay between reports (seconds):")
            user_states[user_id] = UserState.AWAITING_SLEEP_TIME

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_type_multi_'))
def handle_report_type_multi_callback(call):
    user_id = call.from_user.id

    if user_states.get(user_id) != UserState.AWAITING_REPORT_TYPE_FOR_MULTI_TARGET:
        return

    # Delete the message with the options after selection
    if 'last_options_message_id' in user_data[user_id]:
        delete_previous_message(user_id, user_data[user_id]['last_options_message_id'])
        del user_data[user_id]['last_options_message_id']

    parts = call.data.split('_')
    report_type_data = parts[3]

    current_target_idx = user_data[user_id]['current_target_idx']
    target_ids_list = user_data[user_id]['target_ids']

    if report_type_data == 'random':
        report_type, reason_id = get_random_report_type()
        user_data[user_id]['target_ids'][current_target_idx]['use_random_reports'] = True
    else:
        report_id = int(report_type_data)
        report_type, _ = report_options[report_id]
        reason_id = report_id
        user_data[user_id]['target_ids'][current_target_idx]['use_random_reports'] = False

    user_data[user_id]['target_ids'][current_target_idx]['report_type'] = report_type
    user_data[user_id]['target_ids'][current_target_idx]['reason_id'] = reason_id

    bot.answer_callback_query(call.id, f"Selected for {target_ids_list[current_target_idx]['id']}: {report_type}")

    user_data[user_id]['current_target_idx'] += 1
    ask_for_next_target_report_type(user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('report_type_') and not call.data.startswith('report_type_multi_'))
def handle_report_type_callback(call):
    user_id = call.from_user.id

    if user_states.get(user_id) != UserState.AWAITING_REPORT_TYPE:
        return

    # Delete the message with the options after selection
    if 'last_options_message_id' in user_data[user_id]:
        delete_previous_message(user_id, user_data[user_id]['last_options_message_id'])
        del user_data[user_id]['last_options_message_id']

    report_type_data = call.data.replace('report_type_', '')

    if report_type_data == 'random':
        user_data[user_id]['target_ids'][0]['use_random_reports'] = True
        report_type, reason_id = get_random_report_type()
    else:
        report_id = int(report_type_data)
        report_type, _ = report_options[report_id]
        reason_id = report_id
        user_data[user_id]['target_ids'][0]['use_random_reports'] = False

    user_data[user_id]['target_ids'][0]['report_type'] = report_type
    user_data[user_id]['target_ids'][0]['reason_id'] = reason_id

    # Send a new message confirming the selection, instead of editing the old one
    bot.send_message(
        user_id,
        f"Selected: {report_type}{' (random)' if report_type_data == 'random' else ''}"
    )

    if len(user_data[user_id]['valid_sessions']) > 1:
        bot.send_message(user_id, "Enter reports per session (or 'inf' for unlimited):")
        user_states[user_id] = UserState.AWAITING_REPORTS_PER_SESSION
    else:
        bot.send_message(user_id, "Enter delay between reports (seconds):")
        user_states[user_id] = UserState.AWAITING_SLEEP_TIME

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.AWAITING_REPORTS_PER_SESSION)
def handle_reports_per_session_input(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    text = message.text.strip().lower()

    if text == 'inf':
        reports_per_session = float('inf')
    else:
        try:
            reports_per_session = int(text)
            if reports_per_session <= 0:
                bot.send_message(user_id, "Enter positive number or 'inf':")
                return
        except ValueError:
            bot.send_message(user_id, "Invalid input. Enter number or 'inf':")
            return

    user_data[user_id]['reports_per_session'] = reports_per_session
    bot.send_message(user_id, "Enter delay between reports (seconds):")
    user_states[user_id] = UserState.AWAITING_SLEEP_TIME

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == UserState.AWAITING_SLEEP_TIME)
def handle_sleep_time_input(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        bot.send_message(user_id, "Welcome to the Report Bot!\n"
            "This bot is for subscribers only.\n\n"
            "To subscribe, please contact the admin")
        return

    text = message.text.strip()

    try:
        sleep_time = float(text)
        if sleep_time < 0:
            bot.send_message(user_id, "Enter positive number:")
            return
    except ValueError:
        bot.send_message(user_id, "Invalid input. Enter number:")
        return

    user_data[user_id]['sleep_time'] = sleep_time

    target_ids_info = user_data[user_id]['target_ids']
    is_multi_target = user_data[user_id].get('multi_target_mode', False)
    is_multi_report_types = user_data[user_id].get('multi_report_types_mode', False)

    target_display = ""
    report_type_display = ""

    if is_multi_target:
        target_summary_lines = []
        for target_info in target_ids_info:
            target_id = target_info['id']
            report_type = target_info['report_type']
            use_random = target_info.get('use_random_reports', False)
            target_summary_lines.append(f"  - <b>{target_id}</b>: {report_type}{' (random)' if use_random else ''}")
        # FIXED: Properly join lines with newline characters
        joined_lines = "\n".join(target_summary_lines)
        target_display = f"Targets:\n{joined_lines}"
    else:
        target_id = target_ids_info[0]['id']
        target_display = f"Target ID: <b>{target_id}</b>"
        if is_multi_report_types:
            report_types_list = [rt['report_type'] for rt in user_data[user_id]['selected_report_types']]
            report_type_display = f"Report types: <b>{', '.join(report_types_list)}</b>"
        else:
            report_type = target_ids_info[0]['report_type']
            use_random = target_ids_info[0].get('use_random_reports', False)
            report_type_display = f"Report type: <b>{report_type}{' (random)' if use_random else ''}</b>"

    sessions_count = len(user_data[user_id]['valid_sessions'])

    reports_per_session_text = ""
    if 'reports_per_session' in user_data[user_id]:
        rps = user_data[user_id]['reports_per_session']
        reports_per_session_text = f"\nReports/session: <b>{rps if rps != float('inf') else 'unlimited'}</b>"

    summary = (
        f"<b>Summary</b>\n\n"
        f"{target_display}\n"
        f"{report_type_display}\n"
        f"Sessions: <b>{sessions_count}</b>{reports_per_session_text}\n"
        f"Delay: <b>{sleep_time} seconds</b>\n\n"
        f"Start reporting?"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Start", callback_data="confirm_report_start"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel_report")
    )

    bot.send_message(user_id, summary, reply_markup=markup, parse_mode="HTML")

def start_reporting_process(user_id):
    target_ids_info = user_data[user_id]['target_ids']
    sleep_time = user_data[user_id]['sleep_time']
    valid_sessions = user_data[user_id]['valid_sessions']
    reports_per_session = user_data[user_id].get('reports_per_session', float('inf'))
    is_multi_target = user_data[user_id].get('multi_target_mode', False)
    is_multi_report_types = user_data[user_id].get('multi_report_types_mode', False)
    selected_report_types = user_data[user_id].get('selected_report_types', [])

    is_resume = user_id in active_reports and active_reports[user_id].get('paused')

    if not is_resume:
        gif_message_id = send_animated_gif(user_id, f"Reporting in progress")
        status_message = bot.send_message(
            user_id, 
            "Starting reporting process...", 
            parse_mode="HTML"
        )
        status_message_id = status_message.message_id
        good_count = 0
        bad_count = 0
        current_target_idx = 0
        current_multi_report_type_idx = 0
        current_session_index = 0
        current_session = ''
        invalid_sessions = []
    else:
        gif_message_id = active_reports[user_id]['gif_message_id']
        status_message_id = active_reports[user_id]['status_message_id']
        good_count = active_reports[user_id]['good_count']
        bad_count = active_reports[user_id]['bad_count']
        current_target_idx = active_reports[user_id]['current_target_idx']
        current_multi_report_type_idx = active_reports[user_id]['current_multi_report_type_idx']
        current_session_index = active_reports[user_id]['current_session_index']
        current_session = active_reports[user_id]['current_session']
        invalid_sessions = active_reports[user_id]['invalid_sessions']

    active_reports[user_id] = {
        'running': True,
        'paused': False,
        'status_message_id': status_message_id,
        'gif_message_id': gif_message_id,
        'good_count': good_count,
        'bad_count': bad_count,
        'invalid_sessions': invalid_sessions,
        'current_session_index': current_session_index,
        'current_session': current_session,
        'current_target_idx': current_target_idx,
        'is_multi_target': is_multi_target,
        'is_multi_report_types': is_multi_report_types,
        'selected_report_types': selected_report_types,
        'current_multi_report_type_idx': current_multi_report_type_idx,
        'last_report_type_change': '',
        'pause_event': threading.Event()
    }
    active_reports[user_id]['pause_event'].set()

    threading.Thread(target=reporting_thread, args=(user_id, target_ids_info, sleep_time, reports_per_session, valid_sessions, status_message_id, is_multi_target, is_multi_report_types, selected_report_types)).start()

def reporting_thread(user_id, target_ids_info, sleep_time, reports_per_session, valid_sessions, message_id, is_multi_target, is_multi_report_types, selected_report_types):
    report_data = active_reports[user_id]
    good_count = report_data['good_count']
    bad_count = report_data['bad_count']
    invalid_sessions = report_data['invalid_sessions']
    multiple_sessions = len(valid_sessions) > 1
    last_update_time = time.time()
    update_interval = 2 # Interval for updating the status message

    try:
        while report_data['running']:
            report_data['pause_event'].wait()

            if not report_data['running']:
                break

            current_valid_sessions = list(valid_sessions)
            if report_data['current_session_index'] >= len(current_valid_sessions):
                report_data['current_session_index'] = 0

            for i in range(report_data['current_session_index'], len(current_valid_sessions)):
                sessionid = current_valid_sessions[i]

                if not report_data['running']:
                    break

                if sessionid in invalid_sessions:
                    continue

                report_data['current_session_index'] = i
                report_data['current_session'] = sessionid

                csrftoken = get_csrf_token(sessionid)
                if not csrftoken:
                    bad_count += 1
                    invalid_sessions.append(sessionid)
                    if sessionid in valid_sessions:
                        valid_sessions.remove(sessionid)

                    update_status_message(user_id, good_count, bad_count, i+1, len(valid_sessions), f"Session {sessionid[:8]}... is invalid")
                    continue

                session_success = 0
                report_counter = 0

                targets_to_report = target_ids_info
                target_idx_in_cycle = report_data['current_target_idx']
                multi_report_type_idx = report_data['current_multi_report_type_idx']

                while (reports_per_session == float('inf') or report_counter < reports_per_session) and report_data['running']:
                    report_data['pause_event'].wait()

                    if not report_data['running']:
                        break

                    if not targets_to_report:
                        break

                    current_target_info = targets_to_report[target_idx_in_cycle % len(targets_to_report)]
                    target_id = current_target_info['id']

                    current_report_type = ""
                    current_reason_id = 0
                    use_random_reports_for_target = False

                    if user_id in user_data and 'temp_new_multi_target_report_types' in user_data[user_id]:
                        new_target_report_types = user_data[user_id]['temp_new_multi_target_report_types']
                        for new_info in new_target_report_types:
                            for old_info in target_ids_info:
                                if old_info['id'] == new_info['id']:
                                    old_info.update(new_info)
                                    break
                        report_data['last_report_type_change'] = "Report types updated for all targets."
                        del user_data[user_id]['temp_new_multi_target_report_types']

                    if is_multi_report_types:
                        if user_id in user_data and 'temp_new_selected_report_types' in user_data[user_id]:
                            report_data['selected_report_types'] = user_data[user_id]['temp_new_selected_report_types']
                            selected_report_types = report_data['selected_report_types']
                            report_data['last_report_type_change'] = f"All report types changed to: {', '.join([rt['report_type'] for rt in selected_report_types])}"
                            del user_data[user_id]['temp_new_selected_report_types']
                            multi_report_type_idx = 0

                        selected_type_info = selected_report_types[multi_report_type_idx % len(selected_report_types)]
                        current_report_type = selected_type_info['report_type']
                        current_reason_id = selected_type_info['reason_id']
                    else:
                        use_random_reports_for_target = current_target_info.get('use_random_reports', False)
                        current_report_type = current_target_info['report_type']
                        current_reason_id = current_target_info['reason_id']

                        if user_id in user_data and 'temp_new_report_type' in user_data[user_id]:
                            new_report_type_info = user_data[user_id]['temp_new_report_type']
                            current_report_type = new_report_type_info['report_type']
                            current_reason_id = new_report_type_info['reason_id']
                            current_target_info.update(new_report_type_info)
                            current_target_info['use_random_reports'] = False
                            report_data['last_report_type_change'] = f"Report type changed to: {current_report_type}"
                            del user_data[user_id]['temp_new_report_type']

                        elif use_random_reports_for_target:
                            previous_report_type = current_report_type
                            current_report_type, current_reason_id = get_random_report_type()
                            report_data['last_report_type_change'] = f"Report type changed for {target_id}: {previous_report_type} -> {current_report_type}"
                        else:
                            report_data['last_report_type_change'] = ''

                    report_data['current_target_idx'] = target_idx_in_cycle % len(targets_to_report)
                    report_data['current_target_id'] = target_id
                    report_data['current_report_type_display'] = current_report_type
                    report_data['current_multi_report_type_idx'] = multi_report_type_idx % len(selected_report_types) if is_multi_report_types else 0

                    if report_instagram(target_id, sessionid, csrftoken, current_reason_id):
                        good_count += 1
                        session_success += 1
                    else:
                        bad_count += 1

                        is_valid, _ = validate_session(sessionid)
                        if not is_valid:
                            invalid_sessions.append(sessionid)
                            if sessionid in valid_sessions:
                                valid_sessions.remove(sessionid)
                            update_status_message(user_id, good_count, bad_count, i+1, len(valid_sessions), f"Session {sessionid[:8]}... expired")
                            break

                    if sleep_time > 0:
                        time.sleep(sleep_time)

                    report_counter += 1
                    target_idx_in_cycle += 1
                    if is_multi_report_types:
                        multi_report_type_idx += 1

                    # Update status message at regular intervals to keep it fresh
                    if time.time() - last_update_time > update_interval:
                        update_status_message(user_id, good_count, bad_count, i+1, len(valid_sessions))
                        last_update_time = time.time()

                if not report_data['running']:
                    break

                if reports_per_session != float('inf'):
                    update_status_message(user_id, good_count, bad_count, i+1, len(valid_sessions), f"Sent {session_success} reports from session {i+1}/{len(valid_sessions)}")
                else:
                    update_status_message(user_id, good_count, bad_count, i+1, len(valid_sessions), f"Session {i+1}/{len(valid_sessions)} completed a cycle")
                last_update_time = time.time()

            report_data['current_session_index'] = 0

            if not valid_sessions:
                update_status_message(user_id, good_count, bad_count, 0, 0, "No valid sessions remaining!")
                break

            if multiple_sessions and report_data['running']:
                update_status_message(
                    user_id, 
                    good_count, 
                    bad_count, 
                    1, 
                    len(valid_sessions), 
                    "Starting new cycle with sessions..."
                )
                time.sleep(3)
            elif report_data['running']:
                update_status_message(
                    user_id, 
                    good_count, 
                    bad_count, 
                    1, 
                    len(valid_sessions), 
                    "Continuing with single session..."
                )
                time.sleep(3)

        report_data['good_count'] = good_count
        report_data['bad_count'] = bad_count

    except Exception as e:
        error_message = f"Error during reporting: {str(e)}"
        try:
            bot.edit_message_text(
                error_message,
                user_id,
                message_id
            )
        except:
            bot.send_message(user_id, error_message)

    finally:
        if user_id in active_reports and not active_reports[user_id].get('paused'):
            final_target_display = ""
            final_report_type_display = ""

            if is_multi_target:
                final_target_display = "Targets:\n"
                for target_info in target_ids_info:
                    final_target_display += f"  - {target_info['id']} ({target_info['report_type']})\n"
            else:
                final_target_display = f"Target ID: {target_ids_info[0]['id']}"
                if is_multi_report_types:
                    report_types_list = [rt['report_type'] for rt in selected_report_types]
                    final_report_type_display = f"Report types: {', '.join(report_types_list)}"
                else:
                    final_report_type_display = f"Report type: {target_ids_info[0]['report_type']}"

            final_message = (
                f"<b>Final Report</b>\n\n"
                f"Successful reports: <b>{good_count}</b>\n"
                f"Failed reports: <b>{bad_count}</b>\n"
                f"Wait time: <b>{sleep_time} seconds</b>\n"
                f"{final_target_display}\n"
                f"{final_report_type_display}\n\n"
                f"<b>Process completed!</b>"
            )

            try:
                bot.edit_message_text(
                    final_message,
                    user_id,
                    message_id,
                    parse_mode="HTML"
                )
            except:
                bot.send_message(user_id, final_message, parse_mode="HTML")

            user_states[user_id] = UserState.IDLE
            active_reports.pop(user_id, None)
            if user_id in user_data and 'valid_sessions' in user_data[user_id]:
                del user_data[user_id]['valid_sessions']

def update_status_message(user_id, good_count, bad_count, current_session_idx, total_sessions, additional_info=None):
    if user_id not in active_reports:
        return

    report_data = active_reports[user_id]
    current_session = report_data.get('current_session', '')
    session_display = current_session[:8] + "......" if current_session else "None"

    is_multi_target = report_data.get('is_multi_target', False)
    is_multi_report_types = report_data.get('is_multi_report_types', False)
    current_target_id = report_data.get('current_target_id', 'Unknown')
    current_report_type_display = report_data.get('current_report_type_display', 'Unknown')
    report_type_change = report_data.get('last_report_type_change', '')

    target_info_line = ""
    if is_multi_target:
        target_info_line = f"Current Target: <b>{current_target_id}</b>\nReport type: <b>{current_report_type_display}</b>\n"
    elif is_multi_report_types:
        target_info_line = f"Target ID: <b>{current_target_id}</b>\nReport type: <b>{current_report_type_display}</b>\n"
    else:
        target_info_line = f"Target ID: <b>{current_target_id}</b>\nReport type: <b>{current_report_type_display}</b>\n"

    status_text = (
        f"<b>Reporting Status</b>\n\n"
        f"Successful: <b>{good_count}</b>\n"
        f"Failed: <b>{bad_count}</b>\n"
        f"Current session: <b>{session_display}</b>\n"
        f"{target_info_line}"
    )

    if total_sessions > 0:
        status_text += f"Session progress: <b>{current_session_idx}/{total_sessions}</b>\n"

    if report_type_change:
        status_text += f"<i>{report_type_change}</i>\n"

    if additional_info:
        status_text += f"\n<i>{additional_info}</i>\n"

    markup = types.InlineKeyboardMarkup()
    if report_data['running']:
        markup.add(types.InlineKeyboardButton("Pause", callback_data="pause_reporting"))
        markup.add(types.InlineKeyboardButton("Change Report Type", callback_data="change_report_type_mid_process"))
    elif report_data.get('paused'):
        markup.add(types.InlineKeyboardButton("Resume", callback_data="resume_reporting"))
        markup.add(types.InlineKeyboardButton("Change Report Type", callback_data="change_report_type_mid_process"))

    status_text += "\n<i>You can stop with /stop</i>"

    try:
        # Instead of sending a new message, edit the existing status message
        bot.edit_message_text(
            status_text,
            user_id,
            report_data['status_message_id'],
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        console.print(f"[red]Error editing status message: {e}[/red]")

@bot.callback_query_handler(func=lambda call: call.data == "confirm_report_start")
def handle_confirm_report_start(call):
    user_id = call.from_user.id
    # Delete the summary message after confirmation
    delete_previous_message(user_id, call.message.message_id) 
    user_states[user_id] = UserState.REPORTING
    start_reporting_process(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_report")
def handle_cancel_report(call):
    user_id = call.from_user.id
    # Delete the summary message after cancellation
    delete_previous_message(user_id, call.message.message_id) 
    bot.send_message(user_id, "Cancelled")
    user_states[user_id] = UserState.IDLE
    if user_id in active_reports:
        active_reports.pop(user_id, None)
        if user_id in user_data and 'valid_sessions' in user_data[user_id]:
            del user_data[user_id]['valid_sessions']

@bot.callback_query_handler(func=lambda call: call.data == "pause_reporting")
def handle_pause_reporting(call):
    user_id = call.from_user.id
    if user_id in active_reports and active_reports[user_id]['running']:
        active_reports[user_id]['running'] = False
        active_reports[user_id]['paused'] = True
        active_reports[user_id]['pause_event'].clear()
        bot.answer_callback_query(call.id, "Reporting paused.")
        # The update_status_message will now correctly edit the existing message
        update_status_message(user_id, active_reports[user_id]['good_count'], active_reports[user_id]['bad_count'], 
                               active_reports[user_id]['current_session_index'], 
                               len(user_data[user_id]['valid_sessions']), "Process paused.")
    else:
        bot.answer_callback_query(call.id, "No active process to pause.")

@bot.callback_query_handler(func=lambda call: call.data == "resume_reporting")
def handle_resume_reporting(call):
    user_id = call.from_user.id
    if user_id in active_reports and active_reports[user_id].get('paused'):
        if user_id not in user_data or 'valid_sessions' not in user_data[user_id] or not user_data[user_id]['valid_sessions']:
            bot.send_message(user_id, "Cannot resume. Session data not found or no valid sessions. Please start a new process.")
            if user_id in active_reports:
                active_reports.pop(user_id, None)
            user_states[user_id] = UserState.IDLE
            return

        active_reports[user_id]['running'] = True
        active_reports[user_id]['paused'] = False
        active_reports[user_id]['pause_event'].set()

        threading.Thread(target=reporting_thread, 
                       args=(user_id, 
                            user_data[user_id]['target_ids'], 
                            user_data[user_id]['sleep_time'],
                            user_data[user_id].get('reports_per_session', float('inf')),
                            user_data[user_id]['valid_sessions'],
                            active_reports[user_id]['status_message_id'],
                            active_reports[user_id].get('is_multi_target', False),
                            active_reports[user_id].get('is_multi_report_types', False),
                            active_reports[user_id].get('selected_report_types', []))).start()

        bot.answer_callback_query(call.id, "Reporting resumed.")
        # The update_status_message will now correctly edit the existing message
        update_status_message(user_id, 
                            active_reports[user_id]['good_count'], 
                            active_reports[user_id]['bad_count'], 
                            active_reports[user_id]['current_session_index'], 
                            len(user_data[user_id]['valid_sessions']), 
                            "Process resumed.")
    else:
        bot.answer_callback_query(call.id, "No paused process to resume.")

@bot.callback_query_handler(func=lambda call: call.data == "change_report_type_mid_process")
def handle_change_report_type_mid_process(call):
    user_id = call.from_user.id
    if user_id in active_reports and (active_reports[user_id]['running'] or active_reports[user_id].get('paused')):
        if user_id not in user_data:
            user_data[user_id] = {}

        # We don't need to store status_message_to_edit here if update_status_message always edits the same one

        if active_reports[user_id].get('is_multi_target', False):
            user_data[user_id]['current_target_idx_for_change'] = 0
            user_data[user_id]['temp_new_multi_target_report_types'] = []

            target_ids = user_data[user_id]['target_ids']
            if user_data[user_id]['current_target_idx_for_change'] < len(target_ids):
                target_id = target_ids[user_data[user_id]['current_target_idx_for_change']]['id']

                markup = types.InlineKeyboardMarkup()
                for key, (value, desc) in report_options.items():
                    markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", 
                            callback_data=f"set_new_report_type_multi_{key}"))

                markup.add(types.InlineKeyboardButton("Random - Varying report types", 
                        callback_data="set_new_report_type_multi_random"))

                sent_message = bot.send_message(user_id, 
                    f"Choose new report type for target ID: <b>{target_id}</b>", 
                    reply_markup=markup, 
                    parse_mode="HTML")
                user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later

                user_states[user_id] = UserState.AWAITING_MULTI_TARGET_REPORT_TYPE_CHANGE
        elif active_reports[user_id].get('is_multi_report_types', False):
            user_data[user_id]['current_selection_idx'] = 0
            user_data[user_id]['temp_new_selected_report_types'] = []
            user_data[user_id]['selected_report_types_count'] = len(active_reports[user_id]['selected_report_types'])

            markup = types.InlineKeyboardMarkup()
            for key, (value, desc) in report_options.items():
                markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", 
                        callback_data=f"select_multi_report_type_{key}"))

            sent_message = bot.send_message(user_id, 
                f"Select new report type 1 of {user_data[user_id]['selected_report_types_count']}:", 
                reply_markup=markup)
            user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later

            user_states[user_id] = UserState.AWAITING_MULTI_REPORT_TYPES_CHANGE
        else:
            markup = types.InlineKeyboardMarkup()
            for key, (value, desc) in report_options.items():
                markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", 
                        callback_data=f"set_new_report_type_{key}"))

            markup.add(types.InlineKeyboardButton("Random - Varying report types", 
                    callback_data="set_new_report_type_random"))

            sent_message = bot.send_message(user_id, "Choose new report type:", reply_markup=markup)
            user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later
            user_states[user_id] = UserState.AWAITING_NEW_REPORT_TYPE_DURING_PROCESS
    else:
        bot.answer_callback_query(call.id, "No active or paused process to change report type for.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_new_report_type_multi_'))
def handle_set_new_report_type_multi(call):
    user_id = call.from_user.id
    if user_states.get(user_id) != UserState.AWAITING_MULTI_TARGET_REPORT_TYPE_CHANGE:
        return

    # Delete the message with the options after selection
    if 'last_options_message_id' in user_data[user_id]:
        delete_previous_message(user_id, user_data[user_id]['last_options_message_id'])
        del user_data[user_id]['last_options_message_id']

    if 'temp_new_multi_target_report_types' not in user_data[user_id]:
        user_data[user_id]['temp_new_multi_target_report_types'] = []

    parts = call.data.split('_')
    report_type_data = parts[-1]

    current_idx = user_data[user_id]['current_target_idx_for_change']
    target_ids = user_data[user_id]['target_ids']

    if current_idx >= len(target_ids):
        bot.answer_callback_query(call.id, "Invalid target index")
        return

    if report_type_data == 'random':
        report_type, reason_id = get_random_report_type()
        use_random = True
    else:
        report_id = int(report_type_data)
        report_type, _ = report_options[report_id]
        reason_id = report_id
        use_random = False

    target_ids[current_idx]['report_type'] = report_type
    target_ids[current_idx]['reason_id'] = reason_id
    target_ids[current_idx]['use_random_reports'] = use_random

    user_data[user_id]['temp_new_multi_target_report_types'].append({
        'id': target_ids[current_idx]['id'],
        'report_type': report_type,
        'reason_id': reason_id,
        'use_random_reports': use_random
    })

    user_data[user_id]['current_target_idx_for_change'] += 1

    if user_data[user_id]['current_target_idx_for_change'] < len(target_ids):
        next_target_id = target_ids[user_data[user_id]['current_target_idx_for_change']]['id']

        markup = types.InlineKeyboardMarkup()
        for key, (value, desc) in report_options.items():
            markup.add(types.InlineKeyboardButton(f"{key}. {value} - {desc}", 
                    callback_data=f"set_new_report_type_multi_{key}"))

        markup.add(types.InlineKeyboardButton("Random - Varying report types", 
                callback_data="set_new_report_type_multi_random"))

        sent_message = bot.send_message(user_id, 
            f"Choose new report type for target ID: <b>{next_target_id}</b>", 
            reply_markup=markup, 
            parse_mode="HTML")
        user_data[user_id]['last_options_message_id'] = sent_message.message_id # Store message ID to delete later
    else:
        bot.send_message(user_id, "All targets updated. Resuming reporting...")

        active_reports[user_id]['last_report_type_change'] = "All target report types updated."

        if active_reports[user_id].get('paused'):
            active_reports[user_id]['running'] = True
            active_reports[user_id]['paused'] = False
            active_reports[user_id]['pause_event'].set()

            threading.Thread(target=reporting_thread, 
                           args=(user_id, 
                                user_data[user_id]['target_ids'], 
                                user_data[user_id]['sleep_time'],
                                user_data[user_id].get('reports_per_session', float('inf')),
                                user_data[user_id]['valid_sessions'],
                                active_reports[user_id]['status_message_id'],
                                active_reports[user_id].get('is_multi_target', False),
                                active_reports[user_id].get('is_multi_report_types', False),
                                active_reports[user_id].get('selected_report_types', []))).start()

        user_states[user_id] = UserState.REPORTING

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_new_report_type_') and not call.data.startswith('set_new_report_type_multi_'))
def handle_set_new_report_type(call):
    user_id = call.from_user.id
    if user_states.get(user_id) != UserState.AWAITING_NEW_REPORT_TYPE_DURING_PROCESS:
        return

    # Delete the message with the options after selection
    if 'last_options_message_id' in user_data[user_id]:
        delete_previous_message(user_id, user_data[user_id]['last_options_message_id'])
        del user_data[user_id]['last_options_message_id']

    report_type_data = call.data.replace('set_new_report_type_', '')

    if report_type_data == 'random':
        report_type, reason_id = get_random_report_type()
        use_random = True
    else:
        report_id = int(report_type_data)
        report_type, _ = report_options[report_id]
        reason_id = report_id
        use_random = False

    if user_data[user_id]['target_ids']:
        user_data[user_id]['target_ids'][0]['report_type'] = report_type
        user_data[user_id]['target_ids'][0]['reason_id'] = reason_id
        user_data[user_id]['target_ids'][0]['use_random_reports'] = use_random

    bot.send_message(
        user_id,
        f"Report type changed to: {report_type}\nResuming reporting..."
    )

    active_reports[user_id]['last_report_type_change'] = f"Report type changed to: {report_type}"

    if active_reports[user_id].get('paused'):
        active_reports[user_id]['running'] = True
        active_reports[user_id]['paused'] = False
        active_reports[user_id]['pause_event'].set()

        threading.Thread(target=reporting_thread, 
                       args=(user_id, 
                            user_data[user_id]['target_ids'], 
                            user_data[user_id]['sleep_time'],
                            user_data[user_id].get('reports_per_session', float('inf')),
                            user_data[user_id]['valid_sessions'],
                            active_reports[user_id]['status_message_id'],
                            active_reports[user_id].get('is_multi_target', False),
                            active_reports[user_id].get('is_multi_report_types', False),
                            active_reports[user_id].get('selected_report_types', []))).start()

    user_states[user_id] = UserState.REPORTING

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    if user_id not in user_states:
        user_states[user_id] = UserState.IDLE

    if user_states[user_id] == UserState.IDLE:
        bot.send_message(user_id, "Unknown command. Use /help")

if __name__ == "__main__":
    console.print("[green]Bot started![/green]")
    bot.polling(none_stop=True)
