#!/usr/bin/env python
"""
Ngrok Link Update Script

This script automates the process of updating the ngrok URL in the project configuration
when a new ngrok tunnel is started. It:

1. Prompts the user for the new ngrok URL
2. Updates the .env file with the new URL
3. Restarts the supportbot container
4. Sets the webhook with the new URL
5. Verifies the configuration
"""

import os
import sys
import re
import subprocess
import logging
import time
import httpx
from dotenv import load_dotenv
from typing import Optional, Tuple

# Add parent directory to path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def validate_ngrok_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate the ngrok URL format and accessibility."""
    # Check URL format
    if not url.startswith("https://") or not "ngrok-free.app" in url:
        return False, "Invalid ngrok URL format. Must start with https:// and contain ngrok-free.app"
    
    # Check if webhook endpoint is accessible
    try:
        response = httpx.get(f"{url}/webhook", timeout=5.0)
        if response.status_code not in [200, 404, 405]:  # 404/405 are acceptable as they indicate the endpoint exists
            return False, f"Webhook endpoint returned status code {response.status_code}"
    except Exception as e:
        return False, f"Webhook endpoint is not accessible: {str(e)}"
    
    return True, None

def update_env_file(ngrok_url: str) -> Tuple[bool, Optional[str]]:
    """Update the .env file with the new ngrok URL."""
    # Get the domain without https:// prefix
    domain_match = re.match(r'https?://([\w\.-]+)', ngrok_url)
    if not domain_match:
        return False, "Invalid ngrok URL format. Expected format: https://xxxx-xx-xx-xx-xx.ngrok-free.app"
    
    domain = domain_match.group(1)
    logger.info(f"Extracted domain: {domain}")
    
    try:
        # Read current .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if not os.path.exists(env_path):
            return False, f".env file not found at {env_path}"
        
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
        return True, None
    
    except Exception as e:
        return False, f"Error updating .env file: {str(e)}"

def restart_container() -> Tuple[bool, Optional[str]]:
    """Restart the supportbot container."""
    try:
        logger.info("Restarting supportbot container...")
        result = subprocess.run(
            ['docker', 'compose', 'restart', 'supportbot'],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Successfully restarted supportbot container")
            return True, None
        else:
            return False, f"Failed to restart container: {result.stderr}"
    
    except Exception as e:
        return False, f"Error restarting container: {str(e)}"

def verify_container_health(max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Verify that the container is healthy and responding."""
    for attempt in range(max_retries):
        try:
            # Check if container is running
            result = subprocess.run(
                ['docker', 'compose', 'ps', 'supportbot'],
                capture_output=True,
                text=True
            )
            if "running" not in result.stdout.lower():
                return False, "Container is not running"
            
            # Check if the API is responding
            response = httpx.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                return True, None
                
            time.sleep(2)  # Wait before retry
            
        except Exception as e:
            if attempt == max_retries - 1:
                return False, f"Container health check failed: {str(e)}"
            time.sleep(2)
    
    return False, "Container health check failed after maximum retries"

def set_webhook(ngrok_url: str, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Set the webhook with the new ngrok URL."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Setting webhook (attempt {attempt + 1}/{max_retries})...")
            
            # Get the current environment
            env = os.environ.copy()
            
            # Make sure our updated environment variables are included
            if 'RAILWAY_PUBLIC_DOMAIN' not in env:
                return False, "RAILWAY_PUBLIC_DOMAIN not set in environment"
                
            # Run the webhook setup script with our environment
            result = subprocess.run(
                [sys.executable, 'test_webhook_setup.py', '--action', 'set'],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                # Verify webhook was set correctly
                webhook_url = f"{ngrok_url}/webhook"
                if "Webhook successfully set to" in result.stdout and webhook_url in result.stdout:
                    logger.info("Successfully set webhook")
                    return True, None
                else:
                    if attempt < max_retries - 1:
                        logger.warning("Webhook verification failed, retrying...")
                        time.sleep(2)
                        continue
                    return False, "Webhook verification failed"
            else:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to set webhook (attempt {attempt + 1}), retrying...")
                    time.sleep(2)
                    continue
                return False, f"Failed to set webhook: {result.stderr}"
        
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error setting webhook (attempt {attempt + 1}), retrying...")
                time.sleep(2)
                continue
            return False, f"Error setting webhook: {str(e)}"
    
    return False, "Failed to set webhook after maximum retries"

def verify_webhook_config(ngrok_url: str) -> Tuple[bool, Optional[str]]:
    """Verify the final webhook configuration."""
    try:
        # Get bot token from environment
        load_dotenv()
        token = os.getenv('SUPPORT_BOT_TOKEN')
        if not token:
            return False, "Bot token not found in environment"
        
        # Check webhook configuration
        webhook_url = f"{ngrok_url}/webhook"
        with httpx.Client() as client:
            response = client.post(
                f"https://api.telegram.org/bot{token}/getWebhookInfo",
                timeout=10.0
            )
            if response.status_code == 200:
                webhook_info = response.json()
                if webhook_info.get('result', {}).get('url') == webhook_url:
                    return True, None
                else:
                    return False, f"Webhook URL mismatch. Expected {webhook_url}, got {webhook_info.get('result', {}).get('url')}"
            else:
                return False, f"Failed to get webhook info: {response.text}"
    
    except Exception as e:
        return False, f"Error verifying webhook configuration: {str(e)}"

def main():
    """Main function to run the script."""
    print("=== Ngrok Link Update Utility ===")
    print("This script will update your configuration with a new ngrok URL")
    print("and restart the necessary services.")
    print("\nPlease enter the full HTTPS ngrok URL (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app):")
    
    ngrok_url = input("> ").strip()
    
    # Validate input
    is_valid, error_msg = validate_ngrok_url(ngrok_url)
    if not is_valid:
        logger.error(error_msg)
        return 1
    
    # Update the environment file
    success, error_msg = update_env_file(ngrok_url)
    if not success:
        logger.error(error_msg)
        return 1
    
    # Restart the container
    success, error_msg = restart_container()
    if not success:
        logger.error(error_msg)
        return 1
    
    # Wait for container to start and verify health
    print("Waiting for container to start...")
    time.sleep(5)
    success, error_msg = verify_container_health()
    if not success:
        logger.error(error_msg)
        return 1
    
    # Set the webhook
    success, error_msg = set_webhook(ngrok_url)
    if not success:
        logger.error(error_msg)
        return 1
    
    # Verify final webhook configuration
    success, error_msg = verify_webhook_config(ngrok_url)
    if not success:
        logger.error(error_msg)
        return 1
    
    print("\n=== Update Complete ===")
    print(f"Your bot is now configured to use: {ngrok_url}")
    print("Try sending /start or /request to your bot to verify everything works!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 