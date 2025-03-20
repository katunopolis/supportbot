# Local Development Setup

This document explains how to set up a local development environment for the Support Bot project and how to switch between local development and Railway deployment.

## Prerequisites

- Docker Desktop installed and running
- ngrok (for Telegram webhook testing)
- Railway CLI (optional, for managing Railway deployments)

## Setting Up Local Development

### 1. Stop Railway Services

Before starting local development, stop your Railway services to avoid conflicts:

```bash
# Install Railway CLI if not already installed
npm i -g @railway/cli

# Login to your Railway account
railway login

# Link to your project
railway link

# Stop your services
railway down
```

### 2. Configure Environment Variables

Update your `.env` file for local development:

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
# Example: 1a2b3c4d.ngrok.io
RAILWAY_PUBLIC_DOMAIN=6015-185-63-98-50.ngrok-free.app
```

### 3. Set Up ngrok for Webhook Testing

To test Telegram webhooks locally, you need a public HTTPS URL provided by ngrok:

```bash
# Start ngrok tunnel to port 8000
ngrok http 8000
```

Copy the ngrok URL (without the https:// prefix) and update your `.env` file:

```
RAILWAY_PUBLIC_DOMAIN=your-ngrok-url.ngrok.io
```

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