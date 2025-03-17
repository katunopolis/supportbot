# Setting Up Support Bot on a New Machine

This guide will help you set up the Support Bot project from scratch on a new machine, ensuring all components are correctly installed and configured.

## Quick Start

For a fully automated setup, run the setup script:

```bash
python setup.py
```

This script will:
1. Check for required dependencies (Docker, Docker Compose, ngrok, Python)
2. Configure environment variables
3. Set up the database configuration
4. Build Docker containers
5. Provide next steps for starting the application

## Manual Setup

If you prefer to set up the project manually, follow these steps:

### Prerequisites

1. **Install Python 3.9+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure it's added to your PATH

2. **Install Docker and Docker Compose**
   - Docker: [https://www.docker.com/get-started](https://www.docker.com/get-started)
   - Docker Compose: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

3. **Install ngrok**
   - Download from [ngrok.com/download](https://ngrok.com/download)
   - Set up with your auth token: `ngrok authtoken YOUR_AUTH_TOKEN`

4. **Create a Telegram Bot**
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram
   - Follow the instructions to create a new bot
   - Save the API token

5. **Create a Telegram Group for Admins**
   - Create a new group in Telegram
   - Add your bot as a member
   - Get the group ID by:
     1. Sending a message in the group
     2. Forwarding that message to [@getidsbot](https://t.me/getidsbot)
     3. Note the "Forwarded from chat" ID (should be negative)

### Configuration Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd support-bot
   ```

2. **Set up environment variables**
   Create a `.env` file in the project root:
   ```bash
   # Bot configuration
   SUPPORT_BOT_TOKEN=your_bot_token_here
   
   # Database configuration
   DATABASE_URL=postgresql://postgres:postgres@db:5432/supportbot
   
   # Connection pool settings
   MAX_CONNECTIONS=20
   POOL_TIMEOUT=30
   
   # Environment (development/production)
   ENVIRONMENT=development
   
   # Railway settings (needed even for local development)
   # For local testing with ngrok, use your ngrok URL without https:// prefix
   RAILWAY_PUBLIC_DOMAIN=your-ngrok-domain-here.ngrok-free.app
   
   # Admin group ID for notifications
   ADMIN_GROUP_ID=-4771220922
   
   # WebApp URLs (needed for Telegram WebApp functionality)
   BASE_WEBAPP_URL=https://your-ngrok-domain-here.ngrok-free.app
   WEB_APP_URL=https://your-ngrok-domain-here.ngrok-free.app/support-form.html
   ```

3. **Build Docker containers**
   ```bash
   docker-compose build
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Set up ngrok for local development**
   ```bash
   ngrok http 8000
   ```

6. **Update configuration with ngrok URL**
   ```bash
   python run_test.py ngrok-update
   ```

7. **Test bot connection**
   ```bash
   python run_test.py bot
   ```

## Project Structure

- **app/**: Main application code
  - **bot/**: Telegram bot handlers and utilities
  - **api/**: FastAPI endpoints
  - **models/**: Database models
  - **webapp/**: WebApp frontend files
- **docs/**: Documentation
- **tests/**: Testing utilities
- **docker-compose.yml**: Docker configuration
- **setup.py**: Automated setup script

## Troubleshooting

### Docker Issues

- If containers fail to start, check logs with `docker-compose logs`
- Ensure ports 8000, 3000, and 5432 are available on your machine

### ngrok Issues

- If ngrok fails to start, ensure it's properly installed and authenticated
- For connection issues, check firewall settings that might block ngrok
- If your free ngrok session expires (after 2 hours), restart ngrok and update the URL

### Bot Connection Issues

- If the bot doesn't respond, check webhook configuration with `python run_test.py webhook-set`
- Verify your bot token is correct
- Ensure your bot has been added to the admin group

## Migration Between Machines

When migrating the project to a new machine:

1. Copy the entire project directory
2. Run `python setup.py` on the new machine
3. When prompted, enter your existing bot token and admin group ID

For database migration:

1. On the original machine: `docker exec -t support-bot-db-1 pg_dump -U postgres supportbot > supportbot_db_backup.sql`
2. Copy the SQL file to the new machine
3. On the new machine after setup: `cat supportbot_db_backup.sql | docker exec -i support-bot-db-1 psql -U postgres supportbot`

## Updating ngrok URL

Each time you restart ngrok, you'll need to update your configuration with the new URL:

```bash
python run_test.py ngrok-update
```

Follow the prompts to enter the new ngrok URL. The script will:
- Update your .env file
- Restart the supportbot container
- Set the webhook with the new URL
- Test the bot connection 