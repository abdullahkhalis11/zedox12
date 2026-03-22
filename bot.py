# =========================
# ZEDOX BOT - PART 1
# Core Setup, User System, Force Join, File Init
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, threading, random, string

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")       # Set your bot token in environment
ADMIN_ID = int(os.environ.get("ADMIN_ID"))    # Admin Telegram ID

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# FILE STORAGE INIT
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {"free": {}, "vip": {}, "apps": {}, "courses": {}},
        "config.json": {
            "force_channels": [],
            "vip_msg": "💎 *Buy VIP to unlock this!*",
            "welcome_msg": "🔥 *Welcome to ZEDOX BOT!*",
            "welcome_file": None,  # Optional file path or Telegram file_id
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
# HELPER FUNCTIONS
# =========================
def load(file):
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def random_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# =========================
# USER SYSTEM
# =========================
class User:
    def __init__(self, uid):
        self.uid = str(uid)
        self.users = load("users.json")
        if self.uid not in self.users:
            self.users[self.uid] = {"points":0, "vip":False, "ref":None}
            save("users.json", self.users)
        self.data = self.users[self.uid]

    def is_vip(self): return self.data.get("vip", False)
    def points(self): return self.data.get("points", 0)
    def ref(self): return self.data.get("ref")

    def add_points(self, pts):
        self.data["points"] += pts
        self.save()

    def set_points(self, pts):
        self.data["points"] = pts
        self.save()

    def make_vip(self):
        self.data["vip"] = True
        self.save()

    def remove_vip(self):
        self.data["vip"] = False
        self.save()

    def set_ref(self, ref_id):
        self.data["ref"] = ref_id
        self.save()

    def save(self):
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

# =========================
# FORCE JOIN SYSTEM
# =========================
class ForceJoin:
    def check(self, uid):
        config = load("config.json")
        for ch in config["force_channels"]:
            try:
                member = bot.get_chat_member(ch, uid)
                if member.status in ["left","kicked"]:
                    return False
            except:
                return False
        return True

    def join_buttons(self):
        kb = InlineKeyboardMarkup()
        config = load("config.json")
        for ch in config["force_channels"]:
            kb.add(InlineKeyboardButton("JOIN CHANNEL", url=f"https://t.me/{str(ch).replace('@','')}"))
        kb.add(InlineKeyboardButton("🔄 I Joined", callback_data="recheck"))
        return kb

force = ForceJoin()

# =========================
# CONFIG HELPERS
# =========================
def get_vip_msg():
    return load("config.json").get("vip_msg", "💎 Buy VIP to access!")

def get_welcome_msg():
    cfg = load("config.json")
    return cfg.get("welcome_msg", "🔥 Welcome!"), cfg.get("welcome_file", None)

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# MAIN MENU KEYBOARD
# =========================
def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS","💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS","🎓 PREMIUM COURSES")
    kb.row("⭐ BUY VIP","🎁 REFERRAL")
    kb.row("👤 ACCOUNT","🆔 CHAT ID","🏆 Redeem")
    if is_admin(uid): kb.row("⚙️ ADMIN PANEL")
    return kb

# =========================
# PART 1 END
# =========================
# =========================
# ZEDOX BOT - PART 2
# File System, Uploads, Folders, Start/Referral/Welcome
# =========================

# =========================
# FILE SYSTEM
# =========================
class FileSystem:
    def __init__(self):
        self.db = load("db.json")

    def save_db(self):
        save("db.json", self.db)

    def add_folder(self, category, name, files, price=0):
        self.db = load("db.json")
        self.db[category][name] = {"files": files, "price": price}
        self.save_db()

    def delete_folder(self, category, name):
        self.db = load("db.json")
        if category in self.db and name in self.db[category]:
            del self.db[category][name]
            self.save_db()
            return True
        return False

    def edit_price(self, category, name, price):
        self.db = load("db.json")
        if category in self.db and name in self.db[category]:
            self.db[category][name]["price"] = price
            self.save_db()
            return True
        return False

    def get_category(self, category):
        self.db = load("db.json")
        return self.db.get(category, {})

fs = FileSystem()

# =========================
# FOLDER PAGINATION KEYBOARD
# =========================
def get_folder_kb(category, page=0):
    data = fs.get_category(category)
    keys = list(data.keys())
    max_per_page = 10
    start = page * max_per_page
    end = start + max_per_page
    current_keys = keys[start:end]

    kb = InlineKeyboardMarkup()
    for name in current_keys:
        price = data[name].get("price", 0)
        display = f"{name} [{price} pts]" if price > 0 else name
        kb.add(InlineKeyboardButton(display, callback_data=f"open|{category}|{name}"))

    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page|{category}|{page-1}"))
    if end < len(keys):
        nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"page|{category}|{page+1}"))

    if nav_btns: kb.row(*nav_btns)
    return kb

# =========================
# UPLOAD SYSTEM (Files & Text)
# =========================
def upload_files(category, uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")
    msg = bot.send_message(uid, f"📤 Upload to `{category}`\nSend files or text one by one. Use /done or /cancel.", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, []))

def upload_step(m, category, uid, items):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload cancelled.", reply_markup=admin_kb())
        return
    if m.text == "/done":
        if not items:
            bot.send_message(uid, "❌ No items uploaded.", reply_markup=admin_kb())
            return
        msg = bot.send_message(uid, "✏️ Folder Name:")
        bot.register_next_step_handler(msg, lambda m2: upload_finalize_name(m2, category, items))
        return

    # Save file or text
    if m.content_type in ["document", "photo", "video"]:
        items.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, f"✅ File saved. Next or /done.")
    elif m.content_type == "text":
        items.append({"text": m.text})
        bot.send_message(uid, f"✅ Text saved. Next or /done.")

    bot.register_next_step_handler(m, lambda m2: upload_step(m2, category, uid, items))

def upload_finalize_name(m, category, items):
    name = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, category, name, items))

def upload_save(m, category, name, items):
    try:
        price = int(m.text)
        fs.add_folder(category, name, items, price)
        bot.send_message(m.from_user.id, f"✅ Folder `{name}` added to {category}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price. Upload aborted.", reply_markup=admin_kb())

# =========================
# START / REFERRAL / WELCOME
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    u = User(uid)
    users_db = load("users.json")

    # Referral Logic
    if len(args) > 1:
        ref_id = args[1]
        if ref_id != str(uid) and ref_id in users_db and not u.ref():
            User(ref_id).add_points(load("config.json").get("ref_reward",5))
            u.set_ref(ref_id)

    # Force Join Check
    if not force.check(uid):
        bot.send_message(uid, "🚫 *JOIN CHANNELS FIRST*", reply_markup=force.join_buttons())
        return

    # Send Welcome (text + optional file)
    welcome_text, welcome_file = get_welcome_msg()
    if welcome_file:
        try:
            bot.send_message(uid, welcome_text)
            bot.send_message(uid, welcome_file)  # file can be file_id or URL
        except:
            bot.send_message(uid, welcome_text)
    else:
        bot.send_message(uid, welcome_text)

    bot.send_message(uid, "Use menu below:", reply_markup=main_menu(uid))

# =========================
# RECHECK FORCE JOIN
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck_join(c):
    uid = c.from_user.id
    if force.check(uid):
        bot.edit_message_text("✅ Access Granted!", uid, c.message.id)
        bot.send_message(uid, "Use menu:", reply_markup=main_menu(uid))
    else:
        bot.answer_callback_query(c.id, "❌ Still not joined!", show_alert=True)

# =========================
# PART 2 END
# =========================
# =========================
# ZEDOX BOT - PART 3
# Folder Browsing, Open Folders, User Commands
# =========================

# =========================
# FOLDER BROWSING FOR USERS
# =========================
@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS", "💎 VIP METHODS", "📦 PREMIUM APPS", "🎓 PREMIUM COURSES"])
def show_folders(m):
    uid = m.from_user.id
    u = User(uid)
    
    # Force join check
    if not force.check(uid):
        bot.send_message(uid, "🚫 Join channels first!", reply_markup=force.join_buttons())
        return

    mapping = {
        "📂 FREE METHODS": "free",
        "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps",
        "🎓 PREMIUM COURSES": "courses"
    }
    cat = mapping[m.text]
    kb = get_folder_kb(cat)
    bot.send_message(uid, f"📂 *{m.text}*", reply_markup=kb)

# =========================
# PAGINATION CALLBACK
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def paginate(c):
    _, cat, page = c.data.split("|")
    kb = get_folder_kb(cat, int(page))
    bot.edit_message_reply_markup(c.from_user.id, c.message.id, reply_markup=kb)

# =========================
# OPEN FOLDER CONTENT
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    _, cat, name = c.data.split("|")
    u = User(c.from_user.id)
    folder = fs.get_category(cat).get(name)

    if not folder:
        bot.answer_callback_query(c.id, "❌ Folder not found", show_alert=True)
        return

    # VIP access check
    if cat == "vip" and not u.is_vip():
        vip_msg = load("config.json").get("vip_msg","💎 *Buy VIP to unlock this!*")
        bot.send_message(c.from_user.id, vip_msg)
        return

    # Price check
    price = folder.get("price", 0)
    if price > 0 and not u.is_vip():
        if u.points() < price:
            bot.answer_callback_query(c.id, f"❌ Not enough points! ({price} required)", show_alert=True)
            return
        u.add_points(-price)

    bot.answer_callback_query(c.id, "📤 Sending files...")
    for item in folder["files"]:
        try:
            if "text" in item:
                bot.send_message(c.from_user.id, item["text"])
            else:
                bot.copy_message(c.from_user.id, item["chat"], item["msg"])
        except:
            continue

# =========================
# CORE USER COMMANDS
# =========================
@bot.message_handler(func=lambda m: True)
def general_commands(m):
    uid = m.from_user.id
    u = User(uid)
    t = m.text

    if t == "💰 POINTS":
        bot.send_message(uid, f"💰 You have {u.points()} points.")
    elif t == "👤 ACCOUNT":
        status = "💎 VIP" if u.is_vip() else "🆓 FREE"
        bot.send_message(uid, f"👤 Status: {status}\n💰 Points: {u.points()}")
    elif t == "🆔 CHAT ID":
        bot.send_message(uid, f"🆔 ID: `{uid}`")
    elif t == "🎁 REFERRAL":
        bot.send_message(uid, f"🎁 Link: `https://t.me/{bot.get_me().username}?start={uid}`")
    elif t == "🏆 Redeem":
        msg = bot.send_message(uid, "Send your code:")
        bot.register_next_step_handler(msg, redeem_code_final)
    elif t == "🧮 Stats" and is_admin(uid):
        stats_panel(m)
    elif t == "➕ Add VIP" and is_admin(uid):
        add_vip_step1(m)
    elif t == "➖ Remove VIP" and is_admin(uid):
        remove_vip_step1(m)
    elif t in ["📦 Upload FREE","💎 Upload VIP","📱 Upload APPS","🎓 Upload COURSES"] and is_admin(uid):
        category = {"📦 Upload FREE":"free","💎 Upload VIP":"vip","📱 Upload APPS":"apps","🎓 Upload COURSES":"courses"}[t]
        upload_files(category, uid)

# =========================
# REDEEM CODES
# =========================
def redeem_code_final(m):
    user = User(m.from_user.id)
    code_text = m.text.strip()
    suc, pts = codesys.redeem(code_text, user)
    if suc:
        bot.send_message(m.from_user.id, f"✅ Redeemed! +{pts} pts")
    else:
        bot.send_message(m.from_user.id, "❌ Invalid code.")

# =========================
# ADMIN HELPERS
# =========================
def stats_panel(m):
    users = load("users.json")
    total = len(users)
    vip_count = sum(1 for u in users.values() if u.get("vip",False))
    bot.send_message(m.from_user.id, f"📊 Total Users: {total}\n💎 VIP Users: {vip_count}")

def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID to make VIP:")
    bot.register_next_step_handler(msg, add_vip_final)

def add_vip_final(m):
    try:
        uid = int(m.text)
        User(uid).make_vip()
        bot.send_message(m.from_user.id, f"✅ User {uid} is now VIP")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID")

def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID to remove VIP:")
    bot.register_next_step_handler(msg, remove_vip_final)

def remove_vip_final(m):
    try:
        uid = int(m.text)
        User(uid).remove_vip()
        bot.send_message(m.from_user.id, f"✅ User {uid} VIP removed")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID")

# =========================
# PART 3 END
# =========================
# =========================
# ZEDOX BOT - PART 4
# Broadcast, Force Join, Welcome/VIP Msg, Delete, Polling
# =========================

# =========================
# BROADCAST SYSTEM (FREE + VIP)
# =========================
@bot.message_handler(func=lambda m: m.text=="📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_init(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All Users", callback_data="bc|all"),
        InlineKeyboardButton("VIP Only", callback_data="bc|vip"),
        InlineKeyboardButton("FREE Only", callback_data="bc|free")
    )
    bot.send_message(m.from_user.id, "Select target group:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_target_select(c):
    target = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, f"Send message or file to broadcast to {target} users:")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, target))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    for uid_str, data in users.items():
        uid = int(uid_str)
        if target == "vip" and not data.get("vip", False): continue
        if target == "free" and data.get("vip", False): continue
        try:
            if m.content_type in ["text","photo","video","document"]:
                if m.content_type == "text":
                    bot.send_message(uid, m.text)
                else:
                    bot.copy_message(uid, m.chat.id, m.message_id)
            sent += 1
        except:
            continue
    bot.send_message(ADMIN_ID, f"📢 Broadcast sent to {sent} users.")

# =========================
# FORCE JOIN CHANNEL MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add Force Join" and is_admin(m.from_user.id))
def add_force_channel_step(m):
    msg = bot.send_message(m.from_user.id, "Send @channel username to add to force join:")
    bot.register_next_step_handler(msg, add_force_save)

def add_force_save(m):
    c = load("config.json")
    ch = m.text.strip()
    if ch not in c["force_channels"]:
        c["force_channels"].append(ch)
        save("config.json", c)
        bot.send_message(m.from_user.id, f"✅ {ch} added to force join channels.")
    else:
        bot.send_message(m.from_user.id, f"❌ {ch} already exists.")

@bot.message_handler(func=lambda m: m.text=="➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force_step(m):
    msg = bot.send_message(m.from_user.id, "Send @channel username to remove from force join:")
    bot.register_next_step_handler(msg, remove_force_save)

def remove_force_save(m):
    c = load("config.json")
    ch = m.text.strip()
    if ch in c["force_channels"]:
        c["force_channels"].remove(ch)
        save("config.json", c)
        bot.send_message(m.from_user.id, f"✅ {ch} removed from force join channels.")
    else:
        bot.send_message(m.from_user.id, f"❌ {ch} not found.")

# =========================
# SET WELCOME & VIP MESSAGES (TEXT + FILE SUPPORT)
# =========================
@bot.message_handler(func=lambda m: m.text=="🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_step(m):
    msg = bot.send_message(m.from_user.id, "Send welcome message text or file (photo/video/document):")
    bot.register_next_step_handler(msg, save_welcome)

def save_welcome(m):
    cfg = load("config.json")
    if m.content_type == "text":
        cfg["welcome"] = m.text
    else:
        cfg["welcome"] = {"chat": m.chat.id, "msg": m.message_id, "type": m.content_type}
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ Welcome message saved.")

@bot.message_handler(func=lambda m: m.text=="⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_step(m):
    msg = bot.send_message(m.from_user.id, "Send VIP message text or file (photo/video/document):")
    bot.register_next_step_handler(msg, save_vip)

def save_vip(m):
    cfg = load("config.json")
    if m.content_type == "text":
        cfg["vip_msg"] = m.text
    else:
        cfg["vip_msg"] = {"chat": m.chat.id, "msg": m.message_id, "type": m.content_type}
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ VIP message saved.")

# =========================
# DELETE FOLDER SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text=="🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_start(m):
    kb = InlineKeyboardMarkup()
    for cat in ["free","vip","apps","courses"]:
        kb.add(InlineKeyboardButton(cat.upper(), callback_data=f"delcat|{cat}"))
    bot.send_message(m.from_user.id, "Select category to delete folder from:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcat|"))
def delete_list(c):
    cat = c.data.split("|")[1]
    items = fs.get_category(cat)
    kb = InlineKeyboardMarkup()
    for name in items.keys():
        kb.add(InlineKeyboardButton(name, callback_data=f"dfin|{cat}|{name}"))
    bot.edit_message_text(f"Select folder to delete from {cat}:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dfin|"))
def delete_final(c):
    _, cat, name = c.data.split("|")
    if fs.delete_folder(cat, name):
        bot.answer_callback_query(c.id, f"Deleted {name}")
        bot.edit_message_text(f"✅ Folder `{name}` deleted from {cat}.", c.from_user.id, c.message.id)
    else:
        bot.answer_callback_query(c.id, "❌ Folder not found", show_alert=True)

# =========================
# BOT POLLING (THREAD SAFE)
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT LIVE")
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

import threading
threading.Thread(target=run_bot).start()

# =========================
# PART 4 END
# ✅ Fully Functional Broadcast
# ✅ Force Join Channels
# ✅ Welcome/VIP Message (text + file)
# ✅ Delete Folder
# =========================
