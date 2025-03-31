import os
import logging
import asyncio
import sys
from telegram import Bot
from dotenv import load_dotenv

# Add parent directory to path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def setup_webhook():
    """Set up a webhook for the bot using the RAILWAY_PUBLIC_DOMAIN."""
    # Load environment variables
    load_dotenv()
    
    # Get bot token
    token = os.getenv("SUPPORT_BOT_TOKEN")
    if not token:
        logger.error("SUPPORT_BOT_TOKEN not found in environment variables")
        return False
    
    # Get domain for webhook
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if not railway_domain:
        logger.error("RAILWAY_PUBLIC_DOMAIN not found in environment variables")
        return False
    
    # Log the domain we're using
    logger.info(f"Using domain for webhook: {railway_domain}")
    
    # Construct webhook URL - ensure it uses HTTPS
    webhook_url = f"https://{railway_domain}/webhook"
    
    try:
        # Create bot instance
        bot = Bot(token=token)
        
        # Get bot information
        bot_info = await bot.get_me()
        logger.info(f"Setting up webhook for bot: {bot_info.first_name} (@{bot_info.username})")
        
        # Delete any existing webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Deleted existing webhook")
        
        # Set the new webhook
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            max_connections=10,
            drop_pending_updates=True
        )
        
        # Verify webhook was set correctly
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url == webhook_url:
            logger.info(f"✅ Webhook successfully set to: {webhook_url}")
            
            # Display webhook info
            logger.info(f"Pending updates: {webhook_info.pending_update_count}")
            logger.info(f"Max connections: {webhook_info.max_connections}")
            logger.info(f"Allowed updates: {webhook_info.allowed_updates}")
            
            return True
        else:
            logger.error(f"❌ Webhook URL mismatch. Set to {webhook_info.url} instead of {webhook_url}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Webhook setup failed: {e}")
        return False

async def delete_webhook():
    """Delete the current webhook."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get bot token
        token = os.getenv("SUPPORT_BOT_TOKEN")
        if not token:
            logger.error("SUPPORT_BOT_TOKEN not found in environment variables")
            return False
        
        # Create bot instance
        bot = Bot(token=token)
        
        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook successfully deleted")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to delete webhook: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Telegram bot webhook")
    parser.add_argument('--action', choices=['set', 'delete'], required=True, 
                        help="Action to perform: 'set' to configure the webhook, 'delete' to remove it")
    
    args = parser.parse_args()
    
    if args.action == 'set':
        logger.info("Setting up webhook...")
        asyncio.run(setup_webhook())
    elif args.action == 'delete':
        logger.info("Deleting webhook...")
        asyncio.run(delete_webhook()) 