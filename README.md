# Telegram Support Bot

A support bot for Telegram that allows users to submit support requests and admins to manage them, including a fully-featured chat interface.

## Features

- Users can initiate support requests via the `/request` command
- Support request form via Telegram WebApp
- Admin interface for viewing, assigning, and resolving requests
- Chat interface for admins to communicate with users
- Admin notification system for new support requests
- Database storage for all requests and messages

## Setup

### Quick Setup (Recommended)

For a fully automated setup, run:

```bash
python setup.py
```

This script will:
1. Check for required dependencies
2. Configure environment variables
3. Set up the database
4. Build Docker containers
5. Guide you through starting the application

For detailed information about setting up the project on a new machine, see [docs/SETUP.md](docs/SETUP.md).

### Manual Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your values:
   ```
   cp .env.example .env
   ```
3. Update the `.env` file with:
   - Your Telegram Bot Token
   - Admin Group ID
   - Database URL
   - WebApp URL (for hosting the HTML files)
   - Webhook URL (for receiving updates)

## Development

### Running Locally

```bash
# Build and start containers
./dev.ps1 up

# Stop containers
./dev.ps1 down

# View logs
./dev.ps1 logs
```

### Setting Up ngrok for Local Development

For local development with Telegram WebApps, you need an HTTPS URL. Use ngrok:

```bash
# Start ngrok
ngrok http 8000

# Update configuration with new ngrok URL
python run_test.py ngrok-update
```

### Database Migrations

```bash
# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "Migration name"
```

## Testing the WebApp Chat Interface

To test the admin chat functionality:

1. Make sure the bot is running and the WebApp files are accessible at your `BASE_WEBAPP_URL`
2. Create a support request as a user with the `/request` command
3. As an admin, view the request with `/view_ID` (where ID is the request number)
4. Click "Assign to me" to take ownership of the request
5. Click "Open Support Chat" to open the chat interface in Telegram
6. You should now be able to send messages to the user through the WebApp interface

## WebApp Files

The WebApp files are in the `webapp-support-bot` directory:

- `support-form.html` - The form users fill out when requesting support
- `chat.html` - The chat interface for admins to communicate with users

These files need to be hosted somewhere accessible via HTTPS, and the URL should be set in the `.env` file as `BASE_WEBAPP_URL`.

## Troubleshooting

If you encounter issues:

1. Check that your WebApp files are accessible via HTTPS
2. Verify that your bot token and group ID are correct
3. Ensure the database connection is working
4. Check the logs for error messages

## Moving to a New Machine

To set up the project on a new machine:

1. Copy the entire project directory to the new machine
2. Run `python setup.py` on the new machine
3. For database migration, see the detailed instructions in [docs/SETUP.md](docs/SETUP.md)

## Testing

The project includes a dedicated testing directory with utilities for local development and testing:

```
tests/
```

This directory contains:
- Bot connection testing utilities
- Webhook setup and management scripts
- WebApp URL testing tools
- Local browser-based testing for WebApp components
- Configuration for ngrok multi-tunnel setup

For more information on testing, see:
- [tests/README.md](tests/README.md) - Overview of testing utilities
- [docs/TESTING.md](docs/TESTING.md) - Comprehensive testing documentation
- [tests/LOCAL-TESTING.md](tests/LOCAL-TESTING.md) - Detailed instructions for local testing

### Quick Testing Commands

```bash
# Using the convenient test runner script
python run_test.py bot        # Test bot connection
python run_test.py webapp     # Test WebApp URLs
python run_test.py local      # Test locally in browser
python run_test.py webhook-set    # Set up webhook
python run_test.py webhook-delete # Delete webhook
python run_test.py ngrok-update   # Update ngrok URL in configuration

# Or running tests directly
cd tests && python test_bot_connection.py
cd tests && python test_webapp_url.py
cd tests && python test_local_webapp.py
cd tests && python test_webhook_setup.py --action set
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 