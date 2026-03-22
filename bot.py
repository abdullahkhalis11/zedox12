# =========================
# ZEDOX BOT - PART 1
# Core + User System + Force Join + File Storage
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, random, string, threading

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# FILE STORAGE INIT
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {"free": {}, "vip": {}, "apps": {}, "courses": {}, "custom": {}},
        "config.json": {
            "force_channels": [],
            "vip_msg": "💎 *Buy VIP to unlock this!*",
            "welcome": "🔥 *Welcome to ZEDOX BOT*",
            "ref_reward": 5,
            "notify": True
        },
        "codes.json": {}
    }
    for f, d in files.items():
        if not os.path.exists(f):
            with open(f,"w") as file:
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
    def points(self): return self.data.get("points",0)
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
                if member.status in ["left","kicked"]: return False
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
# FILE SYSTEM (FREE/VIP/APPS/COURSES)
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
# PART 2 - ADMIN PANEL & USER INTERACTIONS
# =========================

# =========================
# ADMIN CHECK & KEYBOARDS
# =========================
def is_admin(uid): 
    return uid == ADMIN_ID

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP","➖ Remove VIP","💰 Give Points")
    kb.row("📝 Set Points","⭐ Set VIP Message","🏠 Set Welcome Message")
    kb.row("📤 Broadcast","🗑 Delete Folder","✏️ Edit Folder Price")
    kb.row("📦 Upload FREE","💎 Upload VIP","📱 Upload APPS")
    kb.row("🎓 Upload COURSES","➕ Add Force Join","➖ Remove Force Join")
    kb.row("🧮 Stats","🏆 Generate Codes","❌ Exit Admin")
    return kb

def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS","💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS","🎓 PREMIUM COURSES")
    kb.row("⭐ BUY VIP","🎁 REFERRAL")
    kb.row("👤 ACCOUNT","🆔 CHAT ID","🏆 Redeem")
    if uid == ADMIN_ID: kb.row("⚙️ ADMIN PANEL")
    return kb

# =========================
# ADMIN PANEL HANDLERS
# =========================
@bot.message_handler(func=lambda m: m.text=="⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    bot.send_message(m.from_user.id, "🛠️ *Admin Panel*", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text=="❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin.", reply_markup=main_menu(m.from_user.id))

# =========================
# FOLDER BROWSING WITH PAGINATION
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
# SHOW FOLDERS HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS", "💎 VIP METHODS", "📦 PREMIUM APPS", "🎓 PREMIUM COURSES"])
def show_folders(m):
    uid = m.from_user.id
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
    bot.send_message(uid, f"📂 *{m.text}*", reply_markup=get_folder_kb(cat))

@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def paginate(c):
    _, cat, p = c.data.split("|")
    bot.edit_message_reply_markup(c.from_user.id, c.message.id, reply_markup=get_folder_kb(cat, int(p)))

@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    _, cat, name = c.data.split("|")
    u = User(c.from_user.id)
    folder = fs.get_category(cat).get(name)
    
    # VIP check
    if cat == "vip" and not u.is_vip():
        vip_msg = load("config.json")["vip_msg"]
        bot.send_message(c.from_user.id, vip_msg)
        return

    price = folder.get("price", 0)
    if not u.is_vip() and price > u.points():
        bot.answer_callback_query(c.id, f"❌ Not enough points! ({price} required)", show_alert=True)
        return
    
    if not u.is_vip() and price > 0:
        u.add_points(-price)

    bot.answer_callback_query(c.id, "📤 Sending files...")
    for f in folder["files"]:
        try: 
            bot.copy_message(c.from_user.id, f["chat"], f["msg"])
        except: continue

# =========================
# UPLOAD SYSTEM (FILES + OPTIONAL TEXT)
# =========================
def upload_files(category, uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")
    msg = bot.send_message(uid, f"📤 Upload to `{category}`\nSend files one by one or text. Use buttons to finish or cancel.", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, []))

def upload_step(m, category, uid, files):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload Cancelled.", reply_markup=admin_kb())
        return
    if m.text == "/done":
        if not files:
            bot.send_message(uid, "❌ No files uploaded.")
            return
        msg = bot.send_message(uid, "✏️ Folder Name:")
        bot.register_next_step_handler(msg, lambda m2: upload_finalize_name(m2, category, files))
        return
    
    content = {}
    if m.content_type in ["document","photo","video"]:
        content = {"chat": m.chat.id, "msg": m.message_id, "type": m.content_type}
    elif m.content_type == "text":
        content = {"text": m.text}
    else:
        bot.send_message(uid, "❌ Unsupported type. Use text or file.")
        bot.register_next_step_handler(m, lambda m2: upload_step(m2, category, uid, files))
        return

    files.append(content)
    bot.send_message(uid, f"✅ Saved. Next or /done")
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, category, uid, files))

def upload_finalize_name(m, cat, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, cat, name, files))

def upload_save(m, cat, name, files):
    try:
        price = int(m.text)
        fs.add_folder(cat, name, files, price)
        bot.send_message(m.from_user.id, f"✅ Folder `{name}` added to {cat}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price. Aborted.", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text=="📦 Upload FREE" and is_admin(m.from_user.id))
def up_f(m): upload_files("free", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="💎 Upload VIP" and is_admin(m.from_user.id))
def up_v(m): upload_files("vip", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="📱 Upload APPS" and is_admin(m.from_user.id))
def up_a(m): upload_files("apps", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="🎓 Upload COURSES" and is_admin(m.from_user.id))
def up_c(m): upload_files("courses", m.from_user.id)

# =========================
# START COMMAND + WELCOME MESSAGE
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    u_db = load("users.json")
    
    # Referral Logic
    if len(args) > 1:
        ref_id = args[1]
        if ref_id != str(uid) and ref_id in u_db and not User(uid).data.get("ref"):
            User(ref_id).add_points(load("config.json").get("ref_reward", 5))
            User(uid).set_ref(ref_id)

    # Force join check
    if not force.check(uid):
        bot.send_message(uid, "🚫 *JOIN CHANNELS FIRST*", reply_markup=force.join_buttons())
        return

    cfg = load("config.json")
    welcome = cfg.get("welcome","Welcome!")
    
    # Check if welcome is text or media
    if os.path.exists("welcome_media.json"):
        media_data = load("welcome_media.json").get("data")
        if media_data:
            try:
                if media_data.get("type") == "photo":
                    bot.send_photo(uid, media_data["file_id"], caption=welcome)
                elif media_data.get("type") == "video":
                    bot.send_video(uid, media_data["file_id"], caption=welcome)
                elif media_data.get("type") == "document":
                    bot.send_document(uid, media_data["file_id"], caption=welcome)
                else:
                    bot.send_message(uid, welcome)
            except:
                bot.send_message(uid, welcome)
        else:
            bot.send_message(uid, welcome)
    else:
        bot.send_message(uid, welcome)

    bot.send_message(uid, "Use menu:", reply_markup=main_menu(uid))
    # =========================
# PART 3 - BROADCAST, REDEEM, POINTS, VIP, FORCE JOIN
# =========================

# =========================
# BROADCAST SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text=="📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_init(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All Users", callback_data="bc|all"),
        InlineKeyboardButton("VIP Users", callback_data="bc|vip"),
        InlineKeyboardButton("Free Users", callback_data="bc|free")
    )
    bot.send_message(m.from_user.id, "Select target for broadcast:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_process(c):
    target = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "Send message to broadcast (text or file):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, target))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    for uid in users:
        if target == "vip" and not users[uid]["vip"]: continue
        if target == "free" and users[uid]["vip"]: continue
        try:
            # Forward text or files
            if m.content_type in ["document","photo","video"]:
                bot.copy_message(int(uid), m.chat.id, m.message_id)
            else:
                bot.send_message(int(uid), m.text)
            sent += 1
        except: continue
    bot.send_message(ADMIN_ID, f"📢 Broadcast sent to {sent} users.")

# =========================
# REDEEM CODE SYSTEM
# =========================
class CodeSystem:
    def __init__(self):
        self.codes = load("codes.json")
    
    def save(self):
        save("codes.json", self.codes)

    def generate(self, code, points):
        self.codes[code] = {"points": points, "used": False}
        self.save()

    def redeem(self, code, user: User):
        if code in self.codes and not self.codes[code]["used"]:
            pts = self.codes[code]["points"]
            user.add_points(pts)
            self.codes[code]["used"] = True
            self.save()
            return True, pts
        return False, 0

codesys = CodeSystem()

@bot.message_handler(func=lambda m: m.text=="🏆 Generate Codes" and is_admin(m.from_user.id))
def gen_code_step1(m):
    msg = bot.send_message(m.from_user.id, "Enter code:")
    bot.register_next_step_handler(msg, gen_code_step2)

def gen_code_step2(m):
    code = m.text.strip()
    msg = bot.send_message(m.from_user.id, "Enter points for this code:")
    bot.register_next_step_handler(msg, lambda m2: gen_code_save(code, m2))

def gen_code_save(code, m2):
    try:
        pts = int(m2.text)
        codesys.generate(code, pts)
        bot.send_message(m2.from_user.id, f"✅ Code `{code}` generated with {pts} pts.", reply_markup=admin_kb())
    except:
        bot.send_message(m2.from_user.id, "❌ Invalid points. Aborted.", reply_markup=admin_kb())

def redeem_code_final(m):
    user = User(m.from_user.id)
    suc, pts = codesys.redeem(m.text.strip(), user)
    bot.send_message(m.from_user.id, f"✅ Redeemed! +{pts} pts" if suc else "❌ Invalid Code.")

# =========================
# POINTS MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text=="💰 Give Points" and is_admin(m.from_user.id))
def give_points_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to give points:")
    bot.register_next_step_handler(msg, give_points_step2)

def give_points_step2(m):
    uid = m.text.strip()
    if uid.isdigit():
        msg = bot.send_message(m.from_user.id, "Enter points to give:")
        bot.register_next_step_handler(msg, lambda m2: give_points_final(uid, m2))
    else:
        bot.send_message(m.from_user.id, "❌ Invalid ID.", reply_markup=admin_kb())

def give_points_final(uid, m):
    try:
        pts = int(m.text)
        user = User(uid)
        user.add_points(pts)
        bot.send_message(m.from_user.id, f"✅ Gave {pts} points to {uid}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid points.", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text=="📝 Set Points" and is_admin(m.from_user.id))
def set_points_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to set points:")
    bot.register_next_step_handler(msg, set_points_step2)

def set_points_step2(m):
    uid = m.text.strip()
    msg = bot.send_message(m.from_user.id, "Enter points to set:")
    bot.register_next_step_handler(msg, lambda m2: set_points_final(uid, m2))

def set_points_final(uid, m2):
    try:
        pts = int(m2.text)
        User(uid).set_points(pts)
        bot.send_message(m2.from_user.id, f"✅ Points for {uid} set to {pts}.", reply_markup=admin_kb())
    except:
        bot.send_message(m2.from_user.id, "❌ Invalid input.", reply_markup=admin_kb())

# =========================
# VIP SET / REMOVE
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add VIP" and is_admin(m.from_user.id))
def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to make VIP:")
    bot.register_next_step_handler(msg, add_vip_final)

def add_vip_final(m):
    uid = m.text.strip()
    try:
        User(uid).make_vip()
        bot.send_message(m.from_user.id, f"✅ User {uid} is now VIP.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Failed.", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text=="➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to remove VIP:")
    bot.register_next_step_handler(msg, remove_vip_final)

def remove_vip_final(m):
    uid = m.text.strip()
    try:
        User(uid).remove_vip()
        bot.send_message(m.from_user.id, f"✅ VIP removed for {uid}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Failed.", reply_markup=admin_kb())

# =========================
# FORCE JOIN RECHECK
# =========================
@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck_join(c):
    if force.check(c.from_user.id):
        bot.edit_message_text("✅ Access Granted!", c.from_user.id, c.message.id)
        bot.send_message(c.from_user.id, "Use menu:", reply_markup=main_menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id, "❌ Still not joined!", show_alert=True)
        # =========================
# PART 4 - DELETE SYSTEM, VIP/WELCOME MSG, FINAL POLLING
# =========================

# =========================
# DELETE FOLDER SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text=="🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_start(m):
    kb = InlineKeyboardMarkup()
    for cat in ["free", "vip", "apps", "courses"]:
        kb.add(InlineKeyboardButton(cat.upper(), callback_data=f"delcat|{cat}"))
    bot.send_message(m.from_user.id, "Select Category to delete from:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcat|"))
def delete_list(c):
    cat = c.data.split("|")[1]
    items = fs.get_category(cat)
    kb = InlineKeyboardMarkup()
    for name in items.keys():
        kb.add(InlineKeyboardButton(name, callback_data=f"dfin|{cat}|{name}"))
    bot.edit_message_text(f"Select folder to delete in {cat}:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dfin|"))
def delete_final(c):
    _, cat, name = c.data.split("|")
    if fs.delete_folder(cat, name):
        bot.answer_callback_query(c.id, f"✅ Folder `{name}` deleted.")
        bot.edit_message_text(f"✅ Folder `{name}` has been deleted.", c.from_user.id, c.message.id)
    else:
        bot.answer_callback_query(c.id, "❌ Failed to delete.")

# =========================
# SET VIP & WELCOME MESSAGES
# =========================
@bot.message_handler(func=lambda m: m.text=="⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg_step(m):
    msg = bot.send_message(m.from_user.id, "Send VIP message (text or file with caption):")
    bot.register_next_step_handler(msg, save_vip_msg)

def save_vip_msg(m):
    c = load("config.json")
    if m.content_type in ["document","photo","video"]:
        c["vip_msg"] = {"type": m.content_type, "chat": m.chat.id, "msg": m.message_id, "caption": m.caption}
    else:
        c["vip_msg"] = m.text
    save("config.json", c)
    bot.send_message(m.from_user.id, "✅ VIP message updated.", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text=="🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_step(m):
    msg = bot.send_message(m.from_user.id, "Send Welcome message (text or file with caption):")
    bot.register_next_step_handler(msg, save_welcome_msg)

def save_welcome_msg(m):
    c = load("config.json")
    if m.content_type in ["document","photo","video"]:
        c["welcome"] = {"type": m.content_type, "chat": m.chat.id, "msg": m.message_id, "caption": m.caption}
    else:
        c["welcome"] = m.text
    save("config.json", c)
    bot.send_message(m.from_user.id, "✅ Welcome message updated.", reply_markup=admin_kb())

# =========================
# SEND VIP OR WELCOME
# =========================
def send_vip_msg(uid):
    c = load("config.json")["vip_msg"]
    if isinstance(c, dict):
        if c["type"] == "photo":
            bot.send_photo(uid, c["msg"], caption=c.get("caption",""))
        elif c["type"] == "video":
            bot.send_video(uid, c["msg"], caption=c.get("caption",""))
        else:
            bot.copy_message(uid, c["chat"], c["msg"])
    else:
        bot.send_message(uid, c)

def send_welcome_msg(uid):
    c = load("config.json")["welcome"]
    if isinstance(c, dict):
        if c["type"] == "photo":
            bot.send_photo(uid, c["msg"], caption=c.get("caption",""))
        elif c["type"] == "video":
            bot.send_video(uid, c["msg"], caption=c.get("caption",""))
        else:
            bot.copy_message(uid, c["chat"], c["msg"])
    else:
        bot.send_message(uid, c)

# =========================
# FINAL POLLING & BOT START
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT LIVE")
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

threading.Thread(target=run_bot).start()
