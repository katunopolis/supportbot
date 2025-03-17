# WebApp Configuration Settings

This document outlines the configuration settings required for the Telegram WebApp functionality in the Support Bot.

## Overview

The Support Bot's WebApp functionality requires specific configuration settings to establish the connection between the Telegram bot and the web application interface. These settings define where the WebApp files are hosted and how they can be accessed.

## Environment Variables

The following environment variables should be set in the `.env` file or through your hosting platform's environment variable settings:

```
# WebApp URLs
BASE_WEBAPP_URL=https://example.com
WEBAPP_PUBLIC_URL=https://your-public-webapp-url.com
WEB_APP_URL=https://example.com/support-form.html

# Admin Configuration
ADMIN_GROUP_ID=-4771220922
```

## Configuration File

These settings are defined in `app/config.py`:

```python
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

# Web app specific URL for forms
WEB_APP_URL = os.getenv("WEB_APP_URL", f"{BASE_WEBAPP_URL}/support-form.html")

# Admin group ID (for notifications)
ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID", "-4771220922")
```

## Settings Description

### WEBAPP_PUBLIC_URL (New)

- **Purpose**: Explicitly defines the public URL to access the webapp, overriding automatic URL generation
- **Format**: A valid HTTPS URL
- **Example**: `https://your-webapp-domain.com`
- **Default**: Not set (falls back to BASE_WEBAPP_URL)
- **Note**: This is particularly useful when you have separate domains or tunnels for your API and webapp

### BASE_WEBAPP_URL

- **Purpose**: Defines the base URL where all WebApp HTML files are hosted
- **Format**: A valid HTTPS URL (Telegram requires HTTPS for WebApps)
- **Example**: `https://supportbot-webapp.example.com`
- **Default**: Depends on environment and WEBAPP_PUBLIC_URL setting
- **Note**: This must be a publicly accessible URL, as Telegram will load the WebApp from this location

### WEB_APP_URL

- **Purpose**: Defines the complete URL to the support form HTML file
- **Format**: A valid HTTPS URL pointing to an HTML file
- **Example**: `https://supportbot-webapp.example.com/support-form.html`
- **Default**: Constructed from `BASE_WEBAPP_URL` + `/support-form.html`
- **Usage**: This URL is used when creating the WebApp button for users to open the support form

### ADMIN_GROUP_ID

- **Purpose**: Defines the Telegram group ID where admin notifications are sent
- **Format**: A negative integer (group/channel IDs in Telegram are negative)
- **Example**: `-4771220922`
- **Default**: `-4771220922`
- **Usage**: This ID is used when sending notifications about new support requests, status changes, etc.

## WebApp URLs in Code

These URLs are used in several places throughout the codebase:

1. **User Support Form**: In `app/bot/handlers/start.py` when creating the WebApp button for users:
   ```python
   keyboard = [[InlineKeyboardButton("Open Support Form", web_app=WebAppInfo(url=WEB_APP_URL))]]
   ```

2. **Admin Chat Interface**: In `app/bot/handlers/admin.py` when creating the WebApp button for admins:
   ```python
   chat_webapp_url = f"{BASE_WEBAPP_URL}/chat.html?requestId={request.id}&adminId={admin_id}"
   keyboard.append([
       InlineKeyboardButton("Open Support Chat", web_app=WebAppInfo(url=chat_webapp_url))
   ])
   ```

3. **Admin Notifications**: In `app/bot/handlers/support.py` when notifying admins about new requests:
   ```python
   await bot.send_message(
       chat_id=ADMIN_GROUP_ID,  # Using the configured admin group ID
       text=message
   )
   ```

## WebApp File Hosting

The WebApp HTML files should be hosted in a location that:

1. Is publicly accessible via HTTPS
2. Has proper CORS headers configured to allow requests from Telegram domains
3. Has reasonable uptime and performance

Options for hosting include:

- **Same Server**: Host on the same server as the bot using a web server like Nginx
- **CDN Service**: Host on a Content Delivery Network for better performance
- **Static Site Hosting**: Services like GitHub Pages, Netlify, or Vercel
- **Cloud Storage**: AWS S3, Google Cloud Storage, etc. with static website hosting enabled

## Local Development

For local development, you can set:

```
BASE_WEBAPP_URL=http://localhost:3000
```

However, to test the WebApp integration with Telegram, you'll need to:

1. Use a service like ngrok to expose your local server to the internet
2. Update the `RAILWAY_PUBLIC_DOMAIN` to point to your ngrok URL for the API (port 8000)
3. Either set a separate `WEBAPP_PUBLIC_URL` for the WebApp, or use Docker networking as described below

### Docker Network Configuration

When running the application with Docker Compose, you can leverage internal Docker networking:

```yaml
# In docker-compose.yml
networks:
  support_network:
    driver: bridge

services:
  supportbot:
    # ... other settings ...
    networks:
      - support_network
  
  webapp:
    # ... other settings ...
    networks:
      - support_network
```

This allows direct communication between containers using service names as hostnames:

```python
# In get_webapp_url() function
if os.getenv("ENVIRONMENT") == "development" and "ngrok" in RAILWAY_DOMAIN and not WEBAPP_PUBLIC_URL:
    # Docker bridge network allows access to the webapp container via its service name
    return f"http://webapp:3000/?v={version_param}&r={random_param}"
```

## Security Considerations

1. **HTTPS Required**: Telegram requires all WebApps to be served over HTTPS
2. **CORS Headers**: Ensure your web server has proper CORS headers to allow loading from Telegram domains
3. **Validation**: Always validate query parameters received in the WebApp to prevent injection attacks
4. **Authentication**: Consider implementing additional authentication for sensitive operations within the WebApp 