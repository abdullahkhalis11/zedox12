# =========================
# ZEDOX BOT - PART 1
# CORE SYSTEM
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import json, os, random, string

# =========================
# CONFIG
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
        "db.json": {"free": {}, "vip": {}, "apps": {}},
        "codes.json": {}
    }
    for f, d in files.items():
        if not os.path.exists(f):
            with open(f, "w") as file:
                json.dump(d, file, indent=4)

init_files()

# =========================
# HELPERS
# =========================
def load(file):
    with open(file) as f:
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
        users = load("users.json")
        if self.uid not in users:
            users[self.uid] = {"points": 0, "vip": False}
            save("users.json", users)
        self.data = load("users.json")[self.uid]

    def is_vip(self): return self.data["vip"]
    def points(self): return self.data["points"]

    def add_points(self, pts):
        users = load("users.json")
        users[self.uid]["points"] += pts
        save("users.json", users)

    def set_points(self, pts):
        users = load("users.json")
        users[self.uid]["points"] = pts
        save("users.json", users)

    def make_vip(self):
        users = load("users.json")
        users[self.uid]["vip"] = True
        save("users.json", users)

# =========================
# FILE SYSTEM
# =========================
class FileSystem:
    def __init__(self):
        self.db = load("db.json")

    def save(self):
        save("db.json", self.db)

    def add_folder(self, cat, name, files, price):
        self.db[cat][name] = {"files": files, "price": price}
        self.save()

    def delete_folder(self, cat, name):
        if name in self.db[cat]:
            del self.db[cat][name]
            self.save()
            return True
        return False

    def edit_price(self, cat, name, price):
        if name in self.db[cat]:
            self.db[cat][name]["price"] = price
            self.save()
            return True
        return False

    def get(self, cat):
        return self.db.get(cat, {})

fs = FileSystem()

# =========================
# COUPON SYSTEM
# =========================
class Codes:
    def __init__(self):
        self.codes = load("codes.json")

    def save(self):
        save("codes.json", self.codes)

    def generate(self, pts, count):
        result = []
        for _ in range(count):
            code = "ZEDOX" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.codes[code] = pts
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

codesys = Codes()

# =========================
# ADMIN CHECK
# =========================
def is_admin(uid):
    return uid == ADMIN_ID
# =========================
# PART 2 - ADMIN PANEL
# =========================

def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS", "💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS", "💰 POINTS")
    kb.row("🏆 Redeem")

    if is_admin(uid):
        kb.row("⚙️ ADMIN PANEL")

    return kb

# =========================
# START
# =========================
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.from_user.id, "🔥 Welcome to ZEDOX BOT", reply_markup=main_menu(m.from_user.id))

# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📦 Upload FREE", "💎 Upload VIP", "📱 Upload APPS")
    kb.row("🗑 Delete Folder", "✏️ Edit Price")
    kb.row("🏷 Generate Coupon")
    bot.send_message(m.from_user.id, "Admin Panel", reply_markup=kb)

# =========================
# COUPON GENERATION
# =========================
@bot.message_handler(func=lambda m: m.text == "🏷 Generate Coupon")
def gen1(m):
    msg = bot.send_message(m.from_user.id, "Points?")
    bot.register_next_step_handler(msg, gen2)

def gen2(m):
    pts = int(m.text)
    msg = bot.send_message(m.from_user.id, "Count?")
    bot.register_next_step_handler(msg, lambda m2: gen3(m2, pts))

def gen3(m, pts):
    count = int(m.text)
    codes = codesys.generate(pts, count)
    bot.send_message(m.from_user.id, "\n".join(codes))
# =========================
# PART 3 - FILE MANAGEMENT
# =========================

def upload_files(cat, uid):
    msg = bot.send_message(uid, "Send files, then /done")
    bot.register_next_step_handler(msg, lambda m: upload_step(m, cat, uid, []))

def upload_step(m, cat, uid, files):
    if m.text == "/done":
        msg = bot.send_message(uid, "Folder name?")
        bot.register_next_step_handler(msg, lambda m2: finalize_folder(m2, cat, files))
        return

    files.append({"chat": m.chat.id, "msg": m.message_id})
    bot.send_message(uid, "Saved")
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, cat, uid, files))

def finalize_folder(m, cat, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "Price?")
    bot.register_next_step_handler(msg, lambda m2: save_folder(m2, cat, name, files))

def save_folder(m, cat, name, files):
    fs.add_folder(cat, name, files, int(m.text))
    bot.send_message(m.from_user.id, "Done")

@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE")
def upf(m): upload_files("free", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP")
def upv(m): upload_files("vip", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS")
def upa(m): upload_files("apps", m.from_user.id)

# DELETE FIXED
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder")
def del1(m):
    kb = InlineKeyboardMarkup()
    for c, items in fs.db.items():
        for n in items:
            kb.add(InlineKeyboardButton(f"{n} [{c}]", callback_data=f"del|{c}|{n}"))
    bot.send_message(m.from_user.id, "Select", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del|"))
def del2(c):
    _, cat, name = c.data.split("|")
    fs.delete_folder(cat, name)
    bot.edit_message_text("Deleted", c.message.chat.id, c.message.message_id)

# EDIT FIXED
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Price")
def edit1(m):
    kb = InlineKeyboardMarkup()
    for c, items in fs.db.items():
        for n in items:
            kb.add(InlineKeyboardButton(f"{n} [{c}]", callback_data=f"edit|{c}|{n}"))
    bot.send_message(m.from_user.id, "Select", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit|"))
def edit2(c):
    _, cat, name = c.data.split("|")
    msg = bot.send_message(c.from_user.id, "New price?")
    bot.register_next_step_handler(msg, lambda m: edit3(m, cat, name))

def edit3(m, cat, name):
    fs.edit_price(cat, name, int(m.text))
    bot.send_message(m.from_user.id, "Updated")
# =========================
# PART 4 - USER SIDE
# =========================

def show(cat, uid, page=0):
    data = fs.get(cat)
    names = list(data.keys())

    per = 8
    start = page * per
    end = start + per

    kb = InlineKeyboardMarkup()

    for n in names[start:end]:
        kb.add(InlineKeyboardButton(n, callback_data=f"open|{cat}|{n}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"pg|{cat}|{page-1}"))
    if end < len(names):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"pg|{cat}|{page+1}"))

    if nav:
        kb.row(*nav)

    bot.send_message(uid, f"{cat.upper()} PAGE {page+1}", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📂 FREE METHODS")
def free(m): show("free", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "💎 VIP METHODS")
def vip(m): show("vip", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "📦 PREMIUM APPS")
def apps(m): show("apps", m.from_user.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pg|"))
def page(c):
    _, cat, p = c.data.split("|")
    show(cat, c.from_user.id, int(p))

# OPEN FILES
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def openf(c):
    _, cat, name = c.data.split("|")
    folder = fs.get(cat)[name]

    for f in folder["files"]:
        bot.copy_message(c.from_user.id, f["chat"], f["msg"])

# REDEEM
@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeem(m):
    msg = bot.send_message(m.from_user.id, "Send code")
    bot.register_next_step_handler(msg, redeem2)

def redeem2(m):
    user = User(m.from_user.id)
    ok, pts = codesys.redeem(m.text, user)
    if ok:
        bot.send_message(m.from_user.id, f"Added {pts} points")
    else:
        bot.send_message(m.from_user.id, "Invalid code")

# RUN
bot.infinity_polling()
