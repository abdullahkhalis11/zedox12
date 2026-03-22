# =========================
# ZEDOX BOT - COMPLETE REVISED
# ✅ Ready for Railway
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

def load(file):
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# CLASSES & SYSTEMS
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

class FileSystem:
    def __init__(self): self.db = load("db.json")
    def save_db(self): save("db.json", self.db)
    def add_folder(self, category, name, files, price=0):
        self.db[category][name] = {"files": files, "price": price}
        self.save_db()
    def delete_folder(self, category, name):
        if category in self.db and name in self.db[category]:
            del self.db[category][name]
            self.save_db()
            return True
        return False
    def get_category(self, category): return self.db.get(category, {})

fs = FileSystem()

class Codes:
    def __init__(self): self.codes = load("codes.json")
    def generate(self, points, count=1):
        res = []
        for _ in range(count):
            code = 'ZEDOX'+''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
            self.codes[code] = points
            res.append(code)
        save("codes.json", self.codes)
        return res
    def redeem(self, code, user):
        self.codes = load("codes.json")
        if code in self.codes:
            pts = self.codes[code]
            user.add_points(pts)
            del self.codes[code]
            save("codes.json", self.codes)
            return True, pts
        return False, 0

codesys = Codes()

# =========================
# KEYBOARDS
# =========================

def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS","💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS","🎓 PREMIUM COURSES")
    kb.row("⭐ BUY VIP","🎁 REFERRAL")
    kb.row("👤 ACCOUNT","🏆 Redeem")
    if uid == ADMIN_ID: kb.row("⚙️ ADMIN PANEL")
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP","➖ Remove VIP","💰 Give Points")
    kb.row("📤 Broadcast","🗑 Delete Folder","📦 Upload FREE")
    kb.row("💎 Upload VIP","📱 Upload APPS","🎓 Upload COURSES")
    kb.row("➕ Add Force Join","➖ Remove Force Join","🧮 Stats")
    kb.row("🏆 Generate Codes","❌ Exit Admin")
    return kb

# =========================
# PAGINATION LOGIC
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
# ADMIN HANDLERS
# =========================

@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and m.from_user.id == ADMIN_ID)
def admin_panel(m):
    bot.send_message(m.from_user.id, "🛠️ *Admin Panel*", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and m.from_user.id == ADMIN_ID)
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Back to User Menu", reply_markup=main_menu(m.from_user.id))

@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and m.from_user.id == ADMIN_ID)
def delete_folder_start(m):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("Free", callback_data="del_cat|free"), InlineKeyboardButton("VIP", callback_data="del_cat|vip"))
    kb.row(InlineKeyboardButton("Apps", callback_data="del_cat|apps"), InlineKeyboardButton("Courses", callback_data="del_cat|courses"))
    bot.send_message(m.from_user.id, "Select category to delete from:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_cat|"))
def delete_category_selected(c):
    cat = c.data.split("|")[1]
    folders = fs.get_category(cat)
    if not folders:
        bot.answer_callback_query(c.id, "Category is empty.")
        return
    kb = InlineKeyboardMarkup()
    for name in folders.keys():
        kb.add(InlineKeyboardButton(name, callback_data=f"confirm_del|{cat}|{name}"))
    bot.edit_message_text(f"Select folder to 🗑 DELETE from {cat}:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_del|"))
def delete_confirmed(c):
    _, cat, name = c.data.split("|")
    if fs.delete_folder(cat, name):
        bot.answer_callback_query(c.id, f"Deleted {name}")
        bot.edit_message_text(f"✅ Folder `{name}` deleted successfully.", c.from_user.id, c.message.id)
    else:
        bot.answer_callback_query(c.id, "Error deleting.")

# =========================
# UPLOAD SYSTEM
# =========================

def upload_files(category, uid):
    msg = bot.send_message(uid, f"📤 Uploading to `{category.upper()}`\nSend files one by one. Send /done when finished.")
    bot.register_next_step_handler(msg, lambda m: upload_step(m, category, uid, []))

def upload_step(m, cat, uid, files):
    if m.text == "/done":
        if not files:
            bot.send_message(uid, "❌ No files received. Cancelled.")
            return
        msg = bot.send_message(uid, "✏️ Enter folder name:")
        bot.register_next_step_handler(msg, lambda m2: upload_name(m2, cat, files))
        return
    if m.content_type in ["document", "photo", "video"]:
        files.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, "✅ Saved. Send next or /done")
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, cat, uid, files))

def upload_name(m, cat, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Set price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: upload_finalize(m2, cat, name, files))

def upload_finalize(m, cat, name, files):
    try:
        price = int(m.text)
        fs.add_folder(cat, name, files, price)
        bot.send_message(m.from_user.id, f"✅ Folder `{name}` added to {cat}.")
    except: bot.send_message(m.from_user.id, "❌ Invalid price.")

@bot.message_handler(func=lambda m: m.text.startswith("📦 Upload FREE") and m.from_user.id == ADMIN_ID)
def u_free(m): upload_files("free", m.from_user.id)
@bot.message_handler(func=lambda m: m.text.startswith("💎 Upload VIP") and m.from_user.id == ADMIN_ID)
def u_vip(m): upload_files("vip", m.from_user.id)
@bot.message_handler(func=lambda m: m.text.startswith("📱 Upload APPS") and m.from_user.id == ADMIN_ID)
def u_apps(m): upload_files("apps", m.from_user.id)
@bot.message_handler(func=lambda m: m.text.startswith("🎓 Upload COURSES") and m.from_user.id == ADMIN_ID)
def u_courses(m): upload_files("courses", m.from_user.id)

# =========================
# USER COMMANDS
# =========================

@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    if len(m.text.split()) > 1:
        from_uid = m.text.split()[1]
        users = load("users.json")
        if from_uid != str(uid) and from_uid in users and not User(uid).data.get("ref"):
            users[from_uid]["points"] += load("config.json").get("ref_reward", 5)
            save("users.json", users)
            User(uid).set_ref(from_uid)

    if not force.check(uid):
        bot.send_message(uid, "🚫 *ACCESS DENIED!*\nPlease join our channels to use the bot:", reply_markup=force.join_buttons())
        return
    bot.send_message(uid, load("config.json")["welcome"], reply_markup=main_menu(uid))

@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS", "💎 VIP METHODS", "📦 PREMIUM APPS", "🎓 PREMIUM COURSES"])
def show_folders(m):
    uid = m.from_user.id
    if not force.check(uid):
        bot.send_message(uid, "🚫 Join channels first!", reply_markup=force.join_buttons())
        return
    
    mapping = {
        "📂 FREE METHODS": "free", "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps", "🎓 PREMIUM COURSES": "courses"
    }
    cat = mapping[m.text]
    bot.send_message(uid, f"📂 *{m.text}*", reply_markup=get_folder_kb(cat))

@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def handle_pagination(c):
    _, cat, page = c.data.split("|")
    bot.edit_message_reply_markup(c.from_user.id, c.message.id, reply_markup=get_folder_kb(cat, int(page)))

@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    _, cat, name = c.data.split("|")
    user = User(c.from_user.id)
    folder = fs.get_category(cat).get(name)
    
    if cat == "vip" and not user.is_vip():
        bot.send_message(c.from_user.id, load("config.json")["vip_msg"])
        return

    price = folder.get("price", 0)
    if not user.is_vip() and price > user.points():
        bot.answer_callback_query(c.id, f"❌ Need {price} points!")
        return
    
    if not user.is_vip() and price > 0:
        user.add_points(-price)

    bot.answer_callback_query(c.id, "Sending files...")
    for f in folder["files"]:
        try: bot.copy_message(c.from_user.id, f["chat"], f["msg"])
        except: continue

@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck(c):
    if force.check(c.from_user.id):
        bot.edit_message_text("✅ Access Granted!", c.from_user.id, c.message.id)
        bot.send_message(c.from_user.id, "Use the menu below:", reply_markup=main_menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id, "❌ Still not joined!", show_alert=True)

# =========================
# OTHER ADMIN TOOLS (Simplified)
# =========================

@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and m.from_user.id == ADMIN_ID)
def add_fj(m):
    msg = bot.send_message(m.from_user.id, "Send channel username (with @):")
    bot.register_next_step_handler(msg, lambda m2: (
        config := load("config.json"),
        config["force_channels"].append(m2.text),
        save("config.json", config),
        bot.send_message(m.from_user.id, "✅ Added")
    ))

@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeem(m):
    msg = bot.send_message(m.from_user.id, "Send code:")
    bot.register_next_step_handler(msg, lambda m2: (
        res := codesys.redeem(m2.text, User(m.from_user.id)),
        bot.send_message(m.from_user.id, f"✅ Success! +{res[1]} pts" if res[0] else "❌ Invalid code")
    ))

@bot.message_handler(func=lambda m: m.text == "🎁 REFERRAL")
def ref(m):
    bot.send_message(m.from_user.id, f"🎁 Link: `https://t.me/{bot.get_me().username}?start={m.from_user.id}`")

@bot.message_handler(func=lambda m: m.text == "👤 ACCOUNT")
def acc(m):
    u = User(m.from_user.id)
    bot.send_message(m.from_user.id, f"👤 Status: {'💎 VIP' if u.is_vip() else '🆓 FREE'}\n💰 Points: {u.points()}")

# =========================
# RUN BOT
# =========================
def run():
    print("ZEDOX BOT RUNNING...")
    bot.infinity_polling()

if __name__ == "__main__":
    run()
