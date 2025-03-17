import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from app.config import WEBHOOK_URL, MAX_CONNECTIONS, POOL_TIMEOUT
from app.bot.handlers.start import start, request_support
from app.bot.handlers.support import collect_issue
from app.bot.handlers.admin import assign_request
from app.database.session import get_db, SessionLocal
from sqlalchemy import text
import os
from dotenv import load_dotenv

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

async def rate_limited_handler(handler, update, context):
    """Wrap command handlers with rate limiting."""
    async with command_semaphore:
        return await handler(update, context)

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
            bot = Bot(token=BOT_TOKEN)
            bot_app = (
                Application.builder()
                .bot(bot)                        # Bot instance must be first
                .concurrent_updates(True)        # Then other settings
                .connection_pool_size(MAX_CONNECTIONS)  # Pool settings last
                .pool_timeout(POOL_TIMEOUT)
                .build()
            )
            logging.info("Bot initialized successfully")
            await setup_handlers()  # Setup handlers after initialization
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
                "request",
                lambda u, c: rate_limited_handler(request_support, u, c)
            )
        )
        
        # Message handler
        bot_app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda u, c: rate_limited_handler(
                    lambda u, c: collect_issue(u, c, next(get_db())),
                    u, c
                )
            )
        )
        
        # Callback query handler
        bot_app.add_handler(
            CallbackQueryHandler(
                lambda u, c: rate_limited_handler(
                    lambda u, c: assign_request(u, c, next(get_db())),
                    u, c
                )
            )
        )
        
        logging.info("Bot handlers registered successfully")
        
    except Exception as e:
        logging.error(f"Error setting up handlers: {e}")
        raise

async def setup_webhook():
    """Setup webhook with retry logic and proper error handling."""
    if bot is None:
        raise RuntimeError("Bot not initialized")
        
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
    if bot is None:
        logging.warning("Bot not initialized, no webhook to remove")
        return
        
    try:
        await bot.delete_webhook()
        logging.info("Webhook removed successfully")
    except Exception as e:
        logging.error(f"Error removing webhook: {e}")
        raise

async def process_update(update: dict):
    """Process incoming update from webhook with proper error handling."""
    if bot_app is None:
        raise RuntimeError("Bot application not initialized")
        
    try:
        await bot_app.update_queue.put(Update.de_json(update, bot))
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        raise 