# =========================
# ZEDOX BOT - PART 1 (FULL FINAL)
# =========================

import os, json, time, random, string
import telebot
from telebot.types import *

# =========================
# ENV (RAILWAY)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# INIT FILES
# =========================
def init():
    data = {
        "users.json": {},
        "db.json": {"free": {}, "vip": {}, "apps": {}, "custom": {}},
        "config.json": {
            "force_channels": [],
            "welcome": "🔥 *Welcome to ZEDOX BOT*",
            "vip_msg": "💎 Buy VIP to unlock",
            "ref_reward": 5,
            "notify": True
        },
        "codes.json": {}
    }

    for f, d in data.items():
        if not os.path.exists(f):
            with open(f, "w") as x:
                json.dump(d, x, indent=4)

init()

def load(f): return json.load(open(f))
def save(f, d): json.dump(d, open(f, "w"), indent=4)

# =========================
# USER SYSTEM
# =========================
class User:
    def __init__(self, uid):
        self.uid = str(uid)
        users = load("users.json")

        if self.uid not in users:
            users[self.uid] = {"points":0,"vip":False,"ref":None}
            save("users.json", users)

        self.data = users[self.uid]

    def save(self):
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

    def add_points(self, p):
        self.data["points"] += p
        self.save()

    def set_points(self, p):
        self.data["points"] = p
        self.save()

    def is_vip(self): return self.data["vip"]
    def make_vip(self): self.data["vip"]=True; self.save()
    def remove_vip(self): self.data["vip"]=False; self.save()
    def points(self): return self.data["points"]

# =========================
# FORCE JOIN (FIXED)
# =========================
def check_force(uid):
    config = load("config.json")
    for ch in config["force_channels"]:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status in ["left","kicked"]:
                return False
        except:
            return False
    return True

def force_buttons():
    kb = InlineKeyboardMarkup()
    for ch in load("config.json")["force_channels"]:
        kb.add(InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch.replace('@','')}"))
    kb.add(InlineKeyboardButton("✅ I Joined", callback_data="recheck"))
    return kb

# =========================
# REFERRAL SYSTEM
# =========================
def handle_ref(uid, args):
    users = load("users.json")
    config = load("config.json")
    user = User(uid)

    if len(args)>1:
        ref = args[1]
        if ref != str(uid) and ref in users and not user.data["ref"]:
            users[ref]["points"] += config["ref_reward"]
            user.data["ref"] = ref
            save("users.json", users)

# =========================
# FILE SYSTEM
# =========================
def db(): return load("db.json")
def save_db(d): save("db.json", d)

def add_folder(cat, name, files, price):
    d = db()
    d[cat][name] = {"files": files, "price": price}
    save_db(d)

def delete_folder(cat, name):
    d = db()
    if name in d[cat]:
        del d[cat][name]
        save_db(d)
        return True
    return False

def edit_price(cat, name, price):
    d = db()
    if name in d[cat]:
        d[cat][name]["price"] = price
        save_db(d)
        return True
    return False

# =========================
# CODES SYSTEM
# =========================
def gen_codes(points, count):
    codes = load("codes.json")
    result = []

    for _ in range(count):
        code = "ZEDOX" + ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
        codes[code] = points
        result.append(code)

    save("codes.json", codes)
    return result

def redeem_code(code, user):
    codes = load("codes.json")
    if code in codes:
        pts = codes[code]
        user.add_points(pts)
        del codes[code]
        save("codes.json", codes)
        return True, pts
    return False, 0
    # =========================
# ZEDOX BOT - PART 2 (ADMIN FULL FINAL)
# =========================

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text=="⚙️ ADMIN" and is_admin(m.from_user.id))
def admin_panel(m):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("➕ Add VIP","➖ Remove VIP")
    kb.row("💰 Give Points","📝 Set Points")
    kb.row("⭐ Set VIP Msg","🏠 Set Welcome")
    kb.row("📢 Broadcast","🏆 Generate Codes")
    kb.row("📦 Upload FREE","💎 Upload VIP","📱 Upload APPS")
    kb.row("✏️ Edit Price","🗑 Delete Folder")
    kb.row("➕ Force Join","➖ Force Join")
    kb.row("📊 Stats","❌ Exit")

    bot.send_message(m.chat.id, "🛠 *ADMIN PANEL*", reply_markup=kb)

# =========================
# EXIT ADMIN
# =========================
@bot.message_handler(func=lambda m: m.text=="❌ Exit" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.chat.id,"Exited admin",reply_markup=menu(m.from_user.id))

# =========================
# ADD VIP
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add VIP" and is_admin(m.from_user.id))
def add_vip(m):
    msg = bot.send_message(m.chat.id,"Send user ID")
    bot.register_next_step_handler(msg, add_vip2)

def add_vip2(m):
    try:
        u = User(int(m.text))
        u.make_vip()
        bot.send_message(m.chat.id,"✅ VIP added")
    except:
        bot.send_message(m.chat.id,"❌ Error")

# =========================
# REMOVE VIP
# =========================
@bot.message_handler(func=lambda m: m.text=="➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip(m):
    msg = bot.send_message(m.chat.id,"Send user ID")
    bot.register_next_step_handler(msg, remove_vip2)

def remove_vip2(m):
    try:
        u = User(int(m.text))
        u.remove_vip()
        bot.send_message(m.chat.id,"✅ VIP removed")
    except:
        bot.send_message(m.chat.id,"❌ Error")

# =========================
# GIVE POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="💰 Give Points" and is_admin(m.from_user.id))
def give_points(m):
    msg = bot.send_message(m.chat.id,"User ID?")
    bot.register_next_step_handler(msg, gp2)

def gp2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.chat.id,"Points?")
        bot.register_next_step_handler(msg, lambda x: gp3(x, uid))
    except:
        bot.send_message(m.chat.id,"❌ Error")

def gp3(m, uid):
    try:
        u = User(uid)
        u.add_points(int(m.text))
        bot.send_message(m.chat.id,"✅ Done")
    except:
        bot.send_message(m.chat.id,"❌ Error")

# =========================
# SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="📝 Set Points" and is_admin(m.from_user.id))
def set_points(m):
    msg = bot.send_message(m.chat.id,"User ID?")
    bot.register_next_step_handler(msg, sp2)

def sp2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.chat.id,"New points?")
        bot.register_next_step_handler(msg, lambda x: sp3(x, uid))
    except:
        bot.send_message(m.chat.id,"❌ Error")

def sp3(m, uid):
    try:
        u = User(uid)
        u.set_points(int(m.text))
        bot.send_message(m.chat.id,"✅ Done")
    except:
        bot.send_message(m.chat.id,"❌ Error")

# =========================
# SET VIP MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="⭐ Set VIP Msg" and is_admin(m.from_user.id))
def set_vip_msg(m):
    msg = bot.send_message(m.chat.id,"Send new VIP message")
    bot.register_next_step_handler(msg, set_vip_msg2)

def set_vip_msg2(m):
    cfg = load("config.json")
    cfg["vip_msg"] = m.text
    save("config.json", cfg)
    bot.send_message(m.chat.id,"✅ Updated")

# =========================
# SET WELCOME MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="🏠 Set Welcome" and is_admin(m.from_user.id))
def set_welcome(m):
    msg = bot.send_message(m.chat.id,"Send welcome text")
    bot.register_next_step_handler(msg, set_welcome2)

def set_welcome2(m):
    cfg = load("config.json")
    cfg["welcome"] = m.text
    save("config.json", cfg)
    bot.send_message(m.chat.id,"✅ Updated")

# =========================
# FORCE JOIN ADD (LIVE FIX)
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Force Join" and is_admin(m.from_user.id))
def add_force(m):
    msg = bot.send_message(m.chat.id,"Send channel @username")
    bot.register_next_step_handler(msg, add_force2)

def add_force2(m):
    cfg = load("config.json")
    if m.text not in cfg["force_channels"]:
        cfg["force_channels"].append(m.text)
        save("config.json", cfg)
        bot.send_message(m.chat.id,"✅ Added")
    else:
        bot.send_message(m.chat.id,"Already exists")

# =========================
# FORCE JOIN REMOVE
# =========================
@bot.message_handler(func=lambda m: m.text=="➖ Force Join" and is_admin(m.from_user.id))
def remove_force(m):
    msg = bot.send_message(m.chat.id,"Send channel")
    bot.register_next_step_handler(msg, remove_force2)

def remove_force2(m):
    cfg = load("config.json")
    if m.text in cfg["force_channels"]:
        cfg["force_channels"].remove(m.text)
        save("config.json", cfg)
        bot.send_message(m.chat.id,"✅ Removed")
    else:
        bot.send_message(m.chat.id,"Not found")

# =========================
# STATS
# =========================
@bot.message_handler(func=lambda m: m.text=="📊 Stats" and is_admin(m.from_user.id))
def stats(m):
    users = load("users.json")
    total = len(users)
    vip = sum(1 for u in users.values() if u["vip"])

    bot.send_message(m.chat.id,
        f"👥 Users: {total}\n💎 VIP: {vip}\n🆓 Free: {total-vip}"
    )

# =========================
# MULTIPLE CODE GENERATION (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text=="🏆 Generate Codes" and is_admin(m.from_user.id))
def gen_codes1(m):
    msg = bot.send_message(m.chat.id,"Points per code?")
    bot.register_next_step_handler(msg, gen_codes2)

def gen_codes2(m):
    try:
        pts = int(m.text)
        msg = bot.send_message(m.chat.id,"How many codes?")
        bot.register_next_step_handler(msg, lambda x: gen_codes3(x, pts))
    except:
        bot.send_message(m.chat.id,"❌ Invalid")

def gen_codes3(m, pts):
    try:
        count = int(m.text)
        codes = gen_codes(pts, count)
        bot.send_message(m.chat.id,"✅ Codes:\n"+"\n".join(codes))
    except:
        bot.send_message(m.chat.id,"❌ Error")
        # =========================
# ZEDOX BOT - PART 3 (UPLOAD + BROADCAST + FIXES)
# =========================

# =========================
# UPLOAD SYSTEM (FIXED)
# =========================
upload_sessions = {}

def start_upload(uid, category):
    upload_sessions[uid] = {
        "cat": category,
        "files": []
    }
    bot.send_message(uid, f"📤 Send files for *{category}*\nSend /done when finished")

@bot.message_handler(func=lambda m: m.text=="📦 Upload FREE" and is_admin(m.from_user.id))
def upload_free(m):
    start_upload(m.chat.id, "free")

@bot.message_handler(func=lambda m: m.text=="💎 Upload VIP" and is_admin(m.from_user.id))
def upload_vip(m):
    start_upload(m.chat.id, "vip")

@bot.message_handler(func=lambda m: m.text=="📱 Upload APPS" and is_admin(m.from_user.id))
def upload_apps(m):
    start_upload(m.chat.id, "apps")

# =========================
# HANDLE FILE UPLOAD
# =========================
@bot.message_handler(content_types=['photo','video','document'])
def handle_files(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    file_data = {
        "chat": m.chat.id,
        "msg": m.message_id,
        "type": m.content_type
    }

    upload_sessions[uid]["files"].append(file_data)

    bot.send_message(uid, "✅ File saved. Send more or /done")

# =========================
# FINISH UPLOAD
# =========================
@bot.message_handler(commands=['done'])
def finish_upload(m):
    uid = m.from_user.id

    if uid not in upload_sessions:
        return

    msg = bot.send_message(uid, "✏️ Send folder name")
    bot.register_next_step_handler(msg, save_folder)

def save_folder(m):
    uid = m.from_user.id
    name = m.text

    msg = bot.send_message(uid, "💰 Send price (0 for free)")
    bot.register_next_step_handler(msg, lambda x: save_folder_price(x, name))

def save_folder_price(m, name):
    uid = m.from_user.id

    try:
        price = int(m.text)
        data = upload_sessions.pop(uid)

        add_folder(data["cat"], name, data["files"], price)

        bot.send_message(uid, f"✅ Folder *{name}* added with {price} pts")
    except:
        bot.send_message(uid, "❌ Error")

# =========================
# DELETE FOLDER (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text=="🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_folder_ui(m):
    kb = InlineKeyboardMarkup()
    data = db()

    for cat in data:
        for name in data[cat]:
            kb.add(InlineKeyboardButton(
                f"{name} ({cat})",
                callback_data=f"del|{cat}|{name}"
            ))

    bot.send_message(m.chat.id, "Select folder to delete:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del"))
def delete_folder_cb(c):
    _, cat, name = c.data.split("|")

    if delete_folder(cat, name):
        bot.answer_callback_query(c.id, "✅ Deleted")
    else:
        bot.answer_callback_query(c.id, "❌ Not found")

# =========================
# EDIT PRICE (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text=="✏️ Edit Price" and is_admin(m.from_user.id))
def edit_price_ui(m):
    kb = InlineKeyboardMarkup()
    data = db()

    for cat in data:
        for name in data[cat]:
            kb.add(InlineKeyboardButton(
                f"{name} ({cat})",
                callback_data=f"price|{cat}|{name}"
            ))

    bot.send_message(m.chat.id, "Select folder:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("price"))
def edit_price_cb(c):
    _, cat, name = c.data.split("|")

    msg = bot.send_message(c.from_user.id, f"New price for {name}?")
    bot.register_next_step_handler(msg, lambda m: save_new_price(m, cat, name))

def save_new_price(m, cat, name):
    try:
        price = int(m.text)
        edit_price(cat, name, price)
        bot.send_message(m.chat.id, "✅ Price updated")
    except:
        bot.send_message(m.chat.id, "❌ Error")

# =========================
# BROADCAST (FULL MEDIA SUPPORT)
# =========================
@bot.message_handler(func=lambda m: m.text=="📢 Broadcast" and is_admin(m.from_user.id))
def broadcast_start(m):
    msg = bot.send_message(m.chat.id,"Send message/photo/video/document")
    bot.register_next_step_handler(msg, broadcast_send)

def broadcast_send(m):
    users = load("users.json")
    count = 0

    for uid in users:
        try:
            uid = int(uid)

            if m.content_type == "text":
                bot.send_message(uid, m.text)

            elif m.content_type == "photo":
                bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)

            elif m.content_type == "video":
                bot.send_video(uid, m.video.file_id, caption=m.caption)

            elif m.content_type == "document":
                bot.send_document(uid, m.document.file_id, caption=m.caption)

            count += 1

        except:
            continue

    bot.send_message(ADMIN_ID, f"📢 Sent to {count} users")
    # =========================
# ZEDOX BOT - PART 4 (PAGINATION UI)
# =========================

FOLDERS_PER_PAGE = 8

# =========================
# MAIN MENU
# =========================
def menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE","💎 VIP")
    kb.row("📦 APPS","💰 POINTS")
    kb.row("👤 ACCOUNT","🏆 Redeem")

    if uid == ADMIN_ID:
        kb.row("⚙️ ADMIN")

    return kb

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    args = m.text.split()

    handle_ref(uid, args)
    User(uid)

    if not check_force(uid):
        bot.send_message(uid, "🚫 Join required channels first", reply_markup=force_buttons())
        return

    bot.send_message(uid, load("config.json")["welcome"], reply_markup=menu(uid))

# =========================
# SHOW CATEGORY (PAGE 0)
# =========================
@bot.message_handler(func=lambda m: m.text in ["📂 FREE","💎 VIP","📦 APPS"])
def show_category(m):
    cat_map = {
        "📂 FREE":"free",
        "💎 VIP":"vip",
        "📦 APPS":"apps"
    }

    cat = cat_map[m.text]
    send_folder_page(m.chat.id, cat, 0)

# =========================
# PAGINATION FUNCTION
# =========================
def send_folder_page(uid, cat, page):
    if not check_force(uid):
        bot.send_message(uid,"🚫 Join channels first",reply_markup=force_buttons())
        return

    data = list(db()[cat].items())

    start = page * FOLDERS_PER_PAGE
    end = start + FOLDERS_PER_PAGE
    page_items = data[start:end]

    kb = InlineKeyboardMarkup()

    for name, info in page_items:
        price = info.get("price",0)
        txt = f"{name} ({price} pts)" if price>0 else name
        kb.add(InlineKeyboardButton(txt, callback_data=f"open|{cat}|{name}"))

    # NAVIGATION BUTTONS
    nav = []

    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page|{cat}|{page-1}"))

    if end < len(data):
        nav.append(InlineKeyboardButton("➡️ Next", callback_data=f"page|{cat}|{page+1}"))

    if nav:
        kb.row(*nav)

    bot.send_message(uid, f"📂 {cat.upper()} (Page {page+1})", reply_markup=kb)

# =========================
# PAGE NAVIGATION
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page"))
def page_nav(c):
    _, cat, page = c.data.split("|")
    send_folder_page(c.from_user.id, cat, int(page))

# =========================
# OPEN FOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open"))
def open_folder(c):
    _, cat, name = c.data.split("|")

    uid = c.from_user.id
    user = User(uid)
    folder = db()[cat].get(name)

    if not folder:
        bot.answer_callback_query(c.id,"❌ Not found")
        return

    # VIP CHECK
    if cat=="vip" and not user.is_vip():
        bot.send_message(uid, load("config.json")["vip_msg"])
        return

    # PRICE CHECK
    price = folder.get("price",0)

    if price > 0 and not user.is_vip():
        if user.points() < price:
            bot.answer_callback_query(c.id,"❌ Not enough points")
            return
        user.add_points(-price)

    # SEND FILES
    sent = 0
    for f in folder["files"]:
        try:
            bot.copy_message(uid, f["chat"], f["msg"])
            sent += 1
        except:
            continue

    if load("config.json")["notify"]:
        bot.send_message(uid, f"✅ Sent {sent} files")

# =========================
# RECHECK FORCE JOIN
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck(c):
    if check_force(c.from_user.id):
        bot.send_message(c.from_user.id,"✅ Access Granted",reply_markup=menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id,"❌ Not joined yet")

# =========================
# POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="💰 POINTS")
def points(m):
    u = User(m.from_user.id)
    bot.send_message(m.chat.id, f"💰 Points: {u.points()}")

# =========================
# ACCOUNT
# =========================
@bot.message_handler(func=lambda m: m.text=="👤 ACCOUNT")
def account(m):
    u = User(m.from_user.id)
    status = "VIP" if u.is_vip() else "FREE"

    bot.send_message(
        m.chat.id,
        f"👤 Status: {status}\n💰 Points: {u.points()}"
    )

# =========================
# REDEEM
# =========================
@bot.message_handler(func=lambda m: m.text=="🏆 Redeem")
def redeem(m):
    msg = bot.send_message(m.chat.id,"Send code")
    bot.register_next_step_handler(msg, redeem2)

def redeem2(m):
    user = User(m.from_user.id)
    ok, pts = redeem_code(m.text, user)

    if ok:
        bot.send_message(m.chat.id,f"✅ +{pts} points")
    else:
        bot.send_message(m.chat.id,"❌ Invalid code")

# =========================
# FALLBACK (IMPORTANT)
# =========================
@bot.message_handler(func=lambda m: True)
def fallback(m):
    pass

# =========================
# RUN BOT
# =========================
print("🚀 Bot Running...")
bot.infinity_polling(skip_pending=True)
