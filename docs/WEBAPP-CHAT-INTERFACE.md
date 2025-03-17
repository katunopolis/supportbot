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

// Set theme based on Telegram settings
function setThemeColors() {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f1f1f1');
}
```

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

To keep the conversation current, the interface polls for new messages using the timestamp-based endpoint:

```javascript
function startPolling(requestId) {
    // Clear any existing polling
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Set last message timestamp
    let lastMessageTimestamp = new Date();
    
    // Poll for new messages every 3 seconds
    pollingInterval = setInterval(async () => {
        try {
            // Only poll if we're still in chat view
            if (currentView !== 'chat') {
                clearInterval(pollingInterval);
                return;
            }
            
            const since = lastMessageTimestamp.toISOString();
            const response = await fetch(
                `${API_BASE_URL}/api/chat/${requestId}/messages?since=${encodeURIComponent(since)}`
            );
            
            if (!response.ok) {
                throw new Error(`Failed to poll messages: ${response.status}`);
            }
            
            const newMessages = await response.json();
            
            if (newMessages && newMessages.length > 0) {
                // Update lastMessageTimestamp
                lastMessageTimestamp = new Date(newMessages[newMessages.length - 1].timestamp);
                
                // Add new messages to UI...
            }
            
        } catch (error) {
            console.error('Error polling messages:', error);
        }
    }, 3000);
}
```

### Fallback Mechanism

The interface includes a fallback mechanism to handle API errors gracefully:

```javascript
// If the API fails, create a fallback chat with just the initial message
const fallbackChat = {
    request_id: requestId,
    user_id: tg.initDataUnsafe.user.id,
    status: "pending",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    issue: document.getElementById('issue')?.value || "Support request",
    solution: null,
    messages: [{
        id: 1,
        request_id: requestId,
        sender_id: tg.initDataUnsafe.user.id,
        sender_type: "user",
        message: document.getElementById('issue')?.value || "Support request",
        timestamp: new Date().toISOString()
    }]
};

// Update the chat interface with fallback data
document.getElementById('requestStatus').textContent = `Status: ${fallbackChat.status}`;
document.getElementById('messagesContainer').innerHTML = `
    <div class="status">Issue: ${fallbackChat.issue}</div>
    ${fallbackChat.messages.map(msg => createMessageHTML(msg)).join('')}
    <div class="status">
        Note: We're experiencing some technical difficulties. 
        Your request has been submitted and our team will respond shortly.
    </div>
`;
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