# =========================
# ZEDOX BOT - PART 1 (PRO MAX FINAL)
# Core + Config + Ultra Force Join + User System
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, random, string, threading

# =========================
# CONFIG (RAILWAY ENV)
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
            "courses": {}  # ✅ Premium Courses
        },
        "config.json": {
            "force_channels": [],   # @channel1, @channel2
            "vip_msg": "💎 Buy VIP to unlock this feature!",
            "welcome": "🔥 Welcome to ZEDOX BOT",
            "ref_reward": 5,
            "notify": True
        },
        "codes.json": {}
    }

    for file, data in files.items():
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump(data, f, indent=4)

init_files()

# =========================
# JSON HELPERS
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
        users = load("users.json")

        if self.uid not in users:
            users[self.uid] = {
                "points": 0,
                "vip": False,
                "ref": None
            }
            save("users.json", users)

        self.data = users[self.uid]

    def is_vip(self):
        return self.data.get("vip", False)

    def points(self):
        return self.data.get("points", 0)

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

    def set_ref(self, ref):
        self.data["ref"] = ref
        self.save()

    def save(self):
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

# =========================
# ULTRA FORCE JOIN SYSTEM (FIXED)
# =========================
class ForceJoin:
    def check(self, uid):
        config = load("config.json")  # 🔥 always reload

        channels = config.get("force_channels", [])

        if not channels:
            return True  # no channels → allow

        for ch in channels:
            try:
                member = bot.get_chat_member(ch, uid)
                if member.status in ["left", "kicked"]:
                    return False
            except:
                return False

        return True

    def get_buttons(self):
        config = load("config.json")

        kb = InlineKeyboardMarkup()

        for ch in config.get("force_channels", []):
            kb.add(
                InlineKeyboardButton(
                    f"📢 Join {ch}",
                    url=f"https://t.me/{ch.replace('@','')}"
                )
            )

        kb.add(InlineKeyboardButton("✅ I Joined", callback_data="recheck"))
        return kb

force = ForceJoin()

# =========================
# GLOBAL FORCE BLOCK (CRITICAL)
# =========================
def force_block(uid):
    config = load("config.json")

    channels = config.get("force_channels", [])

    # No channels = skip
    if not channels:
        return False

    # If not joined → BLOCK EVERYTHING
    if not force.check(uid):
        bot.send_message(
            uid,
            "🚫 *Join All Channels First 🥇*\n\n"
            "After joining click *I Joined* below 👇",
            reply_markup=force.get_buttons()
        )
        return True

    return False

# =========================
# REFERRAL SYSTEM
# =========================
class Referral:
    def handle(self, uid, args):
        users = load("users.json")
        config = load("config.json")
        user = User(uid)

        if len(args) > 1:
            ref = args[1]

            if ref != str(uid) and ref in users and not user.data["ref"]:
                users[ref]["points"] += config.get("ref_reward", 5)
                user.set_ref(ref)
                save("users.json", users)

# =========================
# FILE SYSTEM (FOLDERS)
# =========================
class FileSystem:
    def add_folder(self, cat, name, files, price):
        db = load("db.json")
        db[cat][name] = {
            "files": files,
            "price": price
        }
        save("db.json", db)

    def delete_folder(self, cat, name):
        db = load("db.json")
        if name in db.get(cat, {}):
            del db[cat][name]
            save("db.json", db)
            return True
        return False

    def edit_price(self, cat, name, price):
        db = load("db.json")
        if name in db.get(cat, {}):
            db[cat][name]["price"] = price
            save("db.json", db)
            return True
        return False

    def get_category(self, cat):
        return load("db.json").get(cat, {})

fs = FileSystem()

# =========================
# COUPON SYSTEM
# =========================
class Codes:
    def __init__(self):
        self.codes = load("codes.json")

    def generate(self, pts, count):
        result = []
        for _ in range(count):
            code = "ZEDOX" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.codes[code] = pts
            result.append(code)
        self.save()
        return result

    def redeem(self, code, user):
        if code in self.codes:
            pts = self.codes[code]
            user.add_points(pts)
            del self.codes[code]
            self.save()
            return True, pts
        return False, 0

    def save(self):
        save("codes.json", self.codes)

codesys = Codes()
# =========================
# ZEDOX BOT - PART 2 (PRO MAX)
# Admin Panel + Config Control + Folder Management
# =========================

# =========================
# CHECK ADMIN
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN PANEL UI
# =========================
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📦 Upload FREE", "💎 Upload VIP")
    kb.row("📱 Upload APPS", "🎓 Upload COURSES")

    kb.row("✏️ Edit Folder", "🗑 Delete Folder")

    kb.row("⭐ Set VIP Message", "🏠 Set Welcome Message")

    kb.row("➕ Add Force Join", "➖ Remove Force Join")

    kb.row("🏆 Generate Codes", "📤 Broadcast")

    kb.row("❌ Exit Admin")

    bot.send_message(m.from_user.id, "🛠️ *Admin Panel*", reply_markup=kb)

# =========================
# EXIT ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin Panel")

# =========================
# SET VIP MESSAGE (FIXED LIVE)
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send new VIP message:")
    bot.register_next_step_handler(msg, save_vip_msg)

def save_vip_msg(m):
    config = load("config.json")
    config["vip_msg"] = m.text
    save("config.json", config)

    bot.send_message(m.from_user.id, "✅ VIP message updated successfully")

# =========================
# SET WELCOME MESSAGE (FIXED LIVE)
# =========================
@bot.message_handler(func=lambda m: m.text == "🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_msg(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send new Welcome message:")
    bot.register_next_step_handler(msg, save_welcome_msg)

def save_welcome_msg(m):
    config = load("config.json")
    config["welcome"] = m.text
    save("config.json", config)

    bot.send_message(m.from_user.id, "✅ Welcome message updated successfully")

# =========================
# FORCE JOIN ADD (LIVE FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and is_admin(m.from_user.id))
def add_force(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send channel username (with @):")
    bot.register_next_step_handler(msg, add_force_save)

def add_force_save(m):
    config = load("config.json")

    ch = m.text.strip()

    if ch not in config["force_channels"]:
        config["force_channels"].append(ch)
        save("config.json", config)
        bot.send_message(m.from_user.id, f"✅ Channel {ch} added")
    else:
        bot.send_message(m.from_user.id, "❌ Already added")

# =========================
# FORCE JOIN REMOVE
# =========================
@bot.message_handler(func=lambda m: m.text == "➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send channel username to remove:")
    bot.register_next_step_handler(msg, remove_force_save)

def remove_force_save(m):
    config = load("config.json")

    ch = m.text.strip()

    if ch in config["force_channels"]:
        config["force_channels"].remove(ch)
        save("config.json", config)
        bot.send_message(m.from_user.id, f"✅ Removed {ch}")
    else:
        bot.send_message(m.from_user.id, "❌ Not found")

# =========================
# EDIT FOLDER (100% WORKING)
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Folder" and is_admin(m.from_user.id))
def edit_folder_step1(m):
    msg = bot.send_message(m.from_user.id, "Send category:\nfree / vip / apps / courses")
    bot.register_next_step_handler(msg, edit_folder_step2)

def edit_folder_step2(m):
    cat = m.text.lower()

    db = load("db.json")
    if cat not in db:
        bot.send_message(m.from_user.id, "❌ Invalid category")
        return

    msg = bot.send_message(m.from_user.id, "Send folder name:")
    bot.register_next_step_handler(msg, lambda x: edit_folder_step3(x, cat))

def edit_folder_step3(m, cat):
    name = m.text

    db = load("db.json")
    if name not in db[cat]:
        bot.send_message(m.from_user.id, "❌ Folder not found")
        return

    msg = bot.send_message(m.from_user.id, "Send new price:")
    bot.register_next_step_handler(msg, lambda x: edit_folder_step4(x, cat, name))

def edit_folder_step4(m, cat, name):
    try:
        price = int(m.text)

        success = fs.edit_price(cat, name, price)

        if success:
            bot.send_message(m.from_user.id, "✅ Folder updated")
        else:
            bot.send_message(m.from_user.id, "❌ Failed")

    except:
        bot.send_message(m.from_user.id, "❌ Invalid number")

# =========================
# DELETE FOLDER (100% WORKING)
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_folder_step1(m):
    msg = bot.send_message(m.from_user.id, "Send category:\nfree / vip / apps / courses")
    bot.register_next_step_handler(msg, delete_folder_step2)

def delete_folder_step2(m):
    cat = m.text.lower()

    db = load("db.json")
    if cat not in db:
        bot.send_message(m.from_user.id, "❌ Invalid category")
        return

    msg = bot.send_message(m.from_user.id, "Send folder name:")
    bot.register_next_step_handler(msg, lambda x: delete_folder_step3(x, cat))

def delete_folder_step3(m, cat):
    name = m.text

    success = fs.delete_folder(cat, name)

    if success:
        bot.send_message(m.from_user.id, "✅ Folder deleted")
    else:
        bot.send_message(m.from_user.id, "❌ Folder not found")

# =========================
# GENERATE CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Generate Codes" and is_admin(m.from_user.id))
def gen_codes_1(m):
    msg = bot.send_message(m.from_user.id, "Send points per code:")
    bot.register_next_step_handler(msg, gen_codes_2)

def gen_codes_2(m):
    try:
        pts = int(m.text)
        msg = bot.send_message(m.from_user.id, "How many codes?")
        bot.register_next_step_handler(msg, lambda x: gen_codes_3(x, pts))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number")

def gen_codes_3(m, pts):
    try:
        count = int(m.text)
        codes = codesys.generate(pts, count)

        bot.send_message(m.from_user.id, "✅ Codes:\n\n" + "\n".join(codes))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number")
# =========================
# ZEDOX BOT - PART 3 (PRO MAX)
# Upload System + Courses + Redeem + Broadcast
# =========================

# =========================
# UPLOAD SESSION SYSTEM (STABLE)
# =========================
upload_sessions = {}

def start_upload(uid, category):
    upload_sessions[uid] = {
        "category": category,
        "files": []
    }

    bot.send_message(
        uid,
        f"📤 Send files for *{category.upper()}*\n\nSend one by one.\nSend /done when finished."
    )

# =========================
# ADMIN UPLOAD BUTTONS
# =========================
@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE" and is_admin(m.from_user.id))
def upload_free(m):
    start_upload(m.from_user.id, "free")

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP" and is_admin(m.from_user.id))
def upload_vip(m):
    start_upload(m.from_user.id, "vip")

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS" and is_admin(m.from_user.id))
def upload_apps(m):
    start_upload(m.from_user.id, "apps")

@bot.message_handler(func=lambda m: m.text == "🎓 Upload COURSES" and is_admin(m.from_user.id))
def upload_courses(m):
    start_upload(m.from_user.id, "courses")

# =========================
# HANDLE FILE RECEIVING
# =========================
@bot.message_handler(content_types=["document", "photo", "video"])
def handle_upload_files(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return  # ignore normal users

    session = upload_sessions[uid]

    file_data = {
        "chat": m.chat.id,
        "msg": m.message_id,
        "type": m.content_type
    }

    session["files"].append(file_data)

    bot.send_message(uid, "✅ File saved. Send more or /done")

# =========================
# FINISH UPLOAD
# =========================
@bot.message_handler(commands=["done"])
def finish_upload(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    bot.send_message(uid, "✏️ Send folder name:")
    bot.register_next_step_handler(m, upload_name)

def upload_name(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    upload_sessions[uid]["name"] = m.text

    msg = bot.send_message(uid, "💰 Send price (0 for free):")
    bot.register_next_step_handler(msg, upload_price)

def upload_price(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    try:
        price = int(m.text)

        session = upload_sessions[uid]
        category = session["category"]
        name = session["name"]
        files = session["files"]

        fs.add_folder(category, name, files, price)

        del upload_sessions[uid]

        bot.send_message(uid, f"✅ Folder `{name}` uploaded successfully")

    except:
        bot.send_message(uid, "❌ Invalid price")

# =========================
# REDEEM SYSTEM (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeem_start(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    msg = bot.send_message(uid, "🎟 Send your redeem code:")
    bot.register_next_step_handler(msg, redeem_process)

def redeem_process(m):
    uid = m.from_user.id
    user = User(uid)

    success, pts = codesys.redeem(m.text.strip(), user)

    if success:
        bot.send_message(
            uid,
            f"✅ Redeemed Successfully!\n💰 +{pts} points\nTotal: {user.points()}"
        )
    else:
        bot.send_message(uid, "❌ Invalid or used code")

# =========================
# BROADCAST SYSTEM (PRO)
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_menu(m):
    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton("All Users", callback_data="bc_all"),
        InlineKeyboardButton("VIP Users", callback_data="bc_vip"),
        InlineKeyboardButton("Free Users", callback_data="bc_free")
    )

    bot.send_message(m.from_user.id, "📢 Select audience:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc_") and is_admin(c.from_user.id))
def broadcast_select(c):
    target = c.data.split("_")[1]

    bot.answer_callback_query(c.id)

    msg = bot.send_message(c.from_user.id, "✏️ Send message (text/photo/video/file):")
    bot.register_next_step_handler(msg, lambda m: broadcast_send(m, target))

def broadcast_send(m, target):
    users = load("users.json")

    sent = 0

    for uid_str, data in users.items():
        uid = int(uid_str)

        if target == "vip" and not data.get("vip"):
            continue

        if target == "free" and data.get("vip"):
            continue

        try:
            if m.content_type == "text":
                bot.send_message(uid, m.text)

            elif m.content_type == "photo":
                bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)

            elif m.content_type == "video":
                bot.send_video(uid, m.video.file_id, caption=m.caption)

            elif m.content_type == "document":
                bot.send_document(uid, m.document.file_id, caption=m.caption)

            sent += 1

        except:
            continue

    bot.send_message(ADMIN_ID, f"📢 Broadcast sent to {sent} users")
# =========================
# ZEDOX BOT - PART 4
# User Panel, Force Join, Folders, Pagination, Safe Send
# =========================

# =========================
# FORCE JOIN CHECK BEFORE START
# =========================
def force_block(uid):
    for ch in load("config.json")["force_channels"]:
        try:
            member = bot.get_chat_member(ch, uid)
            if member.status in ["left", "kicked"]:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton(f"JOIN {ch}", url=f"https://t.me/{ch.replace('@','')}"))
                kb.add(InlineKeyboardButton("🔄 I Joined", callback_data="recheck"))
                bot.send_message(uid, "🚫 ACCESS DENIED! Join all channels first", reply_markup=kb)
                return True
        except:
            continue
    return False

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
# START COMMAND
# =========================
@bot.message_handler(commands=["start"])
def start_bot(m):
    uid = m.from_user.id
    args = m.text.split()
    Referral().handle_start(uid, args)
    user = User(uid)

    # Force join check
    if force_block(uid):
        return

    config = load("config.json")
    bot.send_message(uid, config.get("welcome", "🔥 Welcome!"), reply_markup=main_menu(uid))

# =========================
# PAGINATION + FOLDER BUTTONS
# =========================
folder_pages = {}

def show_folder_page(uid, category, page=0):
    data = fs.get_category(category)
    items = list(data.items())
    per_page = 10
    total_pages = (len(items) - 1) // per_page + 1

    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    kb = InlineKeyboardMarkup()
    for name, info in page_items:
        price = info.get("price",0)
        display_name = f"{name} [{price} pts]" if price>0 else name
        kb.add(InlineKeyboardButton(display_name, callback_data=f"open|{category}|{name}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page|{category}|{page-1}"))
    if page < total_pages-1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page|{category}|{page+1}"))

    if nav:
        kb.row(*nav)

    bot.send_message(uid, f"📂 {category.upper()} - Page {page+1}/{total_pages}", reply_markup=kb)

# =========================
# FOLDER CATEGORY HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text.lower() in [
    "📂 free methods","free methods",
    "💎 vip methods","vip methods",
    "📦 premium apps","premium apps",
    "🎓 premium courses","premium courses"
])
def folder_category_handler(m):
    uid = m.from_user.id
    if force_block(uid):
        return

    text = m.text.lower()
    cat_map = {
        "📂 free methods":"free","free methods":"free",
        "💎 vip methods":"vip","vip methods":"vip",
        "📦 premium apps":"apps","premium apps":"apps",
        "🎓 premium courses":"courses","premium courses":"courses"
    }

    cat = cat_map[text]
    folder_pages[uid] = cat
    show_folder_page(uid, cat, page=0)

# =========================
# PAGE CALLBACK
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def page_callback(c):
    uid = c.from_user.id
    _, category, page = c.data.split("|")
    page = int(page)
    show_folder_page(uid, category, page)

# =========================
# OPEN FOLDER CALLBACK
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder_callback(c):
    uid = c.from_user.id
    user = User(uid)

    _, cat, name = c.data.split("|")
    folder = fs.get_category(cat).get(name)

    if not folder:
        bot.answer_callback_query(c.id, "❌ Folder not found")
        return

    # VIP check
    if cat=="vip" and not user.is_vip():
        bot.send_message(uid, load("config.json").get("vip_msg","💎 Buy VIP to access!"))
        return

    # Price check
    if not user.is_vip() and folder.get("price",0)>0:
        if user.points()<folder["price"]:
            bot.answer_callback_query(c.id,"❌ Not enough points")
            return
        user.add_points(-folder["price"])

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
# FORCE JOIN RECHECK BUTTON
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck_callback(c):
    uid = c.from_user.id
    if not force_block(uid):
        bot.send_message(uid, "✅ Access granted!", reply_markup=main_menu(uid))

# =========================
# SAFE SEND
# =========================
def safe_send(uid, text=None, reply_markup=None):
    try:
        if text:
            bot.send_message(uid, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error sending to {uid}: {e}")
