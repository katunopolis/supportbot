#!/usr/bin/env python
"""
Ngrok Link Update Script

This script automates the process of updating the ngrok URL in the project configuration:
1. Prompts the user for the new ngrok URL
2. Updates the .env file with the new URL (creates it if it doesn't exist)
3. Restarts the supportbot container
4. Sets the webhook with the new URL
5. Verifies the webhook configuration
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

def validate_ngrok_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate the ngrok URL format and accessibility."""
    if not url.startswith("https://") or "ngrok-free.app" not in url:
        return False, "Invalid ngrok URL format. Must start with https:// and contain ngrok-free.app"
    
    try:
        response = httpx.get(f"{url}/webhook", timeout=5.0)
        if response.status_code not in [200, 404, 405]:
            return False, f"Webhook endpoint returned status code {response.status_code}"
    except Exception as e:
        return False, f"Webhook endpoint is not accessible: {str(e)}"
    
    return True, None

def update_env_file(ngrok_url: str) -> Tuple[bool, Optional[str]]:
    """Update the .env file with the new ngrok URL."""
    domain_match = re.match(r'https?://([\w\.-]+)', ngrok_url)
    if not domain_match:
        return False, "Invalid ngrok URL format. Expected format: https://xxxx-xx-xx.ngrok-free.app"
    
    domain = domain_match.group(1)
    logger.info(f"Extracted domain: {domain}")
    
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

        if create_env_file_if_missing(ngrok_url, domain):
            os.environ['RAILWAY_PUBLIC_DOMAIN'] = domain
            os.environ['BASE_WEBAPP_URL'] = ngrok_url
            os.environ['WEB_APP_URL'] = f"{ngrok_url}/support-form.html"
            return True, None

        with open(env_path, 'r') as f:
            env_lines = f.readlines()
        
        keys = {
            'RAILWAY_PUBLIC_DOMAIN': domain,
            'BASE_WEBAPP_URL': ngrok_url,
            'WEB_APP_URL': f"{ngrok_url}/support-form.html"
        }

        updated_lines = []
        existing_keys = {key: False for key in keys}

        for line in env_lines:
            matched = False
            for key, value in keys.items():
                if line.strip().startswith(f"{key}="):
                    updated_lines.append(f"{key}={value}\n")
                    existing_keys[key] = True
                    matched = True
                    break
            if not matched:
                updated_lines.append(line)

        for key, exists in existing_keys.items():
            if not exists:
                updated_lines.append(f"{key}={keys[key]}\n")

        with open(env_path, 'w') as f:
            f.writelines(updated_lines)

        for key, value in keys.items():
            os.environ[key] = value

        logger.info("Successfully updated .env file")
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
        return False, f"Failed to restart container: {result.stderr}"
    except Exception as e:
        return False, f"Error restarting container: {str(e)}"

def verify_container_health(max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Verify container is up and responding."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps', 'supportbot'],
                capture_output=True,
                text=True
            )
            if "running" not in result.stdout.lower():
                return False, "Container is not running"

            response = httpx.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                return True, None
            time.sleep(2)
        except Exception as e:
            if attempt == max_retries - 1:
                return False, f"Container health check failed: {str(e)}"
            time.sleep(2)
    return False, "Container health check failed after retries"

def set_webhook(ngrok_url: str, max_retries: int = 3) -> Tuple[bool, Optional[str]]:
    """Set the webhook for the bot."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Setting webhook (attempt {attempt + 1})...")
            env = os.environ.copy()
            result = subprocess.run(
                [sys.executable, 'test_webhook_setup.py', '--action', 'set'],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode == 0 and f"{ngrok_url}/webhook" in result.stdout:
                logger.info("Webhook successfully set")
                return True, None
            time.sleep(2)
        except Exception as e:
            if attempt == max_retries - 1:
                return False, f"Webhook setting failed: {str(e)}"
            time.sleep(2)
    return False, "Failed to set webhook"

def verify_webhook_config(ngrok_url: str) -> Tuple[bool, Optional[str]]:
    """Verify that the webhook was configured correctly via Telegram API."""
    try:
        load_dotenv()
        token = os.getenv("SUPPORT_BOT_TOKEN")
        if not token:
            return False, "Missing SUPPORT_BOT_TOKEN in environment"

        response = httpx.post(
            f"https://api.telegram.org/bot{token}/getWebhookInfo",
            timeout=10.0
        )
        if response.status_code == 200:
            webhook_info = response.json()
            expected = f"{ngrok_url}/webhook"
            actual = webhook_info.get("result", {}).get("url")
            if actual == expected:
                return True, None
            return False, f"Expected {expected}, got {actual}"
        return False, f"API error: {response.text}"
    except Exception as e:
        return False, f"Error verifying webhook: {str(e)}"

def main():
    print("=== Ngrok Link Update Utility ===")
    print("Please enter the full HTTPS ngrok URL (e.g., https://xxxx-xx.ngrok-free.app):")

    if len(sys.argv) > 1 and "ngrok-free.app" in sys.argv[1]:
        ngrok_url = sys.argv[1]
        print(f"> {ngrok_url} (from command line)")
    else:
        ngrok_url = input("> ").strip()

    is_valid, error = validate_ngrok_url(ngrok_url)
    if not is_valid:
        logger.error(error)
        return 1

    success, error = update_env_file(ngrok_url)
    if not success:
        logger.error(error)
        return 1

    success, error = restart_container()
    if not success:
        logger.error(error)
        return 1

    print("Waiting for container to initialize...")
    time.sleep(5)
    success, error = verify_container_health()
    if not success:
        logger.error(error)
        return 1

    success, error = set_webhook(ngrok_url)
    if not success:
        logger.error(error)
        return 1

    success, error = verify_webhook_config(ngrok_url)
    if not success:
        logger.error(error)
        return 1

    print("\n✅ Update complete! Your bot is now connected to:")
    print(ngrok_url)
    print("Try sending /start to your bot to verify it's alive.")
    return 0

if __name__ == "__main__":
    sys.exit(main())