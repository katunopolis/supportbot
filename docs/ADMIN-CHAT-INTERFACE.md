# Admin Chat Interface

This document outlines the implementation of the admin chat interface for the Telegram Support Bot.

## Overview

The admin chat interface enables support administrators to communicate directly with users through a Telegram WebApp interface. This functionality allows for seamless support interactions without leaving the Telegram platform.

## Implementation Details

### Admin View Request Handler

The `view_request` function in `app/bot/handlers/admin.py` has been enhanced to include a WebApp button that opens the chat interface directly within Telegram:

```python
# Add ChatApp button for admin to open chat in Telegram WebApp
chat_webapp_url = f"{BASE_WEBAPP_URL}/chat.html?requestId={request.id}&adminId={admin_id}"

# Always add the chat button if the request is assigned or pending
if request.status in ["pending", "in_progress"]:
    keyboard.append([
        InlineKeyboardButton("Open Support Chat", web_app=WebAppInfo(url=chat_webapp_url))
    ])
```

### Admin Callback Handlers

The admin module includes handlers for callback actions:

- `handle_admin_callbacks`: Processes admin actions like assigning requests and initiating request resolution
- `handle_resolution_message`: Handles admin messages providing solutions to resolve support requests

### Chat Interface WebApp

The chat interface is implemented as a Telegram WebApp in `webapp-support-bot/chat.html`:

1. **Initialization**: Uses Telegram WebApp API to initialize the interface and adapt to Telegram's theme
2. **Authentication**: Receives `requestId` and `adminId` as query parameters
3. **Message Display**: Shows chat history with proper formatting for admin and user messages
4. **Message Sending**: Allows admins to send messages to users through the API
5. **Real-time Updates**: Polls for new messages periodically to ensure conversations stay current

## Key Features

- **Themed Interface**: Automatically adapts to the user's Telegram theme
- **Request Context**: Displays the original support request and status
- **Message History**: Shows the full conversation history between admin and user
- **Real-time Updates**: Polls for new messages to ensure the conversation is current
- **Responsive Design**: Works on both mobile and desktop Telegram clients

## API Integration

The chat interface integrates with these API endpoints:

- `GET /api/chat/{request_id}`: Fetches the request details and conversation history
- `POST /api/chat/{request_id}/messages`: Sends new messages in the conversation

## User Flow

1. Admin views a request using the `/view_ID` command
2. Admin clicks "Assign to me" to take ownership of the request
3. Admin clicks "Open Support Chat" to access the chat interface
4. Admin can view the conversation history and send messages to the user
5. Admin can mark the request as resolved when the issue is fixed

## Configuration

The WebApp URL is configured in `app/config.py` through these environment variables:

- `BASE_WEBAPP_URL`: Base URL where WebApp files are hosted
- `WEB_APP_URL`: Complete URL to the support form 