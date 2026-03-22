# =========================
# ZEDOX BOT - PART 1
# Core Setup, User System, VIP, Referral, Force Join
# ✅ Ready for Railway
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, random, string, threading

# =========================
# CONFIGURATION (RAILWAY ENV VARIABLES)
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")      # Set in Railway environment variables
ADMIN_ID = int(os.environ.get("ADMIN_ID"))   # Set in Railway environment variables

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
# REFERRAL SYSTEM
# =========================
class Referral:
    def handle_start(self, uid, args):
        user = User(uid)
        u_db = load("users.json")
        config = load("config.json")
        if len(args) > 1:
            ref = args[1]
            if ref != str(uid) and ref in u_db and not user.ref():
                User(ref).add_points(config.get("ref_reward",5))
                user.set_ref(ref)

# =========================
# FILE SYSTEM & PAGINATION
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
# ZEDOX BOT - PART 2
# Admin Panel, Upload System, Force Join, Broadcast
# =========================

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP","➖ Remove VIP","💰 Give Points")
    kb.row("📝 Set Points","⭐ Set VIP Message","🏠 Set Welcome Message")
    kb.row("📤 Broadcast","🗑 Delete Folder","✏️ Edit Folder Price")
    kb.row("📦 Upload FREE","💎 Upload VIP","📱 Upload APPS","🎓 Upload COURSES")
    kb.row("➕ Add Force Join","➖ Remove Force Join")
    kb.row("🧮 Stats","🏆 Generate Codes","❌ Exit Admin")
    return kb

def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS","💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS","🎓 PREMIUM COURSES")
    kb.row("⭐ BUY VIP","🎁 REFERRAL")
    kb.row("👤 ACCOUNT","🆔 CHAT ID","🏆 Redeem")
    if is_admin(uid): kb.row("⚙️ ADMIN PANEL")
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
# BROADCAST SYSTEM (FULL FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text=="📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_init(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All Users", callback_data="bc|all"),
        InlineKeyboardButton("VIP Users", callback_data="bc|vip"),
        InlineKeyboardButton("Free Users", callback_data="bc|free")
    )
    bot.send_message(m.from_user.id, "Select target audience for broadcast:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_process(c):
    target = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "Send message to broadcast (text or file):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, target))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    for uid, udata in users.items():
        if target == "vip" and not udata["vip"]:
            continue
        if target == "free" and udata["vip"]:
            continue
        try:
            # Broadcast with file if present
            if m.content_type in ["document", "photo", "video"]:
                if m.content_type == "document":
                    bot.send_document(uid, m.document.file_id, caption=m.caption or "")
                elif m.content_type == "photo":
                    bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption or "")
                elif m.content_type == "video":
                    bot.send_video(uid, m.video.file_id, caption=m.caption or "")
            else:
                bot.send_message(uid, m.text)
            sent += 1
        except: continue
    bot.send_message(ADMIN_ID, f"📢 Broadcast sent to {sent} users.")

# =========================
# DELETE SYSTEM
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
    bot.edit_message_text(f"Delete Folder in {cat}:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dfin|"))
def delete_final(c):
    _, cat, name = c.data.split("|")
    fs.delete_folder(cat, name)
    bot.answer_callback_query(c.id, f"Deleted {name}")
    bot.edit_message_text(f"✅ Folder `{name}` has been deleted.", c.from_user.id, c.message.id)

# =========================
# UPLOAD SYSTEM (FILES & TEXT)
# =========================
def upload_files(category, uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")
    msg = bot.send_message(uid, f"📤 Upload to `{category}`\nSend files or text one by one. Use buttons to finish or cancel.", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, []))

def upload_step(m, category, uid, items):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload Cancelled.", reply_markup=admin_kb())
        return
    if m.text == "/done":
        if not items:
            bot.send_message(uid, "❌ No files/text uploaded.")
            return
        msg = bot.send_message(uid, "✏️ Folder Name:")
        bot.register_next_step_handler(msg, lambda m2: upload_finalize_name(m2, category, items))
        return
    # Save files/text
    if m.content_type in ["document","photo","video"]:
        items.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, f"✅ File saved. Send next or /done.")
    elif m.content_type == "text":
        items.append({"text": m.text})
        bot.send_message(uid, f"✅ Text saved. Send next or /done.")
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
# FORCE JOIN ADD/REMOVE
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add Force Join" and is_admin(m.from_user.id))
def add_force_channel_step(m):
    msg = bot.send_message(m.from_user.id, "Send @channel username to add:")
    bot.register_next_step_handler(msg, add_force_save)

def add_force_save(m):
    c = load("config.json")
    c["force_channels"].append(m.text)
    save("config.json", c)
    bot.send_message(m.from_user.id, f"✅ Added {m.text} to force join channels.")

@bot.message_handler(func=lambda m: m.text=="➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force_channel_step(m):
    msg = bot.send_message(m.from_user.id, "Send @channel username to remove:")
    bot.register_next_step_handler(msg, remove_force_save)

def remove_force_save(m):
    c = load("config.json")
    if m.text in c["force_channels"]:
        c["force_channels"].remove(m.text)
        save("config.json", c)
        bot.send_message(m.from_user.id, f"✅ Removed {m.text}")
    else:
        bot.send_message(m.from_user.id, f"❌ {m.text} not found")
        # =========================
# ZEDOX BOT - PART 3
# Folder Browsing, Pagination, VIP Checks, User Commands
# =========================

# =========================
# FOLDER BROWSING & PAGINATION
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
    
    if cat == "vip" and not u.is_vip():
        # Send VIP message
        vip_msg = load("config.json").get("vip_msg","💎 Buy VIP to unlock this!")
        bot.send_message(c.from_user.id, vip_msg)
        return

    # Check points if folder has price
    price = folder.get("price", 0)
    if price > 0 and not u.is_vip():
        if u.points() < price:
            bot.answer_callback_query(c.id, f"❌ Not enough points! ({price} required)", show_alert=True)
            return
        u.add_points(-price)  # Deduct points

    bot.answer_callback_query(c.id, "📤 Sending files/text...")
    for f in folder["files"]:
        try:
            if "text" in f:
                bot.send_message(c.from_user.id, f["text"])
            elif f["type"] == "document":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            elif f["type"] == "photo":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            elif f["type"] == "video":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
        except: continue

# =========================
# START COMMAND / FORCE JOIN / REFERRAL
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    u_db = load("users.json")
    user = User(uid)
    
    # Referral Logic
    if len(args) > 1:
        ref_id = args[1]
        if ref_id != str(uid) and ref_id in u_db and not user.ref():
            reward = load("config.json").get("ref_reward", 5)
            User(ref_id).add_points(reward)
            user.set_ref(ref_id)

    # Force join check
    if not force.check(uid):
        bot.send_message(uid, "🚫 *JOIN CHANNELS FIRST*", reply_markup=force.join_buttons())
        return

    # Send Welcome message (text/file support)
    cfg = load("config.json")
    welcome = cfg.get("welcome","🔥 Welcome!")
    try:
        # Welcome can be file_id (photo, video, document) or text
        if welcome.startswith("file://"):
            fpath = welcome.replace("file://","")
            ext = fpath.split(".")[-1].lower()
            if ext in ["jpg","jpeg","png","webp"]:
                bot.send_photo(uid, open(fpath,"rb"), caption="Welcome!")
            elif ext in ["mp4","mov","mkv"]:
                bot.send_video(uid, open(fpath,"rb"), caption="Welcome!")
            else:
                bot.send_document(uid, open(fpath,"rb"))
        else:
            bot.send_message(uid, welcome)
    except:
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
        bot.answer_callback_query(c.id, "❌ Still not joined!", show_alert=True)

# =========================
# GENERAL USER COMMANDS
# =========================
@bot.message_handler(func=lambda m: True)
def general_commands(m):
    uid = m.from_user.id
    user = User(uid)
    t = m.text
    
    if t == "💰 POINTS":
        bot.send_message(uid, f"💰 You have {user.points()} points.")
    elif t == "👤 ACCOUNT":
        st = "💎 VIP" if user.is_vip() else "🆓 FREE"
        bot.send_message(uid, f"👤 Status: {st}\n💰 Points: {user.points()}")
    elif t == "🆔 CHAT ID":
        bot.send_message(uid, f"🆔 ID: `{uid}`")
    elif t == "🎁 REFERRAL":
        bot.send_message(uid, f"🎁 Link: `https://t.me/{bot.get_me().username}?start={uid}`")
    elif t == "🏆 Redeem":
        msg = bot.send_message(uid, "Send code:")
        bot.register_next_step_handler(msg, redeem_code_final)
    elif t == "🎓 PREMIUM COURSES":
        show_folders(m)
    # Admin commands handled separately
    elif is_admin(uid):
        if t == "🧮 Stats":
            stats_panel(m)
        elif t == "➕ Add VIP":
            add_vip_step1(m)
        elif t == "➕ Add Force Join":
            add_force_channel_step(m)
            # =========================
# ZEDOX BOT - PART 4
# Redeem Codes, Admin, Broadcast, Polling
# =========================

# =========================
# REDEEM CODES SYSTEM
# =========================
class RedeemSystem:
    def __init__(self):
        self.codes = load("codes.json")

    def generate(self, points, count=1):
        new_codes = {}
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.codes[code] = points
            new_codes[code] = points
        save("codes.json", self.codes)
        return new_codes

    def redeem(self, code, user):
        if code in self.codes:
            pts = self.codes[code]
            user.add_points(pts)
            del self.codes[code]
            save("codes.json", self.codes)
            return True, pts
        return False, 0

codesys = RedeemSystem()

def redeem_code_final(m):
    user = User(m.from_user.id)
    suc, pts = codesys.redeem(m.text.strip(), user)
    bot.send_message(m.from_user.id, f"✅ Redeemed! +{pts} pts" if suc else "❌ Invalid Code.")

# =========================
# ADMIN HELPERS
# =========================
def stats_panel(m):
    u = load("users.json")
    bot.send_message(m.from_user.id, f"📊 Total Users: {len(u)}")

def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "Send User ID to make VIP:")
    bot.register_next_step_handler(msg, lambda m2: (User(m2.text).make_vip(), bot.send_message(m.from_user.id, "✅ VIP Granted")))

def add_force_channel_step(m):
    msg = bot.send_message(m.from_user.id, "Send @channel to force join:")
    bot.register_next_step_handler(msg, add_force_save)

def add_force_save(m):
    c = load("config.json")
    if m.text not in c["force_channels"]:
        c["force_channels"].append(m.text)
        save("config.json", c)
        bot.send_message(m.from_user.id, "✅ Force join channel added.")
    else:
        bot.send_message(m.from_user.id, "⚠️ Already exists.")

# =========================
# BROADCAST SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text=="📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_init(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All Users", callback_data="bc|all"),
        InlineKeyboardButton("VIP Only", callback_data="bc|vip"),
        InlineKeyboardButton("Free Only", callback_data="bc|free")
    )
    bot.send_message(m.from_user.id, "Select target for broadcast:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_process(c):
    target = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "Send message for broadcast (text/file supported):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, target))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    for uid in users:
        u = User(uid)
        if target == "vip" and not u.is_vip(): continue
        if target == "free" and u.is_vip(): continue
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
        except: continue
    bot.send_message(ADMIN_ID, f"📢 Broadcast sent to {sent} users.")

# =========================
# UPLOADS SUPPORTING TEXT + FILES
# =========================
def upload_files(category, uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/done", "/cancel")
    msg = bot.send_message(uid, f"📤 Upload to `{category}`\nSend files or text. Use /done to finish, /cancel to abort.", reply_markup=kb)
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, []))

def upload_step(m, category, uid, items):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload Cancelled.", reply_markup=admin_kb())
        return
    if m.text == "/done":
        if not items:
            bot.send_message(uid, "❌ Nothing uploaded.")
            return
        msg = bot.send_message(uid, "✏️ Folder Name:")
        bot.register_next_step_handler(msg, lambda m2: upload_finalize_name(m2, category, items))
        return
    # Save text or file
    if m.content_type == "text":
        items.append({"text": m.text})
    elif m.content_type in ["document", "photo", "video"]:
        items.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, category, uid, items))

def upload_finalize_name(m, cat, items):
    name = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, cat, name, items))

def upload_save(m, cat, name, items):
    try:
        price = int(m.text)
        fs.add_folder(cat, name, items, price)
        bot.send_message(m.from_user.id, f"✅ Folder `{name}` added to {cat}.", reply_markup=admin_kb())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price.", reply_markup=admin_kb())

# Admin commands for uploads
@bot.message_handler(func=lambda m: m.text=="📦 Upload FREE" and is_admin(m.from_user.id))
def up_f(m): upload_files("free", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="💎 Upload VIP" and is_admin(m.from_user.id))
def up_v(m): upload_files("vip", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="📱 Upload APPS" and is_admin(m.from_user.id))
def up_a(m): upload_files("apps", m.from_user.id)
@bot.message_handler(func=lambda m: m.text=="🎓 Upload COURSES" and is_admin(m.from_user.id))
def up_c(m): upload_files("courses", m.from_user.id)

# =========================
# POLLING / BOT START
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
