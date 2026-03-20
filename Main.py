import os
import json
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Environment Variables ─────────────────────────────────────────────────
TOKEN      = os.environ.get("BOT_TOKEN")
RAW_PASS   = os.environ.get("BOT_PASSWORD", "changeme")
OWNER_ID   = int(os.environ.get("OWNER_ID", 0))

# Password stored as SHA-256 hash — never plain text
HASHED_PASSWORD = hashlib.sha256(RAW_PASS.encode()).hexdigest()

# ─── Storage Files ─────────────────────────────────────────────────────────
ACCOUNTS_FILE = "accounts.json"
AUDIT_FILE    = "audit.json"

# ─── Runtime State ─────────────────────────────────────────────────────────
AUTHORIZED_USERS  = {}   # {user_id: datetime of login}
FAILED_ATTEMPTS   = {}   # {user_id: int}
BLOCKED_USERS     = set()
AWAITING_PASSWORD = set()
AWAITING_ADD      = {}   # {user_id: step data}
AWAITING_DELETE   = set()

SESSION_TIMEOUT_MINUTES = 30
MAX_FAILED_ATTEMPTS     = 3


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_accounts() -> dict:
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_accounts(data: dict):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_audit() -> list:
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, "r") as f:
            return json.load(f)
    return []


def save_audit(logs: list):
    with open(AUDIT_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def log_audit(user_id: int, username: str, action: str):
    logs = load_audit()
    logs.append({
        "user_id":   user_id,
        "username":  username,
        "action":    action,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_audit(logs)


def is_session_valid(user_id: int) -> bool:
    if user_id not in AUTHORIZED_USERS:
        return False
    login_time = AUTHORIZED_USERS[user_id]
    if datetime.now() - login_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        del AUTHORIZED_USERS[user_id]
        return False
    return True


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Account List", callback_data="show_list")],
        [InlineKeyboardButton("➕ Add Account",  callback_data="add_account"),
         InlineKeyboardButton("🗑 Delete Account", callback_data="delete_account")],
        [InlineKeyboardButton("📜 Audit Log",    callback_data="audit_log"),
         InlineKeyboardButton("🚪 Logout",       callback_data="logout")]
    ])


def back_keyboard(target="main_menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data=target)]
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in BLOCKED_USERS:
        await update.message.reply_text("🚫 Too many wrong attempts. You are blocked.")
        return

    if is_session_valid(user_id):
        await update.message.reply_text(
            "✅ Already logged in.",
            reply_markup=main_menu_keyboard()
        )
        return

    AWAITING_PASSWORD.add(user_id)
    await update.message.reply_text("🔐 Enter Password:")


# ══════════════════════════════════════════════════════════════════════════════
#  Message Handler (Password + Add Account flow)
# ══════════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    username = update.effective_user.username or str(user_id)
    text     = update.message.text.strip()

    # ── Blocked ──────────────────────────────────────────────────────────────
    if user_id in BLOCKED_USERS:
        await update.message.reply_text("🚫 You are blocked due to too many wrong attempts.")
        return

    # ── Password check ───────────────────────────────────────────────────────
    if user_id in AWAITING_PASSWORD:
        input_hash = hashlib.sha256(text.encode()).hexdigest()

        if input_hash == HASHED_PASSWORD:
            AWAITING_PASSWORD.discard(user_id)
            FAILED_ATTEMPTS[user_id] = 0
            AUTHORIZED_USERS[user_id] = datetime.now()
            log_audit(user_id, username, "Logged in")
            await update.message.reply_text(
                f"✅ Welcome, {username}!\n\nSession expires in {SESSION_TIMEOUT_MINUTES} minutes.",
                reply_markup=main_menu_keyboard()
            )
        else:
            FAILED_ATTEMPTS[user_id] = FAILED_ATTEMPTS.get(user_id, 0) + 1
            remaining = MAX_FAILED_ATTEMPTS - FAILED_ATTEMPTS[user_id]
            log_audit(user_id, username, "Wrong password attempt")

            if FAILED_ATTEMPTS[user_id] >= MAX_FAILED_ATTEMPTS:
                BLOCKED_USERS.add(user_id)
                AWAITING_PASSWORD.discard(user_id)
                log_audit(user_id, username, "Blocked after max failed attempts")
                await update.message.reply_text("🚫 Too many wrong attempts. You are now blocked.")
            else:
                await update.message.reply_text(
                    f"❌ Wrong password. {remaining} attempt(s) remaining."
                )
        return

    # ── Session check ─────────────────────────────────────────────────────────
    if not is_session_valid(user_id):
        AWAITING_PASSWORD.add(user_id)
        await update.message.reply_text("⏰ Session expired. Enter Password:")
        return

    # ── Add Account flow ──────────────────────────────────────────────────────
    if user_id in AWAITING_ADD:
        step = AWAITING_ADD[user_id]

        if step["stage"] == "name":
            step["name"]  = text
            step["stage"] = "email"
            await update.message.reply_text("📧 Enter Email / ID:")

        elif step["stage"] == "email":
            step["email"] = text
            step["stage"] = "password"
            await update.message.reply_text("🔑 Enter Password:")

        elif step["stage"] == "password":
            name     = step["name"]
            accounts = load_accounts()
            accounts[name] = {"email": step["email"], "pw": text}
            save_accounts(accounts)
            log_audit(user_id, username, f"Added account: {name}")
            del AWAITING_ADD[user_id]
            await update.message.reply_text(
                f"✅ Account **{name}** added successfully!",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        return

    # ── Delete Account flow ───────────────────────────────────────────────────
    if user_id in AWAITING_DELETE:
        accounts = load_accounts()
        if text in accounts:
            del accounts[text]
            save_accounts(accounts)
            log_audit(user_id, username, f"Deleted account: {text}")
            AWAITING_DELETE.discard(user_id)
            await update.message.reply_text(
                f"🗑 Account **{text}** deleted.",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "⚠️ Account not found. Try again or /start to go back."
            )
        return

    # ── Default ───────────────────────────────────────────────────────────────
    await update.message.reply_text(
        "Use the menu below 👇",
        reply_markup=main_menu_keyboard()
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Callback Handler
# ══════════════════════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    user_id  = query.from_user.id
    username = query.from_user.username or str(user_id)
    data     = query.data

    await query.answer()

    # ── Auth check ────────────────────────────────────────────────────────────
    if not is_session_valid(user_id):
        AWAITING_PASSWORD.add(user_id)
        await query.message.reply_text("⏰ Session expired. Enter Password:")
        return

    # ── Main Menu ─────────────────────────────────────────────────────────────
    if data == "main_menu":
        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu_keyboard()
        )

    # ── Account List ──────────────────────────────────────────────────────────
    elif data == "show_list":
        accounts = load_accounts()
        if not accounts:
            await query.edit_message_text(
                "📭 No accounts saved yet.",
                reply_markup=back_keyboard()
            )
            return

        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"info_{name}")]
            for name in accounts.keys()
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        await query.edit_message_text(
            "📋 Select an account:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ── Account Details ───────────────────────────────────────────────────────
    elif data.startswith("info_"):
        name     = data.replace("info_", "", 1)
        accounts = load_accounts()
        account  = accounts.get(name)

        if account:
            log_audit(user_id, username, f"Viewed account: {name}")
            response = (
                f"✅ *Name:* `{name}`\n"
                f"📧 *Email/ID:* `{account['email']}`\n"
                f"🔑 *Password:* `{account['pw']}`"
            )
            await query.message.reply_text(
                response,
                parse_mode="Markdown",
                reply_markup=back_keyboard("show_list")
            )
        else:
            await query.message.reply_text("⚠️ Account not found.")

    # ── Add Account ───────────────────────────────────────────────────────────
    elif data == "add_account":
        AWAITING_ADD[user_id] = {"stage": "name"}
        await query.edit_message_text("➕ Enter Account Name:")

    # ── Delete Account ────────────────────────────────────────────────────────
    elif data == "delete_account":
        accounts = load_accounts()
        if not accounts:
            await query.edit_message_text(
                "📭 No accounts to delete.",
                reply_markup=back_keyboard()
            )
            return

        keyboard = [
            [InlineKeyboardButton(f"🗑 {name}", callback_data=f"del_{name}")]
            for name in accounts.keys()
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        await query.edit_message_text(
            "🗑 Select account to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("del_"):
        name     = data.replace("del_", "", 1)
        accounts = load_accounts()
        if name in accounts:
            del accounts[name]
            save_accounts(accounts)
            log_audit(user_id, username, f"Deleted account: {name}")
            await query.edit_message_text(
                f"✅ Account **{name}** deleted.",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard()
            )

    # ── Audit Log (Owner only) ────────────────────────────────────────────────
    elif data == "audit_log":
        if not is_owner(user_id):
            await query.message.reply_text("⛔ Only the owner can view audit logs.")
            return

        logs = load_audit()
        if not logs:
            await query.edit_message_text(
                "📭 No audit logs yet.",
                reply_markup=back_keyboard()
            )
            return

        last_10 = logs[-10:]
        text = "📜 *Last 10 Audit Logs:*\n\n"
        for log in reversed(last_10):
            text += (
                f"👤 `{log['username']}`\n"
                f"🔹 {log['action']}\n"
                f"🕐 {log['timestamp']}\n\n"
            )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=back_keyboard()
        )

    # ── Logout ────────────────────────────────────────────────────────────────
    elif data == "logout":
        if user_id in AUTHORIZED_USERS:
            del AUTHORIZED_USERS[user_id]
            log_audit(user_id, username, "Logged out")
        await query.edit_message_text("🚪 Logged out successfully. Use /start to login again.")


# ══════════════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN not found!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
