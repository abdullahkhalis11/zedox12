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
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)
    
    def remove_vip(self):
        self.data["vip"] = False
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

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
# Admin Panel + Upload + Delete + Edit + Broadcast + Codes + VIP Management
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

    kb.row("👑 Add VIP User", "👑 Remove VIP User")
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
# ADD VIP USER (BY CHAT ID OR USERNAME)
# =========================
@bot.message_handler(func=lambda m: m.text == "👑 Add VIP User" and is_admin(m.from_user.id))
def add_vip_start(m):
    msg = bot.send_message(m.from_user.id, "📝 Send user ID or @username to add VIP:\n\nExample:\n• `123456789`\n• `@username`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, add_vip_process)

def add_vip_process(m):
    user_input = m.text.strip()
    user_id = None
    
    # Check if input is username or ID
    if user_input.startswith('@'):
        # It's a username, try to get user ID
        username = user_input.replace('@', '')
        try:
            # Try to get chat info from username
            chat = bot.get_chat(f"@{username}")
            user_id = chat.id
        except Exception as e:
            bot.send_message(m.from_user.id, f"❌ Could not find user with username {user_input}\n\nMake sure the user has started the bot first.")
            return
    else:
        # It's a numeric ID
        try:
            user_id = int(user_input)
        except:
            bot.send_message(m.from_user.id, "❌ Invalid user ID format")
            return
    
    # Now add VIP to this user
    try:
        # Check if user exists in database
        user = User(user_id)
        if user.is_vip():
            bot.send_message(m.from_user.id, f"⚠️ User `{user_id}` is already VIP!", parse_mode="Markdown")
            return
        
        # Make user VIP
        user.make_vip()
        
        # Notify admin
        bot.send_message(m.from_user.id, f"✅ User `{user_id}` has been upgraded to VIP!", parse_mode="Markdown")
        
        # Notify user if possible
        try:
            bot.send_message(user_id, "🎉 **Congratulations!**\n\nYou have been upgraded to **VIP** by the admin!\n\n✨ Enjoy exclusive VIP content and benefits!", parse_mode="Markdown")
        except:
            # User might have blocked the bot or not started it
            bot.send_message(m.from_user.id, f"⚠️ Could not notify user `{user_id}`. They might not have started the bot.", parse_mode="Markdown")
    
    except Exception as e:
        bot.send_message(m.from_user.id, f"❌ Error: {str(e)}")

# =========================
# REMOVE VIP USER (BY CHAT ID OR USERNAME)
# =========================
@bot.message_handler(func=lambda m: m.text == "👑 Remove VIP User" and is_admin(m.from_user.id))
def remove_vip_start(m):
    msg = bot.send_message(m.from_user.id, "📝 Send user ID or @username to remove VIP:\n\nExample:\n• `123456789`\n• `@username`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, remove_vip_process)

def remove_vip_process(m):
    user_input = m.text.strip()
    user_id = None
    
    # Check if input is username or ID
    if user_input.startswith('@'):
        # It's a username, try to get user ID
        username = user_input.replace('@', '')
        try:
            # Try to get chat info from username
            chat = bot.get_chat(f"@{username}")
            user_id = chat.id
        except Exception as e:
            bot.send_message(m.from_user.id, f"❌ Could not find user with username {user_input}\n\nMake sure the user has started the bot first.")
            return
    else:
        # It's a numeric ID
        try:
            user_id = int(user_input)
        except:
            bot.send_message(m.from_user.id, "❌ Invalid user ID format")
            return
    
    # Now remove VIP from this user
    try:
        # Check if user exists in database
        user = User(user_id)
        if not user.is_vip():
            bot.send_message(m.from_user.id, f"⚠️ User `{user_id}` is not a VIP member!", parse_mode="Markdown")
            return
        
        # Remove VIP status
        user.remove_vip()
        
        # Notify admin
        bot.send_message(m.from_user.id, f"✅ VIP status removed from user `{user_id}`!", parse_mode="Markdown")
        
        # Notify user if possible
        try:
            bot.send_message(user_id, "⚠️ **VIP Status Removed**\n\nYour VIP membership has been removed by the admin.\n\nContact admin for more information.", parse_mode="Markdown")
        except:
            # User might have blocked the bot or not started it
            bot.send_message(m.from_user.id, f"⚠️ Could not notify user `{user_id}`.", parse_mode="Markdown")
    
    except Exception as e:
        bot.send_message(m.from_user.id, f"❌ Error: {str(e)}")

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
    msg = bot.send_message(m.from_user.id, "Category (free/vip/apps/courses):")
    bot.register_next_step_handler(msg, edit2)

def edit2(m):
    cat = m.text.strip().lower()
    if cat not in ["free", "vip", "apps", "courses"]:
        bot.send_message(m.from_user.id, "Invalid category! Use: free, vip, apps, courses")
        return
    msg = bot.send_message(m.from_user.id, "Folder name:")
    bot.register_next_step_handler(msg, lambda m2: edit3(m2, cat))

def edit3(m, cat):
    name = m.text
    msg = bot.send_message(m.from_user.id, "New price:")
    bot.register_next_step_handler(msg, lambda m2: edit4(m2, cat, name))

def edit4(m, cat, name):
    try:
        fs.edit(cat, name, int(m.text))
        bot.send_message(m.from_user.id, "✅ Price updated")
    except:
        bot.send_message(m.from_user.id, "❌ Error updating price")

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
# BROADCAST (FIXED PRO - Added Free Users & HTML Support)
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def bc_start(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📢 All Users", callback_data="bc|all"),
        InlineKeyboardButton("💎 VIP Users", callback_data="bc|vip"),
        InlineKeyboardButton("🆓 Free Users", callback_data="bc|free")
    )
    bot.send_message(m.from_user.id, "📡 Select target users:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_pick(c):
    t = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "📝 Send your broadcast message (text, photo, video, or document):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, t))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    failed = 0

    for uid in users:
        if target == "vip" and not users[uid]["vip"]:
            continue
        if target == "free" and users[uid]["vip"]:
            continue

        try:
            if m.content_type == "text":
                # Support HTML formatting in text messages
                bot.send_message(int(uid), m.text, parse_mode="HTML")
            elif m.content_type == "photo":
                # Support HTML in caption
                caption = m.caption if m.caption else None
                bot.send_photo(int(uid), m.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif m.content_type == "video":
                caption = m.caption if m.caption else None
                bot.send_video(int(uid), m.video.file_id, caption=caption, parse_mode="HTML")
            elif m.content_type == "document":
                caption = m.caption if m.caption else None
                bot.send_document(int(uid), m.document.file_id, caption=caption, parse_mode="HTML")

            sent += 1
        except Exception as e:
            failed += 1
            continue

    result_msg = f"✅ Broadcast completed!\n\n📤 Sent: {sent}\n❌ Failed: {failed}\n🎯 Target: {target.upper()}"
    bot.send_message(ADMIN_ID, result_msg)

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
    kb.row("📦 PREMIUM APPS")

    kb.row("💰 POINTS", "⭐ BUY VIP")
    kb.row("🎁 REFERRAL", "👤 ACCOUNT")

    kb.row("🆔 CHAT ID", "🏆 REDEEM")

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
# SHOW FOLDERS (ALL CATEGORIES - FIXED COURSES)
# =========================
@bot.message_handler(func=lambda m: m.text in [
    "📂 FREE METHODS",
    "💎 VIP METHODS",
    "📦 PREMIUM APPS"
])
def show_folders(m):
    uid = m.from_user.id

    if force_block(uid):
        return

    # Map button text to category names
    mapping = {
        "📂 FREE METHODS": "free",
        "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps"
    }

    cat = mapping.get(m.text)
    
    if cat is None:
        bot.send_message(uid, "❌ Invalid category")
        return

    # Check if category has any folders
    folders = fs.get(cat)
    
    if not folders:
        bot.send_message(uid, f"📂 {m.text}\n\nNo folders available in this category yet!")
        return

    bot.send_message(
        uid,
        f"📂 {m.text}\n\nSelect a folder to view content:",
        reply_markup=get_kb(cat, 0)
    )

# =========================
# PAGINATION HANDLER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def page_handler(c):
    _, cat, page = c.data.split("|")
    
    try:
        bot.edit_message_reply_markup(
            c.from_user.id,
            c.message.message_id,
            reply_markup=get_kb(cat, int(page))
        )
    except Exception as e:
        bot.answer_callback_query(c.id, "Error updating page")

# =========================
# OPEN FOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    uid = c.from_user.id
    user = User(uid)

    try:
        _, cat, name = c.data.split("|")
    except:
        bot.answer_callback_query(c.id, "Invalid folder data")
        return
        
    folder = fs.get(cat).get(name)

    if not folder:
        bot.answer_callback_query(c.id, "❌ Folder not found")
        return

    # VIP restriction for VIP category
    if cat == "vip" and not user.is_vip():
        bot.answer_callback_query(c.id, "❌ This is VIP content", show_alert=True)
        bot.send_message(uid, load("config.json")["vip_msg"])
        return

    price = folder.get("price", 0)

    # Points system for non-VIP users
    if not user.is_vip() and price > 0:
        if user.points() < price:
            bot.answer_callback_query(c.id, f"❌ Need {price} points! You have {user.points()}", show_alert=True)
            return

        user.add_points(-price)
        bot.answer_callback_query(c.id, f"✅ {price} points deducted!")

    bot.answer_callback_query(c.id, "📤 Sending files...")

    count = 0
    for f in folder["files"]:
        try:
            bot.copy_message(uid, f["chat"], f["msg"])
            count += 1
            time.sleep(0.3)  # Small delay to avoid flood
        except Exception as e:
            print(f"Error sending file: {e}")
            continue

    if load("config.json").get("notify", True):
        if count > 0:
            bot.send_message(uid, f"✅ Sent {count} file(s) successfully!")
        else:
            bot.send_message(uid, "❌ Failed to send files. Please try again later.")

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
        bot.send_message(uid, f"💰 Your Points: **{user.points()}**\n\n🎁 Earn more points by:\n• Using referral link\n• Redeeming codes\n• Completing tasks", parse_mode="Markdown")

    elif t == "⭐ BUY VIP":
        bot.send_message(uid, load("config.json")["vip_msg"])

    elif t == "🎁 REFERRAL":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🎁 **Your Referral Link**\n\n{link}\n\n✨ For each friend who joins, you get **{load('config.json').get('ref_reward', 5)} points**!", parse_mode="Markdown")

    elif t == "👤 ACCOUNT":
        status = "💎 VIP Member" if user.is_vip() else "🆓 Free User"
        bot.send_message(uid, f"**👤 Account Info**\n\nStatus: {status}\nPoints: **{user.points()}**\n\nUse /start to refresh", parse_mode="Markdown")

    elif t == "🆔 CHAT ID":
        bot.send_message(uid, f"🆔 Your Chat ID: `{uid}`", parse_mode="Markdown")

    elif t == "🏆 REDEEM":
        msg = bot.send_message(uid, "🎫 Enter your redeem code:")
        bot.register_next_step_handler(msg, redeem_code)

# =========================
# REDEEM FUNCTION
# =========================
def redeem_code(m):
    uid = m.from_user.id
    user = User(uid)

    success, pts = codesys.redeem(m.text.strip().upper(), user)

    if success:
        bot.send_message(uid, f"✅ **Success!**\n\n➕ +{pts} points\n💰 Total Points: **{user.points()}**", parse_mode="Markdown")
    else:
        bot.send_message(uid, "❌ **Invalid Code**\n\nPlease check your code and try again.", parse_mode="Markdown")

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
                "✅ **Access Granted!**\n\nWelcome to ZEDOX BOT!",
                uid,
                c.message.message_id,
                parse_mode="Markdown"
            )
        except:
            pass

        bot.send_message(uid, "🎉 Welcome! Use the menu below to get started.", reply_markup=main_menu(uid))
    else:
        bot.answer_callback_query(c.id, "❌ Please join all required channels first", show_alert=True)

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
        "📦 PREMIUM APPS",
        "💰 POINTS","⭐ BUY VIP",
        "🎁 REFERRAL","👤 ACCOUNT",
        "🆔 CHAT ID","🏆 REDEEM",
        "⚙️ ADMIN PANEL"
    ]

    if m.text and m.text not in known:
        safe_send(uid, "❌ Please use the menu buttons only", main_menu(uid))

# =========================
# AUTO RESTART POLLING
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT RUNNING...")
            print(f"✅ Bot Username: @{bot.get_me().username}")
            print(f"✅ Admin ID: {ADMIN_ID}")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(5)

# =========================
# START BOT
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Keep main thread alive
    while True:
        time.sleep(1)
