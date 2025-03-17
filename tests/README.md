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

### 5. Ngrok Multi-tunnel Configuration

The `ngrok.yml` file contains configuration for running multiple tunnels with ngrok:

```bash
cd tests
ngrok start --all --config=ngrok.yml
```

Note: This requires an ngrok account and authtoken to be configured in the YAML file.

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