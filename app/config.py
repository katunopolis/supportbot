import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: SUPPORT_BOT_TOKEN is not set. Please add it to environment variables.")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Error: DATABASE_URL is not set. Please add it to environment variables.")

# Admin Configuration
ADMIN_GROUP_ID = -4771220922

# URLs
RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if not RAILWAY_DOMAIN:
    raise ValueError("Error: RAILWAY_PUBLIC_DOMAIN is not set. Please add it to environment variables.")

WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}/webhook"
BASE_WEBAPP_URL = "https://webapp-support-bot-production.up.railway.app"

def get_webapp_url():
    """Generate a versioned web app URL."""
    return f"{BASE_WEBAPP_URL}/?v={datetime.now().strftime('%Y%m%d%H%M%S')}&r={os.urandom(4).hex()}"

# Logging Configuration
LOG_LEVEL = "DEBUG"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s' 