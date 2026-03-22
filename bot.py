# =========================
# ZEDOX BOT - COMPLETE FIXED
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json
import os
import time
import random
import string
import threading
import logging

# =========================
# CONFIGURATION (RAILWAY ENV)
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Logging (optional, for debugging)
logging.basicConfig(level=logging.INFO)

# =========================
# FILE STORAGE INIT
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {
            "free": {},
            "vip": {},
            "apps": {},
            "courses": {},
            "custom": {}
        },
        "config.json": {
            "force_channels": [],
            "vip_msg": "💎 *Buy VIP to unlock this!*\n\nContact @admin to get VIP access.",
            "welcome": "🔥 *Welcome to ZEDOX BOT*\n\nExplore our premium content and earn points!",
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
            self.users[self.uid] = {"points": 0, "vip": False, "ref": None}
            save("users.json", self.users)
        self.data = self.users[self.uid]

    def is_vip(self):
        return self.data.get("vip", False)

    def points(self):
        return self.data.get("points", 0)

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
# FORCE JOIN SYSTEM (FIXED)
# =========================
class ForceJoin:
    def __init__(self):
        self.config = load("config.json")

    def check(self, uid):
        channels = self.config.get("force_channels", [])
        if not channels:
            return True
        for ch in channels:
            ch = ch.strip()
            if not ch.startswith("@"):
                ch = "@" + ch
            try:
                member = bot.get_chat_member(ch, uid)
                if member.status in ["left", "kicked", "restricted"]:
                    return False
            except Exception as e:
                logging.error(f"Force join check error for {ch}: {e}")
                return False
        return True

    def join_buttons(self):
        kb = InlineKeyboardMarkup(row_width=1)
        channels = self.config.get("force_channels", [])
        for ch in channels:
            ch = ch.strip()
            if not ch.startswith("@"):
                ch = "@" + ch
            kb.add(InlineKeyboardButton(f"📢 JOIN {ch}", url=f"https://t.me/{ch.replace('@','')}"))
        kb.add(InlineKeyboardButton("✅ I've Joined", callback_data="verify_join"))
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
                self.users[ref]["points"] += self.config.get("ref_reward", 5)
                user.set_ref(ref)
                save("users.json", self.users)
                try:
                    bot.send_message(int(ref), f"🎉 New user joined using your referral link!\nYou earned +{self.config.get('ref_reward',5)} points!")
                except:
                    pass

# =========================
# FILE SYSTEM (FIXED DELETE/EDIT)
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
        if category in self.db and name in self.db[category]:
            del self.db[category][name]
            self.save_db()
            return True
        return False

    def edit_price(self, category, name, price):
        if category in self.db and name in self.db[category]:
            self.db[category][name]["price"] = price
            self.save_db()
            return True
        return False

    def get_category(self, category):
        return self.db.get(category, {})

    def get_all_folders(self):
        all_folders = []
        for cat in ["free", "vip", "apps", "courses"]:
            for folder in self.db[cat].keys():
                all_folders.append((cat, folder))
        return all_folders

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
            code = 'ZEDOX' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.codes[code] = points
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
# PAGINATION HELPERS
# =========================
def paginate(items, page, per_page=10):
    total = len(items)
    pages = (total + per_page - 1) // per_page if total else 1
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], pages

def get_nav_buttons(callback_prefix, page, total_pages):
    buttons = []
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"{callback_prefix}|prev|{page}"))
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="none"))
        if page < total_pages:
            row.append(InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}|next|{page}"))
        buttons.append(row)
    return buttons

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# MAIN MENU
# =========================
def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        ["📂 FREE METHODS", "💎 VIP METHODS"],
        ["📦 PREMIUM APPS", "📚 PREMIUM COURSES"],
        ["💰 POINTS", "⭐ BUY VIP"],
        ["🎁 REFERRAL", "👤 ACCOUNT"],
        ["🆔 CHAT ID", "🏆 Redeem"]
    ]
    for row in buttons:
        kb.row(*row)
    # custom folders (if any)
    custom = load("db.json")["custom"]
    for name in custom:
        kb.row(name)
    if is_admin(uid):
        kb.row("⚙️ ADMIN PANEL")
    return kb

# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    actions = [
        ["➕ Add VIP", "➖ Remove VIP"],
        ["💰 Give Points", "📝 Set Points"],
        ["⭐ Set VIP Message", "🏠 Set Welcome Message"],
        ["📤 Broadcast", "🗑 Delete Folder"],
        ["✏️ Edit Folder Price", "📦 Upload FREE"],
        ["💎 Upload VIP", "📱 Upload APPS"],
        ["📚 Upload Courses", "➕ Add Force Join"],
        ["➖ Remove Force Join", "🧮 Stats"],
        ["🏆 Generate Codes", "❌ Exit Admin"]
    ]
    for row in actions:
        kb.row(*row)
    bot.send_message(m.from_user.id, "🛠️ *Admin Panel*", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin Panel.", reply_markup=main_menu(m.from_user.id))

# =========================
# ADD/REMOVE VIP
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add VIP" and is_admin(m.from_user.id))
def add_vip(m):
    msg = bot.send_message(m.from_user.id, "Send the user ID to make VIP:")
    bot.register_next_step_handler(msg, add_vip2)

def add_vip2(m):
    try:
        uid = int(m.text)
        user = User(uid)
        user.make_vip()
        bot.send_message(m.from_user.id, f"✅ User {uid} is now VIP.")
        try:
            bot.send_message(uid, "🎉 You have been upgraded to VIP by admin!")
        except:
            pass
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.")

@bot.message_handler(func=lambda m: m.text == "➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip(m):
    msg = bot.send_message(m.from_user.id, "Send the user ID to remove VIP:")
    bot.register_next_step_handler(msg, remove_vip2)

def remove_vip2(m):
    try:
        uid = int(m.text)
        user = User(uid)
        user.remove_vip()
        bot.send_message(m.from_user.id, f"✅ VIP removed from {uid}.")
        try:
            bot.send_message(uid, "⚠️ Your VIP status has been removed by admin.")
        except:
            pass
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.")

# =========================
# GIVE / SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text == "💰 Give Points" and is_admin(m.from_user.id))
def give_points(m):
    msg = bot.send_message(m.from_user.id, "Send user ID:")
    bot.register_next_step_handler(msg, give_points2)

def give_points2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "Amount to add:")
        bot.register_next_step_handler(msg, lambda m2: give_points3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.")

def give_points3(m, uid):
    try:
        pts = int(m.text)
        user = User(uid)
        user.add_points(pts)
        bot.send_message(m.from_user.id, f"✅ Added {pts} points to {uid}.")
        try:
            bot.send_message(uid, f"💰 You received +{pts} points from admin!\nTotal: {user.points()}")
        except:
            pass
    except:
        bot.send_message(m.from_user.id, "❌ Invalid amount.")

@bot.message_handler(func=lambda m: m.text == "📝 Set Points" and is_admin(m.from_user.id))
def set_points(m):
    msg = bot.send_message(m.from_user.id, "Send user ID:")
    bot.register_next_step_handler(msg, set_points2)

def set_points2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "New points amount:")
        bot.register_next_step_handler(msg, lambda m2: set_points3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid ID.")

def set_points3(m, uid):
    try:
        pts = int(m.text)
        user = User(uid)
        user.set_points(pts)
        bot.send_message(m.from_user.id, f"✅ Points set to {pts} for {uid}.")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid amount.")

# =========================
# SET VIP/WELCOME MESSAGES
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg(m):
    msg = bot.send_message(m.from_user.id, "Send new VIP message (Markdown allowed):")
    bot.register_next_step_handler(msg, lambda m2: save_config("vip_msg", m2.text))

@bot.message_handler(func=lambda m: m.text == "🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome(m):
    msg = bot.send_message(m.from_user.id, "Send new welcome message (Markdown allowed):")
    bot.register_next_step_handler(msg, lambda m2: save_config("welcome", m2.text))

def save_config(key, value):
    cfg = load("config.json")
    cfg[key] = value
    save("config.json", cfg)
    bot.send_message(ADMIN_ID, f"✅ {key} updated.")

# =========================
# FORCE JOIN MANAGEMENT (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and is_admin(m.from_user.id))
def add_fc(m):
    msg = bot.send_message(m.from_user.id, "Send channel username (with @):")
    bot.register_next_step_handler(msg, add_fc2)

def add_fc2(m):
    cfg = load("config.json")
    ch = m.text.strip()
    if ch not in cfg["force_channels"]:
        cfg["force_channels"].append(ch)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, f"✅ Added {ch}")
    else:
        bot.send_message(m.from_user.id, "❌ Already in list.")

@bot.message_handler(func=lambda m: m.text == "➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_fc(m):
    cfg = load("config.json")
    if not cfg["force_channels"]:
        bot.send_message(m.from_user.id, "No channels to remove.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in cfg["force_channels"]:
        kb.add(InlineKeyboardButton(f"❌ {ch}", callback_data=f"rm_fc|{ch}"))
    kb.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel_rm"))
    bot.send_message(m.from_user.id, "Select channel to remove:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rm_fc") and is_admin(c.from_user.id))
def remove_fc_cb(c):
    ch = c.data.split("|")[1]
    cfg = load("config.json")
    if ch in cfg["force_channels"]:
        cfg["force_channels"].remove(ch)
        save("config.json", cfg)
        bot.answer_callback_query(c.id, f"Removed {ch}")
        bot.edit_message_text(f"✅ Removed {ch}", c.from_user.id, c.message.message_id)
    else:
        bot.answer_callback_query(c.id, "Not found")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_rm" and is_admin(c.from_user.id))
def cancel_rm(c):
    bot.edit_message_text("Operation cancelled.", c.from_user.id, c.message.message_id)
    admin_panel(c.message)

# =========================
# DELETE FOLDER (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_folder(m):
    folders = fs.get_all_folders()
    if not folders:
        bot.send_message(m.from_user.id, "No folders to delete.")
        return
    # Paginate folders
    page = 1
    show_delete_page(m.from_user.id, folders, page)

def show_delete_page(uid, folders, page):
    items, total_pages = paginate(folders, page)
    kb = InlineKeyboardMarkup(row_width=1)
    for cat, name in items:
        kb.add(InlineKeyboardButton(f"🗑 {cat.upper()}: {name}", callback_data=f"del_confirm|{cat}|{name}"))
    nav = get_nav_buttons("del_page", page, total_pages)
    for row in nav:
        kb.row(*row)
    kb.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel_del"))
    bot.send_message(uid, f"Select folder to delete (Page {page}/{total_pages}):", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_page") and is_admin(c.from_user.id))
def del_page_cb(c):
    _, action, cur_page = c.data.split("|")
    page = int(cur_page)
    if action == "next":
        page += 1
    else:
        page -= 1
    folders = fs.get_all_folders()
    show_delete_page(c.from_user.id, folders, page)
    bot.delete_message(c.from_user.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_confirm") and is_admin(c.from_user.id))
def del_confirm(c):
    _, cat, name = c.data.split("|")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Yes", callback_data=f"del_exec|{cat}|{name}"))
    kb.add(InlineKeyboardButton("❌ No", callback_data="cancel_del"))
    bot.edit_message_text(f"⚠️ Delete '{name}' from {cat.upper()}?", 
                         c.from_user.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_exec") and is_admin(c.from_user.id))
def del_exec(c):
    _, cat, name = c.data.split("|")
    if fs.delete_folder(cat, name):
        bot.answer_callback_query(c.id, "Deleted")
        bot.edit_message_text(f"✅ Deleted '{name}'.", c.from_user.id, c.message.message_id)
    else:
        bot.answer_callback_query(c.id, "Failed")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_del" and is_admin(c.from_user.id))
def cancel_del(c):
    bot.edit_message_text("Operation cancelled.", c.from_user.id, c.message.message_id)
    admin_panel(c.message)

# =========================
# EDIT FOLDER PRICE (FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Folder Price" and is_admin(m.from_user.id))
def edit_price(m):
    folders = fs.get_all_folders()
    if not folders:
        bot.send_message(m.from_user.id, "No folders to edit.")
        return
    page = 1
    show_edit_page(m.from_user.id, folders, page)

def show_edit_page(uid, folders, page):
    items, total_pages = paginate(folders, page)
    kb = InlineKeyboardMarkup(row_width=1)
    for cat, name in items:
        price = fs.db[cat][name]["price"]
        kb.add(InlineKeyboardButton(f"💰 {cat.upper()}: {name} [{price} pts]", callback_data=f"edit_sel|{cat}|{name}"))
    nav = get_nav_buttons("edit_page", page, total_pages)
    for row in nav:
        kb.row(*row)
    kb.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel_edit"))
    bot.send_message(uid, f"Select folder to edit (Page {page}/{total_pages}):", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_page") and is_admin(c.from_user.id))
def edit_page_cb(c):
    _, action, cur_page = c.data.split("|")
    page = int(cur_page)
    if action == "next":
        page += 1
    else:
        page -= 1
    folders = fs.get_all_folders()
    show_edit_page(c.from_user.id, folders, page)
    bot.delete_message(c.from_user.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_sel") and is_admin(c.from_user.id))
def edit_sel(c):
    _, cat, name = c.data.split("|")
    msg = bot.send_message(c.from_user.id, f"Send new price for '{name}' (0 for free):")
    bot.register_next_step_handler(msg, lambda m: edit_price2(m, cat, name, c.message.message_id))

def edit_price2(m, cat, name, msg_id):
    try:
        price = int(m.text)
        if fs.edit_price(cat, name, price):
            bot.send_message(m.from_user.id, f"✅ Price updated to {price} points for '{name}'.")
            try:
                bot.delete_message(m.from_user.id, msg_id)
            except:
                pass
        else:
            bot.send_message(m.from_user.id, "❌ Failed to update.")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_edit" and is_admin(c.from_user.id))
def cancel_edit(c):
    bot.edit_message_text("Operation cancelled.", c.from_user.id, c.message.message_id)
    admin_panel(c.message)

# =========================
# STATS
# =========================
@bot.message_handler(func=lambda m: m.text == "🧮 Stats" and is_admin(m.from_user.id))
def stats(m):
    users = load("users.json")
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip"))
    free = total - vip
    db = load("db.json")
    free_folders = len(db["free"])
    vip_folders = len(db["vip"])
    apps_folders = len(db["apps"])
    courses_folders = len(db["courses"])
    msg = f"📊 *Stats*\n\n👥 Total: {total}\n💎 VIP: {vip}\n🆓 Free: {free}\n\n📁 Content:\n📂 Free: {free_folders}\n💎 VIP: {vip_folders}\n📱 Apps: {apps_folders}\n📚 Courses: {courses_folders}"
    bot.send_message(m.from_user.id, msg)

# =========================
# GENERATE CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Generate Codes" and is_admin(m.from_user.id))
def gen_codes(m):
    msg = bot.send_message(m.from_user.id, "Points per code:")
    bot.register_next_step_handler(msg, gen_codes2)

def gen_codes2(m):
    try:
        points = int(m.text)
        msg = bot.send_message(m.from_user.id, "Number of codes (max 50):")
        bot.register_next_step_handler(msg, lambda m2: gen_codes3(m2, points))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

def gen_codes3(m, points):
    try:
        count = min(int(m.text), 50)
        codes = codesys.generate(points, count)
        bot.send_message(m.from_user.id, f"✅ {count} codes generated:\n`{chr(10).join(codes)}`", parse_mode="Markdown")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

# =========================
# UPLOAD FILES
# =========================
def upload_files(category, uid):
    bot.send_message(uid, f"Send files for {category}. Send /done when finished.")
    bot.register_next_step_handler_by_chat_id(uid, lambda m: upload_step(m, category, uid, []))

def upload_step(m, category, uid, files):
    if m.text and m.text == "/done":
        if not files:
            bot.send_message(uid, "No files. Cancelled.")
            return
        msg = bot.send_message(uid, "Folder name:")
        bot.register_next_step_handler(msg, lambda m2: folder_name(m2, category, files))
        return
    if m.content_type in ["document", "photo", "video"]:
        files.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, f"✅ {len(files)} file(s) saved. Send next or /done.")
        bot.register_next_step_handler_by_chat_id(uid, lambda m2: upload_step(m2, category, uid, files))
    else:
        bot.send_message(uid, "Unsupported. Send document/photo/video.")
        bot.register_next_step_handler_by_chat_id(uid, lambda m2: upload_step(m2, category, uid, files))

def folder_name(m, category, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "Price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: final_price(m2, category, name, files))

def final_price(m, category, name, files):
    try:
        price = int(m.text)
        fs.add_folder(category, name, files, price)
        bot.send_message(m.from_user.id, f"✅ Folder '{name}' added to {category} with {len(files)} file(s), price {price} pts.")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price. Cancelled.")

@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE" and is_admin(m.from_user.id))
def upload_free(m):
    upload_files("free", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP" and is_admin(m.from_user.id))
def upload_vip(m):
    upload_files("vip", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS" and is_admin(m.from_user.id))
def upload_apps(m):
    upload_files("apps", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "📚 Upload Courses" and is_admin(m.from_user.id))
def upload_courses(m):
    upload_files("courses", m.from_user.id)

# =========================
# REDEEM CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeem(m):
    if not force.check(m.from_user.id):
        bot.send_message(m.from_user.id, "🚫 Join channels first.", reply_markup=force.join_buttons())
        return
    msg = bot.send_message(m.from_user.id, "Send code:")
    bot.register_next_step_handler(msg, redeem2)

def redeem2(m):
    user = User(m.from_user.id)
    ok, pts = codesys.redeem(m.text.strip(), user)
    if ok:
        bot.send_message(m.from_user.id, f"✅ Redeemed {pts} points! Total: {user.points()}")
    else:
        bot.send_message(m.from_user.id, "❌ Invalid or used code.")

# =========================
# BROADCAST
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def broadcast(m):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("All", callback_data="bcast_all"),
        InlineKeyboardButton("VIP", callback_data="bcast_vip"),
        InlineKeyboardButton("Free", callback_data="bcast_free")
    )
    bot.send_message(m.from_user.id, "Target audience:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bcast_") and is_admin(c.from_user.id))
def bcast_target(c):
    target = c.data.split("_")[1]
    msg = bot.send_message(c.from_user.id, "Send broadcast message (text/photo/video/doc):")
    bot.register_next_step_handler(msg, lambda m: bcast_send(m, target))

def bcast_send(m, target):
    users = load("users.json")
    sent = 0
    failed = 0
    for uid_str, data in users.items():
        if target == "vip" and not data.get("vip"):
            continue
        if target == "free" and data.get("vip"):
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
            sent += 1
        except:
            failed += 1
    bot.send_message(ADMIN_ID, f"Broadcast done.\n✅ Sent: {sent}\n❌ Failed: {failed}")

# =========================
# USER COMMANDS
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    args = m.text.split()
    Referral().handle_start(uid, args)
    if not force.check(uid):
        bot.send_message(uid, "🚫 *ACCESS DENIED!*\n\nPlease join the required channels:", 
                         parse_mode="Markdown", reply_markup=force.join_buttons())
        return
    cfg = load("config.json")
    bot.send_message(uid, cfg["welcome"], reply_markup=main_menu(uid))

@bot.callback_query_handler(func=lambda c: c.data == "verify_join")
def verify(c):
    uid = c.from_user.id
    if force.check(uid):
        bot.edit_message_text("✅ Access granted!", uid, c.message.message_id)
        cfg = load("config.json")
        bot.send_message(uid, cfg["welcome"], reply_markup=main_menu(uid))
    else:
        bot.answer_callback_query(c.id, "Still not joined all channels!")
        bot.edit_message_text("🚫 Still not joined!", uid, c.message.message_id, reply_markup=force.join_buttons())

# =========================
# USER FOLDER BROWSING (PAGINATED)
# =========================
@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS", "💎 VIP METHODS", "📦 PREMIUM APPS", "📚 PREMIUM COURSES"])
def user_category(m):
    uid = m.from_user.id
    if not force.check(uid):
        bot.send_message(uid, "Join channels first.", reply_markup=force.join_buttons())
        return
    cat_map = {
        "📂 FREE METHODS": "free",
        "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps",
        "📚 PREMIUM COURSES": "courses"
    }
    cat = cat_map[m.text]
    folders = list(fs.get_category(cat).items())
    if not folders:
        bot.send_message(uid, f"No {cat.upper()} folders yet.")
        return
    page = 1
    show_user_folders(uid, cat, folders, page)

def show_user_folders(uid, cat, folders, page):
    items, total_pages = paginate(folders, page)
    kb = InlineKeyboardMarkup(row_width=1)
    for name, info in items:
        price = info.get("price", 0)
        display = f"{name} [{price} pts]" if price else name
        kb.add(InlineKeyboardButton(display, callback_data=f"open|{cat}|{name}"))
    nav = get_nav_buttons(f"ufolder_{cat}", page, total_pages)
    for row in nav:
        kb.row(*row)
    bot.send_message(uid, f"📂 {cat.upper()} (Page {page}/{total_pages}):", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ufolder_") and not c.data.startswith("ufolder_open"))
def user_folder_page(c):
    _, cat, action, cur_page = c.data.split("|")
    page = int(cur_page)
    if action == "next":
        page += 1
    else:
        page -= 1
    folders = list(fs.get_category(cat).items())
    show_user_folders(c.from_user.id, cat, folders, page)
    bot.delete_message(c.from_user.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("open"))
def open_folder(c):
    _, cat, name = c.data.split("|")
    user = User(c.from_user.id)
    if not force.check(c.from_user.id):
        bot.answer_callback_query(c.id, "Join channels first!")
        return
    folder = fs.get_category(cat).get(name)
    if not folder:
        bot.answer_callback_query(c.id, "Folder not found")
        return
    if cat == "vip" and not user.is_vip():
        bot.send_message(c.from_user.id, load("config.json")["vip_msg"])
        return
    price = folder.get("price", 0)
    if not user.is_vip() and price > 0:
        if user.points() < price:
            bot.answer_callback_query(c.id, f"Need {price} points!")
            bot.send_message(c.from_user.id, f"You need {price} points. You have {user.points()}.")
            return
        user.add_points(-price)
        bot.send_message(c.from_user.id, f"💰 Used {price} points. Remaining: {user.points()}")
    # send files
    sent = 0
    for f in folder["files"]:
        try:
            if f["type"] == "photo":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            elif f["type"] == "video":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            elif f["type"] == "document":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            sent += 1
        except:
            continue
    if sent:
        bot.send_message(c.from_user.id, f"✅ Sent {sent} file(s) from '{name}'")
    else:
        bot.send_message(c.from_user.id, "❌ No files could be sent.")

# =========================
# GENERAL COMMANDS
# =========================
@bot.message_handler(func=lambda m: m.text in ["💰 POINTS", "⭐ BUY VIP", "🎁 REFERRAL", "👤 ACCOUNT", "🆔 CHAT ID"])
def user_commands(m):
    uid = m.from_user.id
    if not force.check(uid):
        bot.send_message(uid, "Join channels first.", reply_markup=force.join_buttons())
        return
    user = User(uid)
    text = m.text
    if text == "💰 POINTS":
        bot.send_message(uid, f"💰 *Your points:* `{user.points()}`", parse_mode="Markdown")
    elif text == "⭐ BUY VIP":
        bot.send_message(uid, load("config.json")["vip_msg"], parse_mode="Markdown")
    elif text == "🎁 REFERRAL":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🎁 *Referral Link*\n`{link}`\n\nYou earn +{load('config.json')['ref_reward']} points per referral.", parse_mode="Markdown")
    elif text == "👤 ACCOUNT":
        status = "💎 VIP" if user.is_vip() else "🆓 FREE"
        msg = f"👤 *Account*\nStatus: {status}\nPoints: `{user.points()}`"
        if user.ref():
            msg += f"\nReferred by: `{user.ref()}`"
        bot.send_message(uid, msg, parse_mode="Markdown")
    elif text == "🆔 CHAT ID":
        bot.send_message(uid, f"🆔 Your ID: `{uid}`", parse_mode="Markdown")

# =========================
# FALLBACK
# =========================
@bot.message_handler(func=lambda m: True)
def fallback(m):
    if not force.check(m.from_user.id):
        bot.send_message(m.from_user.id, "Join channels first.", reply_markup=force.join_buttons())
        return
    bot.send_message(m.from_user.id, "Use the menu buttons.", reply_markup=main_menu(m.from_user.id))

# =========================
# POLLING
# =========================
def run():
    while True:
        try:
            print("Bot started.")
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    while True:
        time.sleep(1)
