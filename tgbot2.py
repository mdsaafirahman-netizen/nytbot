import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get
PASSWORD = "S1A1F1i1"

GMAIL_DATA = {
    "mdsaafirahman": {"email": "mdsaafirahman@gmail.com", "pw": "Asha11981"},
    "nytsafi": {"email": "nytsafi@gmail.com", "pw": "Asha11981"},
    "blusterprimenyt": {"email": "blusterprimenyt@gmail.com", "pw": "Asha11981"},
    "nytneco": {"email": "nytneco@gmail.com", "pw": "Asha11981"},
    "suaibfakshisafi": {"email": "suaibfakshisafi@gmail.com", "pw": "Asha11981"},
    "pharsa": {"email": "emonpharsa@gmail.com", "pw": "Asha11981"},
    "nyt3rd": {"email": "nyt3rd@gmail.com", "pw": "Asha11981"},
    "shojibxjod": {"email": "shojibxjod@gmail.com", "pw": "Asha11981"},
    "safilvl442": {"email": "safilvl442@gmail.com", "pw": "Asha11981"},
    "nyt2nd": {"email": "nyt2nd@gmail.com", "pw": "Asha11981"},
    "nytsuaib": {"email": "nytsuaib@gmail.com", "pw": "Asha11981"},
    "nytfarr": {"email": "nytfarr@gmail.com", "pw": "Asha11981"},
    "nytbackup": {"email": "nyt1backup@gmail.com", "pw": "Asha11981"},
    "nytzefoy": {"email": "nytzefoy@gmail.com", "pw": "Asha11981"},
    "tiktok - @nytsafi": {"email": "safi007p@gmail.com", "pw": "@A1S1H1A1"},
    "Facebook ( Game id )": {"email": "nyt1backup@gmail.com", "pw": "Asha11981"},
    "Main id security Code": {"email": "mdsaafirahman@gmail.com", "pw": "534757"},
}

AUTHORIZED_USERS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter Password:")

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == PASSWORD:
        AUTHORIZED_USERS.add(user_id)
        keyboard = [[InlineKeyboardButton("List", callback_data="show_list")]]
        await update.message.reply_text(
            "Hlw Sir, Please type /list or click the button below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        return

    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [[InlineKeyboardButton(name, callback_data=f"info_{name}")] for name in GMAIL_DATA.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text("Select an account to see details:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Select an account to see details:", reply_markup=reply_markup)

async def show_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        return

    query = update.callback_query
    await query.answer()

    name = query.data.replace("info_", "")
    account = GMAIL_DATA.get(name)

    if account:
        response = f"✅ **Name:** {name}\n📧 **Gmail:** `{account['email']}`\n🔑 **Password:** `{account['pw']}`"
        await query.message.reply_text(text=response, parse_mode="Markdown")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN variable not found!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", show_list))
    app.add_handler(CallbackQueryHandler(show_list, pattern="^show_list$"))
    app.add_handler(CallbackQueryHandler(show_details, pattern="^info_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
