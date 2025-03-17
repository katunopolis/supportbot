import os
import webbrowser
import logging
import sys
from urllib.parse import urlencode
from dotenv import load_dotenv

# Add parent directory to path so we can import from the app package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_local_webapp():
    """Test the locally running WebApp."""
    # Load environment variables
    load_dotenv()
    
    # Local WebApp URL
    local_webapp_url = "http://localhost:3000"
    
    # Test URLs
    support_form_url = f"{local_webapp_url}/support-form.html"
    chat_url = f"{local_webapp_url}/chat.html"
    
    # Print current configuration
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'not set')}")
    logger.info(f"Current BASE_WEBAPP_URL: {os.getenv('BASE_WEBAPP_URL', 'not set')}")
    logger.info(f"For local testing, using: {local_webapp_url}")
    
    # Test the URLs
    logger.info("\nTesting WebApp URLs:")
    logger.info(f"- Support Form: {support_form_url}")
    logger.info(f"- Chat Interface: {chat_url}")
    
    # Simulate Telegram WebApp parameters
    # These are normally provided by Telegram when the WebApp is opened
    # For testing, we're simulating them
    test_params = {
        "userId": "12345678",
        "requestId": "1", # Use an existing request ID from your database
        "adminId": "98765432",
        "tgWebAppData": "test_data_placeholder",
        "test_mode": "true"
    }
    
    # Create test URLs with parameters
    test_support_form_url = f"{support_form_url}?{urlencode(test_params)}"
    test_chat_url = f"{chat_url}?{urlencode(test_params)}"
    
    # Ask user which URL to open
    print("\nWhich page would you like to test?")
    print("1. Support Request Form")
    print("2. Chat Interface")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        logger.info(f"Opening Support Form in browser: {test_support_form_url}")
        webbrowser.open(test_support_form_url)
    elif choice == "2":
        logger.info(f"Opening Chat Interface in browser: {test_chat_url}")
        webbrowser.open(test_chat_url)
    else:
        logger.error("Invalid choice. Please enter 1 or 2.")
    
    # Instructions for testing
    print("\n=== WebApp Testing Instructions ===")
    print("1. The WebApp should open in your browser")
    print("2. For the Support Form:")
    print("   - Fill out the form and submit")
    print("   - Check if you receive notification in the admin group")
    print("3. For the Chat Interface:")
    print("   - Test sending messages")
    print("   - Verify if messages appear in the UI")
    print("   - Check if messages are stored in the database")
    print("\nNote: This is a local test only. In production, the WebApp must be served over HTTPS.")

if __name__ == "__main__":
    logger.info("Starting local WebApp test...")
    test_local_webapp() 