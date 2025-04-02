#!/usr/bin/env python
"""
Ngrok Link Update Script

This script automates the process of updating the ngrok URL in the project configuration
when a new ngrok tunnel is started. It:

1. Prompts the user for the new ngrok URL
2. Updates the .env file with the new URL (creates it if it doesn't exist)
3. Restarts the supportbot container
4. Sets the webhook with the new URL
5. Verifies the webhook was set correctly
"""

import os
import sys
import re
import subprocess
import logging
import time
from dotenv import load_dotenv

# Add parent directory to path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_env_file_if_missing(ngrok_url, domain):
    """Create a minimal .env file if it doesn't exist."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    
    # If .env file doesn't exist, create a minimal version
    if not os.path.exists(env_path):
        logger.info(f".env file not found at {env_path}, creating a new one")
        
        with open(env_path, 'w') as f:
            f.write(f"""# Bot configuration
SUPPORT_BOT_TOKEN=your_bot_token
WEBHOOK_URL=https://{domain}/webhook
PORT=8000

# Database configuration
DATABASE_URL=sqlite:///./app.db

# Admin configuration
ADMIN_GROUP_ID=-4771220922

# Web App URLs
RAILWAY_PUBLIC_DOMAIN={domain}
BASE_WEBAPP_URL={ngrok_url}
WEB_APP_URL={ngrok_url}/support-form.html

# Environment (development/production)
ENVIRONMENT=development
""")
        
        logger.info("Created new .env file with default values")
        logger.warning("Please update SUPPORT_BOT_TOKEN in the .env file with your actual token")
        return True
    
    return False

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
        # Get path to .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        
        # If .env file doesn't exist, create it
        if create_env_file_if_missing(ngrok_url, domain):
            # File was created, set environment variables and return
            os.environ['RAILWAY_PUBLIC_DOMAIN'] = domain
            os.environ['BASE_WEBAPP_URL'] = ngrok_url
            os.environ['WEB_APP_URL'] = f"{ngrok_url}/support-form.html"
            return True
        
        # Read current .env file
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
        
        # Check if the keys exist
        railway_domain_exists = any(line.strip().startswith('RAILWAY_PUBLIC_DOMAIN=') for line in env_lines)
        base_webapp_exists = any(line.strip().startswith('BASE_WEBAPP_URL=') for line in env_lines)
        web_app_exists = any(line.strip().startswith('WEB_APP_URL=') for line in env_lines)
        
        # Update the relevant lines
        updated_lines = []
        for line in env_lines:
            if line.strip().startswith('RAILWAY_PUBLIC_DOMAIN='):
                updated_lines.append(f'RAILWAY_PUBLIC_DOMAIN={domain}\n')
            elif line.strip().startswith('BASE_WEBAPP_URL='):
                updated_lines.append(f'BASE_WEBAPP_URL={ngrok_url}\n')
            elif line.strip().startswith('WEB_APP_URL='):
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
        import traceback
        logger.error(traceback.format_exc())
        return False

def restart_container():
    """Restart the supportbot container."""
    try:
        logger.info("Restarting supportbot container...")
        
        # Check if Docker is running
        check_docker = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True
        )
        
        if check_docker.returncode != 0:
            logger.warning("Docker doesn't seem to be running. Skipping container restart.")
            return True
        
        # Try different container name formats (handles different Docker Compose versions)
        container_names = ['supportbot', 'support-bot-supportbot-1']
        success = False
        
        for container_name in container_names:
            try:
                result = subprocess.run(
                    ['docker-compose', 'restart', container_name],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully restarted {container_name} container")
                    success = True
                    break
            except Exception:
                continue
        
        if not success:
            logger.warning("Could not restart container. This is not critical if you're not using Docker.")
            return True
            
        return True
    
    except Exception as e:
        logger.error(f"Error restarting container: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Continue anyway, as this is not critical for local development
        return True

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
        
        # Check for success in output
        if result.returncode == 0 and ("Webhook successfully set" in result.stdout or "✅ Webhook successfully set" in result.stdout):
            logger.info("Successfully set webhook")
            # Print the output for verification
            for line in result.stdout.split('\n'):
                if "Webhook successfully set to" in line:
                    logger.info(line.strip())
            return True
        else:
            logger.error(f"Failed to set webhook")
            logger.error(f"Output: {result.stdout}")
            logger.error(f"Error: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_webhook(ngrok_url):
    """Verify that the webhook was set correctly."""
    try:
        logger.info("Verifying webhook setup...")
        
        # Run the bot test script to check webhook status
        result = subprocess.run(
            [sys.executable, os.path.join('..', 'run_test.py'), 'bot'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, 
            text=True,
            env=os.environ.copy()
        )
        
        # Check if webhook is mentioned in the output
        webhook_url = f"https://{ngrok_url.replace('https://', '')}/webhook"
        if webhook_url in result.stdout and ("[SUCCESS] Webhook is set to" in result.stdout or "Webhook is set to" in result.stdout):
            logger.info("Webhook verification successful")
            return True
        else:
            logger.warning("Webhook verification unclear. Please check manually with 'python run_test.py bot'")
            return True  # Continue anyway
    except Exception as e:
        logger.error(f"Error verifying webhook: {e}")
        return False

def main():
    """Main function to run the script."""
    print("=== Ngrok Link Update Utility ===")
    print("This script will update your configuration with a new ngrok URL")
    print("and restart the necessary services.")
    print("\nPlease enter the full HTTPS ngrok URL (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app):")
    
    # Look for command line argument first
    if len(sys.argv) > 1 and "ngrok-free.app" in sys.argv[1]:
        ngrok_url = sys.argv[1]
        print(f"> {ngrok_url} (from command line)")
    else:
        ngrok_url = input("> ").strip()
    
    # Validate input
    if not ngrok_url.startswith("https://") or not "ngrok-free.app" in ngrok_url:
        logger.error("Invalid ngrok URL. Please enter a valid HTTPS ngrok URL.")
        return 1
    
    # Update the environment file
    if not update_env_file(ngrok_url):
        logger.error("Failed to update environment file. Aborting.")
        return 1
    
    # Restart the container (but continue if it fails)
    restart_container()
    
    # Allow some time for container to start
    print("Waiting for container to start...")
    time.sleep(5)
    
    # Set the webhook
    if not set_webhook():
        logger.warning("Failed to set webhook automatically. Trying direct method...")
        
        # Try to set it with the bot test script
        try:
            result = subprocess.run(
                [sys.executable, os.path.join('..', 'run_test.py'), 'webhook-set'],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )
            if "webhook set" in result.stdout.lower():
                logger.info("Successfully set webhook using alternative method")
            else:
                logger.error("Failed to set webhook. Please run 'python run_test.py webhook-set' manually.")
                return 1
        except Exception as e:
            logger.error(f"Error running webhook-set: {e}")
            logger.error("Failed to set webhook. Please run 'python run_test.py webhook-set' manually.")
            return 1
    
    # Verify the webhook was set correctly
    if not verify_webhook(ngrok_url):
        logger.warning("Could not verify webhook status. Please check manually.")
    
    # Test bot connection
    print("\nTesting bot connection...")
    try:
        result = subprocess.run(
            [sys.executable, os.path.join('..', 'run_test.py'), 'bot'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except Exception as e:
        logger.error(f"Error testing bot connection: {e}")
    
    print("\n=== Update Complete ===")
    print(f"Your bot is now configured to use: {ngrok_url}")
    print("Try sending /start or /request to your bot to verify everything works!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 