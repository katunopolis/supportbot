import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from app.config import TOKEN, WEBHOOK_URL
from app.bot.handlers.start import start, request_support
from app.bot.handlers.support import collect_issue
from app.bot.handlers.admin import assign_request

# Initialize bot application
bot_app = Application.builder().token(TOKEN).job_queue(None).build()

async def initialize_bot():
    """Initialize bot and register handlers."""
    try:
        # Initialize the bot
        await bot_app.initialize()
        logging.info("Bot application initialized")
        
        # Register handlers
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("request", request_support))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_issue))
        bot_app.add_handler(CallbackQueryHandler(assign_request))
        logging.info("Bot handlers registered")
        
    except Exception as e:
        logging.error(f"Error initializing bot: {e}")
        raise

async def setup_webhook():
    """Set up webhook for the bot."""
    try:
        bot = Bot(token=TOKEN)
        
        # First, delete any existing webhook
        await bot.delete_webhook()
        logging.info("Existing webhook removed")
        
        # Set the new webhook
        success = await bot.set_webhook(WEBHOOK_URL)
        if success:
            logging.info("Webhook set successfully")
            # Verify webhook status
            webhook_info = await bot.get_webhook_info()
            logging.info(f"Webhook info: {webhook_info}")
        else:
            logging.warning("Webhook request sent, but Telegram did not confirm")
            
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")
        raise

async def remove_webhook():
    """Remove the bot's webhook."""
    try:
        bot = Bot(token=TOKEN)
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