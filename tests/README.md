# Support Bot Testing Utilities

This directory contains utilities and scripts for testing the Support Bot application in various environments.

## Available Test Scripts

### 1. Bot Connection Test

Tests connectivity with the Telegram Bot API and verifies webhook configuration:

```bash
cd tests
python test_bot_connection.py
```

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

### 4. Local WebApp Testing

Test WebApp functionality directly in a browser without requiring Telegram:

```bash
cd tests
python test_local_webapp.py
```

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
```

## Usage Notes

1. Always ensure your `.env` file is correctly configured before running tests
2. The bot must be running (`docker-compose up -d`) for most tests to work
3. Local WebApp testing requires port 3000 to be accessible
4. Bot webhook testing requires ngrok or another tunneling service

## Troubleshooting

- **Bot Connection Issues**: Verify your bot token and admin group ID
- **Webhook Problems**: Check ngrok is running and your `RAILWAY_PUBLIC_DOMAIN` is set correctly
- **WebApp Access**: Ensure the webapp container is running (`docker ps` should show it)
- **Multiple Tunnels**: Free ngrok accounts are limited to one simultaneous tunnel
- **Container Environment Variables**: If changes to .env aren't reflected in the container, try rebuilding with `docker compose up --build -d` 