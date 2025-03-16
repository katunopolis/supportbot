import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from app.config import TOKEN, WEBHOOK_URL
from app.bot.handlers.start import start, request_support
from app.bot.handlers.support import collect_issue
from app.bot.handlers.admin import assign_request
from app.database.session import get_db

# Initialize bot and application with optimized settings
bot = Bot(token=TOKEN)
bot_app = (
    Application.builder()
    .token(TOKEN)
    .job_queue(None)
    .concurrent_updates(True)  # Enable concurrent update handling
    .connection_pool_size(100)  # Increase connection pool size
    .connect_timeout(30.0)  # Increase connection timeout
    .read_timeout(30.0)  # Increase read timeout
    .write_timeout(30.0)  # Increase write timeout
    .pool_timeout(3.0)  # Set pool timeout
    .build()
)

# Command rate limiting
command_semaphore = asyncio.Semaphore(20)  # Limit concurrent command processing

async def rate_limited_handler(handler, update, context):
    """Wrap command handlers with rate limiting."""
    async with command_semaphore:
        return await handler(update, context)

async def initialize_bot():
    """Initialize bot and register handlers with optimized settings."""
    try:
        # Initialize the bot application
        await bot_app.initialize()
        logging.info("Bot application initialized")
        
        # Create connection pool for database
        db = next(get_db())
        
        # Register handlers with rate limiting
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
        
        # Message handler with database session
        bot_app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                lambda u, c: rate_limited_handler(
                    lambda u, c: collect_issue(u, c, db),
                    u, c
                )
            )
        )
        
        # Callback query handler with database session
        bot_app.add_handler(
            CallbackQueryHandler(
                lambda u, c: rate_limited_handler(
                    lambda u, c: assign_request(u, c, db),
                    u, c
                )
            )
        )
        
        logging.info("Bot handlers registered with rate limiting")
        
        # Test bot connection with timeout
        async with asyncio.timeout(5.0):
            me = await bot.get_me()
            logging.info(f"Bot connection test successful. Bot username: @{me.username}")
        
    except Exception as e:
        logging.error(f"Error initializing bot: {e}")
        raise

async def setup_webhook():
    """Set up webhook with retry logic and validation."""
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # Delete existing webhook with timeout
            async with asyncio.timeout(5.0):
                await bot.delete_webhook()
                logging.info("Existing webhook removed")
            
            # Set new webhook with timeout
            async with asyncio.timeout(5.0):
                success = await bot.set_webhook(WEBHOOK_URL)
                if not success:
                    raise ValueError("Telegram did not confirm webhook setup")
                
            # Verify webhook with timeout
            async with asyncio.timeout(5.0):
                webhook_info = await bot.get_webhook_info()
                if webhook_info.url != WEBHOOK_URL:
                    raise ValueError(f"Webhook URL mismatch. Expected {WEBHOOK_URL}, got {webhook_info.url}")
                
                if webhook_info.last_error_date:
                    logging.warning(f"Webhook last error: {webhook_info.last_error_message} at {webhook_info.last_error_date}")
                
                logging.info(f"Webhook successfully set and verified: {webhook_info.url}")
                return
                
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Webhook setup attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"Failed to set webhook after {max_retries} attempts: {e}")
                raise

async def remove_webhook():
    """Remove the bot's webhook."""
    try:
        await bot.delete_webhook()
        logging.info("Webhook removed successfully")
    except Exception as e:
        logging.error(f"Error removing webhook: {e}")
        raise

async def process_update(update_dict: dict):
    """Process incoming update from webhook."""
    try:
        update = Update.de_json(update_dict, bot_app.bot)
        await bot_app.process_update(update)
        return True
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return False 