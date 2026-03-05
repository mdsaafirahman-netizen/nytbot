import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in AUTHORIZED_USERS:
        keyboard = [[InlineKeyboardButton("📂 Open List", callback_data="show_list")]]
        await update.message.reply_text(
            "✅ You are already logged in",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text("🔒 Enter password to access the bot:")


# PASSWORD CHECK
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    # already logged in
    if user_id in AUTHORIZED_USERS:
        return

    user_pass = update.message.text

    if user_pass == PASSWORD:

        AUTHORIZED_USERS.add(user_id)

        # delete password message
        try:
            await update.message.delete()
        except:
            pass

        keyboard = [
            [InlineKeyboardButton("📂 Open List", callback_data="show_list")]
        ]

        await update.message.reply_text(
            "✅ Access Granted",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
         msg = await
    update.message.reply_text("❌ Wrong password. Try again.")
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except:
        pass

# SHOW LIST
async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:

        if update.callback_query:
            await update.callback_query.answer("❌ Enter password first!", show_alert=True)
        else:
            await update.message.reply_text("❌ Enter password first.")

        return

    query = update.callback_query

    if query:
        await query.answer()

    keyboard = []

    for name in GMAIL_DATA.keys():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"info_{name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            "📂 Select account:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📂 Select account:",
            reply_markup=reply_markup
        )


# SHOW ACCOUNT DETAILS
async def show_details(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.callback_query.answer("❌ Access denied!", show_alert=True)
        return

    query = update.callback_query
    await query.answer()

    name = query.data.replace("info_", "")
    account = GMAIL_DATA.get(name)

    if not account:
        return

    text = (
        f"👤 Name: {name}\n"
        f"📧 Gmail: `{account['email']}`\n"
        f"🔑 Password: `{account['pw']}`\n\n"
        f"⚠️ This message will auto delete in 30 seconds"
    )

    msg = await query.message.reply_text(text, parse_mode="Markdown")

    # auto delete after 30 sec
    await asyncio.sleep(30)

    try:
        await msg.delete()
    except:
        pass


# MAIN FUNCTION
def main():

    if not TOKEN:
        print("BOT_TOKEN not found!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
    app.add_handler(CommandHandler("list", show_list))

    app.add_handler(CallbackQueryHandler(show_list, pattern="^show_list$"))
    app.add_handler(CallbackQueryHandler(show_details, pattern="^info_"))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
