#!/usr/bin/env python
"""
Container Webhook Update

This script directly executes a webhook update command inside the supportbot container
to ensure the internal configuration is updated.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def update_webhook_in_container():
    """Update webhook inside the container."""
    try:
        # Get the new ngrok URL
        ngrok_url = input("Enter the current ngrok URL (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app): ").strip()
        
        if not ngrok_url.startswith("https://") or not "ngrok-free.app" in ngrok_url:
            logger.error("Invalid ngrok URL format.")
            return False
            
        domain = ngrok_url.replace("https://", "")
        
        # Execute command inside container
        cmd = [
            "docker", "exec", "support-bot-supportbot-1", 
            "python", "-c", 
            f"""
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def update_webhook():
    # Update environment variables in container
    os.environ['RAILWAY_PUBLIC_DOMAIN'] = '{domain}'
    os.environ['BASE_WEBAPP_URL'] = '{ngrok_url}'
    os.environ['WEB_APP_URL'] = '{ngrok_url}/support-form.html'
    
    # Get bot token from environment 
    load_dotenv()
    token = os.getenv('SUPPORT_BOT_TOKEN')
    
    if not token:
        print("Error: Bot token not found")
        return False
        
    # Delete and set webhook
    webhook_url = '{ngrok_url}/webhook'
    
    try:
        bot = Bot(token=token)
        print(f"Setting webhook to: {{webhook_url}}")
        
        # Delete any existing webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("Deleted existing webhook")
        
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
            print(f"✅ Webhook successfully set to: {{webhook_url}}")
            return True
        else:
            print(f"❌ Webhook URL mismatch. Set to {{webhook_info.url}} instead of {{webhook_url}}")
            return False
            
    except Exception as e:
        print(f"Error: {{e}}")
        return False

asyncio.run(update_webhook())
            """
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("\n--- Output from container ---")
        print(result.stdout)
        
        if result.stderr:
            print("\n--- Errors ---")
            print(result.stderr)
            
        if "Webhook successfully set" in result.stdout:
            logger.info("Webhook successfully updated inside container")
            return True
        else:
            logger.error("Failed to update webhook inside container")
            return False
            
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        return False

def main():
    """Main function to execute the script."""
    print("=== Container Webhook Update Utility ===")
    print("This utility will update the webhook configuration directly inside the container.")
    print("Make sure your ngrok tunnel is running and the URL is correct.\n")
    
    success = update_webhook_in_container()
    
    if success:
        print("\n=== Webhook Update Complete ===")
        print("Try sending /start or /request to your bot to verify everything works!")
    else:
        print("\n=== Webhook Update Failed ===")
        print("Check the logs for errors and try again.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 