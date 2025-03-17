# WebApp Chat Interface

This document outlines the implementation of the Telegram WebApp Chat Interface for the Support Bot.

## Overview

The WebApp Chat Interface provides a seamless in-app chat experience for administrators to communicate with users directly within Telegram. It is implemented as a responsive HTML/CSS/JavaScript application that leverages the Telegram WebApp API.

## File Location

The chat interface is defined in:
- `webapp-support-bot/chat.html`

## Features

The WebApp Chat Interface provides the following features:

1. **Telegram Theme Integration**: Automatically adapts to the user's Telegram color scheme
2. **Real-time Message Display**: Shows messages with timestamps and sender information
3. **Message Composition**: Simple text input with send button
4. **Auto-resize Input**: Text input automatically expands as the user types
5. **Polling Updates**: Periodically checks for new messages
6. **Request Context**: Displays the original support request issue for context
7. **Status Information**: Shows the current status of the support request
8. **Responsive Design**: Works on both mobile and desktop Telegram clients

## Implementation Details

### Telegram WebApp Initialization

The interface initializes the Telegram WebApp environment and adapts to the user's theme:

```javascript
// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Set theme
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f1f1f1');
```

### URL Parameters

The interface receives necessary parameters from the URL:

```javascript
// Get parameters from URL
const urlParams = new URLSearchParams(window.location.search);
const requestId = urlParams.get('requestId');
const adminId = urlParams.get('adminId');
```

### API Integration

The interface integrates with the backend API for data retrieval and updates:

```javascript
// API endpoints - dynamically set based on environment
const isLocalDev = window.location.hostname === 'localhost';
const API_BASE_URL = isLocalDev ? 'http://localhost:8000' : 'https://supportbot-production-b784.up.railway.app';

async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load chat: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        // Process data...
    } catch (error) {
        // Handle error...
    }
}
```

### Message Sending

The interface handles message sending with proper error handling:

```javascript
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/requests/${requestId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender_id: adminId,
                sender_type: 'admin',
                message: text
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
        }
        
        // Add message to UI and clear input...
    } catch (error) {
        // Handle error...
    }
}
```

### Polling for Updates

To keep the conversation current, the interface polls for new messages:

```javascript
function startPolling() {
    pollingInterval = setInterval(pollForNewMessages, 5000);
}

async function pollForNewMessages() {
    if (!lastMessageTimestamp) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}`);
        if (!response.ok) return;
        
        const data = await response.json();
        
        // Filter new messages
        const newMessages = data.messages.filter(msg => {
            const msgTime = new Date(msg.timestamp);
            return msgTime > lastMessageTimestamp;
        });
        
        // Add new messages to UI...
    } catch (error) {
        console.error('Error polling for messages:', error);
    }
}
```

### UI Components

The interface includes these key UI components:

1. **Chat Header**: Displays request information
2. **Messages Container**: Shows the conversation history
3. **Input Container**: Includes text input and send button
4. **Loading Overlay**: Displays during initial loading
5. **Error Message**: Shows any errors that occur

## Styling

The interface is styled using CSS variables that adapt to Telegram's theme:

```css
:root {
    --tg-theme-bg-color: #ffffff;
    --tg-theme-text-color: #000000;
    --tg-theme-button-color: #2481cc;
    --tg-theme-button-text-color: #ffffff;
    --tg-theme-hint-color: #999999;
    --tg-theme-secondary-bg-color: #f1f1f1;
}

/* Styles using these variables */
```

## Event Handling

The interface handles various events:

1. **Send Button Click**: Sends messages
2. **Enter Key Press**: Sends messages (Shift+Enter adds new line)
3. **Input Resize**: Automatically adjusts text input height
4. **Visibility Change**: Pauses/resumes polling when tab is hidden/visible
5. **Back Button**: Handles WebApp back button

## Error Handling

The interface includes robust error handling:

1. **Loading Errors**: Shows error message if chat can't be loaded
2. **Send Errors**: Shows error message if message can't be sent
3. **Missing Parameters**: Checks for required URL parameters

## Deployment

The WebApp HTML file should be hosted at the URL specified in the `BASE_WEBAPP_URL` environment variable. This URL is used when generating the WebApp button in the admin interface. 