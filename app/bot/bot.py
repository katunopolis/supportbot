import logging
import asyncio
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes
)
from app.config import WEBHOOK_URL, MAX_CONNECTIONS, POOL_TIMEOUT, RATE_LIMIT, RATE_LIMIT_TIME
from app.bot.handlers.start import start, help_command, request_support, test_command
from app.bot.handlers.admin import list_requests, view_request, handle_admin_callbacks, handle_message
from app.database.session import get_db, SessionLocal
from sqlalchemy import text
import os
from dotenv import load_dotenv
from app.bot.handlers.support import notify_admin_group, collect_issue, handle_callback_query
import traceback
from typing import Callable, Any, Awaitable, Optional
import time
from collections import defaultdict
from functools import wraps
import httpx

load_dotenv()

# Get bot token from environment variable
BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("SUPPORT_BOT_TOKEN environment variable is not set")

# Initialize bot and application as None
bot = None
bot_app = None

# Command rate limiting
command_semaphore = asyncio.Semaphore(20)  # Limit concurrent command processing

# Rate limiting setup
rate_limits = defaultdict(lambda: {"count": 0, "reset_time": time.time() + RATE_LIMIT_TIME})

async def rate_limited_handler(handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]], 
                        update: Update, 
                        context: ContextTypes.DEFAULT_TYPE) -> Any:
    """Wrapper for rate limiting handlers."""
    if not update.effective_user:
        return await handler(update, context)
        
    user_id = update.effective_user.id
    current_time = time.time()
    
    # Reset rate limit if time expired
    if current_time > rate_limits[user_id]["reset_time"]:
        rate_limits[user_id] = {"count": 0, "reset_time": current_time + RATE_LIMIT_TIME}
    
    # Check if rate limited
    if rate_limits[user_id]["count"] >= RATE_LIMIT:
        # If private chat, inform user
        if update.effective_chat and update.effective_chat.type == "private":
            try:
                remaining_time = int(rate_limits[user_id]["reset_time"] - current_time)
                await update.effective_chat.send_message(
                    f"Rate limit exceeded. Please try again in {remaining_time} seconds."
                )
            except Exception as e:
                logging.error(f"Failed to send rate limit message: {e}")
        return None
        
    # Increment rate limit counter
    rate_limits[user_id]["count"] += 1
    
    try:
        # Process the handler
        return await handler(update, context)
    except Exception as e:
        logging.error(f"Error in handler: {e}")
        traceback.print_exc()
        # Try to notify user of error
        if update.effective_chat and update.effective_chat.type == "private":
            try:
                await update.effective_chat.send_message(
                    "Sorry, an error occurred while processing your request."
                )
            except Exception as notify_err:
                logging.error(f"Failed to send error notification: {notify_err}")
        raise

async def check_database():
    """Check database connection with proper error handling."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.commit()
        db.close()
        logging.info("Database connection test successful")
        return True
    except Exception as e:
        logging.error(f"Database connection test failed: {e}")
        return False

async def initialize_bot():
    """Initialize the bot with proper connection pool settings."""
    global bot, bot_app

    try:
        # Test database connection before initializing bot
        if not await check_database():
            raise RuntimeError("Database connection test failed")

        if bot is None or bot_app is None:
            # Create bot instance
            bot = Bot(token=BOT_TOKEN)
            
            # Initialize the bot object itself
            await bot.initialize()
            
            # Create application with the token directly (don't set both bot and pool_size)
            bot_app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()
            
            # Initialize the application - this was missing
            await bot_app.initialize()
            
            logging.info("Bot initialized successfully")
            await setup_handlers()  # Setup handlers after initialization
            await setup_bot_commands()  # Setup bot commands menu
            return True
        return True
    except Exception as e:
        logging.error(f"Error initializing bot: {e}")
        raise RuntimeError(f"Error during startup: {e}")

async def setup_handlers():
    """Setup bot handlers with rate limiting and proper error handling."""
    if bot_app is None:
        raise RuntimeError("Bot application not initialized")
        
    try:
        # Register command handlers
        bot_app.add_handler(
            CommandHandler(
                "start",
                lambda u, c: rate_limited_handler(start, u, c)
            )
        )
        bot_app.add_handler(
            CommandHandler(
                "help",
                lambda u, c: rate_limited_handler(help_command, u, c)
            )
        )
        bot_app.add_handler(
            CommandHandler(
                "request",
                lambda u, c: rate_limited_handler(request_support, u, c)
            )
        )
        bot_app.add_handler(
            CommandHandler(
                "test",
                lambda u, c: rate_limited_handler(test_command, u, c)
            )
        )
        
        # Admin handlers
        bot_app.add_handler(
            CommandHandler(
                "list",
                lambda u, c: rate_limited_handler(list_requests, u, c)
            )
        )
        
        # View request handler for /view_ID pattern
        bot_app.add_handler(
            MessageHandler(
                filters.Regex(r'^/view_\d+$') & filters.ChatType.PRIVATE,
                lambda u, c: rate_limited_handler(view_request, u, c)
            )
        )
        
        # Callback query handler for admin actions (assign/resolve)
        # These follow the format "assign_123_456" or "resolve_123"
        bot_app.add_handler(
            CallbackQueryHandler(
                lambda u, c: rate_limited_handler(handle_admin_callbacks, u, c),
                pattern=r"^(assign|resolve)_\d+(_\d+)?$"
            )
        )
        
        # Message handler for admin resolution messages and other text
        bot_app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                lambda u, c: rate_limited_handler(handle_message, u, c)
            )
        )
        
        # Add callback query handler for support inline buttons from admin group
        # These follow the format "assign_123", "view_123", "chat_123", or "solve_123"
        bot_app.add_handler(
            CallbackQueryHandler(
                lambda u, c: rate_limited_handler(handle_callback_query, u, c),
                pattern=r"^(assign|view|chat|solve)_\d+$"
            )
        )
        
        logging.info("Bot handlers registered successfully")
        
    except Exception as e:
        logging.error(f"Error setting up handlers: {e}")
        raise

async def setup_webhook():
    """Setup webhook with retry logic and proper error handling."""
    global bot
    
    if bot is None:
        raise RuntimeError("Bot not initialized")
    
    # Ensure the bot is initialized before setting up webhook
    if not getattr(bot, '_initialized', False):
        logging.warning("Bot not fully initialized, initializing before setting webhook")
        try:
            await bot.initialize()
        except Exception as e:
            logging.error(f"Error initializing bot during webhook setup: {e}")
            raise
        
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Remove any existing webhook
            await bot.delete_webhook()
            
            # Set up the new webhook
            await bot.set_webhook(
                url=WEBHOOK_URL,
                allowed_updates=["message", "callback_query"],
                max_connections=MAX_CONNECTIONS,
                drop_pending_updates=True
            )
            
            # Verify webhook
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url != WEBHOOK_URL:
                raise ValueError(f"Webhook URL mismatch: {webhook_info.url} != {WEBHOOK_URL}")
                
            logging.info(f"Webhook set successfully to {WEBHOOK_URL}")
            return
            
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Webhook setup attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"All webhook setup attempts failed: {e}")
                raise

async def remove_webhook():
    """Remove webhook on shutdown with proper error handling."""
    global bot
    
    if bot is None:
        logging.warning("Bot not initialized, no webhook to remove")
        return
        
    try:
        # Make sure the bot is initialized before calling delete_webhook
        if not getattr(bot, '_initialized', False):
            logging.warning("Bot not fully initialized, initializing before removing webhook")
            try:
                await bot.initialize()
            except Exception as e:
                logging.error(f"Error initializing bot during webhook removal: {e}")
                return
                
        await bot.delete_webhook()
        logging.info("Webhook removed successfully")
    except Exception as e:
        logging.error(f"Error removing webhook: {e}")

async def process_update(update_dict: dict):
    """Process update from webhook."""
    global bot, bot_app
    
    try:
        # Make sure the application is initialized
        if bot_app is None or bot is None:
            logging.warning("Bot or application not initialized, initializing now")
            await initialize_bot()
            if bot_app is None or bot is None:
                logging.error("Failed to initialize bot or application")
                return
                
        # Ensure both bot and application are initialized
        if not getattr(bot, '_initialized', False):
            logging.warning("Bot not fully initialized, initializing now")
            try:
                await bot.initialize()
            except Exception as e:
                logging.error(f"Error initializing bot during update processing: {e}")
                return
                
        # Convert dict to Update object
        update = Update.de_json(update_dict, bot)
        logging.info(f"Processing update: {update.update_id}")
        
        # Process update through application
        await bot_app.process_update(update)
        logging.debug(f"Update {update.update_id} processed successfully")
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        raise

async def setup_bot_commands():
    """Set up the bot commands menu."""
    global bot
    
    if bot is None:
        logging.error("Bot not initialized, cannot set commands")
        return
        
    try:
        # Ensure the bot is initialized before setting commands
        if not getattr(bot, '_initialized', False):
            logging.warning("Bot not fully initialized, initializing before setting commands")
            try:
                await bot.initialize()
            except Exception as e:
                logging.error(f"Error initializing bot during command setup: {e}")
                return
                
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help information"),
            BotCommand("request", "Create a new support request"),
            BotCommand("test", "Test if the bot is working correctly"),
            BotCommand("list", "List all support requests (admin only)"),
            BotCommand("view", "View a specific support request (admin only)")
        ]
        await bot.set_my_commands(commands)
        logging.info("Bot commands menu set up successfully")
    except Exception as e:
        logging.error(f"Error setting up bot commands: {e}")

async def handle_message(update: Update, context):
    """Handle text messages - resolution messages from admins and issue collection"""
    # First try to handle as admin resolution message
    try:
        from app.bot.handlers.admin import handle_message as admin_handle_message
        if await admin_handle_message(update, context):
            return
    except Exception as e:
        logging.error(f"Error handling resolution message: {e}")
    
    # Import collect_issue here to avoid circular imports
    from app.bot.handlers.support import collect_issue
    
    # If not a resolution message, try to collect issue
    try:
        await collect_issue(update, context)
    except Exception as e:
        logging.error(f"Error collecting issue: {e}")
        await update.message.reply_text(
            "I'm a support bot. Type /help to see available commands."
        )

async def shutdown():
    """Properly shut down the application when the server stops."""
    global bot, bot_app
    
    try:
        if bot_app:
            await bot_app.shutdown()
            logging.info("Bot application shutdown successful")
            
        if bot:
            await bot.shutdown()
            logging.info("Bot shutdown successful")
    except Exception as e:
        logging.error(f"Error during bot shutdown: {e}")

# Set up application handlers
application = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("request", request_support))
application.add_handler(CommandHandler("test", test_command))
application.add_handler(CommandHandler("requests", list_requests))
application.add_handler(CommandHandler("view", view_request))

# Add callback query handlers
application.add_handler(CallbackQueryHandler(handle_admin_callbacks, pattern=r"^admin:"))
application.add_handler(CallbackQueryHandler(handle_callback_query, pattern=r"^(assign|view|chat|solve)_\d+$"))

# Add message handler for normal text messages
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Function to get the application
def get_application():
    return application 