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
if WEBAPP_PUBLIC_URL:
    # Use explicitly provided public URL for webapp if available
    BASE_WEBAPP_URL = WEBAPP_PUBLIC_URL
elif os.getenv("ENVIRONMENT") == "development" and "ngrok" in RAILWAY_DOMAIN:
    # For local development with ngrok, use same domain but direct to webapp container
    BASE_WEBAPP_URL = f"http://localhost:3000"
elif os.getenv("ENVIRONMENT") == "development":
    # For local development without ngrok
    BASE_WEBAPP_URL = "http://localhost:3000"
else:
    # Production default
    BASE_WEBAPP_URL = "https://webapp-support-bot-production.up.railway.app"

def get_webapp_url():
    """Generate a versioned web app URL."""
    base_url = BASE_WEBAPP_URL
    
    # Add versioning parameters
    version_param = datetime.now().strftime('%Y%m%d%H%M%S')
    random_param = os.urandom(4).hex()
    
    # Always use the RAILWAY_PUBLIC_DOMAIN for WebApp URLs in development mode
    # with ngrok since Telegram requires HTTPS URLs for WebApps
    if os.getenv("ENVIRONMENT") == "development" and "ngrok" in RAILWAY_DOMAIN and not WEBAPP_PUBLIC_URL:
        # Use the same ngrok domain but with the webapp port
        return f"https://{RAILWAY_DOMAIN}/?v={version_param}&r={random_param}"
    
    return f"{base_url}/?v={version_param}&r={random_param}"

# Logging Configuration
LOG_LEVEL = "DEBUG"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Web app specific URL for forms
WEB_APP_URL = os.getenv("WEB_APP_URL", f"{BASE_WEBAPP_URL}/support-form.html")

# Rate limits
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))  # Default to 5 requests
RATE_LIMIT_TIME = int(os.getenv("RATE_LIMIT_TIME", "60"))  # Default to 60 seconds 