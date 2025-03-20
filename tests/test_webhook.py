import asyncio
import os
import sys
import re
import argparse
from telegram import Bot
import subprocess
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import from the app package if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_valid_ngrok_url(url):
    """Validate if the URL is a proper ngrok URL."""
    if not url:
        return False
    
    # Check format (https://xxxx-xx-xx-xx-xx.ngrok-free.app)
    pattern = r'^https://[a-zA-Z0-9\-]+\.ngrok-free\.app$'
    return bool(re.match(pattern, url))

def check_container_running(container_name="support-bot-supportbot-1"):
    """Check if the Docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return container_name in result.stdout.strip()
    except subprocess.CalledProcessError:
        logger.error("Failed to check if container is running")
        return False

async def update_webhook(ngrok_url=None):
    """Update the webhook with the specified ngrok URL."""
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)
    
    # Get bot token
    token = os.getenv("SUPPORT_BOT_TOKEN")
    if not token:
        logger.error("SUPPORT_BOT_TOKEN not found in environment variables")
        return False
    
    # If no URL is provided, use the one from command line or prompt user
    if not ngrok_url:
        parser = argparse.ArgumentParser(description='Update webhook URL for Telegram bot')
        parser.add_argument('--url', help='The ngrok URL to use (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app)')
        args = parser.parse_args()
        
        if args.url:
            ngrok_url = args.url
        else:
            # Prompt user for URL
            ngrok_url = input("Enter ngrok URL (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app): ").strip()
    
    # Validate the URL
    if not is_valid_ngrok_url(ngrok_url):
        logger.error(f"Invalid ngrok URL format: {ngrok_url}")
        logger.error("URL should be in the format: https://xxxx-xx-xx-xx-xx.ngrok-free.app")
        return False
    
    # Construct webhook URL
    webhook_url = f"{ngrok_url}/webhook"
    logger.info(f"Using ngrok URL: {ngrok_url}")
    
    try:
        bot = Bot(token=token)
        
        # Get bot information
        bot_info = await bot.get_me()
        logger.info(f"Connected to bot: {bot_info.first_name} (@{bot_info.username})")
        
        # Get current webhook info
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Current webhook URL: {webhook_info.url}")
        
        # Set webhook to new URL
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Deleted existing webhook")
        
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            max_connections=10,
            drop_pending_updates=True
        )
        logger.info(f"Set webhook to: {webhook_url}")
        
        # Verify webhook was set correctly
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != webhook_url:
            logger.error(f"Webhook URL mismatch. Expected {webhook_url}, got {webhook_info.url}")
            return False
            
        logger.info(f"Webhook is now: {webhook_info.url}")
        
        # Update .env file
        logger.info("Updating .env file...")
        with open(dotenv_path, "r") as f:
            lines = f.readlines()
        
        ngrok_domain = ngrok_url.replace('https://', '')
        updated_env = False
        
        with open(dotenv_path, "w") as f:
            for line in lines:
                if line.startswith("RAILWAY_PUBLIC_DOMAIN="):
                    f.write(f"RAILWAY_PUBLIC_DOMAIN={ngrok_domain}\n")
                    updated_env = True
                elif line.startswith("BASE_WEBAPP_URL="):
                    f.write(f"BASE_WEBAPP_URL={ngrok_url}\n")
                    updated_env = True
                elif line.startswith("WEB_APP_URL="):
                    f.write(f"WEB_APP_URL={ngrok_url}/support-form.html\n")
                    updated_env = True
                else:
                    f.write(line)
        
        if updated_env:
            logger.info(f"Updated .env file with ngrok URL: {ngrok_url}")
        else:
            logger.warning("No environment variables were updated in .env file")
        
        # Check if container is running before attempting to restart
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if check_container_running():
            # Restart the container
            logger.info("Restarting supportbot container...")
            subprocess.run(["docker", "compose", "restart", "supportbot"], cwd=root_dir, check=True)
            
            # Wait for container to restart
            logger.info("Waiting for container to restart...")
            await asyncio.sleep(15)
            
            # Verify containers are running after restart
            if not check_container_running():
                logger.error("Container failed to restart")
                return False
        else:
            logger.warning("Container is not running, skipping restart")
            logger.info("Starting containers with updated environment variables...")
            subprocess.run(["docker", "compose", "up", "-d"], cwd=root_dir, check=True)
            logger.info("Waiting for containers to start...")
            await asyncio.sleep(15)
        
        # Check webhook again
        logger.info("Verifying final webhook configuration...")
        webhook_info = await bot.get_webhook_info()
        
        if webhook_info.url == webhook_url:
            logger.info(f"✅ Success! Final webhook URL: {webhook_info.url}")
            
            # Send a test message to admin group
            admin_group_id = os.getenv("ADMIN_GROUP_ID")
            if admin_group_id:
                try:
                    await bot.send_message(
                        chat_id=admin_group_id,
                        text=f"🔄 Webhook updated to: {webhook_url}"
                    )
                    logger.info("Sent test message to admin group")
                except Exception as e:
                    logger.warning(f"Could not send test message: {e}")
            
            return True
        else:
            logger.error(f"❌ Webhook verification failed. Expected {webhook_url}, got {webhook_info.url}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        return False

async def main():
    success = await update_webhook()
    if not success:
        logger.error("Webhook update failed")
        sys.exit(1)
    
if __name__ == "__main__":
    asyncio.run(main()) 