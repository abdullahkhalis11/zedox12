# =========================
# ZEDOX BOT - PART 1 (UPDATED)
# Core Setup + User + Force Join Strict
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
        self.users = load("users.json")

        if self.uid not in self.users:
            self.users[self.uid] = {
                "points": 0,
                "vip": False,
                "ref": None
            }
            save("users.json", self.users)

        self.data = self.users[self.uid]

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
# FORCE JOIN (STRICT)
# =========================
class ForceJoin:
    def __init__(self):
        self.config = load("config.json")

    def check(self, uid):
        for ch in self.config["force_channels"]:
            try:
                member = bot.get_chat_member(ch, uid)
                if member.status in ["left", "kicked"]:
                    return False
            except:
                return False
        return True

    def buttons(self):
        kb = InlineKeyboardMarkup()
        for ch in self.config["force_channels"]:
            kb.add(
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=f"https://t.me/{ch.replace('@','')}"
                )
            )
        kb.add(InlineKeyboardButton("✅ Joined", callback_data="recheck"))
        return kb

force = ForceJoin()

# =========================
# STRICT BLOCK FUNCTION
# =========================
def force_block(uid):
    if not force.check(uid):
        bot.send_message(
            uid,
            "🚫 *Join All Channels First 🥇*",
            reply_markup=force.buttons()
        )
        return True
    return False

# =========================
# REFERRAL
# =========================
class Referral:
    def __init__(self):
        self.users = load("users.json")
        self.config = load("config.json")

    def handle(self, uid, args):
        user = User(uid)

        if len(args) > 1:
            ref = args[1]

            if ref != str(uid) and ref in self.users and not user.data["ref"]:
                self.users[ref]["points"] += self.config["ref_reward"]
                user.set_ref(ref)
                save("users.json", self.users)
                # =========================
# ZEDOX BOT - PART 2 (UPDATED)
# Admin Panel + Folder Management + Courses
# =========================

# =========================
# CHECK ADMIN
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("➕ Add VIP", "➖ Remove VIP", "💰 Give Points")
    kb.row("📝 Set Points", "⭐ Set VIP Message", "🏠 Set Welcome Message")

    kb.row("📦 Upload FREE", "💎 Upload VIP", "📱 Upload APPS")
    kb.row("🎓 Upload COURSES")  # ✅ NEW

    kb.row("✏️ Edit Folder", "🗑 Delete Folder")

    kb.row("➕ Add Force Join", "➖ Remove Force Join")
    kb.row("📤 Broadcast", "🧮 Stats")

    kb.row("🏆 Generate Codes")
    kb.row("❌ Exit Admin")

    bot.send_message(m.from_user.id, "🛠️ *Admin Panel*", reply_markup=kb)

# =========================
# EXIT ADMIN
# =========================
@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin Panel.", reply_markup=main_menu(m.from_user.id))

# =========================
# ADD VIP
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add VIP" and is_admin(m.from_user.id))
def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID:")
    bot.register_next_step_handler(msg, add_vip_step2)

def add_vip_step2(m):
    try:
        user = User(int(m.text))
        user.make_vip()
        bot.send_message(m.from_user.id, "✅ VIP Added")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID")

# =========================
# REMOVE VIP
# =========================
@bot.message_handler(func=lambda m: m.text == "➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID:")
    bot.register_next_step_handler(msg, remove_vip_step2)

def remove_vip_step2(m):
    try:
        user = User(int(m.text))
        user.remove_vip()
        bot.send_message(m.from_user.id, "✅ VIP Removed")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID")

# =========================
# GIVE POINTS
# =========================
@bot.message_handler(func=lambda m: m.text == "💰 Give Points" and is_admin(m.from_user.id))
def give_points_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID:")
    bot.register_next_step_handler(msg, give_points_step2)

def give_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "Send Points:")
        bot.register_next_step_handler(msg, lambda m2: give_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID")

def give_points_step3(m, uid):
    try:
        pts = int(m.text)
        User(uid).add_points(pts)
        bot.send_message(m.from_user.id, f"✅ {pts} points added")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number")

# =========================
# SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text == "📝 Set Points" and is_admin(m.from_user.id))
def set_points_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID:")
    bot.register_next_step_handler(msg, set_points_step2)

def set_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "Send New Points:")
        bot.register_next_step_handler(msg, lambda m2: set_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID")

def set_points_step3(m, uid):
    try:
        pts = int(m.text)
        User(uid).set_points(pts)
        bot.send_message(m.from_user.id, "✅ Points updated")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid")

# =========================
# EDIT FOLDER (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Folder" and is_admin(m.from_user.id))
def edit_folder_step1(m):
    msg = bot.send_message(m.from_user.id, "Send Category:\n(free/vip/apps/courses)")
    bot.register_next_step_handler(msg, edit_folder_step2)

def edit_folder_step2(m):
    cat = m.text.lower()
    db = load("db.json")

    if cat not in db:
        bot.send_message(m.from_user.id, "❌ Invalid category")
        return

    msg = bot.send_message(m.from_user.id, "Send Folder Name:")
    bot.register_next_step_handler(msg, lambda m2: edit_folder_step3(m2, cat))

def edit_folder_step3(m, cat):
    name = m.text
    db = load("db.json")

    if name not in db[cat]:
        bot.send_message(m.from_user.id, "❌ Folder not found")
        return

    msg = bot.send_message(m.from_user.id, "Send New Price:")
    bot.register_next_step_handler(msg, lambda m2: edit_folder_step4(m2, cat, name))

def edit_folder_step4(m, cat, name):
    try:
        price = int(m.text)
        db = load("db.json")
        db[cat][name]["price"] = price
        save("db.json", db)
        bot.send_message(m.from_user.id, "✅ Folder price updated")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price")

# =========================
# DELETE FOLDER (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_folder_step1(m):
    msg = bot.send_message(m.from_user.id, "Send Category:\n(free/vip/apps/courses)")
    bot.register_next_step_handler(msg, delete_folder_step2)

def delete_folder_step2(m):
    cat = m.text.lower()
    db = load("db.json")

    if cat not in db:
        bot.send_message(m.from_user.id, "❌ Invalid category")
        return

    msg = bot.send_message(m.from_user.id, "Send Folder Name:")
    bot.register_next_step_handler(msg, lambda m2: delete_folder_step3(m2, cat))

def delete_folder_step3(m, cat):
    name = m.text
    db = load("db.json")

    if name in db[cat]:
        del db[cat][name]
        save("db.json", db)
        bot.send_message(m.from_user.id, "✅ Folder deleted")
    else:
        bot.send_message(m.from_user.id, "❌ Folder not found")

# =========================
# FORCE JOIN MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and is_admin(m.from_user.id))
def add_force(m):
    msg = bot.send_message(m.from_user.id, "Send channel @username:")
    bot.register_next_step_handler(msg, add_force2)

def add_force2(m):
    config = load("config.json")
    if m.text not in config["force_channels"]:
        config["force_channels"].append(m.text)
        save("config.json", config)
        bot.send_message(m.from_user.id, "✅ Added")
    else:
        bot.send_message(m.from_user.id, "Already exists")

@bot.message_handler(func=lambda m: m.text == "➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force(m):
    msg = bot.send_message(m.from_user.id, "Send channel @username:")
    bot.register_next_step_handler(msg, remove_force2)

def remove_force2(m):
    config = load("config.json")
    if m.text in config["force_channels"]:
        config["force_channels"].remove(m.text)
        save("config.json", config)
        bot.send_message(m.from_user.id, "✅ Removed")
    else:
        bot.send_message(m.from_user.id, "Not found")

# =========================
# STATS
# =========================
@bot.message_handler(func=lambda m: m.text == "🧮 Stats" and is_admin(m.from_user.id))
def stats(m):
    users = load("users.json")
    total = len(users)
    vip = sum(1 for u in users.values() if u["vip"])

    bot.send_message(
        m.from_user.id,
        f"📊 Users: {total}\n💎 VIP: {vip}\n🆓 Free: {total-vip}"
    )

# =========================
# GENERATE CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Generate Codes" and is_admin(m.from_user.id))
def gen_code1(m):
    msg = bot.send_message(m.from_user.id, "Send Points:")
    bot.register_next_step_handler(msg, gen_code2)

def gen_code2(m):
    try:
        pts = int(m.text)
        msg = bot.send_message(m.from_user.id, "How many codes?")
        bot.register_next_step_handler(msg, lambda m2: gen_code3(m2, pts))
    except:
        bot.send_message(m.from_user.id, "Invalid")

def gen_code3(m, pts):
    try:
        count = int(m.text)
        codes = codesys.generate(pts, count)
        bot.send_message(m.from_user.id, "\n".join(codes))
    except:
        bot.send_message(m.from_user.id, "Invalid")
        # =========================
# ZEDOX BOT - PART 3 (UPDATED)
# Upload System + Courses + Redeem + Broadcast
# =========================

# =========================
# UPLOAD SYSTEM (FIXED)
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
# HANDLE FILE UPLOAD
# =========================
@bot.message_handler(content_types=["document", "photo", "video"])
def handle_upload_files(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    session = upload_sessions[uid]

    f = {
        "chat": m.chat.id,
        "msg": m.message_id,
        "type": m.content_type
    }

    session["files"].append(f)

    bot.send_message(uid, "✅ File saved")

# =========================
# FINISH UPLOAD
# =========================
@bot.message_handler(commands=["done"])
def finish_upload(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    bot.send_message(uid, "✏️ Send folder name:")
    bot.register_next_step_handler(m, upload_folder_name)

def upload_folder_name(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    upload_sessions[uid]["name"] = m.text

    bot.send_message(uid, "💰 Send price (0 = free):")
    bot.register_next_step_handler(m, upload_folder_price)

def upload_folder_price(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    try:
        price = int(m.text)

        session = upload_sessions[uid]
        db = load("db.json")

        category = session["category"]
        name = session["name"]

        db[category][name] = {
            "files": session["files"],
            "price": price
        }

        save("db.json", db)

        del upload_sessions[uid]

        bot.send_message(uid, f"✅ Folder `{name}` added in `{category}`")

    except:
        bot.send_message(uid, "❌ Invalid price")

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

# ✅ NEW COURSES
@bot.message_handler(func=lambda m: m.text == "🎓 Upload COURSES" and is_admin(m.from_user.id))
def upload_courses(m):
    start_upload(m.from_user.id, "courses")

# =========================
# REDEEM SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeem_start(m):
    if force_block(m.from_user.id):
        return

    msg = bot.send_message(m.from_user.id, "✏️ Send your code:")
    bot.register_next_step_handler(msg, redeem_process)

def redeem_process(m):
    user = User(m.from_user.id)

    success, pts = codesys.redeem(m.text.strip(), user)

    if success:
        bot.send_message(
            m.from_user.id,
            f"✅ Redeemed!\n💰 +{pts} points\nTotal: {user.points()}"
        )
    else:
        bot.send_message(m.from_user.id, "❌ Invalid code")

# =========================
# BROADCAST SYSTEM (IMPROVED)
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_menu(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All", callback_data="bc_all"),
        InlineKeyboardButton("VIP", callback_data="bc_vip"),
        InlineKeyboardButton("FREE", callback_data="bc_free")
    )

    bot.send_message(m.from_user.id, "📢 Select audience:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc_") and is_admin(c.from_user.id))
def broadcast_select(c):
    target = c.data.split("_")[1]

    bot.answer_callback_query(c.id)

    msg = bot.send_message(c.from_user.id, "Send message to broadcast:")
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

    bot.send_message(ADMIN_ID, f"📢 Sent to {sent} users")
    # =========================
# ZEDOX BOT - PART 4 (FINAL)
# Pagination + Courses + Strict Force Join
# =========================

# =========================
# MAIN MENU
# =========================
def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("📂 FREE METHODS", "💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS", "🎓 PREMIUM COURSES")  # ✅ NEW
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
def start(m):
    uid = m.from_user.id

    # 🚫 BLOCK FIRST
    if force_block(uid):
        return

    args = m.text.split()
    Referral().handle(uid, args)

    config = load("config.json")
    bot.send_message(uid, config["welcome"], reply_markup=main_menu(uid))

# =========================
# CATEGORY BUTTON HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text in [
    "📂 FREE METHODS",
    "💎 VIP METHODS",
    "📦 PREMIUM APPS",
    "🎓 PREMIUM COURSES"
])
def category_handler(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    text = m.text

    cat_map = {
        "📂 FREE METHODS": "free",
        "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps",
        "🎓 PREMIUM COURSES": "courses"
    }

    category = cat_map[text]

    send_page(uid, category, 0)

# =========================
# PAGINATION SYSTEM
# =========================
PAGE_SIZE = 10

def send_page(uid, category, page):
    db = load("db.json")
    folders = list(db.get(category, {}).items())

    total = len(folders)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    kb = InlineKeyboardMarkup()

    for name, info in folders[start:end]:
        price = info.get("price", 0)
        txt = f"{name} [{price} pts]" if price > 0 else name

        kb.add(InlineKeyboardButton(
            txt,
            callback_data=f"open|{category}|{name}"
        ))

    # Pagination buttons
    nav = []

    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page|{category}|{page-1}"))

    if end < total:
        nav.append(InlineKeyboardButton("➡️ Next", callback_data=f"page|{category}|{page+1}"))

    if nav:
        kb.row(*nav)

    bot.send_message(uid, f"📂 {category.upper()} (Page {page+1})", reply_markup=kb)

# =========================
# PAGE SWITCH
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page"))
def page_callback(c):
    uid = c.from_user.id

    if force_block(uid):
        return

    _, category, page = c.data.split("|")
    page = int(page)

    bot.answer_callback_query(c.id)
    send_page(uid, category, page)

# =========================
# OPEN FOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open"))
def open_folder(c):
    uid = c.from_user.id

    if force_block(uid):
        return

    _, category, name = c.data.split("|")

    user = User(uid)
    db = load("db.json")

    folder = db.get(category, {}).get(name)

    if not folder:
        bot.answer_callback_query(c.id, "❌ Not found")
        return

    # VIP check
    if category == "vip" and not user.is_vip():
        bot.send_message(uid, load("config.json")["vip_msg"])
        return

    price = folder.get("price", 0)

    # Points check
    if price > 0 and not user.is_vip():
        if user.points() < price:
            bot.answer_callback_query(c.id, "❌ Not enough points")
            return

        user.add_points(-price)

    # Send files
    sent = 0

    for f in folder["files"]:
        try:
            bot.copy_message(uid, f["chat"], f["msg"])
            sent += 1
        except:
            continue

    if load("config.json")["notify"]:
        bot.send_message(uid, f"✅ Sent {sent} files from {name}")

# =========================
# FORCE JOIN RECHECK
# =========================
@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck(c):
    uid = c.from_user.id

    if force_block(uid):
        return

    bot.send_message(uid, "✅ Access Granted", reply_markup=main_menu(uid))

# =========================
# GENERAL COMMANDS
# =========================
@bot.message_handler(func=lambda m: True)
def main_handler(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    user = User(uid)
    text = m.text.lower()

    if text in ["💰 points", "points"]:
        bot.send_message(uid, f"💰 Points: {user.points()}")

    elif text in ["⭐ buy vip", "buy vip"]:
        bot.send_message(uid, load("config.json")["vip_msg"])

    elif text in ["🎁 referral", "referral"]:
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🔗 Your referral link:\n{link}")

    elif text in ["👤 account", "account"]:
        status = "VIP" if user.is_vip() else "FREE"
        bot.send_message(uid, f"👤 Status: {status}\n💰 Points: {user.points()}")

    elif text in ["🆔 chat id", "chat id"]:
        bot.send_message(uid, f"🆔 `{uid}`")

# =========================
# SAFE POLLING
# =========================
def run_bot():
    while True:
        try:
            print("🚀 Bot Running...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Error:", e)
            time.sleep(5)

threading.Thread(target=run_bot).start()
