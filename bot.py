import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, time, random, string, threading

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =========================
# FILE INIT
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
# LOAD & SAVE FUNCTIONS
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
            kb.add(InlineKeyboardButton(f"JOIN {ch}", url=f"https://t.me/{str(ch).replace('@','')}"))
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
# COUPON SYSTEM
# =========================
class Codes:
    def __init__(self):
        self.codes = load("codes.json")

    def generate(self, points, count=1):
        result = []
        for _ in range(count):
            code = 'ZEDOX'+''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
            self.codes[code] = points
            result.append(code)
        self.save()
        return result

    def redeem(self, code, user:User):
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
# CHECK ADMIN
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text=="⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    uid = m.from_user.id
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP","➖ Remove VIP","💰 Give Points")
    kb.row("📝 Set Points","⭐ Set VIP Message","🏠 Set Welcome Message")
    kb.row("📤 Broadcast","🗑 Delete Folder","✏️ Edit Folder Price")
    kb.row("📦 Upload FREE","💎 Upload VIP","📱 Upload APPS")
    kb.row("➕ Add Force Join","➖ Remove Force Join","🧮 Stats")
    kb.row("🏆 Generate Codes","❌ Exit Admin")
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
    msg = bot.send_message(m.from_user.id,"✏️ Send the new welcome message:")
    bot.register_next_step_handler(msg, set_welcome_step2)

def set_welcome_step2(m):
    config = load("config.json")
    config["welcome"] = m.text
    save("config.json", config)
    bot.send_message(m.from_user.id,"✅ Welcome message updated.")

# =========================
# FORCE JOIN CHANNEL MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text=="➕ Add Force Join" and is_admin(m.from_user.id))
def add_force_channel_step(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the channel username to force join (with @):")
    bot.register_next_step_handler(msg, add_force_channel_step2)

def add_force_channel_step2(m):
    config = load("config.json")
    if m.text not in config["force_channels"]:
        config["force_channels"].append(m.text)
        save("config.json", config)
        bot.send_message(m.from_user.id,f"✅ Added force join channel `{m.text}`.")
    else:
        bot.send_message(m.from_user.id,"❌ Channel already in force join list.")

@bot.message_handler(func=lambda m: m.text=="➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force_channel_step(m):
    msg = bot.send_message(m.from_user.id,"✏️ Send the channel username to remove from force join (with @):")
    bot.register_next_step_handler(msg, remove_force_channel_step2)

def remove_force_channel_step2(m):
    config = load("config.json")
    if m.text in config["force_channels"]:
        config["force_channels"].remove(m.text)
        save("config.json", config)
        bot.send_message(m.from_user.id,f"✅ Removed force join channel `{m.text}`.")
    else:
        bot.send_message(m.from_user.id,"❌ Channel not found in list.")

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
# MULTIPLE COUPON CODE GENERATION
# =========================
@bot.message_handler(func=lambda m: m.text=="🏆 Generate Codes" and is_admin(m.from_user.id))
def generate_codes_step1(m):
    msg = bot.send_message(m.from_user.id,"✏️ Enter points for the codes:")
    bot.register_next_step_handler(msg, generate_codes_step2)

def generate_codes_step2(m):
    try:
        points = int(m.text)
        msg = bot.send_message(m.from_user.id,"✏️ Enter number of codes to generate:")
        bot.register_next_step_handler(msg, lambda m2: generate_codes_step3(m2, points))
    except:
        bot.send_message(m.from_user.id,"❌ Invalid number.")

def generate_codes_step3(m, points):
    try:
        count = int(m.text)
        codes = codesys.generate(points, count)
        code_text = "\n".join(codes)
        bot.send_message(m.from_user.id,f"✅ Generated {count} codes with {points} points each:\n{code_text}")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid number.")
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
# DELETE FOLDER
# =========================
@bot.message_handler(func=lambda m: m.text=="🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_folder_step1(m):
    kb = InlineKeyboardMarkup()
    for cat, items in fs.db.items():
        for name in items.keys():
            kb.add(InlineKeyboardButton(f"{name} [{cat}]", callback_data=f"delete|{cat}|{name}"))
    bot.send_message(m.from_user.id,"🗑 Select folder to delete:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delete") and is_admin(c.from_user.id))
def delete_folder_callback(c):
    _, cat, name = c.data.split("|")
    if fs.delete_folder(cat, name):
        bot.answer_callback_query(c.id,f"✅ Deleted folder `{name}` from `{cat}`")
    else:
        bot.answer_callback_query(c.id,"❌ Folder not found")

# =========================
# EDIT FOLDER PRICE
# =========================
@bot.message_handler(func=lambda m: m.text=="✏️ Edit Folder Price" and is_admin(m.from_user.id))
def edit_folder_price_step1(m):
    kb = InlineKeyboardMarkup()
    for cat, items in fs.db.items():
        for name in items.keys():
            kb.add(InlineKeyboardButton(f"{name} [{cat}]", callback_data=f"editprice|{cat}|{name}"))
    bot.send_message(m.from_user.id,"✏️ Select folder to edit price:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("editprice") and is_admin(c.from_user.id))
def edit_folder_price_callback(c):
    _, cat, name = c.data.split("|")
    msg = bot.send_message(c.from_user.id,f"✏️ Send new price for folder `{name}`:")
    bot.register_next_step_handler(msg, lambda m: finalize_edit_price(m, cat, name))

def finalize_edit_price(m, cat, name):
    try:
        price = int(m.text)
        if fs.edit_price(cat, name, price):
            bot.send_message(m.from_user.id,f"✅ Folder `{name}` price updated to {price} pts.")
        else:
            bot.send_message(m.from_user.id,"❌ Folder not found.")
    except:
        bot.send_message(m.from_user.id,"❌ Invalid price.")
# =========================
# MAIN MENU AND PAGINATION
# =========================
from math import ceil

def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS","💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS","💰 POINTS")
    kb.row("⭐ BUY VIP","🎁 REFERRAL")
    kb.row("👤 ACCOUNT","🆔 CHAT ID","🏆 Redeem")
    return kb

# =========================
# FORCE JOIN CHECK ON START
# =========================
@bot.message_handler(commands=["start"])
def start_handler(m):
    user = User(m.from_user.id)
    args = m.text.split()
    Referral().handle_start(m.from_user.id, args)

    if not force.check(m.from_user.id):
        bot.send_message(m.from_user.id,"⚠️ You must join the following channels first to use the bot:", reply_markup=force.join_buttons())
    else:
        bot.send_message(m.from_user.id, load("config.json").get("welcome","Welcome!"), reply_markup=main_menu(m.from_user.id))

@bot.callback_query_handler(func=lambda c: c.data=="recheck")
def recheck_force_join(c):
    if force.check(c.from_user.id):
        bot.answer_callback_query(c.id,"✅ All channels joined!")
        bot.send_message(c.from_user.id, load("config.json").get("welcome","Welcome!"), reply_markup=main_menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id,"❌ You still need to join all channels.")

# =========================
# FOLDER PAGINATION
# =========================
def send_folder_page(uid, category, page=1, per_page=8):
    db_category = fs.get_category(category)
    items = list(db_category.items())
    total_pages = max(1, ceil(len(items)/per_page))
    page = max(1, min(page, total_pages))

    kb = InlineKeyboardMarkup()
    start = (page-1)*per_page
    end = start + per_page
    for name, data in items[start:end]:
        price = data.get("price",0)
        kb.add(InlineKeyboardButton(f"{name} ({price} pts)" if price>0 else f"{name} [FREE]", callback_data=f"folder|{category}|{name}"))

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{category}|page|{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"{category}|page|{page+1}"))
    if nav_buttons:
        kb.row(*nav_buttons)

    bot.send_message(uid, f"📁 {category.upper()} Folders (Page {page}/{total_pages})", reply_markup=kb)

# =========================
# HANDLE FOLDER NAVIGATION
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("free|page") or c.data.startswith("vip|page") or c.data.startswith("apps|page"))
def folder_page_callback(c):
    cat, _, page = c.data.split("|")
    send_folder_page(c.from_user.id, cat, int(page))
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("folder|"))
def folder_select_callback(c):
    _, cat, name = c.data.split("|")
    folder = fs.get_category(cat).get(name)
    if folder:
        price = folder.get("price",0)
        files = folder.get("files",[])
        user = User(c.from_user.id)

        if price>0 and not user.is_vip():
            bot.answer_callback_query(c.id,"💎 VIP required or pay points to access.")
        else:
            bot.answer_callback_query(c.id,"📂 Folder opened. Sending files...")
            for f in files:
                try:
                    if f["type"]=="document":
                        bot.forward_message(c.from_user.id,f["chat"],f["msg"])
                    elif f["type"]=="photo":
                        bot.forward_message(c.from_user.id,f["chat"],f["msg"])
                    elif f["type"]=="video":
                        bot.forward_message(c.from_user.id,f["chat"],f["msg"])
                except:
                    continue
    else:
        bot.answer_callback_query(c.id,"❌ Folder not found.")

# =========================
# USER ACCOUNT INFO
# =========================
@bot.message_handler(func=lambda m: m.text=="👤 ACCOUNT")
def account_info(m):
    user = User(m.from_user.id)
    bot.send_message(m.from_user.id,f"👤 User: `{m.from_user.id}`\n💎 VIP: {user.is_vip()}\n💰 Points: {user.points()}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text=="💰 POINTS")
def show_points(m):
    user = User(m.from_user.id)
    bot.send_message(m.from_user.id,f"💰 You have {user.points()} points.")

@bot.message_handler(func=lambda m: m.text=="🆔 CHAT ID")
def show_chatid(m):
    bot.send_message(m.from_user.id,f"🆔 Your Chat ID: `{m.from_user.id}`", parse_mode="Markdown")

# =========================
# VIP PURCHASE HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text=="⭐ BUY VIP")
def buy_vip(m):
    msg = load("config.json").get("vip_msg","💎 VIP Required")
    bot.send_message(m.from_user.id,msg)

# =========================
# REFERRAL HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text=="🎁 REFERRAL")
def show_referral(m):
    user = User(m.from_user.id)
    bot.send_message(m.from_user.id,f"🎁 Your referral ID: `{m.uid}`\nShare it with others to earn points!", parse_mode="Markdown")

# =========================
# FOLDER BUTTONS (FOR MAIN MENU)
# =========================
@bot.message_handler(func=lambda m: m.text=="📂 FREE METHODS")
def free_folders(m):
    send_folder_page(m.from_user.id, "free")

@bot.message_handler(func=lambda m: m.text=="💎 VIP METHODS")
def vip_folders(m):
    send_folder_page(m.from_user.id, "vip")

@bot.message_handler(func=lambda m: m.text=="📦 PREMIUM APPS")
def apps_folders(m):
    send_folder_page(m.from_user.id, "apps")

# =========================
# POLLING AND ERROR HANDLING
# =========================
def start_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Polling error: {e}")
            time.sleep(5)

# Start the bot
if __name__=="__main__":
    start_bot()
