#!/usr/bin/env python
"""
Ngrok Link Update Script

This script automates the process of updating the ngrok URL in the project configuration
when a new ngrok tunnel is started. It:

1. Prompts the user for the new ngrok URL
2. Updates the .env file with the new URL
3. Restarts the supportbot container
4. Sets the webhook with the new URL
"""

import os
import sys
import re
import subprocess
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def update_env_file(ngrok_url):
    """Update the .env file with the new ngrok URL."""
    # Get the domain without https:// prefix
    domain_match = re.match(r'https?://([\w\.-]+)', ngrok_url)
    if not domain_match:
        logger.error("Invalid ngrok URL format. Expected format: https://xxxx-xx-xx-xx-xx.ngrok-free.app")
        return False
    
    domain = domain_match.group(1)
    logger.info(f"Extracted domain: {domain}")
    
    try:
        # Read current .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if not os.path.exists(env_path):
            logger.error(f".env file not found at {env_path}")
            return False
        
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
        
        # Check if the keys exist
        railway_domain_exists = any(line.startswith('RAILWAY_PUBLIC_DOMAIN=') for line in env_lines)
        base_webapp_exists = any(line.startswith('BASE_WEBAPP_URL=') for line in env_lines)
        web_app_exists = any(line.startswith('WEB_APP_URL=') for line in env_lines)
        
        # Update the relevant lines
        updated_lines = []
        for line in env_lines:
            if line.startswith('RAILWAY_PUBLIC_DOMAIN='):
                updated_lines.append(f'RAILWAY_PUBLIC_DOMAIN={domain}\n')
            elif line.startswith('BASE_WEBAPP_URL='):
                updated_lines.append(f'BASE_WEBAPP_URL={ngrok_url}\n')
            elif line.startswith('WEB_APP_URL='):
                updated_lines.append(f'WEB_APP_URL={ngrok_url}/support-form.html\n')
            else:
                updated_lines.append(line)
        
        # Add missing keys if they don't exist
        if not railway_domain_exists:
            updated_lines.append(f'\n# Ngrok configuration\nRAILWAY_PUBLIC_DOMAIN={domain}\n')
        if not base_webapp_exists:
            updated_lines.append(f'BASE_WEBAPP_URL={ngrok_url}\n')
        if not web_app_exists:
            updated_lines.append(f'WEB_APP_URL={ngrok_url}/support-form.html\n')
        
        # Write updated content back to .env file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        logger.info(f"Updated .env file with new ngrok URL: {ngrok_url}")
        # Also set environment variables for current process
        os.environ['RAILWAY_PUBLIC_DOMAIN'] = domain
        os.environ['BASE_WEBAPP_URL'] = ngrok_url
        os.environ['WEB_APP_URL'] = f"{ngrok_url}/support-form.html"
        return True
    
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        return False

def restart_container():
    """Restart the supportbot container."""
    try:
        logger.info("Restarting supportbot container...")
        result = subprocess.run(
            ['docker-compose', 'restart', 'supportbot'],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Successfully restarted supportbot container")
            return True
        else:
            logger.error(f"Failed to restart container: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error restarting container: {e}")
        return False

def set_webhook():
    """Set the webhook with the new ngrok URL."""
    try:
        logger.info("Setting webhook...")
        
        # Get the current environment
        env = os.environ.copy()
        
        # Make sure our updated environment variables are included
        if 'RAILWAY_PUBLIC_DOMAIN' not in env:
            logger.error("RAILWAY_PUBLIC_DOMAIN not set in environment. Cannot continue.")
            return False
            
        # Run the webhook setup script with our environment
        result = subprocess.run(
            [sys.executable, 'test_webhook_setup.py', '--action', 'set'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            env=env  # Pass the environment variables
        )
        
        if result.returncode == 0:
            logger.info("Successfully set webhook")
            # Print the output for verification
            for line in result.stdout.split('\n'):
                if "Webhook successfully set to" in line:
                    logger.info(line.strip())
            return True
        else:
            logger.error(f"Failed to set webhook: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False

def main():
    """Main function to run the script."""
    print("=== Ngrok Link Update Utility ===")
    print("This script will update your configuration with a new ngrok URL")
    print("and restart the necessary services.")
    print("\nPlease enter the full HTTPS ngrok URL (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app):")
    
    ngrok_url = input("> ").strip()
    
    # Validate input
    if not ngrok_url.startswith("https://") or not "ngrok-free.app" in ngrok_url:
        logger.error("Invalid ngrok URL. Please enter a valid HTTPS ngrok URL.")
        return 1
    
    # Update the environment file
    if not update_env_file(ngrok_url):
        logger.error("Failed to update environment file. Aborting.")
        return 1
    
    # Restart the container
    if not restart_container():
        logger.error("Failed to restart container. Please restart it manually.")
        return 1
    
    # Allow some time for container to start
    print("Waiting for container to start...")
    import time
    time.sleep(5)
    
    # Set the webhook
    if not set_webhook():
        logger.error("Failed to set webhook. Please run 'python run_test.py webhook-set' manually.")
        return 1
        
    # Update webhook directly inside the container
    print("\nUpdating webhook inside the container...")
    domain = ngrok_url.replace("https://", "")
    webhook_cmd = [
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
    
    try:
        result = subprocess.run(webhook_cmd, capture_output=True, text=True)
        if "Webhook successfully set" in result.stdout:
            logger.info("Successfully updated webhook inside the container")
        else:
            logger.warning("Failed to update webhook inside the container")
            if result.stderr:
                logger.warning(f"Error: {result.stderr}")
    except Exception as e:
        logger.warning(f"Error running webhook update in container: {e}")
    
    # Test bot connection
    print("\nTesting bot connection...")
    result = subprocess.run(
        [sys.executable, 'test_bot_connection.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=False
    )
    
    print("\n=== Update Complete ===")
    print(f"Your bot is now configured to use: {ngrok_url}")
    print("Try sending /start or /request to your bot to verify everything works!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 