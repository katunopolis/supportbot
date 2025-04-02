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
    print("Loading environment variables...")
    load_dotenv()

    token = os.getenv("SUPPORT_BOT_TOKEN")
    if not token:
        print("ERROR: SUPPORT_BOT_TOKEN not found in environment variables")
        return False
    else:
        print(f"Found bot token: {token[:5]}...{token[-5:]}")

    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if not railway_domain:
        print("ERROR: RAILWAY_PUBLIC_DOMAIN not found in environment variables")
        return False

    print(f"Using domain for webhook: {railway_domain}")
    webhook_url = f"https://{railway_domain}/webhook"
    print(f"Webhook URL: {webhook_url}")

    try:
        print("Creating bot instance...")
        bot = Bot(token=token)

        print("Getting bot information...")
        bot_info = await bot.get_me()
        print(f"Bot: {bot_info.first_name} (@{bot_info.username})")

        print("Deleting existing webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("Deleted existing webhook")

        print(f"Setting webhook to: {webhook_url}")
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            max_connections=10,
            drop_pending_updates=True
        )

        print("Verifying webhook...")
        webhook_info = await bot.get_webhook_info()
        print(f"Current webhook URL: {webhook_info.url}")
        print(f"Expected webhook URL: {webhook_url}")

        if webhook_info.url == webhook_url:
            print(f"[SUCCESS] Webhook successfully set to: {webhook_url}")
            print(f"Pending updates: {webhook_info.pending_update_count}")
            print(f"Max connections: {webhook_info.max_connections}")
            print(f"Allowed updates: {webhook_info.allowed_updates}")
            return True
        else:
            print(f"[ERROR] Webhook URL mismatch. Set to {webhook_info.url} instead of {webhook_url}")
            return False

    except Exception as e:
        print(f"[ERROR] Webhook setup failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def delete_webhook():
    """Delete the current webhook and verify removal."""
    try:
        load_dotenv()
        token = os.getenv("SUPPORT_BOT_TOKEN")
        if not token:
            logger.error("SUPPORT_BOT_TOKEN not found in environment variables")
            return False

        bot = Bot(token=token)

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Deleted webhook, verifying...")

        webhook_info = await bot.get_webhook_info()
        if not webhook_info.url:
            logger.info("[SUCCESS] Webhook successfully deleted")
            return True
        else:
            logger.error(f"[ERROR] Webhook still set to: {webhook_info.url}")
            return False

    except Exception as e:
        logger.error(f"[ERROR] Failed to delete webhook: {e}")
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