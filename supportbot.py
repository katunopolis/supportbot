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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
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

# -------------------------------
# FASTAPI LIFESPAN (STARTUP & SHUTDOWN)
# -------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: initialize DB, set webhook, and initialize bot on startup; remove webhook on shutdown."""
    # Startup tasks
    print("[INFO] Starting up: Initializing database...")
    init_db()
    print("[INFO] Setting webhook...")
    await set_webhook()
    await bot_app.initialize()
    print("[INFO] Startup complete: Bot initialized and webhook set.")
    
    yield
    
    # Shutdown tasks
    print("[INFO] Shutting down: Cleaning up...")
    try:
        # Remove webhook
        from telegram import Bot
        bot = Bot(token=TOKEN)
        await bot.delete_webhook()
        print("[INFO] Webhook removed successfully.")
        
        # Stop the bot application
        await bot_app.stop()
        print("[INFO] Bot application stopped.")
        
        # Close any database connections
        # Add your database cleanup here if needed
        
    except Exception as e:
        print(f"[ERROR] Error during shutdown: {e}")

# Attach lifespan to FastAPI app
fastapi_app = FastAPI(lifespan=lifespan)

# 🔹 Add a CORS middleware to your FastAPI app

from fastapi.middleware.cors import CORSMiddleware

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# FASTAPI ROUTES
# -------------------------------
@fastapi_app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Telegram Support Bot API is running!"}

@fastapi_app.post("/webhook")
async def webhook(update: dict):
    """Handles incoming Telegram updates via webhook."""
    try:
        print(f"[INFO] Received update: {update}")
        update_obj = Update.de_json(update, bot_app.bot)
        await bot_app.process_update(update_obj)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        print(f"[ERROR] Webhook error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
    
@fastapi_app.post("/support-request")
async def support_request_handler(payload: dict):
    """
    Handles support requests from the Web App.
    Expects a JSON payload with keys 'user_id' and 'issue'.
    """
    try:
        user_id = payload.get("user_id")
        issue = payload.get("issue")
        if not user_id or not issue:
            return JSONResponse(content={"message": "Missing user_id or issue"}, status_code=400)
        
        # Save issue to the database
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO requests (user_id, issue) VALUES (?, ?)", (user_id, issue))
            conn.commit()
            request_id = cursor.lastrowid
            
            # Save initial message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, 'user', ?)
            """, (request_id, user_id, issue))
            conn.commit()
        
        # Create web app URL with request ID
        webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}"
        
        # Notify admin group with web app button
        keyboard = [[InlineKeyboardButton("Open Support Chat", web_app=WebAppInfo(url=webapp_url))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot_app.bot.send_message(
            ADMIN_GROUP_ID,
            f"📌 **New Support Request #{request_id}**\n🔹 **User ID:** `{user_id}`\n📄 **Issue:** {issue}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return JSONResponse(content={
            "message": "Support request submitted successfully",
            "request_id": request_id,
            "chat_url": webapp_url
        })
    except Exception as e:
        print(f"[ERROR] Support request error: {e}")
        return JSONResponse(content={"message": str(e)}, status_code=500)

@fastapi_app.get("/chat/{request_id}")
async def get_chat_messages(request_id: int):
    """Get all messages for a specific support request."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, r.user_id, r.assigned_admin
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE m.request_id = ?
                ORDER BY m.timestamp ASC
            """, (request_id,))
            messages = cursor.fetchall()
            
            if not messages:
                return JSONResponse(content={"error": "Request not found"}, status_code=404)
                
            # Format messages for frontend
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg[0],
                    "request_id": msg[1],
                    "sender_id": msg[2],
                    "sender_type": msg[3],
                    "message": msg[4],
                    "timestamp": msg[5],
                    "user_id": msg[6],
                    "assigned_admin": msg[7]
                })
            
            return JSONResponse(content={"messages": formatted_messages})
    except Exception as e:
        print(f"[ERROR] Error fetching chat messages: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.post("/chat/{request_id}/message")
async def send_message(request_id: int, payload: dict):
    """Send a new message in the support chat."""
    try:
        sender_id = payload.get("sender_id")
        sender_type = payload.get("sender_type")
        message = payload.get("message")
        
        if not all([sender_id, sender_type, message]):
            return JSONResponse(content={"error": "Missing required fields"}, status_code=400)
        
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Save message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, ?, ?)
            """, (request_id, sender_id, sender_type, message))
            conn.commit()
            
            # Get request details
            cursor.execute("SELECT user_id, assigned_admin FROM requests WHERE id = ?", (request_id,))
            request = cursor.fetchone()
            
            if not request:
                return JSONResponse(content={"error": "Request not found"}, status_code=404)
            
            user_id, assigned_admin = request
            
            # Notify the other party (user or admin) via Telegram
            if sender_type == "admin":
                # Notify user
                await bot_app.bot.send_message(
                    user_id,
                    f"💬 New message from support:\n{message}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Open Chat", web_app=WebAppInfo(url=f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}"))
                    ]])
                )
            else:
                # Notify admin
                if assigned_admin:
                    await bot_app.bot.send_message(
                        assigned_admin,
                        f"💬 New message from user:\n{message}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Open Chat", web_app=WebAppInfo(url=f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}"))
                        ]])
                    )
        
        return JSONResponse(content={"message": "Message sent successfully"})
    except Exception as e:
        print(f"[ERROR] Error sending message: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# -------------------------------
# DATABASE SETUP & UTILITIES
# -------------------------------
def init_db():
    """Initialize SQLite database for storing support requests and messages."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Create requests table
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
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER,
                    sender_id INTEGER,
                    sender_type TEXT,  -- 'user' or 'admin'
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES requests(id)
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

# -------------------------------
# COMMAND HANDLERS
# -------------------------------
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
    """Handles /request command from the public group by opening a Web App."""
    user_id = update.message.from_user.id
    # Instead of prompting text, we now open the web app:
    webapp_url = "https://webapp-support-bot-production.up.railway.app/"  # Replace with your actual web app URL
    keyboard = [[InlineKeyboardButton("Open Support Form", web_app=WebAppInfo(url=webapp_url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message with the Web App button
    await update.message.reply_text(
        "Click the button below to open our support form:",
        reply_markup=reply_markup
    )
    # (Optionally, store state if needed)
    context.user_data[f"requesting_support_{user_id}"] = True

# -------------------------------
# SUPPORT REQUEST PROCESS
# -------------------------------
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

# -------------------------------
# ADMIN ACTIONS
# -------------------------------
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

# -------------------------------
# MAIN FUNCTION
# -------------------------------
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
