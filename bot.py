# =========================
# ZEDOX BOT - COMPLETE
# Fully Functional with Pagination, Fixed Delete/Edit, Force Join
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
            "vip_msg": "💎 *Buy VIP to unlock this!*\n\nContact @admin to get VIP access.",
            "welcome": "🔥 *Welcome to ZEDOX BOT*\n\nExplore our premium content and earn points!",
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
# FORCE JOIN SYSTEM (COMPLETELY FIXED)
# =========================
class ForceJoin:
    def __init__(self):
        self.config = load("config.json")

    def check(self, uid):
        if not self.config["force_channels"]:
            return True
            
        for ch in self.config["force_channels"]:
            try:
                # Clean channel username
                channel = ch.strip()
                if not channel.startswith('@'):
                    channel = '@' + channel
                
                # Get chat member status
                member = bot.get_chat_member(channel, uid)
                if member.status in ["left", "kicked", "restricted"]:
                    return False
            except Exception as e:
                print(f"Force join check error for {channel}: {e}")
                return False
        return True

    def join_buttons(self):
        kb = InlineKeyboardMarkup(row_width=1)
        for ch in self.config["force_channels"]:
            channel = ch.strip()
            if not channel.startswith('@'):
                channel = '@' + channel
            kb.add(InlineKeyboardButton(f"📢 JOIN {channel}", url=f"https://t.me/{channel.replace('@','')}"))
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
                self.users[ref]["points"] += self.config.get("ref_reward",5)
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
# PAGINATION SYSTEM
# =========================
class Pagination:
    def __init__(self, items, items_per_page=10):
        self.items = items
        self.items_per_page = items_per_page
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page if items else 1
    
    def get_page(self, page):
        if page < 1 or page > self.total_pages:
            return []
        start = (page - 1) * self.items_per_page
        end = start + self.items_per_page
        return self.items[start:end]
    
    def get_buttons(self, page, callback_prefix):
        buttons = []
        if self.total_pages > 1:
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"{callback_prefix}|prev|{page}"))
            nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{self.total_pages}", callback_data="none"))
            if page < self.total_pages:
                nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"{callback_prefix}|next|{page}"))
            buttons.append(nav_buttons)
        return buttons

# =========================
# CHECK ADMIN
# =========================
def is_admin(uid):
    return uid == ADMIN_ID

# =========================
# ADMIN PANEL HANDLER
# =========================
@bot.message_handler(func=lambda m: m.text == "⚙️ ADMIN PANEL" and is_admin(m.from_user.id))
def admin_panel(m):
    uid = m.from_user.id
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
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
    for row in buttons:
        kb.row(*row)
    bot.send_message(uid, "🛠️ *Admin Panel*\nSelect an option below:", reply_markup=kb)

# =========================
# EXIT ADMIN PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "❌ Exit Admin" and is_admin(m.from_user.id))
def exit_admin(m):
    bot.send_message(m.from_user.id, "✅ Exited Admin Panel.", reply_markup=main_menu(m.from_user.id))

# =========================
# ADD VIP
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add VIP" and is_admin(m.from_user.id))
def add_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the Chat ID of the user to add VIP:")
    bot.register_next_step_handler(msg, add_vip_step2)

def add_vip_step2(m):
    try:
        uid = int(m.text)
        user = User(uid)
        user.make_vip()
        bot.send_message(m.from_user.id, f"✅ User `{uid}` is now VIP.")
        try:
            bot.send_message(uid, "🎉 Congratulations! You have been upgraded to VIP by admin!")
        except:
            pass
    except:
        bot.send_message(m.from_user.id, "❌ Invalid Chat ID.")

# =========================
# REMOVE VIP
# =========================
@bot.message_handler(func=lambda m: m.text == "➖ Remove VIP" and is_admin(m.from_user.id))
def remove_vip_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the Chat ID of the user to remove VIP:")
    bot.register_next_step_handler(msg, remove_vip_step2)

def remove_vip_step2(m):
    try:
        uid = int(m.text)
        user = User(uid)
        user.remove_vip()
        bot.send_message(m.from_user.id, f"✅ VIP removed for user `{uid}`.")
        try:
            bot.send_message(uid, "⚠️ Your VIP status has been removed by admin.")
        except:
            pass
    except:
        bot.send_message(m.from_user.id, "❌ Invalid Chat ID.")

# =========================
# GIVE POINTS
# =========================
@bot.message_handler(func=lambda m: m.text == "💰 Give Points" and is_admin(m.from_user.id))
def give_points_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the Chat ID of the user to give points:")
    bot.register_next_step_handler(msg, give_points_step2)

def give_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "✏️ Send the amount of points to add:")
        bot.register_next_step_handler(msg, lambda m2: give_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid Chat ID.")

def give_points_step3(m, uid):
    try:
        pts = int(m.text)
        user = User(uid)
        user.add_points(pts)
        bot.send_message(m.from_user.id, f"✅ Added {pts} points to user `{uid}`.")
        try:
            bot.send_message(uid, f"💰 You received +{pts} points from admin!\nTotal points: {user.points()}")
        except:
            pass
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

# =========================
# SET POINTS
# =========================
@bot.message_handler(func=lambda m: m.text == "📝 Set Points" and is_admin(m.from_user.id))
def set_points_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the Chat ID of the user to set points:")
    bot.register_next_step_handler(msg, set_points_step2)

def set_points_step2(m):
    try:
        uid = int(m.text)
        msg = bot.send_message(m.from_user.id, "✏️ Send the new points amount:")
        bot.register_next_step_handler(msg, lambda m2: set_points_step3(m2, uid))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid Chat ID.")

def set_points_step3(m, uid):
    try:
        pts = int(m.text)
        user = User(uid)
        user.set_points(pts)
        bot.send_message(m.from_user.id, f"✅ Set points of user `{uid}` to {pts}.")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

# =========================
# SET VIP MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text == "⭐ Set VIP Message" and is_admin(m.from_user.id))
def set_vip_msg_step(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the new VIP join message:")
    bot.register_next_step_handler(msg, set_vip_msg_step2)

def set_vip_msg_step2(m):
    config = load("config.json")
    config["vip_msg"] = m.text
    save("config.json", config)
    bot.send_message(m.from_user.id, "✅ VIP message updated.")

# =========================
# SET WELCOME MESSAGE
# =========================
@bot.message_handler(func=lambda m: m.text == "🏠 Set Welcome Message" and is_admin(m.from_user.id))
def set_welcome_step(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the new welcome message:")
    bot.register_next_step_handler(msg, set_welcome_step2)

def set_welcome_step2(m):
    config = load("config.json")
    config["welcome"] = m.text
    save("config.json", config)
    bot.send_message(m.from_user.id, "✅ Welcome message updated.")

# =========================
# FORCE JOIN CHANNEL MANAGEMENT
# =========================
@bot.message_handler(func=lambda m: m.text == "➕ Add Force Join" and is_admin(m.from_user.id))
def add_force_channel_step(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send the channel username to force join (with @):\nExample: @channelname")
    bot.register_next_step_handler(msg, add_force_channel_step2)

def add_force_channel_step2(m):
    config = load("config.json")
    channel = m.text.strip()
    if channel not in config["force_channels"]:
        config["force_channels"].append(channel)
        save("config.json", config)
        bot.send_message(m.from_user.id, f"✅ Added force join channel `{channel}`.")
    else:
        bot.send_message(m.from_user.id, "❌ Channel already in force join list.")

@bot.message_handler(func=lambda m: m.text == "➖ Remove Force Join" and is_admin(m.from_user.id))
def remove_force_channel_step(m):
    config = load("config.json")
    if not config["force_channels"]:
        bot.send_message(m.from_user.id, "❌ No force join channels configured.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in config["force_channels"]:
        kb.add(InlineKeyboardButton(f"❌ {ch}", callback_data=f"remove_fc|{ch}"))
    kb.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel_remove"))
    bot.send_message(m.from_user.id, "Select channel to remove:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("remove_fc") and is_admin(c.from_user.id))
def remove_force_channel_callback(c):
    channel = c.data.split("|")[1]
    config = load("config.json")
    if channel in config["force_channels"]:
        config["force_channels"].remove(channel)
        save("config.json", config)
        bot.answer_callback_query(c.id, f"Removed {channel}")
        bot.edit_message_text(f"✅ Removed force join channel `{channel}`.", c.from_user.id, c.message.message_id)
    else:
        bot.answer_callback_query(c.id, "Channel not found")

# =========================
# DELETE FOLDER (COMPLETELY FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "🗑 Delete Folder" and is_admin(m.from_user.id))
def delete_folder_list(m):
    all_folders = fs.get_all_folders()
    if not all_folders:
        bot.send_message(m.from_user.id, "❌ No folders available to delete.")
        return
    
    pagination = Pagination(all_folders, 10)
    show_delete_folders(m.from_user.id, pagination, 1)

def show_delete_folders(uid, pagination, page):
    folders = pagination.get_page(page)
    if not folders:
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for cat, folder in folders:
        kb.add(InlineKeyboardButton(f"🗑 {cat.upper()}: {folder}", callback_data=f"del_confirm|{cat}|{folder}"))
    
    nav_buttons = pagination.get_buttons(page, "del_page")
    for row in nav_buttons:
        kb.row(*row)
    
    kb.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel_delete"))
    bot.send_message(uid, f"📂 Select folder to delete (Page {page}/{pagination.total_pages}):", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_page") and is_admin(c.from_user.id))
def delete_folder_page(c):
    _, action, current_page = c.data.split("|")
    page = int(current_page)
    if action == "next":
        page += 1
    else:
        page -= 1
    
    all_folders = fs.get_all_folders()
    pagination = Pagination(all_folders, 10)
    show_delete_folders(c.from_user.id, pagination, page)
    bot.delete_message(c.from_user.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_confirm") and is_admin(c.from_user.id))
def delete_folder_confirm(c):
    _, cat, folder = c.data.split("|")
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Yes", callback_data=f"del_execute|{cat}|{folder}"))
    kb.add(InlineKeyboardButton("❌ No", callback_data="cancel_delete"))
    bot.edit_message_text(f"⚠️ Delete folder '{folder}' from {cat.upper()}?\nThis action cannot be undone!", 
                         c.from_user.id, c.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_execute") and is_admin(c.from_user.id))
def delete_folder_execute(c):
    _, cat, folder = c.data.split("|")
    if fs.delete_folder(cat, folder):
        bot.answer_callback_query(c.id, f"✅ Deleted {folder}")
        bot.edit_message_text(f"✅ Folder '{folder}' deleted successfully!", c.from_user.id, c.message.message_id)
    else:
        bot.answer_callback_query(c.id, "❌ Failed to delete")
        bot.edit_message_text(f"❌ Failed to delete '{folder}'.", c.from_user.id, c.message.message_id)

# =========================
# EDIT FOLDER PRICE (COMPLETELY FIXED)
# =========================
@bot.message_handler(func=lambda m: m.text == "✏️ Edit Folder Price" and is_admin(m.from_user.id))
def edit_price_list(m):
    all_folders = fs.get_all_folders()
    if not all_folders:
        bot.send_message(m.from_user.id, "❌ No folders available to edit.")
        return
    
    pagination = Pagination(all_folders, 10)
    show_edit_folders(m.from_user.id, pagination, 1)

def show_edit_folders(uid, pagination, page):
    folders = pagination.get_page(page)
    if not folders:
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for cat, folder in folders:
        price = fs.db[cat][folder]["price"]
        kb.add(InlineKeyboardButton(f"💰 {cat.upper()}: {folder} [{price} pts]", callback_data=f"edit_select|{cat}|{folder}"))
    
    nav_buttons = pagination.get_buttons(page, "edit_page")
    for row in nav_buttons:
        kb.row(*row)
    
    kb.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel_edit"))
    bot.send_message(uid, f"📂 Select folder to edit price (Page {page}/{pagination.total_pages}):", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_page") and is_admin(c.from_user.id))
def edit_folder_page(c):
    _, action, current_page = c.data.split("|")
    page = int(current_page)
    if action == "next":
        page += 1
    else:
        page -= 1
    
    all_folders = fs.get_all_folders()
    pagination = Pagination(all_folders, 10)
    show_edit_folders(c.from_user.id, pagination, page)
    bot.delete_message(c.from_user.id, c.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_select") and is_admin(c.from_user.id))
def edit_price_input(c):
    _, cat, folder = c.data.split("|")
    msg = bot.send_message(c.from_user.id, f"✏️ Send new price for '{folder}' (0 for free):\nCurrent price: {fs.db[cat][folder]['price']} points")
    bot.register_next_step_handler(msg, lambda m: edit_price_step2(m, cat, folder, c.message.message_id))

def edit_price_step2(m, cat, folder, msg_id):
    try:
        price = int(m.text)
        if fs.edit_price(cat, folder, price):
            bot.send_message(m.from_user.id, f"✅ Price updated to {price} points for '{folder}'.")
            try:
                bot.delete_message(m.from_user.id, msg_id)
            except:
                pass
        else:
            bot.send_message(m.from_user.id, "❌ Failed to update price.")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price. Must be a number.")

# =========================
# STATS PANEL
# =========================
@bot.message_handler(func=lambda m: m.text == "🧮 Stats" and is_admin(m.from_user.id))
def stats_panel(m):
    users = load("users.json")
    total = len(users)
    vip_count = sum(1 for u in users.values() if u.get("vip", False))
    free_count = total - vip_count
    
    db = load("db.json")
    free_folders = len(db["free"])
    vip_folders = len(db["vip"])
    apps_folders = len(db["apps"])
    courses_folders = len(db["courses"])
    
    msg = f"📊 *ZEDOX BOT Stats*\n\n"
    msg += f"👥 Total Users: {total}\n"
    msg += f"💎 VIP Users: {vip_count}\n"
    msg += f"🆓 Free Users: {free_count}\n\n"
    msg += f"📁 Content Stats:\n"
    msg += f"📂 Free Methods: {free_folders}\n"
    msg += f"💎 VIP Methods: {vip_folders}\n"
    msg += f"📱 Premium Apps: {apps_folders}\n"
    msg += f"📚 Premium Courses: {courses_folders}"
    
    bot.send_message(m.from_user.id, msg)

# =========================
# GENERATE CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Generate Codes" and is_admin(m.from_user.id))
def generate_codes_step1(m):
    msg = bot.send_message(m.from_user.id, "✏️ Send points value for the codes:")
    bot.register_next_step_handler(msg, generate_codes_step2)

def generate_codes_step2(m):
    try:
        points = int(m.text)
        msg = bot.send_message(m.from_user.id, "✏️ Send number of codes to generate (max 50):")
        bot.register_next_step_handler(msg, lambda m2: generate_codes_step3(m2, points))
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

def generate_codes_step3(m, points):
    try:
        count = min(int(m.text), 50)
        codes = codesys.generate(points, count)
        codes_text = "\n".join(codes)
        bot.send_message(m.from_user.id, f"✅ Generated {count} codes with {points} points each:\n\n`{codes_text}`", parse_mode="Markdown")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid number.")

# =========================
# UPLOAD FILES SYSTEM
# =========================
def upload_files(category, uid):
    msg = bot.send_message(uid, f"📤 Send file(s) to upload for category `{category}`.\nSend multiple files one by one.\nWhen done, send /done.")
    bot.register_next_step_handler(msg, lambda m: upload_files_step(m, category, uid, []))

def upload_files_step(m, category, uid, files):
    if m.text and m.text == "/done":
        if not files:
            bot.send_message(uid, "❌ No files uploaded. Operation cancelled.")
            return
        msg2 = bot.send_message(uid, "✏️ Send the folder name for these files:")
        bot.register_next_step_handler(msg2, lambda m2: upload_folder_finalize(m2, category, files))
        return

    if m.content_type in ["document", "photo", "video"]:
        f = {"chat": m.chat.id, "msg": m.message_id, "type": m.content_type}
        files.append(f)
        bot.send_message(uid, f"✅ File saved. ({len(files)} file(s) so far)\nSend next file or /done when finished.")
    else:
        bot.send_message(uid, "❌ Unsupported type. Send document, photo, or video.")

    bot.register_next_step_handler(m, lambda m2: upload_files_step(m2, category, uid, files))

def upload_folder_finalize(m, category, files):
    folder_name = m.text
    msg_price = bot.send_message(m.from_user.id, "✏️ Send price for this folder (0 for free):")
    bot.register_next_step_handler(msg_price, lambda m2: finalize_folder_price(m2, category, folder_name, files))

def finalize_folder_price(m, category, folder_name, files):
    try:
        price = int(m.text)
        fs.add_folder(category, folder_name, files, price)
        bot.send_message(m.from_user.id, f"✅ Folder `{folder_name}` added to `{category}` with {len(files)} file(s) and price {price} pts.")
    except:
        bot.send_message(m.from_user.id, "❌ Invalid price. Operation cancelled.")

# =========================
# UPLOAD HANDLERS
# =========================
@bot.message_handler(func=lambda m: m.text == "📦 Upload FREE" and is_admin(m.from_user.id))
def upload_free_handler(m):
    upload_files("free", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "💎 Upload VIP" and is_admin(m.from_user.id))
def upload_vip_handler(m):
    upload_files("vip", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "📱 Upload APPS" and is_admin(m.from_user.id))
def upload_apps_handler(m):
    upload_files("apps", m.from_user.id)

@bot.message_handler(func=lambda m: m.text == "📚 Upload Courses" and is_admin(m.from_user.id))
def upload_courses_handler(m):
    upload_files("courses", m.from_user.id)

# =========================
# REDEEM CODES
# =========================
@bot.message_handler(func=lambda m: m.text == "🏆 Redeem")
def redeem_handler(m):
    if not force.check(m.from_user.id):
        bot.send_message(m.from_user.id, "🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return
    msg = bot.send_message(m.from_user.id, "✏️ Send your code to redeem:")
    bot.register_next_step_handler(msg, redeem_step)

def redeem_step(m):
    user = User(m.from_user.id)
    success, pts = codesys.redeem(m.text.strip(), user)
    if success:
        bot.send_message(m.from_user.id, f"✅ Redeemed! You received {pts} points.\n💰 Total points: {user.points()}")
    else:
        bot.send_message(m.from_user.id, "❌ Invalid or already used code.")

# =========================
# BROADCAST SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and is_admin(m.from_user.id))
def broadcast_step1(m):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👥 All Users", callback_data="broadcast_all"),
        InlineKeyboardButton("💎 VIP Users", callback_data="broadcast_vip"),
        InlineKeyboardButton("🆓 Free Users", callback_data="broadcast_free")
    )
    bot.send_message(m.from_user.id, "📢 Select target audience for broadcast:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("broadcast_") and is_admin(c.from_user.id))
def broadcast_callback(c):
    target = c.data.split("_")[1]
    bot.answer_callback_query(c.id)
    msg = bot.send_message(c.from_user.id, "✏️ Send the broadcast message (text/photo/video/document):")
    bot.register_next_step_handler(msg, lambda m: broadcast_send(m, target))

def broadcast_send(m, target):
    users = load("users.json")
    sent_count = 0
    failed_count = 0
    
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
            failed_count += 1
            continue
    
    bot.send_message(ADMIN_ID, f"📢 Broadcast completed!\n✅ Sent: {sent_count}\n❌ Failed: {failed_count}")

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
    
    custom = load("db.json")["custom"]
    for name in custom:
        kb.row(name)
    
    if is_admin(uid):
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
    
    if not force.check(uid):
        bot.send_message(uid, "🚫 *ACCESS DENIED!*\n\nPlease join all required channels to use this bot:", 
                        parse_mode="Markdown", reply_markup=force.join_buttons())
        return
    
    config = load("config.json")
    bot.send_message(uid, config["welcome"], reply_markup=main_menu(uid))

# =========================
# VERIFY JOIN CALLBACK
# =========================
@bot.callback_query_handler(func=lambda c: c.data == "verify_join")
def verify_join(c):
    uid = c.from_user.id
    if force.check(uid):
        bot.edit_message_text("✅ *Access Granted!* ✅\n\nYou can now use the bot.", 
                             uid, c.message.message_id, parse_mode="Markdown")
        config = load("config.json")
        bot.send_message(uid, config["welcome"], reply_markup=main_menu(uid))
    else:
        bot.answer_callback_query(c.id, "❌ You haven't joined all channels yet!")
        bot.edit_message_text("🚫 *ACCESS DENIED!*\n\nPlease join all required channels:", 
                             uid, c.message.message_id, parse_mode="Markdown", 
                             reply_markup=force.join_buttons())

# =========================
# FOLDER BUTTONS WITH PAGINATION
# =========================
@bot.message_handler(func=lambda m: m.text in ["📂 FREE METHODS", "💎 VIP METHODS", "📦 PREMIUM APPS", "📚 PREMIUM COURSES"])
def folder_buttons(m):
    uid = m.from_user.id
    
    if not force.check(uid):
        bot.send_message(uid, "🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return
    
    text = m.text
    cat_map = {
        "📂 FREE METHODS": "free",
        "💎 VIP METHODS": "vip",
        "📦 PREMIUM APPS": "apps",
        "📚 PREMIUM COURSES": "courses"
    }
    cat = cat_map[text]
    
    folders = list(fs.get_category(cat).items())
    if not folders:
        bot.send_message(uid, f"📂 No {cat.upper()} folders available yet.")
        return
    
    pagination = Pagination(folders, 10)
    show_folders_page(uid, cat, pagination, 1)

def show_folders_page(uid, cat, pagination, page):
    folders = pagination.get_page(page)
    if not folders:
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for name, info in folders:
        price = info.get("price", 0)
        display_name = f"{name} [{price} pts]" if price > 0 else name
        kb.add(InlineKeyboardButton(display_name, callback_data=f"open|{cat}|{name}"))
    
    nav_buttons = pagination.get_buttons(page, f"folder_{cat}")
    for row in nav_buttons:
        kb.row(*row)
    
    bot.send_message(uid, f"📂 *{cat.upper()} METHODS* (Page {page}/{pagination.total_pages})\nSelect a folder:", 
                    parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("folder_") and not c.data.startswith("folder_open"))
def folder_page_callback(c):
    _, cat, action, current_page = c.data.split("|")
    page = int(current_page)
    if action == "next":
        page += 1
    else:
        page -= 1
    
    folders = list(fs.get_category(cat).items())
    pagination = Pagination(folders, 10)
    show_folders_page(c.from_user.id, cat, pagination, page)
    try:
        bot.delete_message(c.from_user.id, c.message.message_id)
    except:
        pass

# =========================
# OPEN FOLDER CALLBACK
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("open"))
def open_callback(c):
    _, cat, name = c.data.split("|")
    user = User(c.from_user.id)
    
    if not force.check(c.from_user.id):
        bot.answer_callback_query(c.id, "❌ You haven't joined all channels!")
        bot.send_message(c.from_user.id, "🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return
    
    folder = fs.get_category(cat).get(name)
    if not folder:
        bot.answer_callback_query(c.id, "❌ Folder not found")
        return
    
    # VIP check for VIP category
    if cat == "vip" and not user.is_vip():
        bot.answer_callback_query(c.id, "💎 VIP only content!")
        bot.send_message(c.from_user.id, load("config.json")["vip_msg"])
        return
    
    # Price check
    if not user.is_vip() and folder.get("price", 0) > 0:
        if user.points() < folder["price"]:
            bot.answer_callback_query(c.id, f"❌ Need {folder['price']} points!")
            bot.send_message(c.from_user.id, f"❌ You need {folder['price']} points to access this folder.\n💰 Your points: {user.points()}")
            return
        user.add_points(-folder["price"])
        bot.send_message(c.from_user.id, f"💰 Used {folder['price']} points. Remaining: {user.points()}")
    
    # Send all files
    sent_count = 0
    for f in folder["files"]:
        try:
            if f["type"] == "photo":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            elif f["type"] == "video":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            elif f["type"] == "document":
                bot.copy_message(c.from_user.id, f["chat"], f["msg"])
            sent_count += 1
        except Exception as e:
            print(f"Error sending file: {e}")
            continue
    
    if sent_count > 0:
        bot.send_message(c.from_user.id, f"✅ Sent {sent_count} file(s) from `{name}`")

# =========================
# CANCEL CALLBACKS
# =========================
@bot.callback_query_handler(func=lambda c: c.data in ["cancel_delete", "cancel_edit", "cancel_remove"])
def cancel_callbacks(c):
    bot.answer_callback_query(c.id, "Cancelled")
    bot.edit_message_text("✅ Operation cancelled.", c.from_user.id, c.message.message_id)
    admin_panel(c.message)

@bot.callback_query_handler(func=lambda c: c.data == "none")
def none_callback(c):
    bot.answer_callback_query(c.id)

# =========================
# GENERAL HANDLER
# =========================
@bot.message_handler(func=lambda m: True)
def general_handler(m):
    uid = m.from_user.id
    
    if not force.check(uid):
        bot.send_message(uid, "🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return
    
    user = User(uid)
    text = m.text.lower()
    
    if text in ["💰 points", "points"]:
        bot.send_message(uid, f"💰 *Your Points:* `{user.points()}`", parse_mode="Markdown")
    
    elif text in ["⭐ buy vip", "buy vip"]:
        config = load("config.json")
        bot.send_message(uid, config["vip_msg"], parse_mode="Markdown")
    
    elif text in ["🎁 referral", "referral"]:
        ref_link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(uid, f"🎁 *Your Referral Link*\n\nShare this link with friends:\n`{ref_link}`\n\nYou get +{load('config.json')['ref_reward']} points for each referral!", 
                        parse_mode="Markdown")
    
    elif text in ["👤 account", "account"]:
        status = "💎 VIP" if user.is_vip() else "🆓 FREE"
        msg = f"👤 *Account Information*\n\n"
        msg += f"📊 Status: {status}\n"
        msg += f"💰 Points: `{user.points()}`\n"
        if user.ref():
            msg += f"🔗 Referred by: `{user.ref()}`"
        bot.send_message(uid, msg, parse_mode="Markdown")
    
    elif text in ["🆔 chat id", "chat id"]:
        bot.send_message(uid, f"🆔 *Your Chat ID:*\n`{uid}`", parse_mode="Markdown")

# =========================
# FALLBACK HANDLER
# =========================
@bot.message_handler(func=lambda m: True, content_types=['text', 'document', 'photo', 'video'])
def fallback(m):
    if not force.check(m.from_user.id):
        bot.send_message(m.from_user.id, "🚫 ACCESS DENIED! Join all channels", reply_markup=force.join_buttons())
        return
    safe_send(m.from_user.id, "❌ Command not recognized.\nUse the main menu buttons.", reply_markup=main_menu(m.from_user.id))

def safe_send(uid, text=None, reply_markup=None):
    try:
        if text:
            bot.send_message(uid, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error sending to {uid}: {e}")

# =========================
# POLLING WITH AUTO-RESTART
# =========================
def run_bot():
    while True:
        try:
            print("🚀 ZEDOX BOT started successfully!")
            print(f"🤖 Bot Username: @{bot.get_me().username}")
            print(f"👑 Admin ID: {ADMIN_ID}")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            time.sleep(5)

# =========================
# START BOT
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Keep main thread alive
    while True:
        time.sleep(1)
