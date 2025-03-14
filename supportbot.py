# 🔹 Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
import sqlite3
import telegram  # Catching Forbidden errors
import uvicorn
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import asyncio

# Set up logging
logging.basicConfig(
    filename='bot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 🔹 Load Telegram Bot Token from environment
TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: SUPPORT_BOT_TOKEN is not set. Please add it to environment variables.")

logging.info(f"Bot Token Loaded: {TOKEN[:5]}********")  # Obfuscate token for security

# 🔹 Admin Group Chat ID (Change this to your actual admin group)
ADMIN_GROUP_ID = -4771220922

# 🔹 Webhook URL (Update this based on Railway deployment)
WEBHOOK_URL = "https://supportbot-production-b784.up.railway.app/webhook"

# 🔹 Web App URL with version parameter
WEBAPP_URL = f"https://webapp-support-bot-production.up.railway.app/?v={datetime.now().strftime('%Y%m%d%H%M%S')}&r={os.urandom(4).hex()}"

# 🔹 Initialize Telegram Bot Application (Only once)
bot_app = Application.builder().token(TOKEN).build()

# -------------------------------
# FASTAPI LIFESPAN (STARTUP & SHUTDOWN)
# -------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: initialize DB, set webhook, and initialize bot on startup; remove webhook on shutdown."""
    # Startup tasks
    logging.info("[INFO] Starting up: Initializing database...")
    init_db()
    
    logging.info("[INFO] Initializing bot application...")
    await bot_app.initialize()
    
    logging.info("[INFO] Setting webhook...")
    try:
        from telegram import Bot
        bot = Bot(token=TOKEN)
        # First, delete any existing webhook
        await bot.delete_webhook()
        logging.info("[INFO] Existing webhook removed.")
        
        # Then set the new webhook
        success = await bot.set_webhook(WEBHOOK_URL)
        if success:
            logging.info("[INFO] Webhook set successfully.")
            # Verify webhook status
            webhook_info = await bot.get_webhook_info()
            logging.info(f"[INFO] Webhook info: {webhook_info}")
        else:
            logging.warning("[WARNING] Webhook request sent, but Telegram did not confirm.")
    except Exception as e:
        logging.error(f"[ERROR] Failed to set webhook: {e}")
        # Don't raise the exception, let the app start anyway
    
    logging.info("[INFO] Startup complete: Bot initialized and webhook set.")
    
    yield
    
    # Shutdown tasks
    logging.info("[INFO] Shutting down: Cleaning up...")
    try:
        # Remove webhook
        from telegram import Bot
        bot = Bot(token=TOKEN)
        await bot.delete_webhook()
        logging.info("[INFO] Webhook removed successfully.")
        
        # Stop the bot application
        await bot_app.stop()
        logging.info("[INFO] Bot application stopped.")
        
    except Exception as e:
        logging.error(f"[ERROR] Error during shutdown: {e}")

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
    """Serve the support request form."""
    try:
        return JSONResponse(content={"message": "Telegram Support Bot API is running!"})
    except Exception as e:
        logging.error(f"Error serving index page: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint that verifies webhook status."""
    try:
        from telegram import Bot
        bot = Bot(token=TOKEN)
        webhook_info = await bot.get_webhook_info()
        return {
            "status": "healthy",
            "webhook_url": webhook_info.url,
            "webhook_set": webhook_info.url == WEBHOOK_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

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
            
            # First, get the current max request ID
            cursor.execute("SELECT MAX(id) FROM requests")
            current_max_id = cursor.fetchone()[0] or 0
            logging.info(f"Current max request ID: {current_max_id}")
            
            # Insert new request
            cursor.execute("INSERT INTO requests (user_id, issue) VALUES (?, ?)", (user_id, issue))
            conn.commit()
            request_id = cursor.lastrowid
            
            # Verify the new request ID
            logging.info(f"New request ID generated: {request_id}")
            
            # Save initial message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, 'user', ?)
            """, (request_id, user_id, issue))
            conn.commit()
            
            # Verify the request exists
            cursor.execute("SELECT id FROM requests WHERE id = ?", (request_id,))
            if not cursor.fetchone():
                logging.error(f"Request {request_id} not found after insertion")
                return JSONResponse(content={"error": "Failed to create request"}, status_code=500)
        
        # Create web app URL with request ID
        webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"
        
        # Send stand-by message to user with WebApp button
        try:
            keyboard = [[InlineKeyboardButton(
                text="Open Support Chat",
                web_app=WebAppInfo(url=webapp_url)
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot_app.bot.send_message(
                user_id,
                "✅ Your support request has been received!\n\n"
                "An admin will be with you shortly. Please stand by...",
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Failed to send WebApp button to user: {e}")
            # Fallback to regular URL button
            keyboard = [[InlineKeyboardButton("Open Support Chat", url=webapp_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot_app.bot.send_message(
                user_id,
                "✅ Your support request has been received!\n\n"
                "An admin will be with you shortly. Please stand by...",
                reply_markup=reply_markup
            )
        
        # Build Admin Group Message with Action Buttons
        try:
            buttons = [
                [InlineKeyboardButton(
                    text="Open Support Chat",
                    web_app=WebAppInfo(url=webapp_url)
                )],
                [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
                [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
        except Exception as e:
            logging.error(f"Failed to create WebApp button for admin: {e}")
            # Fallback to regular URL button
            buttons = [
                [InlineKeyboardButton("Open Support Chat", url=webapp_url)],
                [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
                [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
        
        # Log the admin notification
        logging.info(f"Sending admin notification for request #{request_id}")
        
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
        logging.error(f"Support request error: {e}")
        return JSONResponse(content={"message": str(e)}, status_code=500)

@fastapi_app.get("/chat/{request_id}")
async def get_chat_page(request_id: int):
    """Serve the chat page for a specific support request."""
    try:
        logging.info(f"Chat page requested for request #{request_id}")
        # Get request details to verify it exists
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM requests WHERE id = ?", (request_id,))
            request = cursor.fetchone()
            
            if not request:
                logging.error(f"Request #{request_id} not found")
                return JSONResponse(content={"error": "Request not found"}, status_code=404)
                
            user_id = request[0]
            logging.info(f"Found request #{request_id} for user {user_id}")
            
            # Add user_id to chat.html URL
            chat_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"
            logging.info(f"Generated chat URL: {chat_url}")
            return JSONResponse(content={"chat_url": chat_url})
    except Exception as e:
        logging.error(f"Error serving chat page: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.get("/chat/{request_id}/messages")
async def get_chat_messages(request_id: int):
    """Get all messages for a specific support request."""
    try:
        logging.info(f"Fetching messages for request #{request_id}")
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
                logging.warning(f"No messages found for request #{request_id}")
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
            
            logging.info(f"Found {len(formatted_messages)} messages for request #{request_id}")
            logging.debug(f"Messages: {formatted_messages}")
            return JSONResponse(content={"messages": formatted_messages})
    except Exception as e:
        logging.error(f"Error fetching chat messages: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.post("/chat/{request_id}/message")
async def send_message(request_id: int, payload: dict):
    """Send a new message in the support chat."""
    try:
        logging.info(f"Received message for request #{request_id}: {payload}")
        sender_id = payload.get("sender_id")
        sender_type = payload.get("sender_type")
        message = payload.get("message")
        
        if not all([sender_id, sender_type, message]):
            logging.error(f"Missing required fields in payload: {payload}")
            return JSONResponse(content={"error": "Missing required fields"}, status_code=400)
        
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Save message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, ?, ?)
            """, (request_id, sender_id, sender_type, message))
            conn.commit()
            logging.info(f"Message saved to database for request #{request_id}")
            
            # Get request details
            cursor.execute("SELECT user_id, assigned_admin FROM requests WHERE id = ?", (request_id,))
            request = cursor.fetchone()
            
            if not request:
                logging.error(f"Request #{request_id} not found in database")
                return JSONResponse(content={"error": "Request not found"}, status_code=404)
            
            user_id, assigned_admin = request
            logging.info(f"Request #{request_id} details: user_id={user_id}, assigned_admin={assigned_admin}")
            
            # Create web app URL
            webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"
            logging.info(f"Generated web app URL: {webapp_url}")
            
            # Notify the other party (user or admin) via Telegram with web app URL
            if sender_type == "admin":
                # Notify user with web app URL
                try:
                    keyboard = [[InlineKeyboardButton(
                        text="Open Support Chat",
                        web_app=WebAppInfo(url=webapp_url)
                    )]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await bot_app.bot.send_message(
                        user_id,
                        f"💬 New message from support:\n{message}",
                        reply_markup=reply_markup
                    )
                    logging.info(f"Sent notification to user {user_id}")
                except Exception as e:
                    logging.error(f"Failed to send WebApp button to user: {e}")
                    # Fallback to regular URL button
                    keyboard = [[InlineKeyboardButton("Open Support Chat", url=webapp_url)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await bot_app.bot.send_message(
                        user_id,
                        f"💬 New message from support:\n{message}",
                        reply_markup=reply_markup
                    )
            else:
                # Notify admin with web app URL
                if assigned_admin:
                    try:
                        keyboard = [[InlineKeyboardButton(
                            text="Open Support Chat",
                            web_app=WebAppInfo(url=webapp_url)
                        )]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await bot_app.bot.send_message(
                            assigned_admin,
                            f"💬 New message from user:\n{message}",
                            reply_markup=reply_markup
                        )
                        logging.info(f"Sent notification to admin {assigned_admin}")
                    except Exception as e:
                        logging.error(f"Failed to send WebApp button to admin: {e}")
                        # Fallback to regular URL button
                        keyboard = [[InlineKeyboardButton("Open Support Chat", url=webapp_url)]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await bot_app.bot.send_message(
                            assigned_admin,
                            f"💬 New message from user:\n{message}",
                            reply_markup=reply_markup
                        )
        
        logging.info(f"Message saved successfully for request #{request_id}")
        return JSONResponse(content={"message": "Message sent successfully"})
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.get("/logs")
async def get_logs(limit: int = 100, level: str = None):
    """Get logs from the database with optional filtering."""
    try:
        # Add a small delay to ensure fresh data
        await asyncio.sleep(0.1)
        
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            query = "SELECT timestamp, level, message, context FROM logs"
            params = []
            
            if level:
                query += " WHERE level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
            
            # Add cache-busting headers
            headers = {
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "Surrogate-Control": "no-store",
                "Last-Modified": datetime.now().isoformat()
            }
            
            return JSONResponse(
                content={
                    "logs": [
                        {
                            "timestamp": log[0],
                            "level": log[1],
                            "message": log[2],
                            "context": log[3]
                        }
                        for log in logs
                    ],
                    "timestamp": datetime.now().isoformat()  # Add current timestamp to response
                },
                headers=headers
            )
    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        return JSONResponse(
            content={"error": str(e)},
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "Surrogate-Control": "no-store",
                "Last-Modified": datetime.now().isoformat()
            }
        )

@fastapi_app.post("/webapp-log")
async def webapp_log(log_data: dict):
    """Receive logs from the web app and store them in the database."""
    try:
        # Log to database
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (timestamp, level, message, context)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                log_data.get("level", "info"),
                log_data.get("message", ""),
                str(log_data.get("context", {}))
            ))
            conn.commit()
        
        # Also log to file
        logging.info(f"WebApp Log: {log_data}")
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error saving webapp log: {e}")
        return {"status": "error", "message": str(e)}

@fastapi_app.get("/api/health")
async def health_check():
    """Health check endpoint that verifies webhook status."""
    try:
        from telegram import Bot
        bot = Bot(token=TOKEN)
        webhook_info = await bot.get_webhook_info()
        return {
            "status": "healthy",
            "webhook_url": webhook_info.url,
            "webhook_set": webhook_info.url == WEBHOOK_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

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
            # Create logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    message TEXT,
                    context TEXT
                )
            """)
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")

# Custom logging handler to store logs in database
class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            with sqlite3.connect("support_requests.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO logs (timestamp, level, message, context)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.fromtimestamp(record.created).isoformat(),
                    record.levelname,
                    record.getMessage(),
                    str(record.__dict__)
                ))
                conn.commit()
        except Exception:
            self.handleError(record)

# Set up logging with both file and database handlers
def setup_logging():
    """Set up logging with both file and database handlers."""
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        'bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Database handler
    db_handler = DatabaseLogHandler()
    db_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(db_handler)

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
    logging.info(f"User {user_id} requested support")
    
    try:
        # Use the versioned web app URL
        keyboard = [[
            InlineKeyboardButton(
                text="Open Support Form",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the message with the Web App button
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )
        context.user_data[f"requesting_support_{user_id}"] = True
    except Exception as e:
        logging.error(f"Error creating WebApp button: {e}")
        # Fallback to URL button if WebApp fails
        keyboard = [[InlineKeyboardButton("Open Support Form", url=WEBAPP_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )

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

        # Create web app URL
        webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"

        # Build Admin Group Message with Action Buttons
        try:
            buttons = [
                [InlineKeyboardButton(
                    text="Open Support Chat",
                    web_app=WebAppInfo(url=webapp_url)
                )],
                [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
                [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]
            ]
            if update.message.from_user.username:
                buttons.insert(1, [InlineKeyboardButton("Open User Chat", url=f"https://t.me/{update.message.from_user.username}")])
            reply_markup = InlineKeyboardMarkup(buttons)
        except Exception as e:
            logging.error(f"Failed to create WebApp button for admin: {e}")
            # Fallback to regular URL buttons
            buttons = [
                [InlineKeyboardButton("Open Support Chat", url=webapp_url)],
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

        # Send confirmation to user with WebApp button
        try:
            await context.bot.send_message(
                user_id,
                "✅ Your request has been submitted. A support admin will reach out soon.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="Open Support Chat",
                        web_app=WebAppInfo(url=webapp_url)
                    )
                ]])
            )
        except Exception as e:
            logging.error(f"Failed to send WebApp button to user: {e}")
            # Fallback to regular URL button
            await context.bot.send_message(
                user_id,
                "✅ Your request has been submitted. A support admin will reach out soon.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Open Support Chat", url=webapp_url)
                ]])
            )

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
    
    # Create web app URL
    webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"

    # Notify User with web app URL
    try:
        keyboard = [[InlineKeyboardButton(
            text="Open Support Chat",
            web_app=WebAppInfo(url=webapp_url)
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            user_id,
            f"An admin (@{admin_username}) has been assigned to your request.\nClick below to open the chat.",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Failed to send WebApp button to user after assignment: {e}")
        # Fallback to regular URL button
        keyboard = [[InlineKeyboardButton("Open Support Chat", url=webapp_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            user_id,
            f"An admin (@{admin_username}) has been assigned to your request.\nClick below to open the chat.",
            reply_markup=reply_markup
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

# Initialize logging at startup
setup_logging()

if __name__ == "__main__":
    main()
