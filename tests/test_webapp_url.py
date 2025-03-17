import os
import logging
import sys
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

# Add parent directory to path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_webapp_url():
    """Test the WebApp URL configuration and accessibility."""
    # Load environment variables
    load_dotenv()
    
    # Get BASE_WEBAPP_URL
    base_url = os.getenv("BASE_WEBAPP_URL")
    if not base_url:
        logger.error("BASE_WEBAPP_URL not found in environment variables")
        return False
    
    # Construct URLs for testing
    chat_url = f"{base_url}/chat.html"
    support_form_url = f"{base_url}/support-form.html"
    
    # Check if the URLs are properly formatted
    try:
        parsed_base = urlparse(base_url)
        if not parsed_base.scheme or not parsed_base.netloc:
            logger.error(f"❌ Invalid BASE_WEBAPP_URL format: {base_url}")
            return False
        
        logger.info(f"✅ BASE_WEBAPP_URL format is valid: {base_url}")
        
        # Check if the scheme is HTTPS (required for production)
        if parsed_base.scheme != "https" and os.getenv("ENVIRONMENT") != "development":
            logger.warning(f"⚠️ BASE_WEBAPP_URL does not use HTTPS: {base_url}")
            logger.warning("Telegram requires HTTPS for WebApps in production.")
    except Exception as e:
        logger.error(f"❌ Error parsing WebApp URL: {e}")
        return False
    
    # Test if the URLs are accessible
    urls_to_test = [
        ("Base WebApp URL", base_url),
        ("Chat HTML", chat_url),
        ("Support Form HTML", support_form_url)
    ]
    
    all_urls_accessible = True
    
    for name, url in urls_to_test:
        try:
            # Make a HEAD request to check if the URL is accessible
            response = requests.head(url, timeout=5)
            if response.status_code < 400:
                logger.info(f"✅ {name} is accessible: {url}")
            else:
                logger.error(f"❌ {name} returned status code {response.status_code}: {url}")
                all_urls_accessible = False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {name} is not accessible: {url}")
            logger.error(f"  Error: {e}")
            all_urls_accessible = False
    
    # Check integration in config.py
    env = os.getenv("ENVIRONMENT", "not set")
    logger.info(f"Current environment: {env}")
    
    if env == "development":
        logger.info("Development environment: BASE_WEBAPP_URL in config.py should be set to localhost or ngrok URL")
    else:
        logger.info("Production environment: BASE_WEBAPP_URL in config.py should be set to production URL")
    
    # Print configuration suggestion
    logger.info("\nConfiguration for .env file:")
    logger.info(f"BASE_WEBAPP_URL={base_url}")
    logger.info(f"WEB_APP_URL={support_form_url}")
    
    return all_urls_accessible

if __name__ == "__main__":
    logger.info("Testing WebApp URL configuration...")
    
    # Run the test
    result = test_webapp_url()
    
    if result:
        logger.info("✅ WebApp URL tests completed successfully")
    else:
        logger.error("❌ WebApp URL tests failed") 