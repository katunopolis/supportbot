# 🔹 Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
import logging
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import asyncio
from sqlalchemy.orm import Session
from database import get_db, init_db, Request, Message, Log

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
bot_app = Application.builder().token(TOKEN).job_queue(None).build()

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
async def support_request_handler(payload: dict, db: Session = Depends(get_db)):
    """
    Handles support requests from the Web App.
    Expects a JSON payload with keys 'user_id' and 'issue'.
    """
    try:
        user_id = payload.get("user_id")
        issue = payload.get("issue")
        if not user_id or not issue:
            return JSONResponse(content={"message": "Missing user_id or issue"}, status_code=400)
        
        # Create new request in database
        new_request = Request(user_id=user_id, issue=issue)
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        request_id = new_request.id
        
        # Create initial message
        new_message = Message(
            request_id=request_id,
            sender_id=user_id,
            sender_type='user',
            message=issue
        )
        db.add(new_message)
        db.commit()
        
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
            await bot_app.bot.send_message(
                user_id,
                "✅ Your support request has been received!\n\n"
                "An admin will be with you shortly. Please stand by..."
            )
        
        # Build Admin Group Message with Action Buttons
        try:
            buttons = [
                [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
                [InlineKeyboardButton("Open Support Chat", web_app=WebAppInfo(url=webapp_url))]
            ]
            
            reply_markup = InlineKeyboardMarkup(buttons)
            
            admin_message = await bot_app.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=f"📌 *New Support Request #{request_id}*\n🔹 *User ID:* `{user_id}`\n📄 *Issue:* {issue}",
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            if not admin_message.reply_markup:
                try:
                    await admin_message.edit_reply_markup(reply_markup=reply_markup)
                except Exception as edit_error:
                    logging.error(f"Failed to edit message to add buttons: {edit_error}")
        except Exception as e:
            logging.error(f"Failed to send admin notification: {e}", exc_info=True)
            try:
                await bot_app.bot.send_message(
                    chat_id=ADMIN_GROUP_ID,
                    text=f"📌 *New Support Request #{request_id}*\n🔹 *User ID:* `{user_id}`\n📄 *Issue:* {issue}\n\n⚠️ Error: Could not add buttons",
                    parse_mode="Markdown"
                )
            except Exception as retry_error:
                logging.error(f"Failed to send admin notification on retry: {retry_error}")
        
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
async def get_chat_messages(request_id: int, db: Session = Depends(get_db)):
    """Get all messages for a specific support request."""
    try:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            return JSONResponse(content={"error": "Request not found"}, status_code=404)
            
        messages = db.query(Message).filter(Message.request_id == request_id).all()
        
        formatted_messages = [{
            "id": msg.id,
            "request_id": msg.request_id,
            "sender_id": msg.sender_id,
            "sender_type": msg.sender_type,
            "message": msg.message,
            "timestamp": msg.timestamp.isoformat(),
        } for msg in messages]
        
        return JSONResponse(content={"messages": formatted_messages})
    except Exception as e:
        logging.error(f"Error fetching chat messages: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.post("/chat/{request_id}/message")
async def send_message(request_id: int, payload: dict, db: Session = Depends(get_db)):
    """Send a new message in the support chat."""
    try:
        sender_id = payload.get("sender_id")
        sender_type = payload.get("sender_type")
        message_text = payload.get("message")
        
        if not all([sender_id, sender_type, message_text]):
            return JSONResponse(content={"error": "Missing required fields"}, status_code=400)
        
        # Save message to database
        new_message = Message(
            request_id=request_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message_text
        )
        db.add(new_message)
        db.commit()
        
        # Get request details
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            return JSONResponse(content={"error": "Request not found"}, status_code=404)
        
        user_id = request.user_id
        assigned_admin = request.assigned_admin
        
        # Create web app URL
        webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"
        
        # Notify the other party
        if sender_type == "admin":
            try:
                keyboard = [[InlineKeyboardButton(
                    text="Open Support Chat",
                    web_app=WebAppInfo(url=webapp_url)
                )]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await bot_app.bot.send_message(
                    user_id,
                    f"💬 New message from support:\n{message_text}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Failed to send notification to user: {e}")
        else:
            if assigned_admin:
                try:
                    keyboard = [[InlineKeyboardButton(
                        text="Open Support Chat",
                        web_app=WebAppInfo(url=webapp_url)
                    )]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await bot_app.bot.send_message(
                        assigned_admin,
                        f"💬 New message from user:\n{message_text}",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logging.error(f"Failed to send notification to admin: {e}")
        
        return JSONResponse(content={"message": "Message sent successfully"})
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@fastapi_app.get("/logs")
async def get_logs(limit: int = 100, level: str = None, db: Session = Depends(get_db)):
    """Get logs from the database with optional filtering."""
    try:
        query = db.query(Log)
        
        if level:
            query = query.filter(Log.level == level)
        
        logs = query.order_by(Log.timestamp.desc()).limit(limit).all()
        
        return JSONResponse(
            content={
                "logs": [{
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message,
                    "context": log.context
                } for log in logs],
                "timestamp": datetime.now().isoformat()
            },
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "Surrogate-Control": "no-store",
                "Last-Modified": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

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
            # Create requests table with proper AUTOINCREMENT
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
            conn.commit()
            logging.info("Database initialized successfully")
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
        raise

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
    
    # Add separator to log file
    with open('bot.log', 'a', encoding='utf-8') as f:
        f.write('\n' + '='*80 + '\n')
        f.write(f'Bot started at {datetime.now().isoformat()}\n')
        f.write('='*80 + '\n\n')

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
        logging.info(f"Received issue from user {user_id}: {issue_description}")

        # Save issue to database
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            
            # First, get the current max request ID
            cursor.execute("SELECT MAX(id) FROM requests")
            current_max_id = cursor.fetchone()[0] or 0
            logging.info(f"Current max request ID: {current_max_id}")
            
            # Insert new request
            cursor.execute("INSERT INTO requests (user_id, issue) VALUES (?, ?)", (user_id, issue_description))
            conn.commit()
            request_id = cursor.lastrowid
            
            # Verify the new request ID
            logging.info(f"New request ID generated: {request_id}")
            
            # Save initial message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, 'user', ?)
            """, (request_id, user_id, issue_description))
            conn.commit()

        # Create web app URL
        webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}"
        logging.debug(f"Generated WebApp URL: {webapp_url}")

        # Build Admin Group Message with Action Buttons
        try:
            logging.info(f"Creating admin group buttons for request #{request_id}")
            
            # Create WebApp button for admin with proper error handling
            buttons = [
                [InlineKeyboardButton(
                    text="Open Support Chat",
                    web_app=WebAppInfo(url=webapp_url, start_parameter="admin_support_chat")
                )],
                [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
                [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]
            ]
            
            # Log button structure
            logging.debug(f"Button structure created: {[[b.text for b in row] for row in buttons]}")
            
            reply_markup = InlineKeyboardMarkup(buttons)
            
            # Verify button creation
            if not reply_markup or not reply_markup.inline_keyboard:
                raise ValueError("Failed to create button markup")
            
            # Log the admin notification attempt
            logging.info(f"Attempting to send admin notification for request #{request_id}")
            
            # Send message to admin group
            await context.bot.send_message(
                ADMIN_GROUP_ID,
                f"📌 **New Support Request #{request_id}**\n🔹 **User ID:** `{user_id}`\n📄 **Issue:** {issue_description}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logging.info(f"Successfully sent admin notification for request #{request_id}")
            
        except Exception as e:
            logging.error(f"Failed to create WebApp button for admin: {e}", exc_info=True)
            # Instead of falling back to URL button, try to fix the WebApp button
            try:
                logging.info(f"Retrying WebApp button creation for request #{request_id}")
                # Retry with explicit WebAppInfo parameters
                buttons = [
                    [InlineKeyboardButton(
                        text="Open Support Chat",
                        web_app=WebAppInfo(url=webapp_url, start_parameter="admin_support_chat_retry")
                    )],
                    [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")],
                    [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]
                ]
                
                # Log retry button structure
                logging.debug(f"Retry button structure: {[[b.text for b in row] for row in buttons]}")
                
                reply_markup = InlineKeyboardMarkup(buttons)
                
                # Verify WebApp button creation again
                if not reply_markup or not reply_markup.inline_keyboard:
                    raise ValueError("Failed to create WebApp button markup for admin on retry")
                
                await context.bot.send_message(
                    ADMIN_GROUP_ID,
                    f"📌 **New Support Request #{request_id}**\n🔹 **User ID:** `{user_id}`\n📄 **Issue:** {issue_description}",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                logging.info(f"Successfully sent admin notification for request #{request_id} on retry")
            except Exception as retry_error:
                logging.error(f"Failed to send WebApp button for admin on retry: {retry_error}", exc_info=True)
                # If WebApp button fails completely, send message without buttons
                await context.bot.send_message(
                    ADMIN_GROUP_ID,
                    f"📌 **New Support Request #{request_id}**\n🔹 **User ID:** `{user_id}`\n📄 **Issue:** {issue_description}",
                    parse_mode="Markdown"
                )
                logging.warning(f"Sent admin notification without buttons for request #{request_id}")

        # Send confirmation to user with WebApp button
        try:
            logging.info(f"Attempting to send confirmation to user {user_id}")
            keyboard = [[InlineKeyboardButton(
                text="Open Support Chat",
                web_app=WebAppInfo(url=webapp_url, start_parameter="user_support_chat")
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Log user notification attempt
            logging.debug(f"User notification button structure: {[[b.text for b in row] for row in keyboard]}")
            
            await context.bot.send_message(
                user_id,
                "✅ Your request has been submitted. A support admin will reach out soon.",
                reply_markup=reply_markup
            )
            logging.info(f"Successfully sent confirmation to user {user_id}")
        except Exception as e:
            logging.error(f"Failed to send WebApp button to user: {e}", exc_info=True)
            # If WebApp button fails, send message without button
            logging.warning(f"Sending user confirmation without button for request #{request_id}")
            await context.bot.send_message(
                user_id,
                "✅ Your request has been submitted. A support admin will reach out soon."
            )

        context.user_data[f"requesting_support_{user_id}"] = False
        logging.info(f"Support request process completed for user {user_id}")

# -------------------------------
# ADMIN ACTIONS
# -------------------------------
async def assign_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assigns an admin to a request and notifies the user."""
    query = update.callback_query
    admin_id = query.from_user.id
    request_id = int(query.data.split("_")[1])
    
    # Log assignment attempt
    logging.info(f"Admin {admin_id} attempting to assign request #{request_id}")
    logging.debug(f"Callback query data: {query.data}")
    logging.debug(f"Admin details: id={admin_id}, username={query.from_user.username}")

    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Check if request is already assigned
            cursor.execute("SELECT assigned_admin, user_id, issue FROM requests WHERE id = ?", (request_id,))
            request_info = cursor.fetchone()
            
            if not request_info:
                logging.error(f"Request #{request_id} not found in database")
                await query.answer("Error: Request not found.")
                return
                
            current_admin, user_id, issue = request_info
            
            if current_admin:
                logging.warning(f"Request #{request_id} is already assigned to admin {current_admin}")
                await query.answer("This request is already assigned to an admin.")
                return
            
            # Assign the request to the admin
            cursor.execute("""
                UPDATE requests 
                SET assigned_admin = ?, 
                    status = 'Assigned' 
                WHERE id = ?
            """, (admin_id, request_id))
            conn.commit()
            logging.info(f"Database updated: Request #{request_id} assigned to admin {admin_id}")
    except sqlite3.Error as e:
        logging.error(f"Database error during assignment: {e}", exc_info=True)
        await query.answer("Error: Could not assign request.")
        return

    admin_username = query.from_user.username or "Admin"
    
    # Create web app URL for admin chat
    webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}?user_id={user_id}&is_admin=true"
    logging.debug(f"Generated WebApp URL for admin: {webapp_url}")

    try:
        # Update admin group message with new status and buttons
        buttons = [
            [InlineKeyboardButton(
                text="Open User Chat",
                web_app=WebAppInfo(url=webapp_url)
            )],
            [InlineKeyboardButton("Mark as Solved", callback_data=f"solve_{request_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        # Update the original message
        await query.message.edit_text(
            f"📌 **Support Request #{request_id}**\n"
            f"🔹 **User ID:** `{user_id}`\n"
            f"📄 **Issue:** {issue}\n"
            f"👤 **Assigned to:** @{admin_username}\n"
            f"📱 **Status:** Assigned",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Send notification in admin group about assignment
        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"✅ Request #{request_id} has been assigned to @{admin_username}",
            parse_mode="Markdown"
        )
        
        # Notify user about admin assignment
        try:
            keyboard = [[InlineKeyboardButton(
                text="Open Support Chat",
                web_app=WebAppInfo(url=webapp_url)
            )]]
            user_reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                user_id,
                f"✨ Admin @{admin_username} has been assigned to your request.\n"
                f"Click below to start chatting!",
                reply_markup=user_reply_markup
            )
            logging.info(f"User {user_id} notified about admin assignment")
        except Exception as e:
            logging.error(f"Failed to send notification to user: {e}", exc_info=True)
            # If WebApp button fails, send simple message
            await context.bot.send_message(
                user_id,
                f"✨ Admin @{admin_username} has been assigned to your request."
            )
        
        await query.answer("✅ You have been assigned to this request!")
        logging.info(f"Assignment process completed for request #{request_id}")
        
    except Exception as e:
        logging.error(f"Error updating admin message: {e}", exc_info=True)
        await query.answer("Error updating message, but request was assigned.")

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
