# Testing Utilities

This document provides information about the testing utilities available in the `tests/` directory for testing the Support Bot application.

## Table of Contents

1. [Available Test Scripts](#available-test-scripts)
2. [Run Test Utility](#run-test-utility)
3. [Usage Notes](#usage-notes)
4. [Troubleshooting](#troubleshooting)

## Available Test Scripts

### 1. Bot Connection Test

Tests connectivity with the Telegram Bot API and verifies webhook configuration:

```bash
cd tests
python test_bot_connection.py
```

This script will:
- Verify connection to the Telegram Bot API
- Check webhook configuration
- Attempt to send a test message to the admin group
- Verify other bot functionality

### 2. Webhook Management

Set up or delete webhooks for the bot:

```bash
# Set up the webhook
cd tests
python test_webhook_setup.py --action set

# Delete the webhook
cd tests
python test_webhook_setup.py --action delete

# Update webhook with improved error handling and validation
cd tests
python test_webhook.py
# Or specify URL directly
python test_webhook.py --url https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

You can also run these scripts from the project root using the run_test.py utility:

```bash
# From project root
python run_test.py webhook-update
# Or with URL parameter
python run_test.py webhook-update --url https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

### 3. WebApp URL Testing

Test that WebApp URLs are correctly configured and accessible:

```bash
cd tests
python test_webapp_url.py
```

This script checks:
- If the URLs are correctly formatted
- If the WebApp files are accessible via the configured URLs
- If the WebApp is using HTTPS (required for production)

### 4. Local WebApp Testing

Test WebApp functionality directly in a browser without requiring Telegram:

```bash
cd tests
python test_local_webapp.py
```

This will:
- Open a browser with simulated Telegram WebApp parameters
- Allow testing of form submission or chat interface
- Provide guidance on what to test

### 5. Ngrok URL Management

Several scripts are available for managing ngrok URLs:

```bash
# Update webhook and related environment variables with interactive prompt
cd tests
python test_webhook.py

# Update ngrok URL inside the container directly 
cd tests
python update_webhook_in_container.py

# Update all ngrok-related settings using the integrated link updater
cd tests
python ngrok_link_update.py
```

The `ngrok_link_update.py` script provides improved functionality:
- Validates ngrok URL format and accessibility
- Updates environment variables
- Restarts containers
- Verifies container health
- Sets webhook with retries
- Verifies final configuration

### 6. Ngrok Multi-tunnel Configuration

The `ngrok.yml` file contains configuration for running multiple tunnels with ngrok:

```bash
cd tests
ngrok start --all --config=ngrok.yml
```

Note: This requires an ngrok account and authtoken to be configured in the YAML file.

## Run Test Utility

For convenience, you can run all test scripts from the project root using the `run_test.py` utility:

```bash
# Get help and see all available tests
python run_test.py --help

# Examples:
python run_test.py bot              # Test bot connection
python run_test.py webhook-update   # Update webhook with interactive prompt
python run_test.py webhook-set      # Set webhook
python run_test.py webhook-delete   # Delete webhook
python run_test.py webapp           # Test WebApp URL
python run_test.py local           # Test local WebApp
python run_test.py webapp-tunnel   # Set up WebApp ngrok tunnel
python run_test.py ngrok-update    # Update ngrok URL
```

## Usage Notes

1. Always ensure your `.env` file is correctly configured before running tests
2. The bot must be running (`docker compose up -d`) for most tests to work
3. Local WebApp testing requires port 3000 to be accessible
4. Bot webhook testing requires ngrok or another tunneling service
5. For local development, make sure you're using the correct environment variables:
   ```env
   ENVIRONMENT=development
   RAILWAY_PUBLIC_DOMAIN=your-ngrok-url.ngrok-free.app
   ```

## Troubleshooting

### Bot Connection Issues
- Verify your bot token and admin group ID
- Check that the bot is running in Docker
- Ensure the webhook is properly configured

### Webhook Problems
- Check ngrok is running and your `RAILWAY_PUBLIC_DOMAIN` is set correctly
- Verify the webhook URL is accessible
- Check bot logs for any errors

### WebApp Access
- Ensure the webapp container is running (`docker ps` should show it)
- Check that port 3000 is accessible
- Verify the WebApp URL is correctly configured

### Multiple Tunnels
- Free ngrok accounts are limited to one simultaneous tunnel
- Use the `ngrok.yml` configuration file for multiple tunnels
- Consider using a paid ngrok account for development

### Container Environment Variables
- If changes to .env aren't reflected in the container, try rebuilding:
  ```bash
  docker compose up --build -d
  ```
- Verify environment variables in the container:
  ```bash
  docker compose exec supportbot env
  ``` 