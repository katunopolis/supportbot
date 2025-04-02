# WebApp Chat Interface

This document outlines the implementation of the Telegram WebApp Chat Interface for the Support Bot.

## Overview

The WebApp Chat Interface provides a seamless in-app chat experience for users to communicate with support administrators directly within Telegram. It is implemented as a responsive Single-Page Application (SPA) using HTML/CSS/JavaScript that leverages the Telegram WebApp API.

## File Location

The chat interface is defined in:
- `webapp-support-bot/index.html` (Single-Page Application containing both form and chat interfaces)

## Features

The WebApp Chat Interface provides the following features:

1. **Single-Page Application**: Seamless transition between form and chat views without page redirects
2. **Telegram Theme Integration**: Automatically adapts to the user's Telegram color scheme
3. **Real-time Message Display**: Shows messages with timestamps and sender information
4. **Message Composition**: Simple text input with send button
5. **Auto-resize Input**: Text input automatically expands as the user types
6. **Polling Updates**: Periodically checks for new messages
7. **Request Context**: Displays the original support request issue for context
8. **Status Information**: Shows the current status of the support request
9. **Responsive Design**: Works on both mobile and desktop Telegram clients
10. **Fallback Mechanism**: Gracefully handles API errors with fallback UI
11. **ISO 8601 Timestamp Handling**: Properly manages timezone differences between client and server
12. **Time Synchronization**: Adjusts for time differences between client and server clocks

## Implementation Details

### Single-Page Application Approach

The interface uses a SPA approach to avoid redirects, which can cause issues in the Telegram WebApp environment:

```javascript
// Global variables to track current view and request ID
let currentView = 'form';  // 'form' or 'chat'
let currentRequestId = null;
let pollingInterval = null;

/**
 * Switches the view to the chat interface
 * This is a SPA approach that avoids redirects
 */
async function switchToChatView(requestId) {
    try {
        currentView = 'chat';
        currentRequestId = requestId;
        
        // Create a basic chat structure first with loading indicator
        document.querySelector('.container').innerHTML = `
            <div class="chat-container">
                <div class="chat-header">
                    <h2 id="requestTitle">Support Request #${requestId}</h2>
                    <div id="requestStatus">Status: Loading...</div>
                </div>
                <div id="messagesContainer" class="messages-container">
                    <div class="loading-spinner"></div>
                </div>
                <div class="chat-input">
                    <textarea id="messageInput" placeholder="Type your message..." disabled></textarea>
                    <button id="sendButton" disabled>Send</button>
                </div>
            </div>
        `;
        
        // Fetch chat data
        const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}`);
        
        // Process response and update UI...
        
        // Set up chat handlers
        setupChatHandlers(requestId);
        
        // Start polling for new messages
        startPolling(requestId);
    } catch (error) {
        // Handle error...
    }
}
```

### Telegram WebApp Initialization

The interface initializes the Telegram WebApp environment and adapts to the user's theme:

```javascript
// Initialize Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Access Telegram theme colors directly
const setThemeColors = () => {
    // Standard Telegram theme params
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color);
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color);
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color);
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color);
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color);
};

// Set theme colors and update if/when they change
setThemeColors();
tg.onEvent('themeChanged', setThemeColors);
```

The theme handling implementation ensures:
- Proper usage of Telegram's official theme parameters
- Real-time theme updates when the user changes their Telegram theme 
- No fallback colors that might override Telegram's theme
- Consistent appearance across light and dark modes
- CSS variables that can be used throughout the interface

### Time and Timezone Handling

The interface incorporates sophisticated timestamp handling to ensure consistent time display across different timezones:

```javascript
// Initialize server time offset detection
let serverTimeOffset = 0; // Time difference between server and client in milliseconds

// Synchronize client time with server time to account for differences
function syncTimeWithServer(clientTime, serverTime) {
    try {
        const clientDate = new Date(clientTime);
        const serverDate = new Date(serverTime);
        
        // Calculate time difference in milliseconds
        serverTimeOffset = serverDate.getTime() - clientDate.getTime();
        console.log(`Time sync: Server time is ${serverTimeOffset > 0 ? 'ahead by' : 'behind by'} ${Math.abs(serverTimeOffset) / 1000} seconds`);
        
        // Update the time difference indicator if significant
        if (Math.abs(serverTimeOffset) > 60000) { // More than a minute difference
            updateTimeDifferenceIndicator(Math.round(Math.abs(serverTimeOffset) / 60000), serverTimeOffset > 0);
        }
    } catch (e) {
        console.error('Error synchronizing time with server:', e);
    }
}

// Get current timestamp adjusted for server time if needed
function getCurrentTimestamp() {
    const now = new Date();
    
    // If we have a significant server time offset, adjust the timestamp
    if (Math.abs(serverTimeOffset) > 5000) { // Only adjust if offset is more than 5 seconds
        const serverAdjustedTime = new Date(now.getTime() + serverTimeOffset);
        return serverAdjustedTime.toISOString();
    }
    
    return now.toISOString();
}

// Format date for display in messages with proper timezone handling
function formatDateForDisplay(isoString) {
    try {
        // Parse the ISO string (which is in UTC format)
        const date = new Date(isoString);
        
        // Check if the message is from today
        const today = new Date();
        const isToday = date.getDate() === today.getDate() && 
                       date.getMonth() === today.getMonth() && 
                       date.getFullYear() === today.getFullYear();
        
        // Format time explicitly using local values
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const timeString = `${hours}:${minutes}`;
        
        // Format date parts if needed
        if (isToday) {
            // Just show time for today's messages
            return timeString;
        } else {
            // Show date and time for older messages
            const day = date.getDate().toString().padStart(2, '0');
            const month = (date.getMonth() + 1).toString().padStart(2, '0'); // getMonth() is 0-based
            return `${day}/${month} ${timeString}`;
        }
    } catch (e) {
        return '??:??'; // Fallback for invalid dates
    }
}
```

The timestamp handling implementation ensures:
- Proper ISO 8601 format for all timestamps
- Timezone awareness across client and server
- Adjustment for clock differences between client and server
- Context-aware time display (time only for today's messages, date+time for older messages)
- Visual indication when client and server clocks differ significantly
- Consistent timestamp display in message history
- Proper handling of UTC timestamps from server

### API Integration

The interface integrates with the backend API for data retrieval and updates:

```javascript
// API endpoints - dynamically set based on environment
const isLocalDev = window.location.hostname === 'localhost';
const API_BASE_URL = isLocalDev ? 'http://localhost:8000' : '';

async function loadChatHistory(requestId) {
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
async function sendChatMessage(requestId) {
    const messageInput = document.getElementById('messageInput');
    const text = messageInput.value.trim();
    
    if (!text) return;
    
    try {
        // Get current user ID from Telegram WebApp
        const userId = tg.initDataUnsafe.user.id;
        
        // Send message to API
        const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender_id: userId,
                sender_type: 'user',
                message: text
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.status}`);
        }
        
        // Add message to UI and clear input...
    } catch (error) {
        // Handle error...
    }
}
```

### Polling for Updates

To keep the conversation current, the interface polls for new messages using the timestamp-based endpoint with improved handling for timezones:

```javascript
function startPolling(requestId) {
    // Clear any existing polling
    stopPolling();
    
    // Ensure we have a valid timestamp before starting polling
    if (!lastMessageTimestamp) {
        lastMessageTimestamp = getCurrentTimestamp();
    } else {
        lastMessageTimestamp = formatTimestamp(lastMessageTimestamp);
    }
    
    isPolling = true;
    
    async function pollMessages() {
        try {
            const timestamp = formatTimestamp(lastMessageTimestamp);
            
            // Try multiple endpoints for better reliability
            const endpoints = [
                `${API_BASE_URL}/api/chat/${requestId}/messages?since=${encodeURIComponent(timestamp)}`,
                `${API_BASE_URL}/api/support/chat/${requestId}/messages?since=${encodeURIComponent(timestamp)}`
            ];
            
            // Try each endpoint until one succeeds
            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(endpoint, {
                        headers: {
                            'Cache-Control': 'no-cache',
                            'X-Last-Timestamp': timestamp,
                            'X-User-ID': currentUserId,
                            'X-User-Type': currentUserType
                        }
                    });
                    
                    if (response.ok) {
                        const messages = await response.json();
                        
                        // Process new messages with proper timestamp comparison
                        messages.forEach(msg => {
                            const msgTimestamp = formatTimestamp(msg.timestamp);
                            
                            // Only add message if it's newer than last seen
                            if (isNewerTimestamp(msgTimestamp, lastMessageTimestamp)) {
                                addMessage(msg);
                                lastMessageTimestamp = msgTimestamp;
                            }
                        });
                        
                        break; // Exit the endpoints loop if successful
                    }
                } catch (error) {
                    // Will try next endpoint
                }
            }
        } catch (error) {
            console.error('Error polling messages:', error);
        }
    }
    
    // Poll for messages every second
    pollingInterval = setInterval(pollMessages, 1000);
    pollMessages(); // Initial poll
}
```

### Message Display

Messages are displayed with proper timezone handling:

```javascript
function addMessage(message) {
    // Ensure ISO timestamp for display
    const timestamp = formatTimestamp(message.timestamp);
    const displayTime = formatDateForDisplay(timestamp);
    
    // For messages with significant timezone differences, show both local and UTC time
    const date = new Date(timestamp);
    const utcHours = date.getUTCHours().toString().padStart(2, '0');
    const utcMinutes = date.getUTCMinutes().toString().padStart(2, '0');
    const utcTimeString = `${utcHours}:${utcMinutes}`;
    
    const localHours = date.getHours().toString().padStart(2, '0');
    const localMinutes = date.getMinutes().toString().padStart(2, '0');
    const localTimeString = `${localHours}:${localMinutes}`;
    
    // Determine if we need to show both times for clarity
    const showBothTimes = localTimeString !== utcTimeString;
    const timeDisplay = showBothTimes ? 
        `${displayTime} (UTC: ${utcTimeString})` : 
        displayTime;
    
    // Display message with appropriate time information
    // ...
}
```

### Time Indicators

The interface provides visual time indicators in the chat header:

```html
<div class="chat-header">
    <div class="chat-header-row">
        <h3 id="requestTitle">Support Request #${requestId}</h3>
        <div id="requestStatus">Status: ${status}</div>
    </div>
    <div class="time-info">
        <span id="clientTimeDisplay">Local: ${clientTime}</span>
        <span id="serverTimeDisplay">Server: ${serverTime}</span>
    </div>
    <div class="time-difference-indicator" id="timeDifferenceIndicator"></div>
</div>
```

## Styling

The interface is styled using CSS variables that adapt to Telegram's theme, with specific styles for the chat interface:

```css
/* Chat container */
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-width: 100%;
    margin: 0 auto;
}

/* Chat messages */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.message {
    max-width: 80%;
    padding: 8px 12px;
    border-radius: 12px;
    position: relative;
    animation: fadeIn 0.3s ease;
    word-wrap: break-word;
}

.my-message {
    align-self: flex-end;
    background-color: var(--tg-theme-button-color);
    color: var(--tg-theme-button-text-color);
}

.admin-message {
    align-self: flex-start;
    background-color: var(--tg-theme-secondary-bg-color);
    color: var(--tg-theme-text-color);
}
```

## Deployment

The WebApp HTML file should be hosted at the URL specified in the `BASE_WEBAPP_URL` environment variable. This URL is used when generating the WebApp button in the admin interface. 