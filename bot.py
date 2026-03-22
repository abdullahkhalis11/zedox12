# =========================
# ZEDOX BOT - ULTIMATE EDITION
# Professional Telegram File Sharing Bot with VIP System
# =========================

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json, os, time, random, string, threading, datetime, hashlib
from datetime import datetime, timedelta

# =========================
# CONFIGURATION
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================
# EMOJI CONSTANTS
# =========================
EMOJI = {
    "free": "📂",
    "vip": "💎",
    "apps": "📱",
    "courses": "🎓",
    "points": "💰",
    "referral": "🎁",
    "account": "👤",
    "redeem": "🏆",
    "admin": "⚙️",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "lock": "🔒",
    "unlock": "🔓",
    "star": "⭐",
    "fire": "🔥",
    "crown": "👑"
}

# =========================
# INIT FILES
# =========================
def init_files():
    files = {
        "users.json": {},
        "db.json": {"free": {}, "vip": {}, "apps": {}, "courses": {}},
        "config.json": {
            "force_channels": [],
            "vip_msg": "💎 <b>VIP ACCESS REQUIRED</b>\n\nThis content is only available for VIP members.\n\n<b>VIP Benefits:</b>\n• Access to all VIP methods\n• No points deduction\n• Priority support\n• Exclusive content\n\nContact admin to upgrade!",
            "welcome": "🔥 <b>WELCOME TO ZEDOX BOT</b>\n\nYour ultimate source for premium content!",
            "ref_reward": 10,
            "notify": True,
            "bot_name": "ZEDOX BOT",
            "bot_version": "3.0",
            "maintenance": False,
            "daily_bonus": 5,
            "vip_price": "Contact @admin"
        },
        "codes.json": {},
        "stats.json": {"total_views": 0, "total_downloads": 0, "daily_active": {}},
        "transactions.json": []
    }
    for f, d in files.items():
        if not os.path.exists(f):
            with open(f, "w") as file:
                json.dump(d, file, indent=4)

init_files()

def load(f): return json.load(open(f))
def save(f, d): json.dump(d, open(f, "w"), indent=4)

# =========================
# USER CLASS WITH ENHANCED FEATURES
# =========================
class User:
    def __init__(self, uid):
        self.uid = str(uid)
        users = load("users.json")

        if self.uid not in users:
            users[self.uid] = {
                "points": 0,
                "vip": False,
                "ref": None,
                "join_date": str(datetime.now()),
                "last_active": str(datetime.now()),
                "total_downloads": 0,
                "last_daily": None,
                "warnings": 0,
                "banned": False
            }
            save("users.json", users)

        self.data = users[self.uid]
        
        # Update last active
        self.data["last_active"] = str(datetime.now())
        users[self.uid] = self.data
        save("users.json", users)

    def is_vip(self): 
        return self.data.get("vip", False)
    
    def points(self): 
        return self.data.get("points", 0)
    
    def is_banned(self):
        return self.data.get("banned", False)

    def add_points(self, p):
        self.data["points"] += p
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

    def remove_points(self, p):
        if self.data["points"] >= p:
            self.data["points"] -= p
            users = load("users.json")
            users[self.uid] = self.data
            save("users.json", users)
            return True
        return False

    def make_vip(self, days=30):
        self.data["vip"] = True
        self.data["vip_expiry"] = str(datetime.now() + timedelta(days=days))
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)

    def add_download(self):
        self.data["total_downloads"] += 1
        users = load("users.json")
        users[self.uid] = self.data
        save("users.json", users)
        
        # Update stats
        stats = load("stats.json")
        stats["total_downloads"] += 1
        save("stats.json", stats)

    def daily_bonus(self):
        last = self.data.get("last_daily")
        today = datetime.now().strftime("%Y-%m-%d")
        
        if last != today:
            bonus = load("config.json").get("daily_bonus", 5)
            self.add_points(bonus)
            self.data["last_daily"] = today
            users = load("users.json")
            users[self.uid] = self.data
            save("users.json", users)
            return True, bonus
        return False, 0

# =========================
# ENHANCED CODES SYSTEM
# =========================
class Codes:
    def __init__(self):
        self.codes = load("codes.json")

    def generate(self, pts, count, usage_limit=1):
        res = []
        for _ in range(count):
            code = "ZEDOX" + ''.join(random.choices(string.ascii_uppercase+string.digits, k=8))
            self.codes[code] = {
                "points": pts,
                "uses_left": usage_limit,
                "used_by": [],
                "created": str(datetime.now())
            }
            res.append(code)
        self.save()
        return res

    def redeem(self, code, user):
        code_data = self.codes.get(code)
        
        if not code_data:
            return False, 0, "Invalid code"
        
        if code_data["uses_left"] <= 0:
            return False, 0, "Code already used"
        
        if user.uid in code_data["used_by"]:
            return False, 0, "You already used this code"
        
        pts = code_data["points"]
        user.add_points(pts)
        
        code_data["uses_left"] -= 1
        code_data["used_by"].append(user.uid)
        
        if code_data["uses_left"] <= 0:
            del self.codes[code]
        else:
            self.codes[code] = code_data
            
        self.save()
        return True, pts, "Success"

    def save(self):
        save("codes.json", self.codes)

codesys = Codes()

# =========================
# FORCE JOIN SYSTEM
# =========================
def force_block(uid):
    cfg = load("config.json")
    
    if cfg.get("maintenance", False) and uid != ADMIN_ID:
        bot.send_message(uid, "⚠️ <b>Bot Under Maintenance</b>\n\nPlease try again later.", parse_mode="HTML")
        return True

    for ch in cfg["force_channels"]:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status in ["left","kicked"]:
                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{ch.replace('@','')}"))
                kb.add(InlineKeyboardButton("🔄 Verified", callback_data="recheck"))
                bot.send_message(uid, "🔒 <b>CHANNEL VERIFICATION REQUIRED</b>\n\nPlease join the channel below to continue:", reply_markup=kb, parse_mode="HTML")
                return True
        except:
            return True
    return False

# =========================
# ENHANCED FILE SYSTEM
# =========================
class FS:
    def add(self, cat, name, files, price, description=""):
        db = load("db.json")
        db[cat][name] = {
            "files": files, 
            "price": price, 
            "description": description,
            "date_added": str(datetime.now()),
            "downloads": 0
        }
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

    def edit(self, cat, name, price, description=None):
        db = load("db.json")
        if name in db[cat]:
            db[cat][name]["price"] = price
            if description:
                db[cat][name]["description"] = description
            save("db.json", db)
            return True
        return False
    
    def increment_downloads(self, cat, name):
        db = load("db.json")
        if name in db[cat]:
            db[cat][name]["downloads"] += 1
            save("db.json", db)

fs = FS()

def get_kb(cat, page=0, show_stats=False):
    data = list(fs.get(cat).items())
    per = 8
    start = page*per
    items = data[start:start+per]

    kb = InlineKeyboardMarkup(row_width=2)
    
    for name, d in items:
        price = d["price"]
        downloads = d.get("downloads", 0)
        
        if show_stats:
            txt = f"{name} 💰{price} 👁{downloads}"
        else:
            txt = f"{name} [{price} pts]" if price > 0 else name
            
        kb.add(InlineKeyboardButton(txt, callback_data=f"open|{cat}|{name}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"page|{cat}|{page-1}"))
    if start+per < len(data):
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"page|{cat}|{page+1}"))
    if nav:
        kb.row(*nav)
    
    # Add stats toggle
    kb.add(InlineKeyboardButton("📊 Show Stats", callback_data=f"stats|{cat}|{page}"))
    
    return kb

# =========================
# BEAUTIFUL MENUS
# =========================
def main_menu(uid):
    user = User(uid)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn1 = KeyboardButton(f"{EMOJI['free']} FREE METHODS")
    btn2 = KeyboardButton(f"{EMOJI['vip']} VIP METHODS")
    btn3 = KeyboardButton(f"{EMOJI['apps']} PREMIUM APPS")
    btn4 = KeyboardButton(f"{EMOJI['courses']} PREMIUM COURSES")
    
    kb.add(btn1, btn2)
    kb.add(btn3, btn4)
    
    btn5 = KeyboardButton(f"{EMOJI['points']} POINTS")
    btn6 = KeyboardButton(f"{EMOJI['star']} BUY VIP")
    btn7 = KeyboardButton(f"{EMOJI['referral']} REFERRAL")
    btn8 = KeyboardButton(f"{EMOJI['account']} ACCOUNT")
    
    kb.add(btn5, btn6)
    kb.add(btn7, btn8)
    
    btn9 = KeyboardButton(f"{EMOJI['info']} STATS")
    btn10 = KeyboardButton(f"{EMOJI['redeem']} REDEEM")
    btn11 = KeyboardButton(f"{EMOJI['fire']} DAILY BONUS")
    
    kb.add(btn9, btn10, btn11)
    
    if uid == ADMIN_ID:
        kb.add(KeyboardButton(f"{EMOJI['admin']} ADMIN PANEL"))
    
    return kb

def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    kb.add("📦 Upload FREE", "💎 Upload VIP")
    kb.add("📱 Upload APPS", "🎓 Upload COURSES")
    kb.add("✏️ Edit Price", "🗑 Delete Folder")
    kb.add("🏆 Generate Codes", "📤 Broadcast")
    kb.add("⭐ Set VIP Msg", "🏠 Set Welcome")
    kb.add("➕ Add Channel", "➖ Remove Channel")
    kb.add("📊 Bot Stats", "🔧 Maintenance Mode")
    kb.add("👥 Users List", "💰 Add Points")
    kb.add("❌ Exit Admin")
    
    return kb

# =========================
# ADMIN PANEL
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

@bot.message_handler(func=lambda m: m.text == f"{EMOJI['admin']} ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    kb = admin_menu()
    bot.send_message(m.from_user.id, "🔧 <b>ADMIN CONTROL PANEL</b>\n\nWelcome back, Admin!", reply_markup=kb, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "👋 Exited Admin Panel", reply_markup=main_menu(m.from_user.id))

# =========================
# UPLOAD SYSTEM
# =========================
def start_upload(uid, cat, cat_name):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("/done", "/cancel")
    
    msg = bot.send_message(uid, f"📤 <b>Upload to {cat_name}</b>\n\nSend files (photos, videos, documents)\nClick /done when finished\nClick /cancel to abort", 
                          reply_markup=kb, parse_mode="HTML")
    bot.register_next_step_handler(msg, lambda m: upload_step(m, cat, uid, [], cat_name))

def upload_step(m, cat, uid, files, cat_name):
    if m.text == "/cancel":
        bot.send_message(uid, "❌ Upload cancelled", reply_markup=admin_menu())
        return
    
    if m.text == "/done":
        if not files:
            bot.send_message(uid, "⚠️ No files uploaded!")
            return
        
        msg = bot.send_message(uid, "📁 Enter folder name:")
        bot.register_next_step_handler(msg, lambda m2: upload_name(m2, cat, files, cat_name))
        return
    
    if m.content_type in ["document", "photo", "video"]:
        files.append({"chat": m.chat.id, "msg": m.message_id, "type": m.content_type})
        bot.send_message(uid, f"✅ Saved [{len(files)}] files")
    
    bot.register_next_step_handler(m, lambda m2: upload_step(m2, cat, uid, files, cat_name))

def upload_name(m, cat, files, cat_name):
    name = m.text
    msg = bot.send_message(m.from_user.id, "💰 Enter price (points) or 0 for free:")
    bot.register_next_step_handler(msg, lambda m2: upload_save(m2, cat, name, files, cat_name))

def upload_save(m, cat, name, files, cat_name):
    try:
        price = int(m.text)
        msg = bot.send_message(m.from_user.id, "📝 Enter description (optional):\nSend /skip to skip")
        bot.register_next_step_handler(msg, lambda m2: upload_desc(m2, cat, name, files, price, cat_name))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price!", reply_markup=admin_menu())

def upload_desc(m, cat, name, files, price, cat_name):
    description = m.text if m.text != "/skip" else ""
    fs.add(cat, name, files, price, description)
    
    bot.send_message(m.from_user.id, 
                    f"✅ <b>Uploaded to {cat_name}</b>\n\n📁 Name: {name}\n💰 Price: {price} pts\n📦 Files: {len(files)}",
                    reply_markup=admin_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE" and is_admin(m.from_user.id))
def up1(m): start_upload(m.from_user.id, "free", "FREE METHODS")

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP" and is_admin(m.from_user.id))
def up2(m): start_upload(m.from_user.id, "vip", "VIP METHODS")

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS" and is_admin(m.from_user.id))
def up3(m): start_upload(m.from_user.id, "apps", "PREMIUM APPS")

@bot.message_handler(func=lambda m: m.text == "🎓 Upload COURSES" and is_admin(m.from_user.id))
def up4(m): start_upload(m.from_user.id, "courses", "PREMIUM COURSES")

# =========================
# DELETE SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def del_start(m):
    kb = InlineKeyboardMarkup()
    for c in ["free", "vip", "apps", "courses"]:
        emoji = EMOJI.get(c, "📁")
        kb.add(InlineKeyboardButton(f"{emoji} {c.upper()}", callback_data=f"del|{c}"))
    bot.send_message(m.from_user.id, "🗑 <b>Select category to delete from</b>", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("del|"))
def del_list(c):
    cat = c.data.split("|")[1]
    data = fs.get(cat)
    
    if not data:
        bot.answer_callback_query(c.id, "No folders found")
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for name in data:
        kb.add(InlineKeyboardButton(f"❌ {name}", callback_data=f"delf|{cat}|{name}"))
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back_admin"))
    
    bot.edit_message_text(f"🗑 Select folder to delete from {cat.upper()}", 
                         c.from_user.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delf|"))
def del_final(c):
    _, cat, name = c.data.split("|")
    fs.delete(cat, name)
    bot.answer_callback_query(c.id, f"Deleted: {name}")
    bot.edit_message_text(f"✅ Deleted: {name}", c.from_user.id, c.message.message_id)

# =========================
# EDIT PRICE
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Price" and is_admin(m.from_user.id))
def edit_start(m):
    msg = bot.send_message(m.from_user.id, "📝 Enter category (free/vip/apps/courses):")
    bot.register_next_step_handler(msg, edit2)

def edit2(m):
    cat = m.text.strip().lower()
    if cat not in ["free", "vip", "apps", "courses"]:
        bot.send_message(m.from_user.id, "❌ Invalid category!")
        return
    
    msg = bot.send_message(m.from_user.id, "📁 Enter folder name:")
    bot.register_next_step_handler(msg, lambda m2: edit3(m2, cat))

def edit3(m, cat):
    name = m.text
    if name not in fs.get(cat):
        bot.send_message(m.from_user.id, "❌ Folder not found!")
        return
    
    msg = bot.send_message(m.from_user.id, "💰 Enter new price (points):")
    bot.register_next_step_handler(msg, lambda m2: edit4(m2, cat, name))

def edit4(m, cat, name):
    try:
        price = int(m.text)
        fs.edit(cat, name, price)
        bot.send_message(m.from_user.id, f"✅ Price updated: {name} → {price} pts", reply_markup=admin_menu())
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price!")

# =========================
# GENERATE CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Generate Codes" and is_admin(m.from_user.id))
def code1(m):
    msg = bot.send_message(m.from_user.id, "💰 Points per code:")
    bot.register_next_step_handler(msg, code2)

def code2(m):
    pts = int(m.text)
    msg = bot.send_message(m.from_user.id, "🔢 How many codes?")
    bot.register_next_step_handler(msg, lambda m2: code3(m2, pts))

def code3(m, pts):
    count = int(m.text)
    msg = bot.send_message(m.from_user.id, "🔄 Usage limit per code (1 = single use):")
    bot.register_next_step_handler(msg, lambda m2: code4(m2, pts, count))

def code4(m, pts, count):
    limit = int(m.text)
    res = codesys.generate(pts, count, limit)
    
    codes_text = "\n".join(res)
    bot.send_message(m.from_user.id, 
                    f"✅ <b>Generated {count} Codes</b>\n\n💰 Value: {pts} pts each\n🔄 Usage limit: {limit}\n\n<code>{codes_text}</code>",
                    parse_mode="HTML")

# =========================
# BROADCAST SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def bc_start(m):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📢 All Users", callback_data="bc|all"),
        InlineKeyboardButton("💎 VIP Users", callback_data="bc|vip"),
        InlineKeyboardButton("🆓 Free Users", callback_data="bc|free")
    )
    bot.send_message(m.from_user.id, "📡 <b>Broadcast Message</b>\n\nSelect target audience:", 
                    reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc|"))
def bc_pick(c):
    t = c.data.split("|")[1]
    msg = bot.send_message(c.from_user.id, "📝 Send your broadcast message (text/photo/video/document):")
    bot.register_next_step_handler(msg, lambda m: bc_send(m, t))

def bc_send(m, target):
    users = load("users.json")
    sent = 0
    failed = 0
    
    status_msg = bot.send_message(ADMIN_ID, f"📤 Broadcasting to {target.upper()} users...")
    
    for uid in users:
        if target == "vip" and not users[uid]["vip"]:
            continue
        if target == "free" and users[uid]["vip"]:
            continue
        
        try:
            if m.content_type == "text":
                bot.send_message(int(uid), m.text, parse_mode="HTML")
            elif m.content_type == "photo":
                bot.send_photo(int(uid), m.photo[-1].file_id, caption=m.caption, parse_mode="HTML")
            elif m.content_type == "video":
                bot.send_video(int(uid), m.video.file_id, caption=m.caption, parse_mode="HTML")
            elif m.content_type == "document":
                bot.send_document(int(uid), m.document.file_id, caption=m.caption, parse_mode="HTML")
            sent += 1
        except:
            failed += 1
        
        time.sleep(0.05)  # Prevent flooding
    
    bot.edit_message_text(f"✅ <b>Broadcast Complete</b>\n\n🎯 Target: {target.upper()}\n✅ Sent: {sent}\n❌ Failed: {failed}",
                         ADMIN_ID, status_msg.message_id, parse_mode="HTML")

# =========================
# SETTINGS
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Set VIP Msg" and is_admin(m.from_user.id))
def set_vip(m):
    msg = bot.send_message(m.from_user.id, "📝 Send VIP message (HTML supported):")
    bot.register_next_step_handler(msg, save_vip)

def save_vip(m):
    cfg = load("config.json")
    cfg["vip_msg"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ VIP message updated!")

@bot.message_handler(func=lambda m: m.text == "🏠 Set Welcome" and is_admin(m.from_user.id))
def set_wel(m):
    msg = bot.send_message(m.from_user.id, "📝 Send welcome message (HTML supported):")
    bot.register_next_step_handler(msg, save_wel)

def save_wel(m):
    cfg = load("config.json")
    cfg["welcome"] = m.text
    save("config.json", cfg)
    bot.send_message(m.from_user.id, "✅ Welcome message updated!")

@bot.message_handler(func=lambda m: m.text == "➕ Add Channel" and is_admin(m.from_user.id))
def add_force(m):
    msg = bot.send_message(m.from_user.id, "📢 Send channel username (with @):")
    bot.register_next_step_handler(msg, save_force)

def save_force(m):
    cfg = load("config.json")
    if m.text not in cfg["force_channels"]:
        cfg["force_channels"].append(m.text)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, f"✅ Added: {m.text}")
    else:
        bot.send_message(m.from_user.id, "⚠️ Channel already exists!")

@bot.message_handler(func=lambda m: m.text == "➖ Remove Channel" and is_admin(m.from_user.id))
def remove_force(m):
    cfg = load("config.json")
    if cfg["force_channels"]:
        channels = "\n".join(cfg["force_channels"])
        msg = bot.send_message(m.from_user.id, f"📢 Current channels:\n{channels}\n\nSend channel to remove:")
        bot.register_next_step_handler(msg, rem_force)
    else:
        bot.send_message(m.from_user.id, "⚠️ No channels added!")

def rem_force(m):
    cfg = load("config.json")
    if m.text in cfg["force_channels"]:
        cfg["force_channels"].remove(m.text)
        save("config.json", cfg)
        bot.send_message(m.from_user.id, f"✅ Removed: {m.text}")
    else:
        bot.send_message(m.from_user.id, "❌ Channel not found!")

@bot.message_handler(func=lambda m: m.text == "🔧 Maintenance Mode" and is_admin(m.from_user.id))
def maintenance_toggle(m):
    cfg = load("config.json")
    cfg["maintenance"] = not cfg.get("maintenance", False)
    save("config.json", cfg)
    
    status = "ON" if cfg["maintenance"] else "OFF"
    bot.send_message(m.from_user.id, f"🔧 Maintenance Mode: {status}")

@bot.message_handler(func=lambda m: m.text == "📊 Bot Stats" and is_admin(m.from_user.id))
def show_stats(m):
    users = load("users.json")
    stats = load("stats.json")
    
    total_users = len(users)
    vip_users = sum(1 for u in users.values() if u.get("vip", False))
    free_users = total_users - vip_users
    
    total_downloads = stats.get("total_downloads", 0)
    
    # Count files in each category
    db = load("db.json")
    files_count = {
        "free": len(db["free"]),
        "vip": len(db["vip"]),
        "apps": len(db["apps"]),
        "courses": len(db["courses"])
    }
    
    stats_text = f"""
📊 <b>BOT STATISTICS</b>

👥 <b>USERS</b>
├ 👤 Total: {total_users}
├ 💎 VIP: {vip_users}
└ 🆓 Free: {free_users}

📁 <b>CONTENT</b>
├ 📂 Free: {files_count['free']}
├ 💎 VIP: {files_count['vip']}
├ 📱 Apps: {files_count['apps']}
└ 🎓 Courses: {files_count['courses']}

📥 <b>ACTIVITY</b>
└ Total Downloads: {total_downloads}
"""
    
    bot.send_message(m.from_user.id, stats_text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👥 Users List" and is_admin(m.from_user.id))
def users_list(m):
    users = load("users.json")
    
    # Create file with users list
    users_text = "👥 USER LIST\n\n"
    for uid, data in users.items():
        status = "VIP" if data.get("vip") else "FREE"
        points = data.get("points", 0)
        downloads = data.get("total_downloads", 0)
        users_text += f"ID: {uid} | {status} | Points: {points} | DL: {downloads}\n"
    
    # Send as file if too long
    if len(users_text) > 4000:
        with open("users_list.txt", "w") as f:
            f.write(users_text)
        with open("users_list.txt", "rb") as f:
            bot.send_document(m.from_user.id, f, caption=f"📊 Total Users: {len(users)}")
        os.remove("users_list.txt")
    else:
        bot.send_message(m.from_user.id, f"<code>{users_text}</code>", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "💰 Add Points" and is_admin(m.from_user.id))
def add_points_start(m):
    msg = bot.send_message(m.from_user.id, "👤 Enter user ID:")
    bot.register_next_step_handler(msg, add_points_user)

def add_points_user(m):
    uid = m.text
    msg = bot.send_message(m.from_user.id, "💰 Enter points to add:")
    bot.register_next_step_handler(msg, lambda m2: add_points_amount(m2, uid))

def add_points_amount(m, uid):
    try:
        points = int(m.text)
        user = User(uid)
        user.add_points(points)
        bot.send_message(m.from_user.id, f"✅ Added {points} points to {uid}\nTotal: {user.points()}")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid input!")

# =========================
# USER COMMANDS
# =========================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    args = m.text.split()
    
    user = User(uid)
    
    # Check if banned
    if user.is_banned():
        bot.send_message(uid, "🚫 <b>You are banned from using this bot!</b>", parse_mode="HTML")
        return
    
    # Referral system
    if len(args) > 1:
        ref = args[1]
        users = load("users.json")
        
        if ref != str(uid) and ref in users and not user.data.get("ref"):
            User(ref).add_points(load("config.json").get("ref_reward", 10))
            user.data["ref"] = ref
            save("users.json", users)
            bot.send_message(uid, f"🎁 <b>Referral Bonus!</b>\n\n+{load('config.json').get('ref_reward', 10)} points added!", parse_mode="HTML")
    
    # Force join check
    if force_block(uid):
        return
    
    cfg = load("config.json")
    
    # Check daily bonus
    claimed, bonus = user.daily_bonus()
    bonus_msg = f"\n\n🎁 <b>Daily Bonus!</b> +{bonus} points" if claimed else ""
    
    bot.send_message(uid, 
                    f"{cfg.get('welcome', 'Welcome!')}{bonus_msg}\n\n✨ Use the menu below to explore!", 
                    reply_markup=main_menu(uid), parse_mode="HTML")

# =========================
# SHOW FOLDERS
# =========================
@bot.message_handler(func=lambda m: m.text in [
    "📂 FREE METHODS", "💎 VIP METHODS", 
    "📱 PREMIUM APPS", "🎓 PREMIUM COURSES"
])
def show_folders(m):
    uid = m.from_user.id
    
    if force_block(uid):
        return
    
    user = User(uid)
    if user.is_banned():
        bot.send_message(uid, "🚫 You are banned!", parse_mode="HTML")
        return
    
    mapping = {
        "📂 FREE METHODS": ("free", EMOJI['free']),
        "💎 VIP METHODS": ("vip", EMOJI['vip']),
        "📱 PREMIUM APPS": ("apps", EMOJI['apps']),
        "🎓 PREMIUM COURSES": ("courses", EMOJI['courses'])
    }
    
    cat, emoji = mapping[m.text]
    
    # Check VIP access
    if cat == "vip" and not user.is_vip():
        bot.send_message(uid, load("config.json")["vip_msg"], parse_mode="HTML")
        return
    
    folders = fs.get(cat)
    
    if not folders:
        bot.send_message(uid, f"{emoji} <b>{m.text}</b>\n\n📭 No content available yet!", parse_mode="HTML")
        return
    
    bot.send_message(uid, f"{emoji} <b>{m.text}</b>\n\nSelect a folder to view content:", 
                    reply_markup=get_kb(cat, 0, show_stats=(uid==ADMIN_ID)), parse_mode="HTML")

# =========================
# PAGINATION
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("page|"))
def page_handler(c):
    _, cat, page = c.data.split("|")
    show_stats = (c.from_user.id == ADMIN_ID)
    
    try:
        bot.edit_message_reply_markup(
            c.from_user.id,
            c.message.message_id,
            reply_markup=get_kb(cat, int(page), show_stats)
        )
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("stats|"))
def stats_toggle(c):
    _, cat, page = c.data.split("|")
    show_stats = True
    
    try:
        bot.edit_message_reply_markup(
            c.from_user.id,
            c.message.message_id,
            reply_markup=get_kb(cat, int(page), show_stats)
        )
    except:
        pass

# =========================
# OPEN FOLDER
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open|"))
def open_folder(c):
    uid = c.from_user.id
    user = User(uid)
    
    if user.is_banned():
        bot.answer_callback_query(c.id, "🚫 You are banned!", show_alert=True)
        return
    
    _, cat, name = c.data.split("|")
    folder = fs.get(cat).get(name)
    
    if not folder:
        bot.answer_callback_query(c.id, "❌ Folder not found")
        return
    
    # Check VIP access
    if cat == "vip" and not user.is_vip():
        bot.answer_callback_query(c.id, "💎 VIP only content!", show_alert=True)
        bot.send_message(uid, load("config.json")["vip_msg"], parse_mode="HTML")
        return
    
    price = folder.get("price", 0)
    
    # Check points for non-VIP
    if not user.is_vip() and price > 0:
        if user.points() < price:
            bot.answer_callback_query(c.id, f"❌ Need {price} points! You have {user.points()}", show_alert=True)
            return
        
        user.remove_points(price)
        bot.answer_callback_query(c.id, f"✅ -{price} points")
    
    # Send folder info
    description = folder.get("description", "")
    if description:
        bot.send_message(uid, f"📁 <b>{name}</b>\n\n{description}", parse_mode="HTML")
    
    # Send files
    bot.answer_callback_query(c.id, "📤 Sending...")
    
    count = 0
    for f in folder["files"]:
        try:
            bot.copy_message(uid, f["chat"], f["msg"])
            count += 1
            time.sleep(0.2)
        except:
            continue
    
    # Update stats
    user.add_download()
    fs.increment_downloads(cat, name)
    
    bot.send_message(uid, f"✅ <b>Sent {count} files</b>\n\n📁 Folder: {name}", parse_mode="HTML")

# =========================
# USER FEATURES
# =========================
@bot.message_handler(func=lambda m: True)
def user_commands(m):
    uid = m.from_user.id
    user = User(uid)
    
    if user.is_banned():
        bot.send_message(uid, "🚫 You are banned!", parse_mode="HTML")
        return
    
    if force_block(uid):
        return
    
    t = m.text
    
    if t == "💰 POINTS":
        bot.send_message(uid, 
                        f"<b>💰 YOUR POINTS</b>\n\n"
                        f"Total Points: <code>{user.points()}</code>\n\n"
                        f"✨ <b>How to earn:</b>\n"
                        f"• Daily bonus: +{load('config.json').get('daily_bonus', 5)} pts\n"
                        f"• Referral: +{load('config.json').get('ref_reward', 10)} pts\n"
                        f"• Redeem codes\n"
                        f"• Special events",
                        parse_mode="HTML")
    
    elif t == "⭐ BUY VIP":
        cfg = load("config.json")
        bot.send_message(uid, cfg["vip_msg"], parse_mode="HTML")
    
    elif t == "🎁 REFERRAL":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid,
                        f"<b>🎁 REFERRAL PROGRAM</b>\n\n"
                        f"Share your link and earn points!\n\n"
                        f"<code>{link}</code>\n\n"
                        f"✨ <b>Reward:</b> +{load('config.json').get('ref_reward', 10)} points per referral",
                        parse_mode="HTML")
    
    elif t == "👤 ACCOUNT":
        status = "💎 <b>VIP MEMBER</b>" if user.is_vip() else "🆓 <b>FREE USER</b>"
        vip_expiry = user.data.get("vip_expiry", "N/A")
        
        bot.send_message(uid,
                        f"<b>👤 ACCOUNT INFO</b>\n\n"
                        f"Status: {status}\n"
                        f"Points: <code>{user.points()}</code>\n"
                        f"Downloads: <code>{user.data.get('total_downloads', 0)}</code>\n"
                        f"Join Date: <code>{user.data.get('join_date', 'N/A')}</code>\n"
                        f"VIP Expiry: <code>{vip_expiry}</code>",
                        parse_mode="HTML")
    
    elif t == "📊 STATS":
        db = load("db.json")
        total_files = sum(len(db[cat]) for cat in db)
        total_downloads = load("stats.json").get("total_downloads", 0)
        
        bot.send_message(uid,
                        f"<b>📊 BOT STATISTICS</b>\n\n"
                        f"📁 Total Folders: <code>{total_files}</code>\n"
                        f"📥 Total Downloads: <code>{total_downloads}</code>\n"
                        f"👥 Total Users: <code>{len(load('users.json'))}</code>\n\n"
                        f"🤖 Bot Version: {load('config.json').get('bot_version', '1.0')}",
                        parse_mode="HTML")
    
    elif t == "🏆 REDEEM":
        msg = bot.send_message(uid, "🎫 <b>Enter your redeem code:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, redeem_code)
    
    elif t == "🔥 DAILY BONUS":
        claimed, bonus = user.daily_bonus()
        
        if claimed:
            bot.send_message(uid, 
                            f"✅ <b>Daily Bonus Claimed!</b>\n\n"
                            f"+{bonus} points\n"
                            f"Total: <code>{user.points()}</code>\n\n"
                            f"Come back tomorrow for more!",
                            parse_mode="HTML")
        else:
            bot.send_message(uid,
                            f"⏰ <b>Already Claimed!</b>\n\n"
                            f"You've already claimed today's bonus.\n"
                            f"Come back tomorrow!",
                            parse_mode="HTML")
    
    elif t == f"{EMOJI['admin']} ADMIN PANEL" and uid == ADMIN_ID:
        admin_panel(m)
    
    elif t not in ["📂 FREE METHODS", "💎 VIP METHODS", "📱 PREMIUM APPS", "🎓 PREMIUM COURSES"]:
        bot.send_message(uid, "❓ <b>Unknown Command</b>\n\nPlease use the menu buttons below.", 
                        reply_markup=main_menu(uid), parse_mode="HTML")

def redeem_code(m):
    uid = m.from_user.id
    user = User(uid)
    
    success, pts, msg = codesys.redeem(m.text.strip().upper(), user)
    
    if success:
        bot.send_message(uid, f"✅ <b>Code Redeemed!</b>\n\n+{pts} points\nTotal: <code>{user.points()}</code>", parse_mode="HTML")
    else:
        bot.send_message(uid, f"❌ <b>Invalid Code</b>\n\n{msg}", parse_mode="HTML")

# =========================
# FORCE JOIN RECHECK
# =========================
@bot.callback_query_handler(func=lambda c: c.data == "recheck")
def recheck(c):
    uid = c.from_user.id
    
    if not force_block(uid):
        try:
            bot.edit_message_text("✅ <b>Access Granted!</b>\n\nWelcome to ZEDOX BOT!", 
                                 uid, c.message.message_id, parse_mode="HTML")
        except:
            pass
        
        bot.send_message(uid, "🎉 Welcome! Use the menu below.", reply_markup=main_menu(uid), parse_mode="HTML")
    else:
        bot.answer_callback_query(c.id, "❌ Please join all channels first", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "back_admin")
def back_admin(c):
    if c.from_user.id == ADMIN_ID:
        admin_panel(c.message)

# =========================
# ERROR HANDLER
# =========================
@bot.message_handler(content_types=['text','photo','video','document'])
def fallback(m):
    uid = m.from_user.id
    
    if force_block(uid):
        return
    
    # Ignore if it's a known command
    known = ["📂 FREE METHODS", "💎 VIP METHODS", "📱 PREMIUM APPS", "🎓 PREMIUM COURSES",
             "💰 POINTS", "⭐ BUY VIP", "🎁 REFERRAL", "👤 ACCOUNT", "📊 STATS", 
             "🏆 REDEEM", "🔥 DAILY BONUS", "⚙️ ADMIN PANEL"]
    
    if m.text and m.text not in known:
        bot.send_message(uid, "❓ <b>Please use the menu buttons</b>\n\nClick /start to refresh menu.", 
                        reply_markup=main_menu(uid), parse_mode="HTML")

# =========================
# BOT RUNNER
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT RUNNING...")
            print(f"✅ Bot: @{bot.get_me().username}")
            print(f"✅ Admin: {ADMIN_ID}")
            print(f"✅ Version: {load('config.json').get('bot_version', '3.0')}")
            print("-" * 40)
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Keep alive
    while True:
        time.sleep(1)
