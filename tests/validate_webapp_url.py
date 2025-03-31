#!/usr/bin/env python3
"""
Validate WebApp URL Test Script

This script tests the validity of the WebApp URL according to Telegram's requirements:
1. URL must be HTTPS
2. URL must be properly formatted
3. URL must be accessible

Usage:
    python validate_webapp_url.py

"""

import os
import sys
import logging
import requests
import re
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('url-validator')

def validate_webapp_url(url):
    """Validate a URL according to Telegram WebApp requirements."""
    # Check if URL is None or empty
    if not url:
        logger.error("❌ URL is empty or None")
        return False
    
    # Check if URL starts with https://
    if not url.startswith("https://"):
        logger.error(f"❌ URL does not use HTTPS: {url}")
        return False
    
    # Parse URL to check format
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            logger.error(f"❌ Invalid URL format: {url}")
            return False
    except Exception as e:
        logger.error(f"❌ URL parsing error: {e}")
        return False
    
    # Check for valid domain format (no IP addresses allowed by Telegram)
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', parsed.netloc):
        logger.error(f"❌ IP addresses not allowed for WebApp URLs: {parsed.netloc}")
        return False
    
    # Additional Telegram checks:
    # - No localhost in production
    if "localhost" in parsed.netloc or "127.0.0.1" in parsed.netloc:
        logger.warning(f"⚠️ Localhost URLs won't work in production: {url}")
    
    # Check if URL is accessible (optional but helpful)
    try:
        response = requests.head(url, timeout=5)
        if response.status_code >= 400:
            logger.warning(f"⚠️ URL returned status code {response.status_code}: {url}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️ Could not connect to URL: {e}")
    
    logger.info(f"✅ URL format is valid: {url}")
    return True

def check_env_webapp_urls():
    """Check all WebApp URLs from environment variables."""
    base_url = os.getenv("BASE_WEBAPP_URL")
    web_app_url = os.getenv("WEB_APP_URL")
    
    logger.info("=== Checking WebApp URLs ===")
    logger.info(f"BASE_WEBAPP_URL={base_url}")
    logger.info(f"WEB_APP_URL={web_app_url}")
    
    # Check BASE_WEBAPP_URL
    if base_url:
        logger.info("\n--- Validating BASE_WEBAPP_URL ---")
        base_valid = validate_webapp_url(base_url)
    else:
        logger.error("❌ BASE_WEBAPP_URL is not set")
        base_valid = False
    
    # Check WEB_APP_URL
    if web_app_url:
        logger.info("\n--- Validating WEB_APP_URL ---")
        webapp_valid = validate_webapp_url(web_app_url)
    else:
        logger.error("❌ WEB_APP_URL is not set")
        webapp_valid = False
    
    # Check generated URLs
    if base_url:
        logger.info("\n--- Validating generated URLs ---")
        # Support form URL
        support_form_url = f"{base_url}/support-form.html?user_id=12345"
        logger.info(f"Support Form URL: {support_form_url}")
        validate_webapp_url(support_form_url)
        
        # Chat URL
        chat_url = f"{base_url}/chat.html?request_id=67890&admin_id=54321"
        logger.info(f"Chat URL: {chat_url}")
        validate_webapp_url(chat_url)
    
    return base_valid and webapp_valid

if __name__ == "__main__":
    logger.info("Starting WebApp URL validation")
    
    # Check for .env file and load it if exists
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_file):
        logger.info(f"Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # Run validation
    result = check_env_webapp_urls()
    
    # Print summary
    logger.info("\n=== Validation Summary ===")
    if result:
        logger.info("✅ All WebApp URLs are valid")
        sys.exit(0)
    else:
        logger.error("❌ Some WebApp URLs are invalid")
        logger.info("\nImportant Notes for WebApp URLs:")
        logger.info("1. URLs MUST start with https:// (Telegram requirement)")
        logger.info("2. URLs must be publicly accessible")
        logger.info("3. IP addresses are not allowed (must use domain names)")
        logger.info("4. Localhost won't work in production")
        sys.exit(1) 