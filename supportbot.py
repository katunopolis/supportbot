# 🔹 Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import telegram  # Catching Forbidden errors
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

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

from telegram import WebAppInfo

async def request_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /request command from the public group by opening the Web App support form."""
    user_id = update.message.from_user.id
    webapp_url = "https://your-webapp.netlify.app"  # Replace with your actual web app URL

    # Build a button that opens the support web app
    keyboard = [[InlineKeyboardButton("Open Support Form", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # If the message is not in a private chat, simply send the button
    if update.message.chat.type != "private":
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )
    else:
        # In a private chat, you can also use the web app button or prompt text input
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )

async def collect_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collects user issue details and notifies the admin group."""
    user_id = update.message.from_user.id

    if context.user_data.get(f"requesting_support_{user_id}"):
        issue_description = update.message.text
        print(f"[DEBUG] Received issue from user {user_id}: {issue_description}")

        # Save issue to database
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO requests (user_id, issue) VALUES (?, ?)", (user_id, issue_description))
            conn.commit()
            request_id = cursor.lastrowid
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
    print(f"[DEBUG] Assigning request #{request_id} to admin {admin_id}")

    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE requests SET assigned_admin = ?, status = 'Assigned' WHERE id = ?", (admin_id, request_id))
            cursor.execute("SELECT user_id FROM requests WHERE id = ?", (request_id,))
            user = cursor.fetchone()
    except sqlite3.Error as e:
        print(f"[ERROR] Database error during assignment: {e}")
        await query.answer("Error: Could not assign request.")
        return

    if not user:
        await query.answer("Error: Request not found in database.")
        return

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
#  ✅ FASTAPI LIFESPAN (STARTUP & SHUTDOWN)
# ===============================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles FastAPI startup and shutdown events."""
    print("[INFO] Starting up: Initializing database and setting webhook...")
    init_db()
    await set_webhook()
    await bot_app.initialize()
    print("[INFO] Startup complete: Webhook set and bot initialized.")
    yield
    print("[INFO] Shutting down: Removing webhook...")
    from telegram import Bot
    try:
        bot = Bot(token=TOKEN)
        await bot.delete_webhook()
        print("[INFO] Webhook removed successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to remove webhook on shutdown: {e}")

# Attach lifespan to FastAPI app
fastapi_app = FastAPI(lifespan=lifespan)

# Re-add the root and webhook routes to the new fastapi_app instance
@fastapi_app.get("/")
async def root():
    return {"message": "Telegram Support Bot API is running!"}

@fastapi_app.post("/webhook")
async def webhook(update: dict):
    """Handles incoming Telegram updates via webhook."""
    try:
        update = Update.de_json(update, bot_app.bot)
        await bot_app.process_update(update)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        print(f"[ERROR] Webhook error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

# ===============================
#  ✅ MAIN FUNCTION
# ===============================

def main():
    """Starts FastAPI server and registers bot handlers."""
    # Register Telegram handlers BEFORE starting FastAPI
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("request", request_support))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_issue))
    bot_app.add_handler(CallbackQueryHandler(assign_request))

    print("🚀 Bot is running on webhook mode...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
