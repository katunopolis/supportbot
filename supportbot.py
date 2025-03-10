import os
import sqlite3
import telegram  # Catching Forbidden errors
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv  # Load .env variables
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Load environment variables from .env file
load_dotenv()

# 🔹 Load Telegram Bot Token from environment
TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: SUPPORT_BOT_TOKEN is not set. Please add it to environment variables.")

print(f"Bot Token Loaded: {TOKEN[:5]}********")  # Obfuscate token for security

# 🔹 Admin Group Chat ID (Change this to your actual admin group)
ADMIN_GROUP_ID = -4771220922

# 🔹 Root endpoint to confirm the app is running
@fastapi_app.get("/")
async def root():
    return {"message": "Telegram Support Bot API is running!"}

# 🔹 Webhook URL (Update this based on Railway deployment)
WEBHOOK_URL = "https://supportbot-production-b784.up.railway.app/webhook"

# 🔹 FastAPI Application (Used for webhook communication)
fastapi_app = FastAPI()

# 🔹 Initialize Telegram Bot Application
bot_app = Application.builder().token(TOKEN).build()

# ===============================
#  ✅ DATABASE SETUP & UTILITIES
# ===============================

def init_db():
    """Initialize SQLite database for storing support requests."""
    conn = sqlite3.connect("support_requests.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            issue TEXT,
            assigned_admin INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'Open',
            solution TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

async def set_webhook():
    """Sets Telegram bot webhook for handling messages via FastAPI."""
    from telegram import Bot
    bot = Bot(token=TOKEN)
    await bot.set_webhook(WEBHOOK_URL)

# ===============================
#  ✅ COMMAND HANDLERS
# ===============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command in private chat."""
    user_id = update.message.from_user.id
    if context.user_data.get(f"pending_request_{user_id}"):
        await update.message.reply_text("Welcome back! Please describe your issue:")
        context.user_data[f"requesting_support_{user_id}"] = True
        context.user_data.pop(f"pending_request_{user_id}", None)
    else:
        await update.message.reply_text("Welcome! Use /request in the group to get support.")

async def request_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /request command from the public group."""
    user_id = update.message.from_user.id

    if update.message.chat.type != "private":
        try:
            await context.bot.send_message(user_id, "I see you need support! Please describe the issue:")
            context.user_data[f"requesting_support_{user_id}"] = True
            await context.bot.send_message(update.message.chat_id, f"@{update.message.from_user.username}, check your private messages.")
        except telegram.error.Forbidden:
            # Bot can't DM user → Ask them to start chat manually
            context.user_data[f"pending_request_{user_id}"] = True
            keyboard = [[InlineKeyboardButton("Start Chat with Bot", url=f"https://t.me/{context.bot.username}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"@{update.message.from_user.username}, click below to start a private chat with the bot.",
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text("Please describe your issue:")
        context.user_data[f"requesting_support_{user_id}"] = True

# ===============================
#  ✅ SUPPORT REQUEST PROCESS
# ===============================

async def collect_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collects user issue details and notifies the admin group."""
    user_id = update.message.from_user.id

    if context.user_data.get(f"requesting_support_{user_id}"):
        issue_description = update.message.text
        print(f"[DEBUG] Received issue from user {user_id}: {issue_description}")

        # Save issue to database
        conn = sqlite3.connect("support_requests.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO requests (user_id, issue) VALUES (?, ?)", (user_id, issue_description))
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()

        # Build Admin Group Message with Action Buttons
        buttons = [
            [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
            [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]
        ]
        if update.message.from_user.username:
            buttons.insert(1, [InlineKeyboardButton("Open User Chat", url=f"https://t.me/{update.message.from_user.username}")])

        reply_markup = InlineKeyboardMarkup(buttons)

        # Notify Admin Group
        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"📌 **New Support Request #{request_id}**\n🔹 **User ID:** `{user_id}`\n📄 **Issue:** {issue_description}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Your request has been submitted. A support admin will reach out soon.")
        context.user_data[f"requesting_support_{user_id}"] = False

# ===============================
#  ✅ ADMIN ACTIONS
# ===============================

async def assign_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assigns an admin to a request and notifies the user."""
    query = update.callback_query
    admin_id = query.from_user.id
    request_id = int(query.data.split("_")[1])

    conn = sqlite3.connect("support_requests.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET assigned_admin = ?, status = 'Assigned' WHERE id = ?", (admin_id, request_id))
    cursor.execute("SELECT user_id FROM requests WHERE id = ?", (request_id,))
    user = cursor.fetchone()
    conn.commit()
    conn.close()

    if user:
        user_id = user[0]
        admin_username = query.from_user.username or "Admin"
        admin_link = f"https://t.me/{admin_username}" if admin_username else f"tg://user?id={admin_id}"

        # Notify User
        await context.bot.send_message(
            user_id,
            f"An admin (@{admin_username}) has been assigned to your request.\nClick below to open a direct chat.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Admin Chat", url=admin_link)]])
        )
        await query.answer("You have been assigned to this request.")

# ===============================
#  ✅ TELEGRAM WEBHOOK HANDLER
# ===============================

@fastapi_app.post("/webhook")
async def webhook(update: dict):
    """Handles incoming Telegram updates via webhook."""
    update = Update.de_json(update, bot_app.bot)
    await bot_app.process_update(update)

# ===============================
#  ✅ MAIN FUNCTION
# ===============================

def main():
    """Initializes bot, database, and webhook, then starts FastAPI server."""
    init_db()  # Ensure database is set up

    # Add Telegram command handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("request", request_support))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_issue))
    bot_app.add_handler(CallbackQueryHandler(assign_request))

    # Set webhook before running server
    import asyncio
    asyncio.run(set_webhook())

    print("🚀 Bot is running on webhook mode...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()