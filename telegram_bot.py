import os
import sys
import subprocess

# Ensure critical packages exist even if Render skips build step
def ensure_package(pkg, import_name=None):
    name = import_name or pkg.split("==")[0].replace('-', '_')
    try:
        __import__(name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

required_packages = [
    ("requests", "requests"),
    ("python-telegram-bot==20.8", "telegram"),
]

for pkg, module in required_packages:
    ensure_package(pkg, module)

import requests
import random
import string
import time
import json
import threading
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# Fix Windows encoding issue
if sys.platform == 'win32':
    try:
        import codecs
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

# Bot Configuration - Can be set via environment variables for Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "8208170457:AAEznHYzZw6VDSjrK5VDoL88rVwuEUGVi_A")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7200333065"))
GROUP_LINK = os.getenv("GROUP_LINK", "https://t.me/+w7VwgotOFrRkNTM1")
GROUP_USERNAME = os.getenv("GROUP_USERNAME", "w7VwgotOFrRkNTM1")  # Without @
LIVE_CHANNEL_ID = os.getenv("LIVE_CHANNEL_ID", None)  # Channel ID for live valid codes (optional)

# Mining Configuration
NUM_THREADS = 10
DELAY_PER_REQUEST = 0.5
START_PREFIXES = [p.strip().upper() for p in os.getenv("START_PREFIXES", "T,D").split(",") if p.strip()]

# API Configuration
BASE_URL = "https://www.scanandwinpromo.tictac.com"
REGISTER_URL = f"{BASE_URL}/in/en/xp/scanandwinpromo/home/register/"
OTP_URL = f"{BASE_URL}/in/en/xp/scanandwinpromo/home/generateOTP/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; RMX2030) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7499.116 Mobile Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Referer': REGISTER_URL,
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': BASE_URL,
    'Connection': 'keep-alive',
}

# Data storage
DATA_FILE = "bot_data.json"
active_miners = {}  # {user_id: {'running': bool, 'thread': thread, 'stats': {...}}}
verified_users = set()  # Store verified user IDs
file_lock = threading.Lock()


def schedule_coroutine(app, coroutine):
    """Safely run a coroutine from worker threads"""
    asyncio.run_coroutine_threadsafe(coroutine, app.loop)


def update_status_message(user_id, stats, app, force=False):
    """Edit the live status message for a user"""
    miner_state = active_miners.get(user_id)
    if not miner_state:
        return
    message_id = miner_state.get('status_message_id')
    if not message_id:
        return
    now = time.time()
    if not force:
        last_push = miner_state.get('last_status_push', 0)
        if now - last_push < 5:
            return
    miner_state['last_status_push'] = now
    checked = stats.get('checked', 0)
    last_hundred = checked % 100
    percent = int((last_hundred / 100) * 100)
    bar_slots = 20
    filled_slots = max(0, min(bar_slots, int(bar_slots * percent / 100)))
    bar = "█" * filled_slots + "░" * (bar_slots - filled_slots)
    next_target = 100 - last_hundred if last_hundred != 0 else 100
    text = (
        "⚙️ Live Mining Status\n"
        f"Checked: {checked:,}\n"
        f"Valid: {stats.get('valid', 0)}\n"
        f"Last Code: {stats.get('last_code', '--')}\n"
        f"Progress (last 100): [{bar}] {percent}%\n"
        f"Next milestone in {next_target} checks\n"
        f"Threads Active: {NUM_THREADS}\n"
        f"Updated: {datetime.now().strftime('%H:%M:%S')}"
    )
    try:
        schedule_coroutine(
            app,
            app.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text
            )
        )
    except Exception as e:
        print(f"Error updating status message for {user_id}: {e}")

def load_data():
    """Load user data from file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    """Save user data to file"""
    with file_lock:
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")

def get_user_data(user_id, username=None):
    """Get user's data"""
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            'valid_codes': [],
            'total_checked': 0,
            'valid_found': 0,
            'phone': "9876543210",
            'username': username or f"User_{user_id_str[:8]}",
            'created_at': datetime.now().isoformat()
        }
        save_data(data)
    elif username and data[user_id_str].get('username') != username:
        data[user_id_str]['username'] = username
        save_data(data)
    return data[str(user_id)]

def save_valid_code(user_id, code):
    """Save valid code for user"""
    data = load_data()
    user_id_str = str(user_id)
    
    if user_id_str not in data:
        data[user_id_str] = {
            'valid_codes': [],
            'total_checked': 0,
            'valid_found': 0,
            'phone': "9876543210",
            'username': f"User_{user_id_str[:8]}",
            'created_at': datetime.now().isoformat()
        }
    
    if code not in data[user_id_str]['valid_codes']:
        data[user_id_str]['valid_codes'].append(code)
        data[user_id_str]['valid_found'] = len(data[user_id_str]['valid_codes'])
        data[user_id_str]['total_checked'] = data[user_id_str].get('total_checked', 0) + 1
        save_data(data)
    return True

def choose_prefix():
    """Pick a prefix letter (from configured list or random)"""
    if START_PREFIXES:
        candidate = random.choice(START_PREFIXES)
        if candidate and candidate[0].isalpha():
            return candidate[0]
    return random.choice(string.ascii_uppercase)


def generate_coupon():
    """Generate random coupon code"""
    chars = string.ascii_uppercase + string.digits
    prefix = choose_prefix()
    return prefix + ''.join(random.choice(chars) for _ in range(5))

def check_coupon(code, session, phone):
    """Check if coupon is valid"""
    data = {'phone': phone, 'ccode': code}
    try:
        response = session.post(OTP_URL, data=data, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return False, f"Server error {response.status_code}"

        try:
            result = response.json()
        except:
            return False, "Bad response"

        status = result.get('status')
        message = result.get('message', '')
        
        # Check if campaign is not live
        if message and ('not yet live' in message.lower() or 'campaign is not' in message.lower() or 'not live' in message.lower()):
            return False, "Campaign Not Live"
        
        if status == 'success':
            return True, "VALID"
        else:
            return False, message if message else "Invalid"

    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.RequestException:
        return False, "Network error"
    except Exception:
        return False, "Error"

def mining_worker(user_id, phone, app, stop_event):
    """Worker thread for mining codes"""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        session.get(REGISTER_URL, timeout=15)
    except:
        pass
    
    stats = {'checked': 0, 'valid': 0, 'last_code': '--'}
    if user_id in active_miners:
        active_miners[user_id]['stats'] = stats
    
    while not stop_event.is_set():
        if user_id not in active_miners or not active_miners[user_id]['running']:
            break
            
        code = generate_coupon()
        stats['checked'] += 1
        stats['last_code'] = code
        
        try:
            is_valid, msg = check_coupon(code, session, phone)
            
            if is_valid:
                stats['valid'] += 1
                save_valid_code(user_id, code)
                
                # Send notification to user who found it
                try:
                    schedule_coroutine(
                        app,
                        app.bot.send_message(
                            chat_id=user_id,
                            text=f"🎉 VALID CODE FOUND!\n\nCode: {code}\nSaved to your account!"
                        )
                    )
                except:
                    pass
                
                # Broadcast to all verified users (live valid codes)
                try:
                    data = load_data()
                    for uid_str, user_data in data.items():
                        uid = int(uid_str)
                        if uid not in verified_users:
                            continue

                        if uid == user_id:
                            continue  # already notified

                        if user_data.get("log_live_valid", False):
                            try:
                                schedule_coroutine(
                                    app,
                                    app.bot.send_message(
                                        chat_id=uid,
                                        text=(
                                            "🔥 LIVE VALID CODE!\n\n"
                                            f"Code: {code}\n"
                                            f"Finder: {user_data.get('username', 'Unknown')}\n"
                                            "Saved in shared log!"
                                        )
                                    )
                                )
                            except Exception as e:
                                print(f"Error sending live code to {uid}: {e}")
                except Exception as e:
                    print(f"Error broadcasting code: {e}")

                if stats['valid'] % 10 == 0:
                    try:
                        milestone_data = get_user_data(user_id)
                        recent_codes = milestone_data['valid_codes'][-10:] or milestone_data['valid_codes']
                        summary_text = "🏆 Valid Code Milestone Reached!\n"
                        summary_text += f"Total Valid Codes: {len(milestone_data['valid_codes'])}\n"
                        summary_text += "Last 10 codes:\n"
                        summary_text += "\n".join(recent_codes)
                        schedule_coroutine(
                            app,
                            app.bot.send_message(
                                chat_id=user_id,
                                text=summary_text
                            )
                        )
                    except Exception as e:
                        print(f"Error sending milestone summary to {user_id}: {e}")
            
            # Update stats every 100 codes (less spam)
            if stats['checked'] % 100 == 0:
                try:
                    schedule_coroutine(
                        app,
                        app.bot.send_message(
                            chat_id=user_id,
                            text=f"📊 Mining Progress\n\nChecked: {stats['checked']:,}\nValid: {stats['valid']}"
                        )
                    )
                except:
                    pass
        except Exception as e:
            print(f"Error in mining worker: {e}")
        
        update_status_message(user_id, stats, app)
        time.sleep(DELAY_PER_REQUEST)
    
    # Update total checked in user data
    try:
        data = load_data()
        user_id_str = str(user_id)
        if user_id_str in data:
            data[user_id_str]['total_checked'] = data[user_id_str].get('total_checked', 0) + stats['checked']
            save_data(data)
    except:
        pass
    
    # Final stats
    try:
        user_data = get_user_data(user_id)
        schedule_coroutine(
            app,
            app.bot.send_message(
                chat_id=user_id,
                text=(
                    "⏹️ Mining Stopped\n\n"
                    f"Final Stats:\nChecked: {stats['checked']:,}\n"
                    f"Valid Found: {stats['valid']}\n"
                    f"Total Valid Codes: {len(user_data['valid_codes'])}"
                )
            )
        )
    except:
        pass
    
    try:
        miner_state = active_miners.get(user_id)
        if miner_state and miner_state.get('status_message_id'):
            final_text = (
                "✅ Mining Session Finished\n"
                f"Checked: {stats['checked']:,}\n"
                f"Valid Found: {stats['valid']}\n"
                f"Last Code: {stats.get('last_code', '--')}"
            )
            schedule_coroutine(
                app,
                app.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=miner_state['status_message_id'],
                    text=final_text
                )
            )
            miner_state['status_message_id'] = None
    except Exception as e:
        print(f"Error finalizing status message for {user_id}: {e}")
    
    # Clean up
    if user_id in active_miners:
        active_miners[user_id]['running'] = False

def load_verified_users():
    """Load verified users from data file"""
    data = load_data()
    verified = set()
    for user_id, user_data in data.items():
        if user_data.get('verified', False):
            verified.add(int(user_id))
    return verified

def save_verified_user(user_id):
    """Mark user as verified"""
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            'valid_codes': [],
            'total_checked': 0,
            'valid_found': 0,
            'phone': "9876543210",
            'username': f"User_{user_id_str[:8]}",
            'verified': True,
            'created_at': datetime.now().isoformat()
        }
    else:
        data[user_id_str]['verified'] = True
    save_data(data)
    verified_users.add(user_id)

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        print(f"Received /start command from user {user_id} (@{username})")
        
        # Check if user is verified (skip for admin)
        if user_id == ADMIN_ID:
            verified_users.add(user_id)
        
        if user_id not in verified_users:
                keyboard = [
                    [InlineKeyboardButton("🔗 Join Group", url=GROUP_LINK)],
                    [InlineKeyboardButton("✅ I've Joined - Verify", callback_data="verify_group")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "⚠️ Group Verification Required\n\n"
                    f"Please join our group to use this bot:\n{GROUP_LINK}\n\n"
                    "After joining, click the verify button below:",
                    reply_markup=reply_markup
                )
                return
        
        # User is verified or admin, show main menu
        user_data = get_user_data(user_id, username)
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("⏹️ Stop Mining", callback_data="stop_mining")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("💎 My Valid Codes", callback_data="my_codes")],
            [InlineKeyboardButton("🔥 Live Valid Codes", callback_data="live_codes")],
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Welcome to TicTac Coupon Miner Bot!\n\n"
            "Your Stats:\n"
            f"- Valid Codes: {len(user_data['valid_codes'])}\n"
            f"- Total Checked: {user_data['total_checked']:,}\n\n"
            "Use the buttons below to control mining.",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error in start handler: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "verify_group":
        # Fake verification - just mark user as verified
        save_verified_user(user_id)
        verified_users.add(user_id)
        
        # Show main menu
        username = query.from_user.username or query.from_user.first_name
        user_data = get_user_data(user_id, username)
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("⏹️ Stop Mining", callback_data="stop_mining")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("💎 My Valid Codes", callback_data="my_codes")],
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ Verification Successful!\n\n"
            "Welcome to TicTac Coupon Miner Bot!\n\n"
            "Your Stats:\n"
            f"- Valid Codes: {len(user_data['valid_codes'])}\n"
            f"- Total Checked: {user_data['total_checked']:,}\n\n"
            "Use the buttons below to control mining.",
            reply_markup=reply_markup
        )
    
    elif data == "start_mining":
        if user_id in active_miners and active_miners[user_id]['running']:
            await query.edit_message_text("⚠️ Mining is already running! Use /stop to stop it.")
            return
        
        user_data = get_user_data(user_id)
        phone = user_data.get('phone', '9876543210')
        
        stop_event = threading.Event()
        thread = threading.Thread(
            target=mining_worker,
            args=(user_id, phone, context.application, stop_event),
            daemon=True
        )
        
        active_miners[user_id] = {
            'running': True,
            'thread': thread,
            'stop_event': stop_event,
            'stats': {'checked': 0, 'valid': 0, 'last_code': '--'},
            'status_message_id': None,
            'last_status_push': 0
        }
        
        status_message = await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⚙️ Live Mining Status\n"
                "Checked: 0\n"
                "Valid: 0\n"
                "Last Code: --\n"
                "Threads Active: {0}".format(NUM_THREADS)
            )
        )
        active_miners[user_id]['status_message_id'] = status_message.message_id
        active_miners[user_id]['last_status_push'] = 0
        
        thread.start()
        
        await query.edit_message_text(
            "✅ Mining Started!\n\n"
            "Scanning codes...\n"
            "You'll be notified when valid codes are found!"
        )
    
    elif data == "stop_mining":
        if user_id not in active_miners or not active_miners[user_id]['running']:
            await query.edit_message_text("⚠️ No mining session is currently running!")
            return
        
        active_miners[user_id]['stop_event'].set()
        active_miners[user_id]['running'] = False
        
        await query.edit_message_text("⏹️ Stopping mining... Please wait a moment.")
    
    elif data == "my_stats":
        user_data = get_user_data(user_id)
        stats_text = "📊 Your Mining Stats\n\n"
        stats_text += f"Valid Codes Found: {len(user_data['valid_codes'])}\n"
        stats_text += f"Total Checked: {user_data['total_checked']:,}\n"
        
        if user_id in active_miners and active_miners[user_id]['running']:
            current_stats = active_miners[user_id]['stats']
            stats_text += "\nCurrent Session:\n"
            stats_text += f"Checked: {current_stats.get('checked', 0):,}\n"
            stats_text += f"Valid: {current_stats.get('valid', 0)}"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]]
        await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "live_codes":
        # Show live valid codes from all users
        data_dict = load_data()
        all_codes = []
        
        for uid, user_data in data_dict.items():
            for code in user_data.get('valid_codes', []):
                username = user_data.get('username', f"User_{uid[:8]}")
                all_codes.append({
                    'code': code,
                    'user': username
                })
        
        if not all_codes:
            await query.edit_message_text("❌ No valid codes found yet. Start mining to find codes!")
            return
        
        codes_text = f"🔥 LIVE VALID CODES ({len(all_codes)} total)\n\n"
        
        for item in all_codes[-30:]:
            codes_text += f"{item['code']} - {item['user']}\n"
        
        codes_text += "\n"
        
        if len(all_codes) > 30:
            codes_text += f"\nShowing last 30 codes. Total: {len(all_codes)}\n"
        
        codes_text += "\n💡 Tip: Use /live command for full list!"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]]
        await query.edit_message_text(codes_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "toggle_live_log":
        data_dict = load_data()
        user_data = data_dict.get(str(user_id), {})
        new_state = not user_data.get("log_live_valid", False)
        user_data["log_live_valid"] = new_state
        data_dict[str(user_id)] = user_data
        save_data(data_dict)

        status = "ON" if new_state else "OFF"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]]
        await query.edit_message_text(
            f"📣 Live valid code logs are now {status}.\n\n"
            "When ON, you will get real-time logged codes similar to the VALID_TICTAC_COUPONS file.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "my_codes":
        user_data = get_user_data(user_id)
        codes = user_data['valid_codes']
        
        if not codes:
            await query.edit_message_text("❌ No valid codes found yet. Start mining to find codes!")
            return
        
        codes_text = f"💎 Your Valid Codes ({len(codes)})\n\n"
        for code in codes[-20:]:  # Show last 20 codes
            codes_text += f"{code}\n"
        codes_text += "\n"
        
        if len(codes) > 20:
            codes_text += f"\nShowing last 20 codes. Total: {len(codes)}"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_menu")]]
        await query.edit_message_text(codes_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("❌ You are not authorized to access admin panel!")
            return
        
        admin_data = load_data()
        total_users = len(admin_data)
        total_codes = sum(len(user['valid_codes']) for user in admin_data.values())
        
        keyboard = [
            [InlineKeyboardButton("📊 All Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("💎 All Valid Codes", callback_data="admin_codes")],
            [InlineKeyboardButton("👥 User List", callback_data="admin_users")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
        ]
        
        await query.edit_message_text(
            f"👑 Admin Panel\n\n"
            f"📊 Total Users: {total_users}\n"
            f"💎 Total Valid Codes: {total_codes}\n\n"
            f"Select an option:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "admin_stats":
        if user_id != ADMIN_ID:
            return
        
        admin_data = load_data()
        stats_text = "📊 All Users Stats\n\n"
        
        for uid, user_data in list(admin_data.items())[:20]:
            username = user_data.get('username', f"User {uid[:8]}")
            stats_text += f"👤 {username}\n"
            stats_text += f"   ✅ Codes: {len(user_data['valid_codes'])}\n"
            stats_text += f"   🔍 Checked: {user_data.get('total_checked', 0):,}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "admin_codes":
        if user_id != ADMIN_ID:
            return
        
        admin_data = load_data()
        all_codes = []
        
        for uid, user_data in admin_data.items():
            for code in user_data['valid_codes']:
                all_codes.append(f"{code} (User: {uid[:8]})")
        
        if not all_codes:
            await query.edit_message_text("❌ No valid codes found from any user yet.")
            return
        
        codes_text = f"💎 All Valid Codes ({len(all_codes)})\n\n"
        for code in all_codes[-30:]:  # Show last 30
            codes_text += f"{code}\n"
        codes_text += "\n"
        
        if len(all_codes) > 30:
            codes_text += f"\nShowing last 30 codes. Total: {len(all_codes)}"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(codes_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "admin_users":
        if user_id != ADMIN_ID:
            return
        
        admin_data = load_data()
        users_text = "👥 All Users\n\n"
        
        for idx, (uid, user_data) in enumerate(list(admin_data.items())[:30], 1):
            username = user_data.get('username', f"User {uid[:8]}")
            users_text += f"{idx}. {username} (ID: {uid[:8]})\n"
            users_text += f"   Codes: {len(user_data['valid_codes'])}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_panel")]]
        await query.edit_message_text(users_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "back_menu":
        user_data = get_user_data(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Mining", callback_data="start_mining")],
            [InlineKeyboardButton("⏹️ Stop Mining", callback_data="stop_mining")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("💎 My Valid Codes", callback_data="my_codes")],
            [InlineKeyboardButton("🔥 Live Valid Codes", callback_data="live_codes")],
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
        
        await query.edit_message_text(
            f"👋 TicTac Coupon Miner Bot\n\n"
            f"📊 Your Stats:\n"
            f"- Valid Codes: {len(user_data['valid_codes'])}\n"
            f"- Total Checked: {user_data['total_checked']:,}\n\n"
            f"Use buttons below to control mining:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def setphone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set phone number for mining"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a phone number!\n\nUsage: /setphone 9876543210")
        return
    
    phone = context.args[0]
    if not phone.isdigit() or len(phone) != 10:
        await update.message.reply_text("❌ Invalid phone number! Please provide a 10-digit number.")
        return
    
    username = update.effective_user.username or update.effective_user.first_name
    data = load_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            'valid_codes': [],
            'total_checked': 0,
            'valid_found': 0,
            'phone': phone,
            'username': username or f"User_{user_id_str[:8]}",
            'created_at': datetime.now().isoformat()
        }
    else:
        data[user_id_str]['phone'] = phone
        if username:
            data[user_id_str]['username'] = username
    
    save_data(data)
    await update.message.reply_text(f"✅ Phone number set to: {phone}\n\nYou can now start mining!")

async def live_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live valid codes from all users"""
    user_id = update.effective_user.id
    
    # Check if user is verified
    if user_id not in verified_users and user_id != ADMIN_ID:
        await update.message.reply_text("⚠️ Please verify first using /start")
        return
    
    data = load_data()
    all_codes = []
    
    # Collect all valid codes with user info
    for uid, user_data in data.items():
        for code in user_data.get('valid_codes', []):
            username = user_data.get('username', f"User_{uid[:8]}")
            all_codes.append({
                'code': code,
                'user': username,
                'timestamp': user_data.get('created_at', '')
            })
    
    if not all_codes:
        await update.message.reply_text("❌ No valid codes found yet. Start mining to find codes!")
        return
    
    # Sort by most recent (if we had timestamps, but for now just show all)
    codes_text = f"🔥 LIVE VALID CODES ({len(all_codes)} total)\n\n"
    
    # Show last 50 codes
    for item in all_codes[-50:]:
        codes_text += f"{item['code']} - {item['user']}\n"
    
    codes_text += "\n"
    
    if len(all_codes) > 50:
        codes_text += f"\nShowing last 50 codes. Total: {len(all_codes)}\n"
    
    codes_text += "\n💡 Tip: Start mining to find more codes!"
    
    await update.message.reply_text(codes_text)

def main():
    """Start the bot"""
    try:
        # Load verified users
        global verified_users
        verified_users = load_verified_users()
        verified_users.add(ADMIN_ID)  # Admin is always verified
        
        print("Starting TicTac Coupon Miner Telegram Bot...")
        print(f"Admin ID: {ADMIN_ID}")
        print(f"Group Link: {GROUP_LINK}")
        print(f"Bot Token: {BOT_TOKEN[:20]}...")
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("setphone", setphone))
        application.add_handler(CommandHandler("live", live_codes))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Start bot
        print("Bot is running! Press Ctrl+C to stop.")
        print("Waiting for messages...")
        print("Send /start to your bot in Telegram to test!")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES, 
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        print(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
