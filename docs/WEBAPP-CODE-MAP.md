# WebApp Support Bot Code Map

This document provides a comprehensive overview of the WebApp components of the Support Bot project, focusing on the frontend architecture, key files, and interactions with the backend API.

## WebApp Structure

```
webapp-support-bot/
├── index.html              # Main entry point and support request form
├── chat.html               # Chat interface for support conversations
├── support-form.html       # Dedicated support request form
├── css/                    # Stylesheet directory
│   ├── style.css           # Main styles for the WebApp
│   └── chat-style.css      # Styles specific to the chat interface
├── js/                     # JavaScript directory
│   ├── webapp.js           # Main WebApp functionality
│   ├── chat.js             # Chat interface functionality
│   └── telegram-utils.js   # Telegram WebApp API utilities
└── assets/                 # Images and other static assets
```

## Key Components

### 1. Support Request Form (`index.html` / `support-form.html`)

The Support Request Form is the initial interface users interact with when they start the WebApp from Telegram. It:

- Collects issue details from the user
- Integrates with Telegram theme
- Handles form submission to the API
- Transitions to chat view after submission

#### Key HTML Elements:

```html
<div class="container">
    <div class="form-container">
        <h2>Submit Support Request</h2>
        <form id="supportForm">
            <div class="form-group">
                <label for="issue">Describe your issue:</label>
                <textarea id="issue" required></textarea>
                <div id="issueLength">0/500 characters</div>
            </div>
            <button type="submit" id="submitButton">Submit Request</button>
        </form>
        <div id="error" class="error"></div>
        <div id="loading" class="loading-spinner" style="display: none;"></div>
    </div>
</div>
```

#### Key JavaScript Functions:

- `initializeWebApp()`: Sets up the Telegram WebApp environment
- `submitRequest()`: Handles form submission and API interaction
- `validateForm()`: Validates user input before submission
- `switchToChatView()`: Transitions to the chat interface after submission

### 2. Chat Interface (`chat.html`)

The Chat Interface provides the conversation view between users and support administrators. It:

- Displays the message history
- Polls for new messages in real-time
- Allows sending new messages
- Adapts to Telegram's theme

#### Key HTML Elements:

```html
<div class="chat-container">
    <div class="chat-header">
        <h2 id="requestTitle">Support Request #${requestId}</h2>
        <div id="requestStatus">Status: ${data.status}</div>
    </div>
    <div id="messagesContainer" class="messages-container">
        <!-- Messages are dynamically inserted here -->
    </div>
    <div class="chat-input">
        <textarea id="messageInput" placeholder="Type your message..."></textarea>
        <button id="sendButton">Send</button>
    </div>
</div>
```

#### Key JavaScript Functions:

- `loadChatHistory(requestId)`: Fetches chat data with fallback mechanisms
- `sendChatMessage(requestId)`: Sends new messages to the API
- `startPolling(requestId)`: Begins polling for new messages
- `addMessage(text, isAdmin, timestamp, isMine)`: Adds messages to the UI
- `scrollToBottom()`: Scrolls to the most recent messages

### 3. Telegram WebApp Integration

Both interfaces integrate with the Telegram WebApp API to provide a seamless experience within Telegram:

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
}
```

## Data Flow in WebApp

### 1. Support Request Submission

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│            │     │            │     │            │
│  Form      │────▶│  submitForm│────▶│  API Call  │
│  Elements  │     │  Handler   │     │  POST      │
│            │     │            │     │            │
└────────────┘     └────────────┘     └────────────┘
                                             │
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │  Response  │
                                      │  Handler   │
                                      │            │
                                      └────────────┘
                                             │
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │  Transition│
                                      │  To Chat   │
                                      │            │
                                      └────────────┘
```

### 2. Chat Interface Initialization

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│            │     │            │     │            │
│  Chat View │────▶│  loadChat  │────▶│ Try Main   │
│  Loaded    │     │  History   │     │ Endpoint   │
│            │     │            │     │            │
└────────────┘     └────────────┘     └────────────┘
                                             │
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │ Success?   │─────Yes──▶ Done
                                      │            │
                                      └────────────┘
                                             │
                                             │ No
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │ Try Next   │
                                      │ Fallback   │
                                      │            │
                                      └────────────┘
```

### 3. Message Polling Sequence

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│            │     │            │     │            │
│  Start     │────▶│  setInterval │──▶│  API Call  │
│  Polling   │     │  (3 sec)   │     │  GET       │
│            │     │            │     │            │
└────────────┘     └────────────┘     └────────────┘
                                             │
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │  Process   │
                                      │  Response  │
                                      │            │
                                      └────────────┘
                                             │
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │  Update UI │
                                      │  If Needed │
                                      │            │
                                      └────────────┘
```

## Key API Interactions

### 1. Support Request Submission

```javascript
async function submitRequest() {
    // Show loading indicator
    showLoading();
    hideError();
    
    // Get form data
    const issue = document.getElementById('issue').value.trim();
    
    // Disable button during submission
    const submitButton = document.getElementById('submitButton');
    submitButton.disabled = true;
    
    try {
        // Get current user ID from Telegram WebApp
        const userId = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;
        
        if (!userId) {
            throw new Error("Could not identify user");
        }
        
        // Prepare request data
        const requestData = {
            user_id: userId,
            issue: issue
        };
        
        // Log the attempt
        logWebAppEvent('info', 'Submitting support request', {
            platform: tg.platform,
            userId: userId,
            issueLength: issue.length,
            buttonState: 'submitting'
        });
        
        // Submit the request
        const response = await fetch(`${API_BASE_URL}/support-request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to submit request: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Log successful submission
        logWebAppEvent('info', 'Support request submitted successfully', {
            platform: tg.platform,
            userId: userId,
            requestId: data.request_id,
            buttonState: 'success'
        });
        
        // Switch to chat view with the request ID
        switchToChatView(data.request_id);
        
    } catch (error) {
        // Log error
        logWebAppEvent('error', 'Failed to submit support request', {
            platform: tg.platform,
            userId: tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 'unknown',
            error: error.message,
            buttonState: 'error'
        });
        
        // Show error message
        showError(`Failed to submit request: ${error.message}`);
        
        // Re-enable button for retry
        submitButton.disabled = false;
        hideLoading();
    }
}
```

### 2. Chat History Loading with Fallbacks

```javascript
async function loadChatHistory(requestId) {
    try {
        const endpoints = [
            `${API_BASE_URL}/api/chat_api/${requestId}`,
            `${API_BASE_URL}/api/support/chat/${requestId}`,
            `${API_BASE_URL}/debug/chat/${requestId}`,
            `${API_BASE_URL}/fixed-chat/${requestId}`
        ];

        let lastError = null;
        let data = null;
        
        for (const endpoint of endpoints) {
            try {
                console.log(`Attempting to fetch chat history from: ${endpoint}`);
                const response = await fetch(endpoint);
                
                if (!response.ok) {
                    console.warn(`Failed to load chat history from ${endpoint}: ${response.status} ${response.statusText}`);
                    lastError = new Error(`HTTP error: ${response.status}`);
                    continue;
                }
                
                data = await response.json();
                console.log(`Chat history loaded from ${endpoint}:`, data);
                
                if (!data) {
                    console.warn(`Endpoint ${endpoint} returned null or empty data`);
                    lastError = new Error('Null response');
                    continue;
                }
                
                // If we got data, break out of the loop
                console.log(`Successfully loaded data from ${endpoint}`);
                break;
            } catch (error) {
                console.error(`Error loading chat history from ${endpoint}:`, error);
                lastError = error;
            }
        }
        
        // If all attempts failed or returned null
        if (!data) {
            throw lastError || new Error('Failed to load chat history from all endpoints');
        }
        
        // Process the data and update UI
        // ...rest of implementation...
    } catch (error) {
        console.error('Error loading chat:', error);
        showError(`Error Loading Chat\n${error.message}\n\nYour request has been submitted. Please try again later.`);
        hideLoading();
    }
}
```

### 3. Message Polling Implementation

```javascript
function startPolling(requestId) {
    // Clear any existing polling
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Set last message timestamp
    let lastMessageTimestamp = new Date();
    
    // Log start of polling
    console.log(`Starting polling for request ${requestId} from timestamp ${lastMessageTimestamp.toISOString()}`);
    
    // Poll for new messages every 3 seconds
    pollingInterval = setInterval(async () => {
        try {
            const since = lastMessageTimestamp.toISOString();
            const response = await fetch(
                `${API_BASE_URL}/api/chat/${requestId}/messages?since=${encodeURIComponent(since)}`
            );
            
            if (!response.ok) {
                console.warn(`Failed to poll messages: ${response.status} ${response.statusText}`);
                return;
            }
            
            const newMessages = await response.json();
            
            if (newMessages && newMessages.length > 0) {
                console.log(`Received ${newMessages.length} new messages`);
                
                // Update lastMessageTimestamp to the most recent message time
                lastMessageTimestamp = new Date(newMessages[newMessages.length - 1].timestamp);
                
                // Add new messages to the UI
                newMessages.forEach(msg => {
                    const msgIsFromAdmin = msg.sender_type === 'admin';
                    const isMine = isAdmin ? msgIsFromAdmin : !msgIsFromAdmin;
                    addMessage(msg.message, msgIsFromAdmin, new Date(msg.timestamp), isMine);
                });
                
                // Scroll to bottom
                scrollToBottom();
            }
        } catch (error) {
            console.error('Error polling messages:', error);
            // Polling continues even after errors
        }
    }, 3000);
}
```

## UI Components and Styling

The WebApp uses a combination of HTML, CSS, and JavaScript to create a responsive user interface that adapts to Telegram's theme:

### Theme Integration

```javascript
function setThemeColors() {
    // Apply Telegram theme colors to CSS variables
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f1f1f1');
}
```

### Message Bubbles

Messages are displayed in chat bubbles with different styles for user and admin messages:

```html
<div class="message ${isAdmin ? 'admin-message' : 'user-message'} ${isMine ? 'mine' : ''}">
    <div class="message-content">${text}</div>
    <div class="message-time">${formattedTime}</div>
</div>
```

```css
.message {
    max-width: 80%;
    margin-bottom: 10px;
    padding: 10px 15px;
    border-radius: 15px;
    position: relative;
}

.user-message {
    background-color: var(--tg-theme-button-color);
    color: var(--tg-theme-button-text-color);
    align-self: flex-end;
    border-bottom-right-radius: 5px;
}

.admin-message {
    background-color: var(--tg-theme-secondary-bg-color);
    color: var(--tg-theme-text-color);
    align-self: flex-start;
    border-bottom-left-radius: 5px;
}
```

## Error Handling and Logging

The WebApp implements comprehensive error handling and logging:

### WebApp Event Logging

```javascript
async function logWebAppEvent(level, message, context = {}) {
    try {
        // Add standard Telegram context
        const fullContext = {
            ...context,
            platform: tg.platform || 'unknown',
            version: tg.version || 'unknown',
            viewportHeight: tg.viewportHeight,
            viewportStableHeight: tg.viewportStableHeight,
            isExpanded: tg.isExpanded,
            backgroundColor: tg.backgroundColor
        };
        
        // Log to console first (for immediate feedback)
        console.log(`WebApp ${level}: ${message}`, fullContext);
        
        // Send to server logging endpoint
        await fetch(`${API_BASE_URL}/api/webapp-log`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                level,
                message,
                context: fullContext
            })
        });
    } catch (e) {
        // Log locally if server logging fails
        console.error('Failed to log event to server:', e);
    }
}
```

### Fallback Mechanisms

The WebApp implements multiple fallback mechanisms to ensure reliability:

1. **Multiple API Endpoints**: Tries several endpoints in sequence
2. **Graceful Error UI**: Shows user-friendly error messages
3. **Continued Polling**: Polling continues even after intermittent errors
4. **Local Error Logging**: Logs errors locally when server logging fails

## Current Behavior and Future Enhancements

### Current Implementation for Messages Polling

The logs show the current polling behavior for messages:

```
supportbot-1 | 2025-03-18 11:05:03,309 - INFO - Returning empty array for chat messages polling: /api/chat/32/messages
supportbot-1 | INFO: 172.19.0.1:48170 - "GET /api/chat/32/messages?since=2025-03-18T10%3A48%3A36.250Z HTTP/1.1" 200 OK
```

These logs indicate:
- The client polls every 3 seconds
- It uses a timestamp parameter to retrieve only new messages
- The server returns an empty array response, which is handled gracefully

### Planned Enhancements

1. **Real-time Message Updates**:
   - Consider WebSockets for true real-time communication
   - Implement Server-Sent Events (SSE) as a fallback

2. **Optimized Polling**:
   - Add exponential backoff for quieter periods
   - Implement pagination for high-volume chats

3. **UI Enhancements**:
   - Add typing indicators
   - Implement read receipts
   - Add support for rich media messages

4. **Performance Optimizations**:
   - Implement virtual scrolling for long chats
   - Add message caching to reduce API calls

## Implementing Admin Chat Interface

The next phase will involve implementing the admin chat interface. Key components will include:

1. **Request Assignment**:
   - Admin clicks "Assign" in notification
   - Request status updates to "assigned"
   - Other admins see assignment status

2. **Admin Chat UI**:
   - Similar to user chat but with admin controls
   - Ability to view user details
   - Options to mark as resolved

3. **Integration Points**:
   - Shared database tables for messages
   - Common API endpoints with role-based permissions
   - Consistent message format for both interfaces

The existing WebApp code provides a strong foundation for these enhancements, with the modular architecture making it straightforward to extend. 