# Local Testing for Telegram Bot Integration

This document provides guidance on how to test the Telegram bot integration in your local development environment.

## Prerequisites

1. A Telegram bot token (from [@BotFather](https://t.me/BotFather))
2. [ngrok](https://ngrok.com/) or another tunneling service installed
3. Python 3.9+ with required dependencies installed

## Setup Steps

### 1. Configure Local Environment

Create a `.env` file in the project root with the following configuration:

```
# Bot configuration
SUPPORT_BOT_TOKEN=your_actual_bot_token_here
ENVIRONMENT=development

# Replace with your ngrok URL (without https://)
RAILWAY_PUBLIC_DOMAIN=your-ngrok-domain.ngrok-free.app

# Admin configuration (use actual admin group ID)
ADMIN_GROUP_ID=-4771220922

# WebApp URLs for local testing
BASE_WEBAPP_URL=https://your-ngrok-domain.ngrok-free.app
WEB_APP_URL=https://your-ngrok-domain.ngrok-free.app/support-form.html
```

### 2. Start Local Services

1. **Start the web server** for serving WebApp files:
   ```bash
   ./dev.ps1 up webapp
   ```

2. **Start ngrok** to expose your local servers:
   ```bash
   # For the bot webhook (port 8000)
   ngrok http 8000
   
   # For the WebApp (port 3000)
   ngrok http 3000
   ```

3. **Update your `.env`** file with the ngrok URLs:
   - Use the HTTPS URL from the first ngrok instance for `RAILWAY_PUBLIC_DOMAIN`
   - Use the HTTPS URL from the second ngrok instance for `BASE_WEBAPP_URL`

4. **Start the bot server**:
   ```bash
   ./dev.ps1 up supportbot
   ```

### 3. Updating ngrok URLs

When you need to update the ngrok URL (e.g., when ngrok generates a new URL), use the following command:

```bash
python run_test.py webhook-update --url https://your-new-ngrok-url.ngrok-free.app
```

This command will:
1. Update the `.env` file with the new URL
2. Restart all containers to apply the changes
3. Update the Telegram webhook
4. Verify the configuration
5. Send a test message to confirm everything is working

#### Troubleshooting ngrok Updates

If you encounter issues when updating the ngrok URL:

1. **Validation Errors**:
   - The script validates the URL by checking the webhook endpoint
   - A 404 or 405 response is acceptable as it indicates the endpoint exists
   - Other error codes may indicate connectivity issues

2. **Environment Variable Issues**:
   - Make sure the `.env` file is properly mounted in the container
   - Check that the `docker-compose.yml` file is using `env_file` instead of explicit environment variables
   - Verify the environment variables in the container using:
     ```bash
     docker compose exec supportbot env | findstr RAILWAY
     ```

3. **Container Restart Issues**:
   - If containers don't restart properly, try:
     ```bash
     docker compose down
     docker compose up -d --build
     ```
   - This ensures all containers are rebuilt with the new environment variables

4. **Webhook Verification**:
   - After updating, verify the webhook is set correctly:
     ```bash
     python run_test.py webhook-update --url https://your-ngrok-url.ngrok-free.app
     ```
   - The script will show the current webhook URL and confirm it's set correctly

### 4. Start Docker Containers

```bash
# For Windows
./dev.ps1 up

# For Linux/Mac
./dev.sh up
```

## Using the Local Environment

- API server: http://localhost:8000
- Web application: http://localhost:3000
- PostgreSQL database: localhost:5432 (username: postgres, password: postgres)

## Switching Back to Railway Deployment

### 1. Stop Local Docker Containers

```bash
# For Windows
./dev.ps1 down

# For Linux/Mac
./dev.sh down
```

### 2. Update Environment Variables for Railway

If you made any changes to the configuration, ensure they're properly set in Railway's environment variables.

### 3. Restart Railway Services

```bash
# Start all services
railway up
```

Or start specific services:

```bash
railway service up --service supportbot
railway service up --service webapp-support-bot
```

## Troubleshooting

### Webhook Issues

If your Telegram bot isn't receiving messages, check:

1. The ngrok tunnel is running and accessible
2. Your `.env` file has the correct RAILWAY_PUBLIC_DOMAIN value
3. The webhook was properly set in Telegram (check logs)
4. Run the improved ngrok update script to verify and fix configuration:
   ```bash
   python run_test.py ngrok-update
   ```

### Database Issues

If you encounter database issues:

1. Ensure PostgreSQL container is running: `docker ps`
2. Check database logs: `./dev.ps1 logs` (focus on 'db' service logs)
3. If needed, reset the database:
   ```
   ./dev.ps1 down
   docker volume rm postgres_data
   ./dev.ps1 up
   ```

### Container Issues

To check container status and logs:

```bash
# View container status
docker ps

# View logs for all services
./dev.ps1 logs

# View logs for a specific service
./dev.ps1 logs supportbot
```

## Recent Modifications (March 2025)

### 1. Docker Compose Updates

The `docker-compose.yml` file has been updated to include all three services:
- supportbot (FastAPI backend)
- webapp (Express.js frontend)
- db (PostgreSQL database)

### 2. Development Scripts

Both Windows (`dev.ps1`) and Linux/Mac (`dev.sh`) development scripts have been updated to use the newer `docker compose` syntax (with space) instead of the older `docker-compose` command.

### 3. Environment Configuration

The `.env` file has been configured for local development with the following key settings:

```
# Bot configuration
SUPPORT_BOT_TOKEN=your_telegram_bot_token_here

# Database configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/supportbot

# Connection pool settings
MAX_CONNECTIONS=20
POOL_TIMEOUT=30

# Environment (development/production)
ENVIRONMENT=development

# Railway settings (needed even for local development)
# For local testing with ngrok, use your ngrok URL without https:// prefix
RAILWAY_PUBLIC_DOMAIN=6015-185-63-98-50.ngrok-free.app
```

### 4. Webapp Configuration

The `config.py` file has been updated to use the local webapp URL when in development mode:

```python
# Use local webapp URL when in development mode
if os.getenv("ENVIRONMENT") == "development":
    BASE_WEBAPP_URL = "http://localhost:3000"
else:
    BASE_WEBAPP_URL = "https://webapp-support-bot-production.up.railway.app"
```

This ensures that the bot correctly refers users to your local webapp instance during development.

### 5. API Endpoint URLs in Webapp

In the `webapp-support-bot/index.html` file, all API endpoint URLs have been changed from Railway production URLs to local development URLs:

```javascript
// Changed from:
// const response = await fetch('https://supportbot-production-b784.up.railway.app/support-request', {

// To:
const response = await fetch('http://localhost:8000/support-request', {
    // ...
});

// Also changed webapp-log endpoints:
fetch('http://localhost:8000/webapp-log', {
    // ...
});
```

### 6. API Routes for Webapp Integration

The `support-bot/app/api/routes/support.py` file has been updated with additional endpoint handlers:

1. `/support-request` - Enhanced to handle request creation with platform information
2. `/webapp-log` - Added to handle logging from the webapp

### 7. Bot Webhook and Command Handling

The `support-bot/app/bot/bot.py` file has been modified to:

1. Fix command processing by properly registering bot commands
2. Improve webhook handling for local development with ngrok
3. Add better error handling and logging

### 8. Bot Initialization and Network Configuration

The `support-bot/app/bot/bot.py` file has been updated to fix initialization issues with python-telegram-bot library version 20+:

1. Added proper initialization of both Application and Bot objects:
   ```python
   # Create bot instance
   bot = Bot(token=BOT_TOKEN)
            
   # Initialize the bot object itself
   await bot.initialize()
            
   # Create application with the token directly
   bot_app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()
            
   # Initialize the application
   await bot_app.initialize()
   ```

2. Added robust error handling for bot interactions:
   - Ensuring bot and application are initialized before making API calls
   - Adding graceful shutdown procedures
   - Improving webhook management

### 9. Docker Network Configuration

The `docker-compose.yml` file has been updated to include a proper network configuration:

```yaml
networks:
  support_network:
    driver: bridge
```

This ensures that the containers (supportbot, webapp, and db) can communicate with each other using service names as hostnames. 

### 10. WebApp URL Configuration

The WebApp URL configuration has been improved:

1. Added support for a separate `WEBAPP_PUBLIC_URL` environment variable
2. Updated the Docker network configuration to allow direct container-to-container communication
3. Modified the `get_webapp_url()` function to use the appropriate URL based on the environment:
   ```python
   # If we're in development mode with ngrok but no explicit webapp URL,
   # access the webapp container directly via Docker network
   if os.getenv("ENVIRONMENT") == "development" and "ngrok" in RAILWAY_DOMAIN and not WEBAPP_PUBLIC_URL:
       # Docker bridge network allows access to the webapp container via its service name
       return f"http://webapp:3000/?v={version_param}&r={random_param}"
   ```

### 11. Improved Ngrok URL Update Process

The ngrok URL update process has been significantly improved with better error handling and verification:

1. Added URL validation and accessibility checks
2. Implemented container health verification
3. Added retry mechanisms for webhook setup
4. Improved error messages and logging
5. Added final configuration verification
6. Removed complex inline Python code in favor of proper functions
7. Updated to use modern Docker commands
8. Added proper type hints and error handling

The new process is more reliable and provides better feedback when issues occur.

## Reverting Changes for Production

When moving back to Railway deployment, the following changes need to be reverted:

### 1. Update API Endpoint URLs in Webapp

In `webapp-support-bot/index.html`, change all localhost URLs back to Railway production URLs:

```javascript
// Change from:
const response = await fetch('http://localhost:8000/support-request', {

// Back to:
const response = await fetch('https://supportbot-production-b784.up.railway.app/support-request', {
    // ...
});

// Also change webapp-log endpoints back:
fetch('https://supportbot-production-b784.up.railway.app/webapp-log', {
    // ...
});
```

### 2. Environment Variables

In Railway dashboard, ensure the environment variables are correctly set:

- `ENVIRONMENT=production`
- `RAILWAY_PUBLIC_DOMAIN=<your-railway-domain>`

### 3. Restart Railway Services

Use the Railway CLI to restart your services:

```bash
railway up
```

Or start specific services:

```bash
railway service up --service supportbot
railway service up --service webapp-support-bot
```

### 4. Verify Webhook Configuration

After deploying to Railway, verify that the webhook is properly set up by checking the logs in the Railway dashboard or using the Telegram Bot API's getWebhookInfo method.

## Testing the Integration

### 1. Basic Bot Connectivity

Run the bot connection test script:

```bash
python test_bot_connection.py
```

This will verify:
- Connection to the Telegram Bot API
- Webhook configuration
- Ability to send messages to the admin group

### 2. WebApp URL Accessibility

Test if your WebApp URLs are properly configured and accessible:

```bash
python test_webapp_url.py
```

This checks:
- If the URLs are correctly formatted
- If the WebApp files are accessible via the configured URLs
- If the WebApp is using HTTPS (required for production)

### 3. End-to-End Testing

1. **Test user workflow**:
   - Start a chat with your bot in Telegram
   - Send the `/request` command
   - Verify the WebApp opens
   - Submit a test support request

2. **Test admin workflow**:
   - Check that the admin group receives notification about the new request
   - Use the `/view_ID` command to view the request details
   - Test the "Assign to me" functionality
   - Click "Open Support Chat" to verify the chat interface opens

## Cleaning Up

When you're done testing, you can remove the webhook to prevent receiving updates locally:

```bash
python test_webhook_setup.py --action delete
```

And stop all services:

```bash
./dev.ps1 down
```

## Next Steps

After successful local testing, you may:
1. Deploy to your production environment
2. Update the webhook URL to point to your production server
3. Verify that all functionality works in the production environment 