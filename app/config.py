import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: SUPPORT_BOT_TOKEN is not set. Please add it to environment variables.")

# Connection Pool Configuration
MAX_CONNECTIONS = 10  # Maximum number of connections in the pool
POOL_TIMEOUT = 30    # Connection pool timeout in seconds

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Admin Configuration
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-4771220922")

# URLs
RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if not RAILWAY_DOMAIN:
    raise ValueError("Error: RAILWAY_PUBLIC_DOMAIN is not set. Please add it to environment variables.")

WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}/webhook"

# WebApp URLs - prioritize WEBAPP_PUBLIC_URL if set
WEBAPP_PUBLIC_URL = os.getenv("WEBAPP_PUBLIC_URL")

# Set BASE_WEBAPP_URL based on environment and available URLs
BASE_WEBAPP_URL = os.getenv("BASE_WEBAPP_URL")
if not BASE_WEBAPP_URL:
    if WEBAPP_PUBLIC_URL:
        # Use explicitly provided public URL for webapp if available
        BASE_WEBAPP_URL = WEBAPP_PUBLIC_URL
    elif os.getenv("ENVIRONMENT") == "development" and "ngrok" in RAILWAY_DOMAIN:
        # For local development with ngrok, use ngrok domain
        BASE_WEBAPP_URL = f"https://{RAILWAY_DOMAIN}"
    elif os.getenv("ENVIRONMENT") == "development":
        # For local development without ngrok
        BASE_WEBAPP_URL = "http://localhost:3000"
    else:
        # Production default
        BASE_WEBAPP_URL = "https://webapp-support-bot-production.up.railway.app"

# Ensure BASE_WEBAPP_URL is a proper URL that works with Telegram WebApp
if not BASE_WEBAPP_URL.startswith(("http://", "https://")):
    # Add protocol if missing
    BASE_WEBAPP_URL = f"https://{BASE_WEBAPP_URL}"

# For Telegram WebApp, we must use HTTPS
if "telegram" in os.getenv("ENVIRONMENT", "").lower() and not BASE_WEBAPP_URL.startswith("https://"):
    # Force HTTPS for Telegram WebApp
    BASE_WEBAPP_URL = BASE_WEBAPP_URL.replace("http://", "https://")

print(f"Using BASE_WEBAPP_URL: {BASE_WEBAPP_URL}")

# Web app specific URL for forms
WEB_APP_URL = os.getenv("WEB_APP_URL", f"{BASE_WEBAPP_URL}/support-form.html")

def get_webapp_url():
    """Generate a clean web app URL that's compatible with Telegram WebApp requirements."""
    base_url = BASE_WEBAPP_URL
    
    # Always ensure we have HTTPS for Telegram WebApps
    if not base_url.startswith("https://"):
        base_url = base_url.replace("http://", "https://")
    
    # For public groups, we need to use the most stable, clean URL possible
    # Avoid query parameters and ensure we're using a specific HTML file
    if WEB_APP_URL and WEB_APP_URL.endswith(".html"):
        # Use the explicit HTML file path if configured
        return WEB_APP_URL
    
    # Default to the support form if no specific URL is configured
    # No query parameters or versioning for maximum compatibility
    return f"{base_url}/support-form.html"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '''
[%(asctime)s] %(levelname)s:
  Source: %(name)s
  Message: %(message)s
'''

# Rate limits
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))  # Default to 5 requests
RATE_LIMIT_TIME = int(os.getenv("RATE_LIMIT_TIME", "60"))  # Default to 60 seconds 