# Troubleshooting Guide

This document provides solutions for common issues you might encounter when running the Support Bot.

## Bot Command Issues

### Commands Not Working

**Symptom**: The bot doesn't respond to commands like `/start`, `/help`, or `/request` despite being online.

**Possible Causes and Solutions**:

1. **Bot Initialization Error** - The Application isn't properly initialized via `Application.initialize()`
   - Check logs for error messages like: `This Application was not initialized via 'Application.initialize'!`
   - Ensure the bot initialization includes both the Application and Bot initialization calls:
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

2. **Webhook Configuration Issues**:
   - The webhook URL may be incorrect or not accessible
   - Run `python run_test.py webhook-set` to verify and reset the webhook

3. **Bot Token Invalid**:
   - Check if the bot token is valid and not revoked
   - Run `python run_test.py bot` to test the bot connection

## WebApp Issues

### WebApp Not Loading or 404 Error

**Symptom**: When clicking the WebApp button on Telegram, you get a 404 error or the app doesn't load.

**Possible Causes and Solutions**:

1. **Incorrect WebApp URL Configuration**:
   - Check the `BASE_WEBAPP_URL` or `WEBAPP_PUBLIC_URL` in your `.env` file
   - Ensure the URL is accessible from the internet (HTTPS required)
   - For local development with ngrok, ensure you have the correct URL

2. **Docker Network Issues**:
   - If you're using Docker and getting container communication errors, check your network configuration:
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

3. **Multiple ngrok Tunnels**:
   - Free ngrok accounts are limited to one tunnel at a time
   - Use `WEBAPP_PUBLIC_URL` environment variable to specify a separate WebApp URL:
     ```
     WEBAPP_PUBLIC_URL=https://your-webapp-public-url.com
     ```

## Database Connection Issues

**Symptom**: The bot starts but can't connect to the database.

**Possible Causes and Solutions**:

1. **Database Connection String**:
   - Check the `DATABASE_URL` in your `.env` file
   - Make sure it has the correct format: `postgresql://username:password@hostname:port/database`

2. **Database Container Not Running**:
   - Check if the database container is running: `docker ps`
   - Restart the database container if needed: `docker restart support-bot-db-1`

3. **Database Schema Issues**:
   - If the database schema is outdated, you might need to recreate it:
     ```bash
     docker-compose down
     docker volume rm postgres_data
     docker-compose up -d
     ```

## Telegram API Errors

**Symptom**: Bot operations fail with Telegram API errors.

**Possible Causes and Solutions**:

1. **Rate Limiting**:
   - Telegram limits how many requests you can make to the API
   - Add rate limiting or exponential backoff to your bot code

2. **Invalid Bot Token**:
   - Check if your bot token is valid
   - Create a new bot token from BotFather if needed

3. **Permission Issues**:
   - Ensure the bot has been added to groups with proper permissions
   - For admin group functionality, the bot must be a member of the admin group

## Log Analysis

When troubleshooting, always check the logs for specific error messages:

```bash
# View logs for the supportbot container
docker logs support-bot-supportbot-1

# View logs with specific filtering
docker logs support-bot-supportbot-1 | grep -i "error"
```

Common error patterns to look for:
- `Error initializing bot`
- `Error setting up webhook`
- `Error processing update`
- `Application not initialized`
- `Bot is not properly initialized`
- `Database connection failed`

## Getting Help

If you've tried the solutions above and are still experiencing issues:

1. Create an issue on the GitHub repository with detailed information about your problem
2. Include relevant logs and error messages
3. Specify your environment (local development, Railway, etc.)
4. List the steps you've already taken to troubleshoot the issue 