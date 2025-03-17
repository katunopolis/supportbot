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

### 3. Configure Webhook

Use the provided test script to set up the webhook with your ngrok URL:

```bash
python test_webhook_setup.py --action set
```

This script will:
1. Delete any existing webhook
2. Set a new webhook using your `RAILWAY_PUBLIC_DOMAIN`
3. Verify the webhook was set correctly

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

## Troubleshooting

### Webhook Issues

- **Webhook not receiving updates**: Verify your ngrok tunnel is running and the URL is correctly set in the webhook
- **Webhook validation errors**: Ensure your HTTPS certificate is valid (ngrok provides this automatically)
- **Port conflicts**: Check if other services are using the required ports

### WebApp Issues

- **WebApp not loading**: Verify the WebApp files are being served correctly by your local server
- **CORS errors**: Check browser console for CORS issues when accessing the WebApp
- **Telegram integration errors**: Ensure the WebApp is using HTTPS and proper Telegram WebApp API calls

### Connection Issues

- **API connection errors**: Verify your bot token is correct and has not been revoked
- **Admin group messages failing**: Ensure the bot has been added to the admin group and has permission to send messages

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