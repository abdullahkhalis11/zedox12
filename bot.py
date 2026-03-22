# =========================
# ZEDOX BOT - PART 1
# Core Setup + User + DB + Codes + Force Join
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, random, string, threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# INIT FILES
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {"free": {}, "vip": {}, "apps": {}, "courses": {}},
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

def load(f): return json.load(open(f))
def save(f, d): json.dump(d, open(f, "w"), indent=4)

# =========================
# USER
# =========================
class User:
    def __init__(self, uid):
        self.uid = str(uid)
        users = load("users.json")

        if self.uid not in users:
            users[self.uid] = {"points":0,"vip":False,"ref":None}
            save("users.json", users)

        self.data = users[self.uid]

    def is_vip(self): return self.data["vip"]
    def points(self): return self.data["points"]

    def add_points(self, p):
        self.data["points"] += p
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

    def make_vip(self):
        self.data["vip"] = True
        self.add_points(0)

# =========================
# CODES SYSTEM (FIXED)
# =========================
class Codes:
    def __init__(self):
        self.codes = load("codes.json")

    def generate(self, pts, count):
        res = []
        for _ in range(count):
            code = "ZEDOX" + ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
            self.codes[code] = pts
            res.append(code)
        self.save()
        return res

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
# FORCE JOIN (STRICT)
# =========================
def force_block(uid):
    cfg = load("config.json")

    for ch in cfg["force_channels"]:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status in ["left","kicked"]:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.replace('@','')}"))
                kb.add(InlineKeyboardButton("🔄 I Joined", callback_data="recheck"))
                bot.send_message(uid, "🚫 Join all channels first!", reply_markup=kb)
                return True
        except:
            return True
    return False

# =========================
# FILE SYSTEM + PAGINATION
# =========================
class FS:
    def add(self, cat, name, files, price):
        db = load("db.json")
        db[cat][name] = {"files": files, "price": price}
        save("db.json", db)

    def get(self, cat):
        return load("db.json")[cat]

    def delete(self, cat, name):
        db = load("db.json")
        if name in db[cat]:
            del db[cat][name]
            save("db.json", db)
            return True
        return False

    def edit(self, cat, name, price):
        db = load("db.json")
        if name in db[cat]:
            db[cat][name]["price"] = price
            save("db.json", db)
            return True
        return False

fs = FS()

def get_kb(cat, page=0):
    data = list(fs.get(cat).items())
    per = 10
    start = page*per
    items = data[start:start+per]

    kb = InlineKeyboardMarkup()
    for name, d in items:
        price = d["price"]
        txt = f"{name} [{price} pts]" if price>0 else name
        kb.add(InlineKeyboardButton(txt, callback_data=f"open|{cat}|{name}"))

    nav=[]
    if page>0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"page|{cat}|{page-1}"))
    if start+per < len(data):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"page|{cat}|{page+1}"))
    if nav: kb.row(*nav)

    return kb
    # =========================
# ZEDOX BOT - PART 2
# Admin Panel + Upload + Delete + Edit + Broadcast + Codes
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

    kb.row("🏆 Generate Codes", "📤 Broadcast")

    kb.row("⭐ Set VIP Message", "🏠 Set Welcome")

    kb.row("➕ Add Force Join", "➖ Remove Force Join")

    kb.row("❌ Exit Admin")
    return kb

# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    bot.send_message(m.from_user.id, "⚙️ Admin Panel", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "Exited Admin", reply_markup=main_menu(m.from_user.id))

# =========================
# VIP / WELCOME SETTINGS (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip(m):
    msg = bot.send_message(m.from_user.id, "Send VIP message:")
    bot.register_next_step_handler(msg, save_vip)

def save_vip(m):
    cfg = load("config.json")
    cfg["vip_msg"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ Updated")

@bot.message_handler(func=lambda m: m.text == "🏠 Set Welcome" and is_admin(m.from_user.id))
def set_wel(m):
    msg = bot.send_message(m.from_user.id, "Send welcome message:")
    bot.register_next_step_handler(msg, save_wel)

def save_wel(m):
    cfg = load("config.json")
    cfg["welcome"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ Updated")

# =========================
# FORCE JOIN MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and is_admin(m.from_user.id))
def add_force(m):
    msg = bot.send_message(m.from_user.id, "Send @channel:")
    bot.register_next_step_handler(msg, save_force)

def save_force(m):
    cfg = load("config.json")
    if m.text not in cfg["force_channels"]:
        cfg["force_channels"].append(m.text)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, "✅ Added")
    else:
        bot.send_message(m.from_user.id, "Already exists")

@bot.message_handler(func=lambda m: m.text == "➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force(m):
    msg = bot.send_message(m.from_user.id, "Send channel:")
    bot.register_next_step_handler(msg, rem_force)

def rem_force(m):
    cfg = load("config.json")
    if m.text in cfg["force_channels"]:
        cfg["force_channels"].remove(m.text)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, "Removed")
    else:
        bot.send_message(m.from_user.id, "Not found")

# =========================
# UPLOAD SYSTEM (WITH CANCEL)
# =========================
def start_upload(uid, cat):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")

    msg = bot.send_message(uid, f"Upload files to {cat}", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, cat, uid, []))

def upload_step(m, cat, uid, files):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Cancelled", reply_markup=admin_menu())
        return

    if m.text == "/done":
        if not files:
            bot.send_message(uid, "No files")
            return

        msg = bot.send_message(uid, "Folder name:")
        bot.register_next_step_handler(msg, lambda m2: upload_name(m2, cat, files))
        return

    if m.content_type in ["document","photo","video"]:
        files.append({"chat":m.chat.id,"msg":m.message_id,"type":m.content_type})
        bot.send_message(uid, f"Saved {len(files)}")

    bot.register_next_step_handler(m, lambda m2: upload_step(m2, cat, uid, files))

def upload_name(m, cat, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "Price:")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, cat, name, files))

def upload_save(m, cat, name, files):
    try:
        price = int(m.text)
        fs.add(cat, name, files, price)
        bot.send_message(m.from_user.id, "✅ Uploaded", reply_markup=admin_menu())
    except:
        bot.send_message(m.from_user.id, "Invalid")

@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE" and is_admin(m.from_user.id))
def up1(m): start_upload(m.from_user.id, "free")

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP" and is_admin(m.from_user.id))
def up2(m): start_upload(m.from_user.id, "vip")

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS" and is_admin(m.from_user.id))
def up3(m): start_upload(m.from_user.id, "apps")

@bot.message_handler(func=lambda m: m.text == "🎓 Upload COURSES" and is_admin(m.from_user.id))
def up4(m): start_upload(m.from_user.id, "courses")

# =========================
# DELETE SYSTEM (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def del_start(m):
    kb = InlineKeyboardMarkup()
    for c in ["free","vip","apps","courses"]:
        kb.add(InlineKeyboardButton(c, callback_data=f"del|{c}"))
    bot.send_message(m.from_user.id, "Select category", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del|"))
def del_list(c):
    cat = c.data.split("|")[1]
    data = fs.get(cat)

    kb = InlineKeyboardMarkup()
    for name in data:
        kb.add(InlineKeyboardButton(name, callback_data=f"delf|{cat}|{name}"))

    bot.edit_message_text("Select folder", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delf|"))
def del_final(c):
    _, cat, name = c.data.split("|")
    fs.delete(cat, name)
    bot.answer_callback_query(c.id, "Deleted")
    bot.edit_message_text("Done", c.from_user.id, c.message.id)

# =========================
# EDIT PRICE (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Folder Price" and is_admin(m.from_user.id))
def edit_start(m):
    msg = bot.send_message(m.from_user.id, "Category:")
    bot.register_next_step_handler(msg, edit2)

def edit2(m):
    cat = m.text
    msg = bot.send_message(m.from_user.id, "Folder name:")
    bot.register_next_step_handler(msg, lambda m2: edit3(m2, cat))

def edit3(m, cat):
    name = m.text
    msg = bot.send_message(m.from_user.id, "New price:")
    bot.register_next_step_handler(msg, lambda m2: edit4(m2, cat, name))

def edit4(m, cat, name):
    try:
        fs.edit(cat, name, int(m.text))
        bot.send_message(m.from_user.id, "Updated")
    except:
        bot.send_message(m.from_user.id, "Error")

# =========================
# GENERATE CODES (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Generate Codes" and is_admin(m.from_user.id))
def code1(m):
    msg = bot.send_message(m.from_user.id, "Points per code:")
    bot.register_next_step_handler(msg, code2)

def code2(m):
    pts = int(m.text)
    msg = bot.send_message(m.from_user.id, "How many?")
    bot.register_next_step_handler(msg, lambda m2: code3(m2, pts))

def code3(m, pts):
    count = int(m.text)
    res = codesys.generate(pts, count)
    bot.send_message(m.from_user.id, "\n".join(res))

# =========================
# BROADCAST (FIXED PRO)
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def bc_start(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All", callback_data="bc|all"),
        InlineKeyboardButton("VIP", callback_data="bc|vip")
    )
    bot.send_message(m.from_user.id, "Target:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_pick(c):
    t = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "Send message:")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, t))

def bc_send(m, target):
    users = load("users.json")
    sent = 0

    for uid in users:
        if target == "vip" and not users[uid]["vip"]:
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

    bot.send_message(ADMIN_ID, f"Sent to {sent}")
    # =========================
# ZEDOX BOT - PART 3
# User Panel + Start + Folders + Redeem + Referral
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

    # Referral system
    if len(args) > 1:
        ref = args[1]
        users = load("users.json")

        if ref != str(uid) and ref in users and not user.data.get("ref"):
            User(ref).add_points(load("config.json").get("ref_reward", 5))
            user.data["ref"] = ref
            save("users.json", users)

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
# SHOW FOLDERS (ALL CATEGORIES)
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
        reply_markup=get_kb(cat, 0)
    )

# =========================
# PAGINATION HANDLER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def page_handler(c):
    _, cat, page = c.data.split("|")

    bot.edit_message_reply_markup(
        c.from_user.id,
        c.message.id,
        reply_markup=get_kb(cat, int(page))
    )

# =========================
# OPEN FOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    uid = c.from_user.id
    user = User(uid)

    _, cat, name = c.data.split("|")
    folder = fs.get(cat).get(name)

    if not folder:
        bot.answer_callback_query(c.id, "❌ Not found")
        return

    # VIP restriction
    if cat == "vip" and not user.is_vip():
        bot.send_message(uid, load("config.json")["vip_msg"])
        return

    price = folder.get("price", 0)

    # Points system
    if not user.is_vip() and price > 0:
        if user.points() < price:
            bot.answer_callback_query(c.id, "❌ Not enough points", show_alert=True)
            return

        user.add_points(-price)

    bot.answer_callback_query(c.id, "📤 Sending...")

    count = 0
    for f in folder["files"]:
        try:
            bot.copy_message(uid, f["chat"], f["msg"])
            count += 1
        except:
            continue

    if load("config.json").get("notify", True):
        bot.send_message(uid, f"✅ Sent {count} files")

# =========================
# USER COMMANDS
# =========================
@bot.message_handler(func=lambda m: True)
def user_commands(m):
    uid = m.from_user.id
    user = User(uid)

    if force_block(uid):
        return

    t = m.text

    if t == "💰 POINTS":
        bot.send_message(uid, f"💰 Points: {user.points()}")

    elif t == "⭐ BUY VIP":
        bot.send_message(uid, load("config.json")["vip_msg"])

    elif t == "🎁 REFERRAL":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🎁 Your link:\n{link}")

    elif t == "👤 ACCOUNT":
        status = "💎 VIP" if user.is_vip() else "🆓 FREE"
        bot.send_message(uid, f"{status}\nPoints: {user.points()}")

    elif t == "🆔 CHAT ID":
        bot.send_message(uid, f"`{uid}`")

    elif t == "🏆 Redeem":
        msg = bot.send_message(uid, "Send code:")
        bot.register_next_step_handler(msg, redeem_code)

# =========================
# REDEEM FUNCTION
# =========================
def redeem_code(m):
    uid = m.from_user.id
    user = User(uid)

    success, pts = codesys.redeem(m.text.strip(), user)

    if success:
        bot.send_message(uid, f"✅ +{pts} points\nTotal: {user.points()}")
    else:
        bot.send_message(uid, "❌ Invalid code")
        # =========================
# ZEDOX BOT - PART 4
# Final System + Stability + Polling
# =========================

# =========================
# FORCE JOIN RECHECK
# =========================
@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck(c):
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
        bot.answer_callback_query(c.id, "❌ Join all channels first", show_alert=True)

# =========================
# SAFE SEND FUNCTIONS
# =========================
def safe_send(uid, text=None, kb=None):
    try:
        if text:
            bot.send_message(uid, text, reply_markup=kb)
    except Exception as e:
        print(f"[SEND ERROR] {uid}: {e}")

def safe_copy(uid, chat, msg):
    try:
        bot.copy_message(uid, chat, msg)
    except Exception as e:
        print(f"[COPY ERROR] {uid}: {e}")

# =========================
# FALLBACK HANDLER (SAFE)
# =========================
@bot.message_handler(content_types=['text','photo','video','document'])
def fallback(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    known = [
        "📂 FREE METHODS","💎 VIP METHODS",
        "📦 PREMIUM APPS","🎓 PREMIUM COURSES",
        "💰 POINTS","⭐ BUY VIP",
        "🎁 REFERRAL","👤 ACCOUNT",
        "🆔 CHAT ID","🏆 Redeem",
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
# START BOT
# =========================
threading.Thread(target=run_bot).start()
