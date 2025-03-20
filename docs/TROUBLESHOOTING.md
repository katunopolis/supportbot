# Troubleshooting Guide

This document provides solutions to common issues you might encounter when working with the Support Bot.

## Table of Contents

- [General Issues](#general-issues)
- [Logging Issues](#logging-issues)
- [Database Issues](#database-issues)
- [Telegram Bot Issues](#telegram-bot-issues)
- [WebApp Issues](#webapp-issues)
- [Docker Issues](#docker-issues)
- [Circular Import Issues](#circular-import-issues)
- [Database Field Mismatches](#database-field-mismatches)
- [Callback Pattern Issues](#callback-pattern-issues)
- [Chat Message Visibility Issues](#chat-message-visibility-issues)
- [API Routing Issues](#api-routing-issues)

## General Issues

### Bot doesn't start

**Symptoms:**
- Bot container starts but immediately stops
- Errors in logs mentioning "cannot import name X"

**Solution:**
1. Check the logs for specific import errors:
   ```bash
   docker compose logs supportbot
   ```
2. Look for circular dependencies between modules
3. Fix imports by using local imports within functions (see [Circular Import Issues](#circular-import-issues))

### Changes not being applied

**Symptoms:**
- You made changes to the code, but they don't seem to be active

**Solution:**
1. Make sure you've restarted the container:
   ```bash
   docker compose restart supportbot
   ```
2. Check if your changes caused any errors in the logs
3. Verify that your changes were saved properly in the source files

## Logging Issues

### Understanding Log Output

**Log Format:**
```
[TIMESTAMP] LEVEL:
  Source: module_name
  Message: actual log message
```

**Log Levels:**
- INFO: Normal operational messages
- WARNING: Issues that need attention but aren't critical
- ERROR: Critical issues that need immediate attention
- DEBUG: Detailed debugging information (only in development)

### Common Logging Issues

#### Noisy or Unreadable Logs

**Symptoms:**
- Too many debug messages
- Hard to find important information
- Logs filled with internal framework messages

**Solution:**
1. Adjust log level in `.env` file:
   ```
   LOG_LEVEL=INFO  # Instead of DEBUG
   ```
2. Use the log filter system:
   ```python
   # In your code
   logging.getLogger('httpcore').setLevel(logging.WARNING)
   logging.getLogger('httpx').setLevel(logging.INFO)
   ```

#### Missing Important Information

**Symptoms:**
- Can't find relevant error messages
- Important events not being logged

**Solution:**
1. Add appropriate logging calls in your code:
   ```python
   logging.info("Processing request #%d", request_id)
   logging.error("Failed to process request: %s", str(error))
   ```
2. Check log filter configuration in `app/logging/setup.py`
3. Verify database logging handler is working

#### Database Logging Issues

**Symptoms:**
- Logs not being saved to database
- Database connection errors in logs

**Solution:**
1. Check database connection in logging handler
2. Verify Log model schema matches database
3. Monitor database size and clean old logs:
   ```sql
   DELETE FROM logs WHERE timestamp < NOW() - INTERVAL '30 days';
   ```

### Viewing Logs

#### Docker Container Logs

To view real-time logs with improved readability:
```bash
docker logs support-bot-supportbot-1 --follow
```

The logs will show:
- Support request creation/updates
- Message sending/receiving
- Admin actions
- Error messages
- Important system events

#### Database Logs

To view logs stored in the database:
```sql
SELECT timestamp, level, message 
FROM logs 
ORDER BY timestamp DESC 
LIMIT 100;
```

### Log Configuration

The logging system is configured in several files:

1. `app/config.py`:
   ```python
   LOG_LEVEL = "INFO"
   LOG_FORMAT = '''
   [%(asctime)s] %(levelname)s:
     Source: %(name)s
     Message: %(message)s
   '''
   ```

2. `app/logging/setup.py`:
   - Configures log handlers
   - Sets up log filtering
   - Initializes database logging

3. `app/logging/handlers.py`:
   - Implements database logging
   - Handles log record formatting
   - Manages database connections

## Database Issues

### Unable to connect to the database

**Symptoms:**
- Error messages about database connection failures
- "Connection refused" errors

**Solution:**
1. Ensure the database container is running:
   ```bash
   docker compose ps
   ```
2. Check the database configuration in `.env` file
3. Try to reset the database container:
   ```bash
   docker compose down db
   docker compose up -d db
   ```

### Database schema errors

**Symptoms:**
- Errors like "column X does not exist" 
- "relation does not exist" errors

**Solution:**
1. Check for mismatches between your SQLAlchemy models and actual database schema
2. Ensure field names in models match field names in database
3. Consider running database migrations if schema changes are needed

## Telegram Bot Issues

### Webhook setup issues

**Symptoms:**
- Bot doesn't respond to messages
- Error about webhook connection failures

**Solution:**
1. Verify your ngrok tunnel is running and accessible
2. Update the webhook URL:
   ```bash
   python tests/ngrok_link_update.py
   ```
3. Check the webhook status:
   ```bash
   python tests/test_webhook_setup.py
   ```

### Callback query errors

**Symptoms:**
- Buttons in messages don't do anything when clicked
- Error logs showing callback query failures

**Solution:**
1. Check that callback data format matches the pattern in your handlers
2. Ensure consistent callback data format across all button creations
3. Verify that the correct handler is registered for your callback patterns
4. Update callback patterns in application setup to match button data format

## WebApp Issues

### WebApp not loading

**Symptoms:**
- Clicking the WebApp button doesn't open anything
- Browser console shows errors

**Solution:**
1. Check that your ngrok domain is correctly set in the `.env` file
2. Verify the domain in `.env` matches the one in the webhook
3. Restart the containers to apply environment changes:
   ```bash
   docker compose restart
   ```

### Cannot submit support requests

**Symptoms:**
- Clicking Submit in the WebApp returns an error
- Server logs show database or API errors

**Solution:**
1. Check server logs for specific errors
2. Verify that all required fields are being submitted
3. Ensure database connection is working
4. Check for field name mismatches between model and database schema

### Chat Polling Issues

**Symptoms:**
- Messages not updating in real-time
- Duplicate messages appearing
- Timestamp-related errors in console or logs
- API returns 500 errors for chat list endpoints

**Solution:**
1. Check for API routing issues in `main.py`:
   - Ensure the proxy middleware properly routes requests to API handlers
   - Update special handling for `/api/chat/` URLs to call the actual API handlers instead of returning empty arrays
   ```python
   # For message polling requests, use the real chat API instead of returning empty array
   if "messages" in path:
       try:
           # Parse the request_id from the path and use the actual API handler
           from app.api.routes.chat import get_messages
           from app.database.session import get_db
           
           # Call the actual API handler
           messages = await get_messages(int(request_id), since_param, db)
           return JSONResponse(content=messages)
       except Exception as e:
           logging.error(f"Error handling message polling: {str(e)}")
   ```

2. Run the timestamp tests to verify correct timestamp handling:
   ```bash
   python run_test.py timestamps
   ```

3. Ensure proper ISO 8601 timestamp formatting:
   - All timestamps should include the 'Z' suffix for UTC
   - Backend should use `datetime.now(timezone.utc)` for creation
   - Frontend should validate and normalize timestamps with `ensureISOTimestamp` function

4. Check the browser console for errors related to polling or timestamps
5. Verify that the frontend properly encodes the timestamp parameter in URLs

### Timestamp Handling Issues

**Symptoms:**
- Inconsistent date/time display in chat messages
- Errors about invalid timestamps in logs
- Multiple polling instances causing duplicate messages
- Messages not appearing in chronological order

**Solution:**
1. Ensure consistent use of ISO 8601 format with UTC timezone:
   - Backend: `timestamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')`
   - Frontend: `new Date().toISOString()`

2. Validate and normalize timestamps on the frontend:
   ```javascript
   function ensureISOTimestamp(timestamp) {
       if (!timestamp || timestamp === 'undefined') {
           return new Date().toISOString();
       }
       try {
           const date = new Date(timestamp);
           if (isNaN(date.getTime())) {
               throw new Error('Invalid date');
           }
           return date.toISOString();
       } catch (e) {
           console.error('Invalid timestamp:', timestamp);
           return new Date().toISOString();
       }
   }
   ```

3. Implement proper polling state management to prevent multiple instances:
   ```javascript
   function stopPolling() {
       if (pollingInterval) {
           clearInterval(pollingInterval);
           pollingInterval = null;
       }
       isPolling = false;
   }
   
   function startPolling() {
       if (isPolling) {
           console.warn('Already polling, skipping');
           return;
       }
       
       stopPolling(); // Clean up any existing interval
       isPolling = true;
       // Start new polling...
   }
   ```

4. Add event listeners for page visibility changes to manage polling:
   ```javascript
   document.addEventListener('visibilitychange', () => {
       if (document.visibilityState === 'visible') {
           startPolling();
       } else {
           stopPolling();
       }
   });
   ```

5. Run the timestamp test script to verify your implementation:
   ```bash
   python run_test.py timestamps
   ```

## Docker Issues

### Container fails to start

**Symptoms:**
- Container exits immediately after starting
- Docker logs show Python errors

**Solution:**
1. Check container logs:
   ```bash
   docker compose logs supportbot
   ```
2. Look for import errors or syntax errors
3. Fix any code errors and restart the container

### Configuration issues

**Symptoms:**
- Environment variables not being recognized
- Settings not being applied

**Solution:**
1. Verify your `.env` file is correctly formatted
2. Check that the container is using the correct environment file
3. Rebuild the container if needed:
   ```bash
   docker compose build supportbot
   docker compose up -d supportbot
   ```

## Circular Import Issues

**Symptoms:**
- Import errors like "cannot import name X"
- Containers fail to start due to import errors

**Solution:**
1. Identify circular dependencies between modules (A imports B, B imports A)
2. Use one of these strategies to resolve:
   - Move imports inside functions where they're used:
     ```python
     # Instead of global import
     # from app.bot.bot import bot
     
     async def some_function():
         # Local import inside function
         from app.bot.bot import bot
         await bot.send_message(...)
     ```
   - Create a separate module for shared functionality
   - Use dependency injection patterns
3. For the specific bot reference problem, import inside handler functions:
   ```python
   async def handle_callback(update, context):
       # Import bot locally to avoid circular reference
       from app.bot.bot import bot
       
       # Now use bot
       await bot.send_message(...)
   ```

## Database Field Mismatches

**Symptoms:**
- Errors like "column X does not exist"
- Data not being saved or retrieved correctly

**Solution:**
1. Check your database models against actual database schema:
   ```bash
   # Connect to database and check schema
   docker compose exec db psql -U postgres -d supportbot -c "\d requests"
   ```
2. Ensure field names in models match field names in database:
   ```python
   # In models.py
   class Request(Base):
       # Column must match DB field name
       assigned_admin = Column(Integer, nullable=True)
       # NOT assigned_to if DB has assigned_admin
   ```
3. If changing models, either update database schema or adapt the code to match existing schema

## Callback Pattern Issues

**Symptoms:**
- Admin buttons don't work when clicked
- No response or wrong response to button clicks

**Solution:**
1. Check the format of callback data in button creation:
   ```python
   InlineKeyboardButton("Open Chat", callback_data=f"chat_{request_id}")
   ```
2. Ensure handler pattern matches the callback data format:
   ```python
   # Must match the format used in buttons
   application.add_handler(CallbackQueryHandler(
       handle_callback_query, 
       pattern=r"^(assign|view|chat|solve)_\d+$"
   ))
   ```
3. Check for any discrepancies in callback data formats (e.g., using colons vs. underscores)
4. Keep callback patterns consistent throughout the application

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

### Chat API 404 Error

**Symptom**: After submitting a support request, you see "Error Loading Chat: Failed to load chat: 404" in the WebApp.

**Possible Causes and Solutions**:

1. **Missing API Endpoint**:
   - The `/api/chat/{request_id}/messages` endpoint might be missing from your backend
   - Add the endpoint to handle retrieving messages since a specific timestamp:
     ```python
     @router.get("/{request_id}/messages", response_model=List[MessageResponse])
     async def get_messages_since(
         request_id: int, 
         since: Optional[str] = None,
         db: Session = Depends(get_db)
     ):
         # Implementation details...
     ```

2. **Proxy Route Blocking API Requests**:
   - The proxy route in `main.py` might be blocking legitimate API requests
   - Update the condition to properly handle API routes:
     ```python
     # Check if this is a chat-related API route that should be allowed
     is_chat_api = path.startswith("/api/chat/")
     
     # Don't proxy most /api/* routes, but allow chat API endpoints
     if ((path.startswith("/api/") and not is_chat_api) or 
         path == "/webhook" or 
         path == "/healthz"):
         logging.info(f"Not proxying special route: {path}")
         return Response(content="Not Found", status_code=404)
     ```

3. **Frontend Using Incorrect API URL**:
   - The frontend might be using the wrong URL format for API requests
   - Update the API endpoint URLs in the WebApp code:
     ```javascript
     // Correct endpoint for fetching chat data
     const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}`);
     
     // Correct endpoint for sending messages
     const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}/messages`, {
         method: 'POST',
         // Other request details...
     });
     ```

### "Failed to fetch" Error in Chat Interface

**Symptom**: After submitting a support request, you see "Error Loading Chat: Failed to fetch" in the WebApp.

**Possible Causes and Solutions**:

1. **Direct Fallback for Chat API Requests**:
   - Modify the `main.py` file to directly handle chat API requests with a fallback:
     ```python
     # Special handling for /api/chat/ URLs
     if path.startswith("/api/chat/"):
         # For message polling requests, return an empty array to avoid failures
         if "messages" in path:
             logging.info(f"Returning empty array for chat messages polling: {path}")
             return JSONResponse(content=[])
         
         # For main chat data requests, use our reliable fixed-chat endpoint
         try:
             request_id = chat_path.split("/")[0]
             if request_id.isdigit():
                 # Use our reliable fixed-chat endpoint
                 redirect_url = f"http://localhost:8000/fixed-chat/{request_id}"
                 # Implementation details...
         except Exception as e:
             logging.error(f"Error redirecting chat request: {str(e)}")
     ```

2. **Add a Reliable Fixed Response Endpoint**:
   - Create a dedicated endpoint that always returns a valid response:
     ```python
     @app.get("/fixed-chat/{request_id}")
     async def fixed_chat(request_id: int):
         """A reliable endpoint that always returns a valid chat structure with a fixed response."""
         # Return a valid chat structure even if database access fails
     ```

3. **Implement Multiple Fallback Endpoints in the Frontend**:
   - Update `loadChatHistory` function to try multiple endpoints in sequence:
     ```javascript
     async function loadChatHistory(requestId) {
         const endpoints = [
             `${API_BASE_URL}/api/chat_api/${requestId}`,
             `${API_BASE_URL}/api/support/chat/${requestId}`,
             `${API_BASE_URL}/debug/chat/${requestId}`,
             `${API_BASE_URL}/fixed-chat/${requestId}`
         ];

         let lastError = null;
         for (const endpoint of endpoints) {
             try {
                 // Try each endpoint until one succeeds
                 // Implementation details...
             } catch (error) {
                 lastError = error;
             }
         }
         
         // If we get here, all endpoints failed
         throw lastError || new Error('Failed to load chat history from all endpoints');
     }
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

## Chat Message Visibility Issues

### Symptoms
- Admin can only see their own messages but not user messages
- User can only see their own messages but not admin responses
- Messages are being sent successfully but not displayed to the other party

### Diagnosis
The issue was identified in the `chat.html` file's message rendering logic. The `addMessage` function was incorrectly handling message display for different sender types.

The key problematic code:

```javascript
// Original problematic code
function addMessage(message) {
    const isAdmin = message.sender_type === 'admin';
    const isMine = message.sender_id === (adminIdFromQuery || tg.initDataUnsafe?.user?.id);

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isAdmin ? 'admin-message' : 'user-message'} ${isMine ? 'my-message' : ''}`;
    
    // The rest of the function
}
```

The issue was that both sides rendered all messages, but the styling made them appear incorrectly or invisible to the other party.

### Solution
1. **Fixed message rendering logic**: Updated the `addMessage` function to properly display messages from both admin and user.
2. **Added sender identification**: Added labels to show who sent each message.
3. **Added type checking**: Ensured IDs are properly compared as strings to prevent type mismatches.
4. **Implemented duplicate prevention**: Added code to prevent duplicate messages when refreshing or reconnecting.

```javascript
// Fixed code
function addMessage(message) {
    // Don't process duplicate messages
    if (message.id) {
        const existingMsg = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMsg) {
            console.log(`Message ID ${message.id} already exists, skipping`);
            return;
        }
    }
    
    const isAdmin = message.sender_type === 'admin';
    const isMine = message.sender_id.toString() === currentUserId.toString();
    
    // Create message div
    const messageDiv = document.createElement('div');
    
    // Apply appropriate classes
    messageDiv.className = `message ${isAdmin ? 'admin-message' : 'user-message'} ${isMine ? 'my-message' : ''}`;
    
    // Add message ID as data attribute if available
    if (message.id) {
        messageDiv.setAttribute('data-message-id', message.id);
    }

    // Add sender identifier for clarity
    const senderLabel = isAdmin ? 'Admin' : 'User';
    
    messageDiv.innerHTML = `
        <div class="message-sender">${isMine ? 'You' : senderLabel}</div>
        <div class="message-content">${escapeHtml(message.message)}</div>
        <div class="message-time">${time}</div>
        <div class="message-timestamp" style="display: none;">${timestamp}</div>
    `;
}
```

5. **Enhanced CSS styling**: Updated CSS to clearly differentiate between admin and user messages.

```css
.user-message {
    background-color: var(--tg-theme-secondary-bg-color);
    color: var(--tg-theme-text-color);
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}

.admin-message {
    background-color: var(--tg-theme-button-color);
    color: var(--tg-theme-button-text-color);
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}

.my-message {
    align-self: flex-end;
    border-bottom-right-radius: 4px;
    border-bottom-left-radius: var(--message-radius);
}

.my-message.user-message {
    background-color: #e1f5fe;
    color: #0277bd;
}

.my-message.admin-message {
    background-color: #1976d2;
    color: white;
}
```

6. **Added debug logging**: Implemented detailed console logging to help identify issues with message processing.

### Verification
To verify the fix is working correctly:
1. Open the chat interface from both admin and user sides
2. Check for the "v1.2.1-fix" indicator in the header
3. Send messages from both sides and verify they appear for both parties
4. Check browser console logs for any rendering errors

## API Routing Issues

// ... existing code ... 