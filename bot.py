# =========================
# ZEDOX BOT - PART 1
# Core Setup, User System, Force Join, Welcome
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
        "db.json": {"free": {}, "vip": {}, "apps": {}, "courses": {}},
        "config.json": {
            "force_channels": [],
            "vip_msg": "💎 *This is VIP content, get VIP to unlock!*",
            "welcome_msg": "🔥 *Welcome to ZEDOX BOT!*",
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
            except: return False
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
# WELCOME AND VIP MESSAGE HANDLER
# =========================
def send_welcome(uid):
    cfg = load("config.json")
    msg = cfg.get("welcome_msg", "🔥 Welcome!")
    bot.send_message(uid, msg)

def send_vip_msg(uid):
    cfg = load("config.json")
    msg = cfg.get("vip_msg", "💎 VIP content!")
    bot.send_message(uid, msg)

# =========================
# START COMMAND
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
        bot.send_message(uid, "🚫 *Please join the required channels first!*", reply_markup=force.join_buttons())
        return

    send_welcome(uid)
    bot.send_message(uid, "✅ Access granted!")

# =========================
# FORCE JOIN RECHECK BUTTON
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck_join(c):
    if force.check(c.from_user.id):
        bot.edit_message_text("✅ Access Granted!", c.from_user.id, c.message.id)
        send_welcome(c.from_user.id)
    else:
        bot.answer_callback_query(c.id, "❌ Still not joined!", show_alert=True)

# =========================
# RUN BOT
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT PART 1 LIVE")
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

threading.Thread(target=run_bot).start()
# =========================
# ZEDOX BOT - PART 2
# Admin Panel, VIP/Points Management, Settings
# =========================

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN KEYBOARD
# =========================
def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP","➖ Remove VIP","💰 Give Points")
    kb.row("📝 Set Points","⭐ Set VIP Message","🏠 Set Welcome Message")
    kb.row("📤 Broadcast","🧮 Stats","🏆 Generate Codes","❌ Exit Admin")
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
# ADMIN PANEL HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text=="⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    bot.send_message(m.from_user.id, "🛠️ *Admin Panel*", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text=="❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin.", reply_markup=main_menu(m.from_user.id))

# =========================
# ADD VIP
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add VIP" and is_admin(m.from_user.id))
def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to grant VIP:")
    bot.register_next_step_handler(msg, add_vip_step2)

def add_vip_step2(m):
    try:
        uid = int(m.text)
        u = User(uid)
        u.make_vip()
        bot.send_message(m.from_user.id, f"✅ User {uid} is now VIP.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.", reply_markup=admin_kb())

# =========================
# REMOVE VIP
# =========================
@bot.message_handler(func=lambda m: m.text=="➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to remove VIP:")
    bot.register_next_step_handler(msg, remove_vip_step2)

def remove_vip_step2(m):
    try:
        uid = int(m.text)
        u = User(uid)
        u.remove_vip()
        bot.send_message(m.from_user.id, f"✅ User {uid} VIP removed.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.", reply_markup=admin_kb())

# =========================
# GIVE POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="💰 Give Points" and is_admin(m.from_user.id))
def give_points_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to give points:")
    bot.register_next_step_handler(msg, give_points_step2)

def give_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "Send number of points to add:")
        bot.register_next_step_handler(msg, lambda m2: give_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.", reply_markup=admin_kb())

def give_points_step3(m, uid):
    try:
        pts = int(m.text)
        u = User(uid)
        u.add_points(pts)
        bot.send_message(m.from_user.id, f"✅ Added {pts} points to {uid}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.", reply_markup=admin_kb())

# =========================
# SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="📝 Set Points" and is_admin(m.from_user.id))
def set_points_step1(m):
    msg = bot.send_message(m.from_user.id, "Send user ID to set points:")
    bot.register_next_step_handler(msg, set_points_step2)

def set_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "Send number of points to set:")
        bot.register_next_step_handler(msg, lambda m2: set_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.", reply_markup=admin_kb())

def set_points_step3(m, uid):
    try:
        pts = int(m.text)
        u = User(uid)
        u.set_points(pts)
        bot.send_message(m.from_user.id, f"✅ Points of {uid} set to {pts}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.", reply_markup=admin_kb())

# =========================
# SET VIP MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg_step1(m):
    msg = bot.send_message(m.from_user.id, "Send new VIP message (text):")
    bot.register_next_step_handler(msg, set_vip_msg_step2)

def set_vip_msg_step2(m):
    cfg = load("config.json")
    cfg["vip_msg"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ VIP message updated.", reply_markup=admin_kb())

# =========================
# SET WELCOME MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_step1(m):
    msg = bot.send_message(m.from_user.id, "Send new Welcome message (text or file):")
    bot.register_next_step_handler(msg, set_welcome_step2)

def set_welcome_step2(m):
    cfg = load("config.json")
    if m.content_type in ["text"]:
        cfg["welcome_msg"] = m.text
    elif m.content_type in ["photo","video","document"]:
        cfg["welcome_msg"] = f"file:{m.chat.id}-{m.message_id}"  # store file reference
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ Welcome message updated.", reply_markup=admin_kb())
    # =========================
# ZEDOX BOT - PART 3
# Upload System, Delete, User Browsing, Pagination
# =========================

# =========================
# FILE SYSTEM CLASS
# =========================
class FileSystem:
    def __init__(self):
        self.db = load("db.json")

    def save_db(self):
        save("db.json", self.db)

    def add_folder(self, category, name, files, price=0, text=""):
        self.db = load("db.json")
        self.db[category][name] = {"files": files, "price": price, "text": text}
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
# FOLDER PAGINATION
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
# UPLOAD SYSTEM
# =========================
def upload_files(category, uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")
    msg = bot.send_message(uid, f"📤 Upload to `{category}`\nSend files (or text). /done to finish, /cancel to abort.", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, [], ""))

def upload_step(m, category, uid, files, text):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload Cancelled.", reply_markup=admin_kb())
        return
    if m.text == "/done":
        if not files and not text:
            bot.send_message(uid, "❌ Nothing uploaded.")
            return
        msg = bot.send_message(uid, "✏️ Folder Name:")
        bot.register_next_step_handler(msg, lambda m2: upload_finalize_name(m2, category, files, text))
        return

    if m.content_type in ["document","photo","video"]:
        files.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, f"✅ File {len(files)} saved. Next or /done.")
    elif m.content_type == "text":
        text += m.text + "\n"
        bot.send_message(uid, "✅ Text added. Next or /done.")
    
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, category, uid, files, text))

def upload_finalize_name(m, cat, files, text):
    name = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, cat, name, files, text))

def upload_save(m, cat, name, files, text):
    try:
        price = int(m.text)
        fs.add_folder(cat, name, files, price, text)
        bot.send_message(m.from_user.id, f"✅ Folder `{name}` added to {cat}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price. Aborted.", reply_markup=admin_kb())

# Upload shortcuts
@bot.message_handler(func=lambda m: m.text=="📦 Upload FREE" and is_admin(m.from_user.id))
def up_f(m): upload_files("free", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="💎 Upload VIP" and is_admin(m.from_user.id))
def up_v(m): upload_files("vip", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="📱 Upload APPS" and is_admin(m.from_user.id))
def up_a(m): upload_files("apps", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="🎓 Upload COURSES" and is_admin(m.from_user.id))
def up_c(m): upload_files("courses", m.from_user.id)

# =========================
# DELETE SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text=="🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_start(m):
    kb = InlineKeyboardMarkup()
    for cat in ["free","vip","apps","courses"]:
        kb.add(InlineKeyboardButton(cat.upper(), callback_data=f"delcat|{cat}"))
    bot.send_message(m.from_user.id, "Select category to delete from:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcat|"))
def delete_list(c):
    cat = c.data.split("|")[1]
    items = fs.get_category(cat)
    kb = InlineKeyboardMarkup()
    for name in items.keys():
        kb.add(InlineKeyboardButton(name, callback_data=f"dfin|{cat}|{name}"))
    bot.edit_message_text(f"Delete folder in {cat}:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dfin|"))
def delete_final(c):
    _, cat, name = c.data.split("|")
    fs.delete_folder(cat, name)
    bot.answer_callback_query(c.id, f"Deleted {name}")
    bot.edit_message_text(f"✅ Folder `{name}` deleted.", c.from_user.id, c.message.id)

# =========================
# USER FOLDER BROWSING
# =========================
@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS","💎 VIP METHODS","📦 PREMIUM APPS","🎓 PREMIUM COURSES"])
def show_folders(m):
    uid = m.from_user.id
    if not force.check(uid):
        bot.send_message(uid, "🚫 Join channels first!", reply_markup=force.join_buttons())
        return
    
    mapping = {
        "📂 FREE METHODS":"free",
        "💎 VIP METHODS":"vip",
        "📦 PREMIUM APPS":"apps",
        "🎓 PREMIUM COURSES":"courses"
    }
    cat = mapping[m.text]
    bot.send_message(uid, f"📂 *{m.text}*", reply_markup=get_folder_kb(cat))

# Pagination
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def paginate(c):
    _, cat, p = c.data.split("|")
    bot.edit_message_reply_markup(c.from_user.id, c.message.id, reply_markup=get_folder_kb(cat,int(p)))

# Open folder
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    _, cat, name = c.data.split("|")
    u = User(c.from_user.id)
    folder = fs.get_category(cat).get(name)
    
    if cat=="vip" and not u.is_vip():
        bot.send_message(c.from_user.id, load("config.json")["vip_msg"])
        return

    price = folder.get("price",0)
    if not u.is_vip() and price>u.points():
        bot.answer_callback_query(c.id, f"❌ Not enough points! ({price} required)", show_alert=True)
        return
    
    if not u.is_vip() and price>0:
        u.add_points(-price)

    bot.answer_callback_query(c.id, "📤 Sending files...")

    # send text first if exists
    if folder.get("text"):
        bot.send_message(c.from_user.id, folder["text"])

    for f in folder["files"]:
        try: bot.copy_message(c.from_user.id, f["chat"], f["msg"])
        except: continue
        # =========================
# ZEDOX BOT - PART 4
# Broadcast, Redeem Codes, Force Join, Welcome, Admin Settings
# =========================

# =========================
# REDEEM CODES SYSTEM
# =========================
class CodeSystem:
    def __init__(self):
        self.codes = load("codes.json")

    def save(self):
        save("codes.json", self.codes)

    def generate(self, code, points):
        self.codes[code] = points
        self.save()

    def redeem(self, code, user:User):
        if code in self.codes:
            pts = self.codes[code]
            user.add_points(pts)
            del self.codes[code]
            self.save()
            return True, pts
        return False, 0

codesys = CodeSystem()

# =========================
# FORCE JOIN
# =========================
class ForceJoin:
    def check(self, uid):
        config = load("config.json")
        for ch in config["force_channels"]:
            try:
                member = bot.get_chat_member(ch, uid)
                if member.status in ["left","kicked"]: return False
            except: return False
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
# START COMMAND / REFERRAL
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    u = User(uid)

    # Referral
    if len(args)>1:
        ref_id = args[1]
        if ref_id != str(uid) and ref_id in load("users.json") and not u.ref():
            User(ref_id).add_points(load("config.json").get("ref_reward",5))
            u.set_ref(ref_id)

    # Force join check
    if not force.check(uid):
        bot.send_message(uid, "🚫 *JOIN CHANNELS FIRST*", reply_markup=force.join_buttons())
        return

    # Welcome message
    cfg = load("config.json")
    welcome = cfg.get("welcome","🔥 Welcome!")
    if os.path.exists("welcome.txt"):
        with open("welcome.txt","r") as f:
            welcome = f.read()

    # check if media file exists
    if os.path.exists("welcome_file"):
        with open("welcome_file","rb") as f:
            bot.send_message(uid, welcome)
            bot.send_document(uid, f)
    else:
        bot.send_message(uid, welcome)

    bot.send_message(uid, "Use menu:", reply_markup=main_menu(uid))

# =========================
# RECHECK FORCE JOIN
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck_join(c):
    if force.check(c.from_user.id):
        bot.edit_message_text("✅ Access Granted!", c.from_user.id, c.message.id)
        bot.send_message(c.from_user.id, "Use menu:", reply_markup=main_menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id,"❌ Still not joined!", show_alert=True)

# =========================
# BROADCAST SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text=="📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_init(m):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("All Users", callback_data="bc|all"),
           InlineKeyboardButton("VIP Only", callback_data="bc|vip"),
           InlineKeyboardButton("Free Only", callback_data="bc|free"))
    bot.send_message(m.from_user.id,"Select target for broadcast:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_process(c):
    target = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id,"Send message to broadcast (can be text or reply with file):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, target))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    for uid in users:
        if target=="vip" and not users[uid]["vip"]: continue
        if target=="free" and users[uid]["vip"]: continue
        try:
            if m.content_type=="text":
                bot.send_message(uid, m.text)
            else:
                bot.copy_message(uid, m.chat.id, m.message_id)
            sent+=1
        except: continue
    bot.send_message(ADMIN_ID, f"📢 Broadcast sent to {sent} users.")

# =========================
# REDEEM CODE HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text=="🏆 Redeem")
def redeem_start(m):
    msg = bot.send_message(m.from_user.id,"Send code to redeem:")
    bot.register_next_step_handler(msg, redeem_final)

def redeem_final(m):
    user = User(m.from_user.id)
    suc, pts = codesys.redeem(m.text.strip(), user)
    bot.send_message(m.from_user.id, f"✅ Redeemed! +{pts} pts" if suc else "❌ Invalid Code.")

# =========================
# ADMIN: GENERATE CODES
# =========================
@bot.message_handler(func=lambda m: m.text=="🏆 Generate Codes" and is_admin(m.from_user.id))
def generate_codes(m):
    msg = bot.send_message(m.from_user.id,"Send code and points separated by space (e.g. CODE123 10):")
    bot.register_next_step_handler(msg, generate_codes_save)

def generate_codes_save(m):
    try:
        code, pts = m.text.split()
        codesys.generate(code, int(pts))
        bot.send_message(m.from_user.id,f"✅ Code `{code}` generated for {pts} points")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid format")

# =========================
# ADMIN: SET VIP MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg(m):
    msg = bot.send_message(m.from_user.id,"Send VIP message text:")
    bot.register_next_step_handler(msg, set_vip_msg_save)

def set_vip_msg_save(m):
    c = load("config.json")
    c["vip_msg"] = m.text
    save("config.json", c)
    bot.send_message(m.from_user.id,"✅ VIP message updated.")

# =========================
# ADMIN: SET WELCOME MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome(m):
    msg = bot.send_message(m.from_user.id,"Send welcome message text (or reply with file):")
    bot.register_next_step_handler(msg, set_welcome_save)

def set_welcome_save(m):
    if m.content_type=="text":
        c = load("config.json")
        c["welcome"] = m.text
        save("config.json", c)
        bot.send_message(m.from_user.id,"✅ Welcome message updated.")
    else:
        # save file for future
        with open("welcome_file","wb") as f:
            if m.content_type=="document":
                f.write(bot.download_file(bot.get_file(m.document.file_id).file_path))
            elif m.content_type=="photo":
                f.write(bot.download_file(bot.get_file(m.photo[-1].file_id).file_path))
            elif m.content_type=="video":
                f.write(bot.download_file(bot.get_file(m.video.file_id).file_path))
        c = load("config.json")
        c["welcome"] = m.caption or "Welcome!"
        save("config.json", c)
        bot.send_message(m.from_user.id,"✅ Welcome file saved.")

# =========================
# ADMIN: GIVE POINTS / SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="💰 Give Points" and is_admin(m.from_user.id))
def give_points(m):
    msg = bot.send_message(m.from_user.id,"Send ID and points to ADD (e.g. 123456 10):")
    bot.register_next_step_handler(msg, give_points_save)

def give_points_save(m):
    try:
        uid, pts = m.text.split()
        User(int(uid)).add_points(int(pts))
        bot.send_message(m.from_user.id,f"✅ Added {pts} points to {uid}")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid format")

@bot.message_handler(func=lambda m: m.text=="📝 Set Points" and is_admin(m.from_user.id))
def set_points(m):
    msg = bot.send_message(m.from_user.id,"Send ID and points to SET (e.g. 123456 10):")
    bot.register_next_step_handler(msg, set_points_save)

def set_points_save(m):
    try:
        uid, pts = m.text.split()
        User(int(uid)).set_points(int(pts))
        bot.send_message(m.from_user.id,f"✅ Points for {uid} set to {pts}")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid format")
