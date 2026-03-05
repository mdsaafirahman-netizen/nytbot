import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
PASSWORD = "S1A1F1i1"
AUTHORIZED_USERS = set()

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ You are already logged in!")
        return
    await update.message.reply_text("🔒 Enter password:")

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        return
    if update.message.text == PASSWORD:
        AUTHORIZED_USERS.add(user_id)
        await update.message.reply_text("✅ Access Granted!")
    else:
        await update.message.reply_text("❌ Wrong password!")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
app.run_polling()

print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
