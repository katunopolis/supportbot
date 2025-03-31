# Support Bot Documentation

Welcome to the Support Bot documentation! This section provides comprehensive information about the support bot's functionality, configuration, and development guidelines.

## Overview

The Support Bot is a Telegram-based customer support system that:

1. Allows users to submit support requests via a WebApp interface
2. Notifies admins in a group chat about new requests 
3. Provides a real-time chat interface for communication between users and admins
4. Supports admin actions like assigning and resolving requests
5. Enables admins to provide detailed solutions when resolving requests
6. Notifies users about request status changes and resolutions

## Key Features

- **User-friendly WebApp interface** for submitting support requests
- **Real-time chat** between users and support admins
- **Admin notification system** for new support requests
- **Admin action buttons** for quick handling of requests
- **Solution entry flow** when resolving requests
- **Automatic notifications** to users when their requests are solved
- **Persistent storage** of all support conversations
- **Secure authentication** via Telegram

## Getting Started

- [Setup Guide](SETUP.md) - Instructions for setting up the Support Bot
- [Local Development](LOCAL-DEVELOPMENT.md) - Guide for local development
- [Testing](TESTING.md) - How to test the bot components
- [Testing Utilities](TESTING-UTILITIES.md) - Available test scripts and utilities
- [Configuration](CONFIG-SETTINGS.md) - Available configuration options

## Architecture and Components

- [Code Map](CODE-MAP.md) - Overview of the codebase structure
- [WebApp Code Map](WEBAPP-CODE-MAP.md) - WebApp architecture details
- [Database Schema](DATABASE.md) - Database models and relationships
- [API Documentation](API.md) - API endpoints and usage
- [Chat Interface](WEBAPP-CHAT-INTERFACE.md) - How the chat interface works
- [Docker Setup](DOCKER.md) - Docker configuration and usage

## Admin Documentation

- [Admin Chat Interface](ADMIN-CHAT-INTERFACE.md) - How admins interact with the chat
- [Admin Workflows](ADMIN-WORKFLOW.md) - Common admin workflows
- [Monitoring](MONITORING.md) - Monitoring and logging features

## Technical Documentation

- [Circular Dependency Fix](CIRCULAR-DEPENDENCY-FIX.md) - Resolving circular import issues
- [Local Testing](LOCAL-TESTING.md) - Testing procedures for development
- [Troubleshooting](TROUBLESHOOTING.md) - Solutions for common problems
- [Changelog](CHANGELOG.md) - History of changes and releases

## Recent Updates

### Enhanced Admin Solution Flow

We've added an improved workflow for request resolution:

1. When an admin clicks the "Solve" button on a request:
   - The bot prompts the admin to provide solution details
   - The admin can enter a detailed solution text in a private chat with the bot
   
2. After the admin provides the solution:
   - The request is marked as solved in the database
   - The solution text is stored with the request
   - The user receives a notification with the solution details
   - The admin group is notified that the request was resolved
   
3. Key benefits:
   - Better documentation of request resolutions
   - More helpful notifications for users
   - Improved tracking of admin actions

### Fixed Issues

Recent fixes include:

1. **Circular Import Resolution** - Improved the code architecture to handle circular dependencies
2. **Database Field Consistency** - Ensured consistency between code models and database schema
3. **Callback Pattern Matching** - Fixed button handling to ensure consistent pattern matching
4. **Bot Reference Handling** - Added proper error handling for bot references

## Contribution

Please refer to our [contribution guidelines](CONTRIBUTING.md) if you want to contribute to the Support Bot project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Local Development Setup

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- ngrok (for local webhook testing)
- Railway CLI (optional, for deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/support-bot.git
cd support-bot
```

### 2. Set Up Environment Variables

Copy the example environment file and configure your variables:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
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
RAILWAY_PUBLIC_DOMAIN=your-ngrok-url.ngrok-free.app
```

### 3. Set Up ngrok for Webhook Testing

To test Telegram webhooks locally, you need a public HTTPS URL provided by ngrok:

```bash
# Start ngrok tunnel to port 8000
ngrok http 8000
```

Copy the ngrok URL (without the https:// prefix) and update your configuration using the improved update script:

```bash
python run_test.py ngrok-update
```

This script will:
1. Validate the ngrok URL format and accessibility
2. Update your `.env` file with the new URL
3. Restart the supportbot container
4. Verify container health
5. Set the webhook with retries
6. Verify the final webhook configuration
7. Test the bot connection

The script provides better error handling and verification at each step, making it more reliable than manual updates.

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

## Recent Improvements

### 1. Improved Ngrok URL Update Process

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

### 2. Docker Network Configuration

The `docker-compose.yml` file has been updated to include a proper network configuration:

```yaml
networks:
  support_network:
    driver: bridge
```

This ensures that the containers (supportbot, webapp, and db) can communicate with each other using service names as hostnames.

### 3. WebApp URL Configuration

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

## Deployment

### Railway Deployment

1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Link your project:
   ```bash
   railway link
   ```

4. Deploy:
   ```bash
   railway up
   ```

### Environment Variables in Railway

Make sure to set these environment variables in Railway:

- `SUPPORT_BOT_TOKEN`: Your Telegram bot token
- `DATABASE_URL`: Railway PostgreSQL connection string
- `ENVIRONMENT`: Set to "production"
- `RAILWAY_PUBLIC_DOMAIN`: Your Railway domain
- `MAX_CONNECTIONS`: Database connection pool size
- `POOL_TIMEOUT`: Database connection timeout

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 