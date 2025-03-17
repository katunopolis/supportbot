# Testing the Support Bot

This document provides information about testing the Support Bot application in various environments and scenarios.

## Table of Contents

1. [Testing Utilities](#testing-utilities)
2. [Local Testing](#local-testing)
3. [Bot Testing](#bot-testing)
4. [WebApp Testing](#webapp-testing)
5. [Webhook Management](#webhook-management)
6. [Troubleshooting](#troubleshooting)

## Testing Utilities

The project includes several testing utilities located in the `tests/` directory:

- `test_bot_connection.py`: Verifies the bot's connection to the Telegram API
- `test_webhook_setup.py`: Sets up or deletes the webhook for testing
- `test_webapp_url.py`: Tests the WebApp URL generation
- `test_local_webapp.py`: Tests the local WebApp server
- `setup_webapp_tunnel.py`: Sets up a separate ngrok tunnel for the WebApp
- `ngrok_link_update.py`: Automates updating the ngrok URL when it changes

### Using Testing Utilities

These utilities can be run directly or through the `run_test.py` script:

```bash
# Test bot connection
python run_test.py bot

# Set up webhook
python run_test.py webhook-set

# Delete webhook
python run_test.py webhook-delete

# Test WebApp URL
python run_test.py webapp

# Test local WebApp
python run_test.py local

# Set up WebApp ngrok tunnel
python run_test.py webapp-tunnel

# Update the ngrok URL (when it changes)
python run_test.py ngrok-update
```

### Setting Up Local Testing with ngrok

For local development with ngrok, you'll need to:

1. Install ngrok: [https://ngrok.com/download](https://ngrok.com/download)
2. Set up your ngrok credentials: `ngrok authtoken YOUR_AUTH_TOKEN`
3. Start the ngrok tunnel for the bot API:
   ```bash
   ngrok http 8000
   ```
4. Get the ngrok URL (e.g., `https://1234-56-78-90-12.ngrok-free.app`)
5. Update your configuration with the new URL:
   ```bash
   python run_test.py ngrok-update
   ```
   This will automatically:
   - Update your `.env` file with the new URL
   - Restart the supportbot container
   - Set the webhook with the new URL
   - Test the bot connection

6. For the WebApp to work properly, you need to set up a separate tunnel for the webapp:
   ```bash
   python run_test.py webapp-tunnel
   ```
   This will:
   - Create a new ngrok tunnel for port 3000 (WebApp)
   - Update your `.env` file with the correct `WEBAPP_PUBLIC_URL`
   - Display instructions for restarting the bot

7. Restart the bot container:
   ```bash
   docker restart support-bot-supportbot-1
   ```

Now both the bot API and the WebApp should be accessible through their respective ngrok tunnels.

## Local Testing

### Prerequisites

1. A Telegram bot token (from [@BotFather](https://t.me/BotFather))
2. [ngrok](https://ngrok.com/) or another tunneling service installed
3. Python 3.9+ with required dependencies installed

### Setup Steps

#### 1. Configure Local Environment

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

#### 2. Start Local Services

1. **Start the web server** for serving WebApp files:
   ```bash
   docker-compose up -d webapp
   ```

2. **Start ngrok** to expose your local server:
   ```bash
   # For the bot webhook (port 8000) and WebApp (port 3000)
   ngrok start --all --config=tests/ngrok.yml
   ```

   Note: Free ngrok accounts are limited to 1 simultaneous tunnel. You may need to use the configuration file approach to run multiple tunnels from a single session.

3. **Update your `.env`** file with the ngrok URLs

4. **Start the bot server**:
   ```bash
   docker-compose up -d supportbot
   ```

#### 3. Configure Webhook

Use the provided test script to set up the webhook with your ngrok URL:

```bash
cd tests
python test_webhook_setup.py --action set
```

## Bot Testing

### Bot Connection Test

To test the connection to the Telegram Bot API and verify the webhook configuration:

```bash
cd tests
python test_bot_connection.py
```

This will:
- Verify connection to the Telegram Bot API
- Check webhook configuration
- Attempt to send a test message to the admin group
- Verify other bot functionality

## WebApp Testing

### WebApp URL Testing

To test if your WebApp URLs are properly configured and accessible:

```bash
cd tests
python test_webapp_url.py
```

This checks:
- If the URLs are correctly formatted
- If the WebApp files are accessible via the configured URLs
- If the WebApp is using HTTPS (required for production)

### Local WebApp Testing

For testing WebApp functionality directly in a browser without requiring Telegram:

```bash
cd tests
python test_local_webapp.py
```

This will:
- Open a browser with simulated Telegram WebApp parameters
- Allow testing of form submission or chat interface
- Provide guidance on what to test

## Webhook Management

To manage the bot's webhook configuration:

```bash
# Set up the webhook
cd tests
python test_webhook_setup.py --action set

# Delete the webhook
cd tests
python test_webhook_setup.py --action delete
```

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

### ngrok Limitations

Free ngrok accounts are limited to 1 simultaneous tunnel. To work around this:

1. **Use a configuration file** with multiple tunnels defined:
   ```yaml
   # tests/ngrok.yml
   version: "2"
   authtoken: "" # Add your authtoken if you have one
   tunnels:
     api:
       addr: 8000
       proto: http
     webapp:
       addr: 3000
       proto: http
   ```

2. **Start all tunnels from a single agent session**:
   ```bash
   ngrok start --all --config=tests/ngrok.yml
   ```

3. Alternatively, for local-only testing of the WebApp, use `http://localhost:3000` for direct browser access 