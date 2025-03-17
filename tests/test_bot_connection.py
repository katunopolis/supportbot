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

async def test_bot_connection():
    """Test the connection to the Telegram Bot API."""
    # Load environment variables
    load_dotenv()
    
    # Get bot token
    token = os.getenv("SUPPORT_BOT_TOKEN")
    if not token:
        logger.error("SUPPORT_BOT_TOKEN not found in environment variables")
        return False
    
    admin_group_id = os.getenv("ADMIN_GROUP_ID", "-4771220922")
    
    try:
        # Create bot instance
        bot = Bot(token=token)
        
        # Get bot information
        bot_info = await bot.get_me()
        logger.info(f"✅ Connected to bot: {bot_info.first_name} (@{bot_info.username})")
        
        # Check webhook status
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.info(f"✅ Webhook is set to: {webhook_info.url}")
            
            # Check if webhook domain matches RAILWAY_PUBLIC_DOMAIN
            railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
            if railway_domain and railway_domain not in webhook_info.url:
                logger.warning(
                    f"⚠️ Webhook domain mismatch: webhook uses {webhook_info.url} but RAILWAY_PUBLIC_DOMAIN is {railway_domain}"
                )
        else:
            logger.warning("⚠️ No webhook set. Bot will not receive updates through webhook.")
        
        # Try to send a test message to admin group
        try:
            message = await bot.send_message(
                chat_id=admin_group_id,
                text="🔄 Testing bot connection from local environment"
            )
            logger.info(f"✅ Successfully sent test message to admin group. Message ID: {message.message_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send message to admin group: {e}")
        
        # Try to get updates (only works if webhook is not set)
        if not webhook_info.url:
            updates = await bot.get_updates(limit=5)
            logger.info(f"✅ Retrieved {len(updates)} recent updates")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot connection test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting bot connection test...")
    
    # Get environment information
    env = os.getenv("ENVIRONMENT", "not set")
    base_url = os.getenv("BASE_WEBAPP_URL", "not set")
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "not set")
    
    logger.info(f"Environment: {env}")
    logger.info(f"BASE_WEBAPP_URL: {base_url}")
    logger.info(f"RAILWAY_PUBLIC_DOMAIN: {railway_domain}")
    
    # Run the test
    result = asyncio.run(test_bot_connection())
    
    if result:
        logger.info("✅ Bot connection test completed successfully")
    else:
        logger.error("❌ Bot connection test failed") 