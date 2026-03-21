# =========================
# ZEDOX BOT - PART 1
# Core Setup, User System, VIP, Referral, Force Join
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, time, random, string, threading

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Set in Railway
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # Set in Railway
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# FILE STORAGE INIT
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {"free": {}, "vip": {}, "apps": {}, "custom": {}},
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

    def is_vip(self):
        return self.data.get("vip", False)

    def points(self):
        return self.data.get("points",0)

    def ref(self):
        return self.data.get("ref")

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
    def __init__(self):
        self.config = load("config.json")

    def check(self, uid):
        for ch in self.config["force_channels"]:
            try:
                member = bot.get_chat_member(ch, uid)
                if member.status in ["left","kicked"]:
                    return False
            except:
                return False
        return True

    def join_buttons(self):
        kb = InlineKeyboardMarkup()
        for ch in self.config["force_channels"]:
            kb.add(InlineKeyboardButton("JOIN CHANNEL", url=f"https://t.me/{str(ch).replace('@','')}"))
        kb.add(InlineKeyboardButton("🔄 I Joined", callback_data="recheck"))
        return kb

force = ForceJoin()

# =========================
# REFERRAL SYSTEM
# =========================
class Referral:
    def __init__(self):
        self.users = load("users.json")
        self.config = load("config.json")

    def handle_start(self, uid, args):
        user = User(uid)
        if len(args) > 1:
            ref = args[1]
            if ref != str(uid) and ref in self.users and not user.ref():
                self.users[ref]["points"] += self.config.get("ref_reward",5)
                user.set_ref(ref)
                save("users.json", self.users)

# =========================
# FILE SYSTEM
# =========================
class FileSystem:
    def __init__(self):
        self.db = load("db.json")

    def save_db(self):
        save("db.json", self.db)

    def add_folder(self, category, name, files, price=0):
        self.db[category][name] = {"files": files, "price": price}
        self.save_db()

    def delete_folder(self, category, name):
        if name in self.db[category]:
            del self.db[category][name]
            self.save_db()
            return True
        return False

    def edit_price(self, category, name, price):
        if name in self.db[category]:
            self.db[category][name]["price"] = price
            self.save_db()
            return True
        return False

    def get_category(self, category):
        return self.db.get(category, {})

fs = FileSystem()
# =========================
# ZEDOX BOT - PART 2
# Admin Panel & Management, Redeem Codes, Broadcast
# =========================

# =========================
# CHECK ADMIN
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN PANEL HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text=="⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    uid = m.from_user.id
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP","➖ Remove VIP","💰 Give Points")
    kb.row("📝 Set Points","⭐ Set VIP Message","🏠 Set Welcome Message")
    kb.row("📤 Broadcast","🗑 Delete Folder","✏️ Edit Folder Price")
    kb.row("📦 Upload FREE","💎 Upload VIP","📱 Upload APPS")
    kb.row("🏷 Generate Coupon","➕ Add Force Join","➖ Remove Force Join")
    kb.row("🧮 Stats","❌ Exit Admin")
    bot.send_message(uid,"🛠️ *Admin Panel*\nSelect an option below:", reply_markup=kb)

# =========================
# EXIT ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text=="❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id,"✅ Exited Admin Panel.", reply_markup=main_menu(m.from_user.id))

# =========================
# ADD VIP
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add VIP" and is_admin(m.from_user.id))
def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the Chat ID of the user to add VIP:")
    bot.register_next_step_handler(msg, add_vip_step2)

def add_vip_step2(m):
    try:
        uid = int(m.text)
        user = User(uid)
        user.make_vip()
        bot.send_message(m.from_user.id,f"✅ User `{uid}` is now VIP.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid Chat ID.")

# =========================
# REMOVE VIP
# =========================
@bot.message_handler(func=lambda m: m.text=="➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the Chat ID of the user to remove VIP:")
    bot.register_next_step_handler(msg, remove_vip_step2)

def remove_vip_step2(m):
    try:
        uid = int(m.text)
        user = User(uid)
        user.remove_vip()
        bot.send_message(m.from_user.id,f"✅ VIP removed for user `{uid}`.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid Chat ID.")

# =========================
# GIVE POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="💰 Give Points" and is_admin(m.from_user.id))
def give_points_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the Chat ID of the user to give points:")
    bot.register_next_step_handler(msg, give_points_step2)

def give_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id,"✏️ Send the amount of points to add:")
        bot.register_next_step_handler(msg, lambda m2: give_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id,"❌ Invalid Chat ID.")

def give_points_step3(m, uid):
    try:
        pts = int(m.text)
        user = User(uid)
        user.add_points(pts)
        bot.send_message(m.from_user.id,f"✅ Added {pts} points to user `{uid}`.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid number.")

# =========================
# SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text=="📝 Set Points" and is_admin(m.from_user.id))
def set_points_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the Chat ID of the user to set points:")
    bot.register_next_step_handler(msg, set_points_step2)

def set_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id,"✏️ Send the new points amount:")
        bot.register_next_step_handler(msg, lambda m2: set_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id,"❌ Invalid Chat ID.")

def set_points_step3(m, uid):
    try:
        pts = int(m.text)
        user = User(uid)
        user.set_points(pts)
        bot.send_message(m.from_user.id,f"✅ Set points of user `{uid}` to {pts}.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid number.")

# =========================
# SET VIP MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg_step(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the new VIP join message:")
    bot.register_next_step_handler(msg, set_vip_msg_step2)

def set_vip_msg_step2(m):
    config = load("config.json")
    config["vip_msg"] = m.text
    save("config.json", config)
    bot.send_message(m.from_user.id,"✅ VIP message updated.")

# =========================
# SET WELCOME MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text=="🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_step(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the new welcome message (can include photo/video later):")
    bot.register_next_step_handler(msg, set_welcome_step2)

def set_welcome_step2(m):
    config = load("config.json")
    config["welcome"] = m.text
    save("config.json", config)
    bot.send_message(m.from_user.id,"✅ Welcome message updated.")

# =========================
# STATS PANEL
# =========================
@bot.message_handler(func=lambda m: m.text=="🧮 Stats" and is_admin(m.from_user.id))
def stats_panel(m):
    users = load("users.json")
    total = len(users)
    vip_count = sum(1 for u in users.values() if u["vip"])
    free_count = total - vip_count
    msg = f"📊 *ZEDOX BOT Stats*\n\n👥 Total Users: {total}\n💎 VIP Users: {vip_count}\n🆓 Free Users: {free_count}"
    bot.send_message(m.from_user.id, msg)

# =========================
# MULTIPLE COUPON GENERATION
# =========================
@bot.message_handler(func=lambda m: m.text=="🏷 Generate Coupon" and is_admin(m.from_user.id))
def generate_coupon_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send points for each coupon:")
    bot.register_next_step_handler(msg, generate_coupon_step2)

def generate_coupon_step2(m):
    try:
        points = int(m.text)
        msg = bot.send_message(m.from_user.id,"✏️ How many coupons to generate?")
        bot.register_next_step_handler(msg, lambda m2: generate_coupon_step3(m2, points))
    except:
        bot.send_message(m.from_user.id,"❌ Invalid number.")

def generate_coupon_step3(m, points):
    try:
        count = int(m.text)
        from random import choices
        from string import ascii_uppercase, digits
        codes = []
        for _ in range(count):
            code = "ZEDOX"+''.join(choices(ascii_uppercase+digits,k=6))
            codesys.codes[code] = points
            codes.append(code)
        codesys.save()
        bot.send_message(m.from_user.id,f"✅ Generated {count} coupon(s):\n" + "\n".join(codes))
    except:
        bot.send_message(m.from_user.id,"❌ Invalid number.")
# =========================
# ZEDOX BOT - PART 3
# Upload System, Redeem Codes, Broadcast, Folder Price
# =========================

# =========================
# UPLOAD FILES SYSTEM
# =========================
def upload_files(category, uid):
    msg = bot.send_message(uid, f"📤 Send file(s) to upload for category `{category}`.\nSend multiple files one by one.\nWhen done, send /done.")
    bot.register_next_step_handler(msg, lambda m: upload_files_step(m, category, uid, []))

def upload_files_step(m, category, uid, files):
    if m.text == "/done":
        # Ask folder name and price
        msg2 = bot.send_message(uid, "✏️ Send the folder name for these files:")
        bot.register_next_step_handler(msg2, lambda m2: upload_folder_finalize(m2, category, files))
        return

    if m.content_type in ["document","photo","video"]:
        f = {"chat": m.chat.id, "msg": m.message_id, "type": m.content_type}
        files.append(f)
        bot.send_message(uid,"✅ File saved. Send next file or /done when finished.")
    else:
        bot.send_message(uid,"❌ Unsupported type. Send document, photo, or video.")

    bot.register_next_step_handler(m, lambda m2: upload_files_step(m2, category, uid, files))

def upload_folder_finalize(m, category, files):
    folder_name = m.text
    msg_price = bot.send_message(m.from_user.id,"✏️ Send price for this folder (0 for free):")
    bot.register_next_step_handler(msg_price, lambda m2: finalize_folder_price(m2, category, folder_name, files))

def finalize_folder_price(m, category, folder_name, files):
    try:
        price = int(m.text)
        fs.add_folder(category, folder_name, files, price)
        bot.send_message(m.from_user.id,f"✅ Folder `{folder_name}` added to `{category}` with {len(files)} file(s) and price {price} pts.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid price. Operation cancelled.")

# =========================
# HANDLERS FOR UPLOAD BUTTONS
# =========================
@bot.message_handler(func=lambda m: m.text=="📦 Upload FREE" and is_admin(m.from_user.id))
def upload_free_handler(m):
    upload_files("free", m.from_user.id)

@bot.message_handler(func=lambda m: m.text=="💎 Upload VIP" and is_admin(m.from_user.id))
def upload_vip_handler(m):
    upload_files("vip", m.from_user.id)

@bot.message_handler(func=lambda m: m.text=="📱 Upload APPS" and is_admin(m.from_user.id))
def upload_apps_handler(m):
    upload_files("apps", m.from_user.id)

# =========================
# REDEEM CODES HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text=="🏆 Redeem")
def redeem_handler(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send your code to redeem:")
    bot.register_next_step_handler(msg, redeem_step)

def redeem_step(m):
    user = User(m.from_user.id)
    success, pts = codesys.redeem(m.text.strip(), user)
    if success:
        bot.send_message(m.from_user.id,f"✅ Redeemed! You received {pts} points.\n💰 Total points: {user.points()}")
    else:
        bot.send_message(m.from_user.id,"❌ Invalid or already used code.")

# =========================
# BROADCAST SYSTEM (TEXT/PHOTO/VIDEO/DOCUMENT)
# =========================
@bot.message_handler(func=lambda m: m.text=="📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_step1(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("All Users", callback_data="broadcast_all"),
        InlineKeyboardButton("VIP Users", callback_data="broadcast_vip"),
        InlineKeyboardButton("Free Users", callback_data="broadcast_free")
    )
    bot.send_message(m.from_user.id,"📢 Select target audience for broadcast:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("broadcast_") and is_admin(c.from_user.id))
def broadcast_callback(c):
    target = c.data.split("_")[1]
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.from_user.id,"✏️ Send the broadcast message (can be text/photo/video/document):")
    bot.register_next_step_handler(msg, lambda m: broadcast_send(m, target))

def broadcast_send(m, target):
    users = load("users.json")
    sent_count = 0
    for uid_str, data in users.items():
        if target == "vip" and not data.get("vip", False):
            continue
        if target == "free" and data.get("vip", False):
            continue
        uid = int(uid_str)
        try:
            if m.content_type == "text":
                bot.send_message(uid, m.text)
            elif m.content_type == "photo":
                bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)
            elif m.content_type == "video":
                bot.send_video(uid, m.video.file_id, caption=m.caption)
            elif m.content_type == "document":
                bot.send_document(uid, m.document.file_id, caption=m.caption)
            sent_count += 1
        except:
            continue
    bot.send_message(ADMIN_ID,f"📢 Broadcast sent to {sent_count} users.")

# =========================
# EDIT FOLDER PRICE
# =========================
@bot.message_handler(func=lambda m: m.text=="✏️ Edit Folder Price" and is_admin(m.from_user.id))
def edit_folder_price_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send category (free/vip/apps/custom):")
    bot.register_next_step_handler(msg, edit_folder_price_step2)

def edit_folder_price_step2(m):
    category = m.text.lower()
    msg = bot.send_message(m.from_user.id,"✏️ Send folder name to edit price:")
    bot.register_next_step_handler(msg, lambda m2: edit_folder_price_step3(m2, category))

def edit_folder_price_step3(m, category):
    folder_name = m.text
    msg = bot.send_message(m.from_user.id,"✏️ Send new price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: finalize_edit_price(m2, category, folder_name))

def finalize_edit_price(m, category, folder_name):
    try:
        price = int(m.text)
        if fs.edit_price(category, folder_name, price):
            bot.send_message(m.from_user.id,f"✅ Price updated for `{folder_name}` in `{category}` to {price} pts.")
        else:
            bot.send_message(m.from_user.id,"❌ Folder not found.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid price.")
# =========================
# ZEDOX BOT - PART 4
# Folder Buttons, Force Join, Welcome, Polling & Error Handling
# =========================

# =========================
# MAIN MENU
# =========================
def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS","💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS","💰 POINTS")
    kb.row("⭐ BUY VIP","🎁 REFERRAL")
    kb.row("👤 ACCOUNT","🆔 CHAT ID","🏆 Redeem")
    for name in load("db.json")["custom"]:
        kb.row(name)
    if uid == ADMIN_ID:
        kb.row("⚙️ ADMIN PANEL")
    return kb

# =========================
# START COMMAND
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    Referral().handle_start(uid, args)
    user = User(uid)

    if not force.check(uid):
        bot.send_message(uid,"🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return

    config = load("config.json")
    bot.send_message(uid, config["welcome"], reply_markup=main_menu(uid))

# =========================
# FOLDER BUTTONS SHOW PRICE
# =========================
@bot.message_handler(func=lambda m: m.text.lower() in ["📂 free methods","free methods",
                                                      "💎 vip methods","vip methods",
                                                      "📦 premium apps","premium apps"])
def folder_buttons(m):
    uid = m.from_user.id
    text = m.text.lower()
    cat_map = {"📂 free methods":"free","free methods":"free",
               "💎 vip methods":"vip","vip methods":"vip",
               "📦 premium apps":"apps","premium apps":"apps"}
    cat = cat_map[text]
    kb = InlineKeyboardMarkup()
    for name, info in fs.get_category(cat).items():
        price = info.get("price",0)
        display_name = f"{name} [{price} pts]" if price>0 else name
        kb.add(InlineKeyboardButton(display_name, callback_data=f"open|{cat}|{name}"))
    bot.send_message(uid, f"📂 Select {cat.upper()} Folder:", reply_markup=kb)

# =========================
# OPEN FOLDER CALLBACK
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open"))
def open_callback(c):
    _, cat, name = c.data.split("|")
    user = User(c.from_user.id)
    folder = fs.get_category(cat).get(name)
    if not folder:
        bot.answer_callback_query(c.id,"❌ Folder not found")
        return

    # VIP check
    if cat=="vip" and not user.is_vip():
        bot.send_message(c.from_user.id, load("config.json")["vip_msg"])
        return

    # Price check for free users
    if not user.is_vip() and folder.get("price",0) > 0:
        if user.points() < folder["price"]:
            bot.answer_callback_query(c.id,"❌ Not enough points")
            return
        user.add_points(-folder["price"])

    # Send all files
    sent_count = 0
    for f in folder["files"]:
        try:
            bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            sent_count += 1
        except:
            continue
    if load("config.json")["notify"]:
        bot.send_message(c.from_user.id,f"✅ Sent {sent_count} file(s) from `{name}`")

# =========================
# FORCE JOIN RECHECK
# =========================
@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck_join(c):
    uid = c.from_user.id
    if force.check(uid):
        bot.send_message(uid,"✅ Access granted!", reply_markup=main_menu(uid))
    else:
        bot.send_message(uid,"🚫 Still not joined all channels!", reply_markup=force.join_buttons())

# =========================
# SAFE SEND & COPY FUNCTIONS
# =========================
def safe_send(uid, text=None, reply_markup=None):
    try:
        if text:
            bot.send_message(uid, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error sending to {uid}: {e}")

def safe_copy(uid, chat_id, msg_id):
    try:
        bot.copy_message(uid, chat_id, msg_id)
    except Exception as e:
        print(f"Error copying message to {uid}: {e}")

# =========================
# GENERAL HANDLER (Main Commands)
# =========================
@bot.message_handler(func=lambda m: True)
def general_handler(m):
    uid = m.from_user.id
    user = User(uid)

    # Force join check
    if not force.check(uid):
        bot.send_message(uid,"🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return

    text = m.text.lower()
    if text in ["💰 points","points"]:
        bot.send_message(uid,f"💰 You have {user.points()} points.")
    elif text in ["⭐ buy vip","buy vip"]:
        bot.send_message(uid, load("config.json")["vip_msg"])
    elif text in ["🎁 referral","referral"]:
        ref_link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid,f"🎁 Share your referral link:\n{ref_link}")
    elif text in ["👤 account","account"]:
        status = "💎 VIP" if user.is_vip() else "🆓 FREE"
        bot.send_message(uid,f"👤 Account Status: {status}\n💰 Points: {user.points()}")
    elif text in ["🆔 chat id","chat id"]:
        bot.send_message(uid,f"🆔 Your Chat ID: `{uid}`")

# =========================
# FALLBACK HANDLER
# =========================
@bot.message_handler(func=lambda m: True, content_types=['text','document','photo','video'])
def fallback(m):
    safe_send(m.from_user.id,"❌ Command not recognized or unsupported input.\nUse main menu buttons.", reply_markup=main_menu(m.from_user.id))

# =========================
# POLLING WITH AUTO-RESTART
# =========================
def run_bot():
    while True:
        try:
            print("🚀 Bot started. Listening for messages...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)

# =========================
# START BOT THREAD
# =========================
import threading
threading.Thread(target=run_bot).start()
