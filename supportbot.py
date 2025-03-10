# 🔹 Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import telegram  # Catching Forbidden errors
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# 🔹 Initialize FastAPI App FIRST before using it
fastapi_app = FastAPI()

# 🔹 Load Telegram Bot Token from environment
TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: SUPPORT_BOT_TOKEN is not set. Please add it to environment variables.")

print(f"Bot Token Loaded: {TOKEN[:5]}********")  # Obfuscate token for security

# 🔹 Admin Group Chat ID (Change this to your actual admin group)
ADMIN_GROUP_ID = -4771220922

# 🔹 Webhook URL (Update this based on Railway deployment)
WEBHOOK_URL = "https://supportbot-production-b784.up.railway.app/webhook"

# 🔹 Initialize Telegram Bot Application (Only once)
bot_app = Application.builder().token(TOKEN).build()
await bot_app.initialize()  # ✅ Ensure it is awaited

# ✅ **Root Route (For health check)**
@fastapi_app.get("/")
async def root():
    return {"message": "Telegram Support Bot API is running!"}

# ✅ **Webhook Route (For Telegram to send updates)**
@fastapi_app.post("/webhook")
async def webhook(update: dict):
    """Handles incoming Telegram updates via webhook."""
    try:
        print(f"[INFO] Received update: {update}")  # ✅ Debugging output

        if not bot_app.running:
            print("[INFO] Initializing bot before processing webhook...")
            await bot_app.initialize()

        update = Update.de_json(update, bot_app.bot)
        await bot_app.process_update(update)

        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        print(f"[ERROR] Webhook error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# ===============================
#  ✅ DATABASE SETUP & UTILITIES
# ===============================

def init_db():
    """Initialize SQLite database for storing support requests."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
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
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")

async def set_webhook():
    """Sets Telegram bot webhook for handling messages via FastAPI."""
    from telegram import Bot
    try:
        bot = Bot(token=TOKEN)
        success = await bot.set_webhook(WEBHOOK_URL)
        if success:
            print("[INFO] Webhook set successfully.")
        else:
            print("[WARNING] Webhook request sent, but Telegram did not confirm.")
    except Exception as e:
        print(f"[ERROR] Failed to set webhook: {e}")

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
        request_id = cursor.lastrowid  # ✅ Define request_id properly
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
#  ✅ FASTAPI LIFESPAN (STARTUP & SHUTDOWN)
# ===============================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup & shutdown tasks using FastAPI lifespan."""
    print("[INFO] Initializing bot on startup...")
    init_db()
    await set_webhook()
    await bot_app.initialize()  # ✅ Ensure bot initializes correctly
    print("[INFO] Webhook set successfully.")
    yield
    print("[INFO] Cleaning up bot on shutdown...")
    from telegram import Bot
    bot = Bot(token=TOKEN)
    await bot.delete_webhook()
    print("[INFO] Webhook removed. Bot shutting down.")

# ✅ Attach lifespan to FastAPI
fastapi_app = FastAPI(lifespan=lifespan)

# ===============================
#  ✅ MAIN FUNCTION
# ===============================

def main():
    """Starts FastAPI server and registers bot handlers."""
    # ✅ Register Telegram handlers BEFORE starting FastAPI
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("request", request_support))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_issue))

    print("🚀 Bot is running on webhook mode...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
