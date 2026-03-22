# =========================
# ZEDOX BOT - PART 1 (FINAL PRO)
# Core Setup + User + DB + Force Join
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, random, string, threading

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# INIT FILES
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {
            "free": {},
            "vip": {},
            "apps": {},
            "courses": {},   # ✅ NEW
            "custom": {}
        },
        "config.json": {
            "force_channels": [],
            "vip_msg": "💎 Buy VIP to unlock this!",
            "welcome": "🔥 Welcome to ZEDOX BOT",
            "ref_reward": 5,
            "notify": True
        },
        "codes.json": {}
    }

    for f, d in files.items():
        if not os.path.exists(f):
            with open(f, "w") as file:
                json.dump(d, file, indent=4)

init_files()

# =========================
# LOAD / SAVE
# =========================
def load(file):
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# USER SYSTEM
# =========================
class User:
    def __init__(self, uid):
        self.uid = str(uid)
        self.users = load("users.json")

        if self.uid not in self.users:
            self.users[self.uid] = {
                "points": 0,
                "vip": False,
                "ref": None
            }
            save("users.json", self.users)

        self.data = self.users[self.uid]

    def is_vip(self): return self.data["vip"]
    def points(self): return self.data["points"]

    def add_points(self, pts):
        self.data["points"] += pts
        self.save()

    def make_vip(self):
        self.data["vip"] = True
        self.save()

    def save(self):
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

# =========================
# FORCE JOIN (STRICT)
# =========================
def force_block(uid):
    config = load("config.json")

    for ch in config["force_channels"]:
        try:
            member = bot.get_chat_member(ch, uid)

            if member.status in ["left", "kicked"]:
                kb = InlineKeyboardMarkup()

                kb.add(InlineKeyboardButton(
                    f"JOIN {ch}",
                    url=f"https://t.me/{ch.replace('@','')}"
                ))

                kb.add(InlineKeyboardButton(
                    "🔄 I Joined",
                    callback_data="recheck"
                ))

                bot.send_message(
                    uid,
                    "🚫 *Join all channels first!*",
                    reply_markup=kb
                )
                return True

        except:
            return True

    return False

# =========================
# FILE SYSTEM
# =========================
class FileSystem:
    def __init__(self):
        self.db = load("db.json")

    def save_db(self):
        save("db.json", self.db)

    def add_folder(self, cat, name, files, price=0):
        self.db = load("db.json")
        self.db[cat][name] = {"files": files, "price": price}
        self.save_db()

    def delete_folder(self, cat, name):
        self.db = load("db.json")
        if name in self.db[cat]:
            del self.db[cat][name]
            self.save_db()
            return True
        return False

    def edit_price(self, cat, name, price):
        self.db = load("db.json")
        if name in self.db[cat]:
            self.db[cat][name]["price"] = price
            self.save_db()
            return True
        return False

    def get_category(self, cat):
        return load("db.json").get(cat, {})

fs = FileSystem()

# =========================
# PAGINATION (10 ITEMS)
# =========================
def get_folder_kb(cat, page=0):
    data = fs.get_category(cat)
    keys = list(data.keys())

    per_page = 10
    start = page * per_page
    end = start + per_page

    kb = InlineKeyboardMarkup()

    for name in keys[start:end]:
        price = data[name]["price"]
        txt = f"{name} [{price} pts]" if price > 0 else name
        kb.add(InlineKeyboardButton(txt, callback_data=f"open|{cat}|{name}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page|{cat}|{page-1}"))
    if end < len(keys):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page|{cat}|{page+1}"))

    if nav:
        kb.row(*nav)

    return kb
# =========================
# ZEDOX BOT - PART 2 (FINAL)
# Admin Panel + Upload + Delete + Config
# =========================

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN MENU
# =========================
def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📦 Upload FREE", "💎 Upload VIP")
    kb.row("📱 Upload APPS", "🎓 Upload COURSES")

    kb.row("✏️ Edit Folder Price", "🗑 Delete Folder")

    kb.row("⭐ Set VIP Message", "🏠 Set Welcome Message")

    kb.row("➕ Add Force Join", "➖ Remove Force Join")

    kb.row("🏆 Generate Codes", "📤 Broadcast")

    kb.row("❌ Exit Admin")
    return kb

@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    bot.send_message(m.from_user.id, "🛠️ Admin Panel", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin", reply_markup=main_menu(m.from_user.id))

# =========================
# VIP / WELCOME SETTINGS
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg(m):
    msg = bot.send_message(m.from_user.id, "Send new VIP message:")
    bot.register_next_step_handler(msg, save_vip_msg)

def save_vip_msg(m):
    cfg = load("config.json")
    cfg["vip_msg"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ VIP message updated")

@bot.message_handler(func=lambda m: m.text == "🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_msg(m):
    msg = bot.send_message(m.from_user.id, "Send new welcome message:")
    bot.register_next_step_handler(msg, save_welcome_msg)

def save_welcome_msg(m):
    cfg = load("config.json")
    cfg["welcome"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ Welcome message updated")

# =========================
# FORCE JOIN MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and is_admin(m.from_user.id))
def add_force(m):
    msg = bot.send_message(m.from_user.id, "Send channel username (@channel):")
    bot.register_next_step_handler(msg, save_force_add)

def save_force_add(m):
    cfg = load("config.json")
    ch = m.text.strip()

    if ch not in cfg["force_channels"]:
        cfg["force_channels"].append(ch)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, "✅ Added")
    else:
        bot.send_message(m.from_user.id, "❌ Already exists")

@bot.message_handler(func=lambda m: m.text == "➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force(m):
    msg = bot.send_message(m.from_user.id, "Send channel to remove:")
    bot.register_next_step_handler(msg, save_force_remove)

def save_force_remove(m):
    cfg = load("config.json")
    ch = m.text.strip()

    if ch in cfg["force_channels"]:
        cfg["force_channels"].remove(ch)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, "✅ Removed")
    else:
        bot.send_message(m.from_user.id, "❌ Not found")

# =========================
# UPLOAD SYSTEM (WITH CANCEL)
# =========================
def start_upload(uid, category):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")

    msg = bot.send_message(uid, f"📤 Upload files to {category}\nUse /done or /cancel", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, []))

def upload_step(m, cat, uid, files):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload cancelled", reply_markup=admin_menu())
        return

    if m.text == "/done":
        if not files:
            bot.send_message(uid, "❌ No files uploaded")
            return

        msg = bot.send_message(uid, "Send folder name:")
        bot.register_next_step_handler(msg, lambda m2: upload_name(m2, cat, files))
        return

    if m.content_type in ["document", "photo", "video"]:
        files.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, f"✅ File {len(files)} saved")

    bot.register_next_step_handler(m, lambda m2: upload_step(m2, cat, uid, files))

def upload_name(m, cat, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "Send price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, cat, name, files))

def upload_save(m, cat, name, files):
    try:
        price = int(m.text)
        fs.add_folder(cat, name, files, price)
        bot.send_message(m.from_user.id, f"✅ Folder `{name}` saved", reply_markup=admin_menu())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price")

# Upload buttons
@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE" and is_admin(m.from_user.id))
def up_free(m): start_upload(m.from_user.id, "free")

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP" and is_admin(m.from_user.id))
def up_vip(m): start_upload(m.from_user.id, "vip")

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS" and is_admin(m.from_user.id))
def up_apps(m): start_upload(m.from_user.id, "apps")

@bot.message_handler(func=lambda m: m.text == "🎓 Upload COURSES" and is_admin(m.from_user.id))
def up_courses(m): start_upload(m.from_user.id, "courses")

# =========================
# DELETE SYSTEM (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_start(m):
    kb = InlineKeyboardMarkup()
    for cat in ["free","vip","apps","courses"]:
        kb.add(InlineKeyboardButton(cat.upper(), callback_data=f"delcat|{cat}"))
    bot.send_message(m.from_user.id, "Select category:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcat|"))
def delete_list(c):
    cat = c.data.split("|")[1]
    data = fs.get_category(cat)

    kb = InlineKeyboardMarkup()
    for name in data.keys():
        kb.add(InlineKeyboardButton(name, callback_data=f"delfin|{cat}|{name}"))

    bot.edit_message_text("Select folder to delete:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delfin|"))
def delete_final(c):
    _, cat, name = c.data.split("|")

    if fs.delete_folder(cat, name):
        bot.answer_callback_query(c.id, "Deleted")
        bot.edit_message_text(f"✅ `{name}` deleted", c.from_user.id, c.message.id)
    else:
        bot.answer_callback_query(c.id, "Error")

# =========================
# EDIT PRICE (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Folder Price" and is_admin(m.from_user.id))
def edit_start(m):
    msg = bot.send_message(m.from_user.id, "Send category (free/vip/apps/courses):")
    bot.register_next_step_handler(msg, edit_step2)

def edit_step2(m):
    cat = m.text.lower()
    msg = bot.send_message(m.from_user.id, "Send folder name:")
    bot.register_next_step_handler(msg, lambda m2: edit_step3(m2, cat))

def edit_step3(m, cat):
    name = m.text
    msg = bot.send_message(m.from_user.id, "Send new price:")
    bot.register_next_step_handler(msg, lambda m2: edit_step4(m2, cat, name))

def edit_step4(m, cat, name):
    try:
        price = int(m.text)
        if fs.edit_price(cat, name, price):
            bot.send_message(m.from_user.id, "✅ Updated")
        else:
            bot.send_message(m.from_user.id, "❌ Failed")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price")
        # =========================
# ZEDOX BOT - PART 3 (FINAL)
# User Panel + Pagination + Folder Access + Referral + Redeem
# =========================

# =========================
# MAIN MENU
# =========================
def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📂 FREE METHODS", "💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS", "🎓 PREMIUM COURSES")

    kb.row("💰 POINTS", "⭐ BUY VIP")
    kb.row("🎁 REFERRAL", "👤 ACCOUNT")

    kb.row("🆔 CHAT ID", "🏆 Redeem")

    if uid == ADMIN_ID:
        kb.row("⚙️ ADMIN PANEL")

    return kb

# =========================
# START COMMAND (STRICT FORCE JOIN)
# =========================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    args = m.text.split()

    user = User(uid)

    # Referral
    if len(args) > 1:
        ref_id = args[1]
        users = load("users.json")

        if ref_id != str(uid) and ref_id in users and not user.data.get("ref"):
            User(ref_id).add_points(load("config.json").get("ref_reward", 5))
            user.data["ref"] = ref_id
            user.save()

    # FORCE JOIN BLOCK
    if force_block(uid):
        return

    cfg = load("config.json")

    bot.send_message(
        uid,
        cfg.get("welcome", "Welcome!"),
        reply_markup=main_menu(uid)
    )

# =========================
# SHOW FOLDERS (PAGINATION)
# =========================
@bot.message_handler(func=lambda m: m.text in [
    "📂 FREE METHODS",
    "💎 VIP METHODS",
    "📦 PREMIUM APPS",
    "🎓 PREMIUM COURSES"
])
def show_folders(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    mapping = {
        "📂 FREE METHODS": "free",
        "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps",
        "🎓 PREMIUM COURSES": "courses"
    }

    cat = mapping[m.text]

    bot.send_message(
        uid,
        f"📂 {m.text}",
        reply_markup=get_folder_kb(cat, 0)
    )

# =========================
# PAGINATION BUTTONS
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def paginate(c):
    _, cat, page = c.data.split("|")

    bot.edit_message_reply_markup(
        c.from_user.id,
        c.message.id,
        reply_markup=get_folder_kb(cat, int(page))
    )

# =========================
# OPEN FOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    uid = c.from_user.id
    user = User(uid)

    _, cat, name = c.data.split("|")

    folder = fs.get_category(cat).get(name)

    if not folder:
        bot.answer_callback_query(c.id, "❌ Folder not found")
        return

    # VIP CHECK
    if cat == "vip" and not user.is_vip():
        bot.send_message(uid, load("config.json")["vip_msg"])
        return

    price = folder.get("price", 0)

    # POINT CHECK
    if not user.is_vip() and price > 0:
        if user.points() < price:
            bot.answer_callback_query(c.id, "❌ Not enough points", show_alert=True)
            return

        user.add_points(-price)

    bot.answer_callback_query(c.id, "📤 Sending files...")

    sent = 0
    for f in folder["files"]:
        try:
            bot.copy_message(uid, f["chat"], f["msg"])
            sent += 1
        except:
            continue

    if load("config.json").get("notify", True):
        bot.send_message(uid, f"✅ Sent {sent} file(s) from `{name}`")

# =========================
# GENERAL USER COMMANDS
# =========================
@bot.message_handler(func=lambda m: True)
def user_commands(m):
    uid = m.from_user.id
    user = User(uid)

    # Force Join Always First
    if force_block(uid):
        return

    text = m.text

    if text == "💰 POINTS":
        bot.send_message(uid, f"💰 You have {user.points()} points")

    elif text == "⭐ BUY VIP":
        bot.send_message(uid, load("config.json")["vip_msg"])

    elif text == "🎁 REFERRAL":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🎁 Your link:\n{link}")

    elif text == "👤 ACCOUNT":
        status = "💎 VIP" if user.is_vip() else "🆓 FREE"
        bot.send_message(uid, f"{status}\n💰 Points: {user.points()}")

    elif text == "🆔 CHAT ID":
        bot.send_message(uid, f"`{uid}`")

    elif text == "🏆 Redeem":
        msg = bot.send_message(uid, "Send your code:")
        bot.register_next_step_handler(msg, redeem_code)

# =========================
# REDEEM SYSTEM
# =========================
def redeem_code(m):
    uid = m.from_user.id
    user = User(uid)

    success, pts = codesys.redeem(m.text.strip(), user)

    if success:
        bot.send_message(uid, f"✅ Redeemed +{pts} points\nTotal: {user.points()}")
    else:
        bot.send_message(uid, "❌ Invalid or used code")
        # =========================
# ZEDOX BOT - PART 4 (FINAL)
# Polling + Error Handling + Recheck + Stability
# =========================

# =========================
# FORCE JOIN RECHECK BUTTON
# =========================
@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck_join(c):
    uid = c.from_user.id

    if not force_block(uid):
        try:
            bot.edit_message_text(
                "✅ Access Granted!",
                uid,
                c.message.id
            )
        except:
            pass

        bot.send_message(uid, "🎉 Welcome!", reply_markup=main_menu(uid))
    else:
        bot.answer_callback_query(c.id, "❌ Join all channels first!", show_alert=True)

# =========================
# SAFE SEND FUNCTIONS
# =========================
def safe_send(uid, text=None, kb=None):
    try:
        if text:
            bot.send_message(uid, text, reply_markup=kb)
    except Exception as e:
        print(f"[SEND ERROR] {uid} -> {e}")

def safe_copy(uid, chat, msg):
    try:
        bot.copy_message(uid, chat, msg)
    except Exception as e:
        print(f"[COPY ERROR] {uid} -> {e}")

# =========================
# FALLBACK HANDLER
# =========================
@bot.message_handler(content_types=['text','photo','video','document'])
def fallback_handler(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    # Ignore known commands handled already
    known = [
        "📂 FREE METHODS","💎 VIP METHODS",
        "📦 PREMIUM APPS","🎓 PREMIUM COURSES",
        "💰 POINTS","⭐ BUY VIP","🎁 REFERRAL",
        "👤 ACCOUNT","🆔 CHAT ID","🏆 Redeem",
        "⚙️ ADMIN PANEL"
    ]

    if m.text not in known:
        safe_send(uid, "❌ Use menu buttons only", main_menu(uid))

# =========================
# AUTO RESTART POLLING
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT RUNNING...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(5)

# =========================
# START THREAD
# =========================
threading.Thread(target=run_bot).start()
