# =========================
# ZEDOX BOT - COMPLETE ALL-IN-ONE
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
# CORE CLASSES
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
    def points(self): return self.data.get("points", 0)
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
                if member.status in ["left", "kicked"]: return False
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
    def get_category(self, category):
        self.db = load("db.json")
        return self.db.get(category, {})

fs = FileSystem()

class Codes:
    def generate(self, points, count=1):
        c_db = load("codes.json")
        res = []
        for _ in range(count):
            code = 'ZEDOX'+''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
            c_db[code] = points
            res.append(code)
        save("codes.json", c_db)
        return res
    def redeem(self, code, user):
        c_db = load("codes.json")
        if code in c_db:
            pts = c_db[code]
            user.add_points(pts)
            del c_db[code]
            save("codes.json", c_db)
            return True, pts
        return False, 0

codesys = Codes()

# =========================
# KEYBOARDS & UI
# =========================

def main_menu(uid):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📂 FREE METHODS", "💎 VIP METHODS")
    kb.row("📦 PREMIUM APPS", "🎓 PREMIUM COURSES")
    kb.row("⭐ BUY VIP", "🎁 REFERRAL")
    kb.row("👤 ACCOUNT", "🆔 CHAT ID", "🏆 Redeem")
    if uid == ADMIN_ID: kb.row("⚙️ ADMIN PANEL")
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add VIP", "➖ Remove VIP", "💰 Give Points")
    kb.row("📝 Set Points", "⭐ Set VIP Message", "🏠 Set Welcome Message")
    kb.row("📤 Broadcast", "🗑 Delete Folder", "📦 Upload FREE")
    kb.row("💎 Upload VIP", "📱 Upload APPS", "🎓 Upload COURSES")
    kb.row("➕ Add Force Join", "➖ Remove Force Join", "🧮 Stats")
    kb.row("🏆 Generate Codes", "❌ Exit Admin")
    return kb

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

@bot.message_handler(func=lambda m: m.text == "➕ Add VIP" and m.from_user.id == ADMIN_ID)
def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the Chat ID to add VIP:")
    bot.register_next_step_handler(msg, lambda m2: (User(int(m2.text)).make_vip(), bot.send_message(m.from_user.id, "✅ Added")))

@bot.message_handler(func=lambda m: m.text == "➖ Remove VIP" and m.from_user.id == ADMIN_ID)
def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the Chat ID to remove VIP:")
    bot.register_next_step_handler(msg, lambda m2: (User(int(m2.text)).remove_vip(), bot.send_message(m.from_user.id, "✅ Removed")))

@bot.message_handler(func=lambda m: m.text == "💰 Give Points" and m.from_user.id == ADMIN_ID)
def give_pts_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send Chat ID:")
    bot.register_next_step_handler(msg, give_pts_step2)

def give_pts_step2(m):
    uid = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Points to add:")
    bot.register_next_step_handler(msg, lambda m2: (User(uid).add_points(int(m2.text)), bot.send_message(m.from_user.id, "✅ Added")))

@bot.message_handler(func=lambda m: m.text == "🧮 Stats" and m.from_user.id == ADMIN_ID)
def stats(m):
    u = load("users.json")
    v = sum(1 for x in u.values() if x["vip"])
    bot.send_message(m.from_user.id, f"📊 *Stats*\nTotal: {len(u)}\nVIP: {v}\nFree: {len(u)-v}")

@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and m.from_user.id == ADMIN_ID)
def del_start(m):
    kb = InlineKeyboardMarkup()
    cats = ["free", "vip", "apps", "courses"]
    for c in cats: kb.add(InlineKeyboardButton(c.upper(), callback_data=f"del_cat|{c}"))
    bot.send_message(m.from_user.id, "Select category to delete from:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_cat|"))
def del_list(c):
    cat = c.data.split("|")[1]
    items = fs.get_category(cat)
    kb = InlineKeyboardMarkup()
    for k in items.keys(): kb.add(InlineKeyboardButton(k, callback_data=f"cf_del|{cat}|{k}"))
    bot.edit_message_text(f"Select folder to delete in {cat}:", c.from_user.id, c.message.id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cf_del|"))
def del_done(c):
    _, cat, name = c.data.split("|")
    fs.delete_folder(cat, name)
    bot.answer_callback_query(c.id, f"Deleted {name}")
    bot.edit_message_text(f"✅ Folder `{name}` deleted.", c.from_user.id, c.message.id)

# =========================
# BROADCAST SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and m.from_user.id == ADMIN_ID)
def bc_start(m):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("All", callback_data="bc|all"), InlineKeyboardButton("VIP", callback_data="bc|vip"))
    bot.send_message(m.from_user.id, "Target Audience:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_get_msg(c):
    target = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "Send message to broadcast (text/image/video):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, target))

def bc_send(m, target):
    users = load("users.json")
    count = 0
    for uid, data in users.items():
        if target == "vip" and not data["vip"]: continue
        try:
            if m.content_type == "text": bot.send_message(uid, m.text)
            elif m.content_type == "photo": bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)
            elif m.content_type == "video": bot.send_video(uid, m.video.file_id, caption=m.caption)
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"📢 Sent to {count} users.")

# =========================
# UPLOAD SYSTEM
# =========================
def upload_files(cat, uid):
    msg = bot.send_message(uid, f"📤 Uploading to `{cat.upper()}`\nSend files. Send /done when finished.")
    bot.register_next_step_handler(msg, lambda m: upload_step(m, cat, uid, []))

def upload_step(m, cat, uid, files):
    if m.text == "/done":
        msg = bot.send_message(uid, "✏️ Folder Name:")
        bot.register_next_step_handler(msg, lambda m2: upload_price(m2, cat, files))
        return
    if m.content_type in ["document", "photo", "video"]:
        files.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, "✅ File added. Next or /done")
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, cat, uid, files))

def upload_price(m, cat, files):
    name = m.text
    msg = bot.send_message(m.from_user.id, "✏️ Price (0 for free):")
    bot.register_next_step_handler(msg, lambda m2: (fs.add_folder(cat, name, files, int(m2.text)), bot.send_message(m.from_user.id, "✅ Added")))

@bot.message_handler(func=lambda m: m.text.startswith("📦 Upload FREE") and m.from_user.id == ADMIN_ID)
def up_f(m): upload_files("free", m.from_user.id)
@bot.message_handler(func=lambda m: m.text.startswith("💎 Upload VIP") and m.from_user.id == ADMIN_ID)
def up_v(m): upload_files("vip", m.from_user.id)
@bot.message_handler(func=lambda m: m.text.startswith("📱 Upload APPS") and m.from_user.id == ADMIN_ID)
def up_a(m): upload_files("apps", m.from_user.id)
@bot.message_handler(func=lambda m: m.text.startswith("🎓 Upload COURSES") and m.from_user.id == ADMIN_ID)
def up_c(m): upload_files("courses", m.from_user.id)

# =========================
# USER SYSTEM
# =========================

@bot.message_handler(commands=["start"])
def start(m):
    uid = m.from_user.id
    # Referral Logic
    if len(m.text.split()) > 1:
        ref_id = m.text.split()[1]
        u_db = load("users.json")
        if ref_id != str(uid) and ref_id in u_db and not User(uid).data.get("ref"):
            User(ref_id).add_points(load("config.json")["ref_reward"])
            User(uid).set_ref(ref_id)
    
    if not force.check(uid):
        bot.send_message(uid, "🚫 *JOIN CHANNELS FIRST*", reply_markup=force.join_buttons())
        return
    bot.send_message(uid, load("config.json")["welcome"], reply_markup=main_menu(uid))

@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS", "💎 VIP METHODS", "📦 PREMIUM APPS", "🎓 PREMIUM COURSES"])
def show_cats(m):
    if not force.check(m.from_user.id):
        bot.send_message(m.from_user.id, "🚫 Join channels!", reply_markup=force.join_buttons())
        return
    map = {"📂 FREE METHODS":"free", "💎 VIP METHODS":"vip", "📦 PREMIUM APPS":"apps", "🎓 PREMIUM COURSES":"courses"}
    cat = map[m.text]
    bot.send_message(m.from_user.id, f"📂 *{m.text}*", reply_markup=get_folder_kb(cat))

@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def paginate(c):
    _, cat, p = c.data.split("|")
    bot.edit_message_reply_markup(c.from_user.id, c.message.id, reply_markup=get_folder_kb(cat, int(p)))

@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_f(c):
    _, cat, name = c.data.split("|")
    u = User(c.from_user.id)
    folder = fs.get_category(cat).get(name)
    if cat == "vip" and not u.is_vip():
        bot.send_message(c.from_user.id, load("config.json")["vip_msg"])
        return
    if not u.is_vip() and folder["price"] > u.points():
        bot.answer_callback_query(c.id, "❌ Not enough points!", show_alert=True)
        return
    if not u.is_vip() and folder["price"] > 0: u.add_points(-folder["price"])
    for f in folder["files"]:
        try: bot.copy_message(c.from_user.id, f["chat"], f["msg"])
        except: continue

@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck(c):
    if force.check(c.from_user.id):
        bot.send_message(c.from_user.id, "✅ Welcome!", reply_markup=main_menu(c.from_user.id))
    else:
        bot.answer_callback_query(c.id, "❌ Join all channels!", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeemer(m):
    msg = bot.send_message(m.from_user.id, "Send code:")
    bot.register_next_step_handler(msg, lambda m2: (
        res := codesys.redeem(m2.text.strip(), User(m.from_user.id)),
        bot.send_message(m.from_user.id, f"✅ Success! +{res[1]} pts" if res[0] else "❌ Invalid")
    ))

@bot.message_handler(func=lambda m: True)
def other_buttons(m):
    t = m.text
    u = User(m.from_user.id)
    if t == "👤 ACCOUNT":
        bot.send_message(m.from_user.id, f"👤 Status: {'💎 VIP' if u.is_vip() else '🆓 FREE'}\n💰 Points: {u.points()}")
    elif t == "🆔 CHAT ID":
        bot.send_message(m.from_user.id, f"🆔: `{m.from_user.id}`")
    elif t == "🎁 REFERRAL":
        bot.send_message(m.from_user.id, f"🎁 Link: `https://t.me/{bot.get_me().username}?start={m.from_user.id}`")
    elif t == "➕ Add Force Join" and m.from_user.id == ADMIN_ID:
        msg = bot.send_message(m.from_user.id, "Send channel @username:")
        bot.register_next_step_handler(msg, lambda m2: (
            conf := load("config.json"),
            conf["force_channels"].append(m2.text),
            save("config.json", conf),
            bot.send_message(m.from_user.id, "✅ Added")
        ))

# =========================
# POLLING
# =========================
if __name__ == "__main__":
    print("ZEDOX BOT RUNNING...")
    bot.infinity_polling()
