# WebApp Support Bot Code Map

This document provides a comprehensive overview of the WebApp components of the Support Bot project, focusing on the frontend architecture, key files, and interactions with the backend API.

## WebApp Structure

```
webapp-support-bot/
├── index.html              # Main entry point and support request form
├── chat.html               # Chat interface for support conversations
├── support-form.html       # Dedicated support request form
├── admin-panel.html        # Admin panel for managing support requests
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

The Chat Interface provides the conversation view between users and support administrators. It includes robust error handling and fallback mechanisms:

#### Enhanced Chat Loading

```javascript
async function loadChatHistory(requestId) {
    const endpoints = [
        `${API_BASE_URL}/api/chat/${requestId}`,
        `${API_BASE_URL}/api/support/chat/${requestId}`,
        `${API_BASE_URL}/debug/chat/${requestId}`,
        `${API_BASE_URL}/fixed-chat/${requestId}`
    ];

    let lastError = null;
    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint);
            if (response.ok) {
                const data = await response.json();
                return data;
            }
        } catch (error) {
            lastError = error;
            logWebAppEvent('error', `Failed to load chat from ${endpoint}`, {
                requestId,
                error: error.message
            });
        }
    }
    
    throw lastError || new Error('Failed to load chat history from all endpoints');
}
```

#### Enhanced Message Polling

```javascript
async function startPolling(requestId) {
    if (isPolling) {
        console.warn('Already polling, skipping startPolling');
        return;
    }
    
    stopPolling(); // Clean up any existing interval
    
    // Ensure we have a valid timestamp before starting polling
    if (!lastMessageTimestamp) {
        console.warn('No lastMessageTimestamp available, initializing with current time');
        lastMessageTimestamp = new Date().toISOString();
    } else {
        lastMessageTimestamp = ensureISOTimestamp(lastMessageTimestamp);
    }
    
    isPolling = true;
    let retryCount = 0;
    const maxRetryDelay = 5000;
    const baseDelay = 1000;
    
    async function pollMessages() {
        // Skip if we're initializing or if polling has been stopped
        if (isInitializing || !isPolling) {
            return;
        }

        try {
            const timestamp = ensureISOTimestamp(lastMessageTimestamp);
            
            const response = await fetch(
                `${API_BASE_URL}/api/chat/${requestId}/messages?since=${encodeURIComponent(timestamp)}`,
                { 
                    headers: { 
                        'Cache-Control': 'no-cache',
                        'X-Last-Timestamp': timestamp
                    }
                }
            );
            
            if (response.ok) {
                const messages = await response.json();
                if (messages && messages.length > 0) {
                    messages.forEach(msg => {
                        const msgTimestamp = ensureISOTimestamp(msg.timestamp);
                        if (msgTimestamp > lastMessageTimestamp) {
                            msg.timestamp = msgTimestamp;
                            addMessage(msg);
                            lastMessageTimestamp = msgTimestamp;
                        }
                    });
                    scrollToBottom();
                    retryCount = 0;
                }
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Error polling messages:', error);
            retryCount++;
            
            if (retryCount > 3) {
                stopPolling();
                await loadChatHistory(); // Reload chat history instead of just reinitializing
                return;
            }
            
            // Back off exponentially on errors
            const delay = Math.min(baseDelay * Math.pow(2, retryCount), maxRetryDelay);
            clearInterval(pollingInterval);
            if (isPolling) { // Only set new interval if still polling
                pollingInterval = setInterval(pollMessages, delay);
            }
        }
    }

    pollingInterval = setInterval(pollMessages, baseDelay);
    pollMessages(); // Initial poll
}
```

#### Enhanced Error Handling

```javascript
function handleError(error, context) {
    // Log the error with context
    logWebAppEvent('error', error.message, {
        context,
        platform: tg.platform,
        viewportHeight: tg.viewportHeight,
        timestamp: new Date().toISOString()
    });

    // Show user-friendly error message
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = 'An error occurred. Please try again.';
    errorDiv.style.display = 'block';

    // Hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}
```

#### WebApp Event Logging

```javascript
async function logWebAppEvent(level, message, context = {}) {
    try {
        await fetch(`${API_BASE_URL}/api/logs/webapp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                level,
                message,
                context: {
                    ...context,
                    platform: tg.platform,
                    colorScheme: tg.colorScheme,
                    viewportHeight: tg.viewportHeight
                }
            })
        });
    } catch (error) {
        console.error('Failed to log event:', error);
    }
}
```

### 3. Admin Panel Interface (`admin-panel.html`)

The Admin Panel interface provides administrators with a comprehensive dashboard to manage all support requests:

#### Key HTML Elements:

```html
<div class="container">
    <div class="header">
        <h1>Support Requests</h1>
    </div>
    
    <div id="requestList" class="request-list">
        <!-- Requests will be populated here -->
    </div>
    
    <div id="loading" class="loading" style="display: none;">
        Loading requests...
    </div>
    
    <div id="error" class="error" style="display: none;">
        Error loading requests. Please try again.
    </div>
</div>
```

#### Key JavaScript Functions:

- `loadOpenRequests()`: Fetches and displays all open support requests
- `openChat(requestId)`: Opens the chat interface for a specific request
- `solveRequest(requestId)`: Marks a request as solved
- `setThemeColors()`: Adapts the interface to match Telegram's theme

#### API Interactions:

```javascript
async function loadOpenRequests() {
    try {
        const response = await fetch('/api/support/requests?status=open');
        if (!response.ok) {
            throw new Error('Failed to load requests');
        }
        
        const requests = await response.json();
        
        if (requests.length === 0) {
            requestList.innerHTML = '<div class="request-card">No open requests at the moment.</div>';
        } else {
            requests.forEach(request => {
                const card = document.createElement('div');
                card.className = 'request-card';
                
                card.innerHTML = `
                    <div class="request-header">
                        <span class="request-id">Request #${request.id}</span>
                        <span class="request-status status-${request.status.toLowerCase()}">${request.status}</span>
                    </div>
                    <div class="request-issue">${request.issue}</div>
                    <div class="request-actions">
                        <button class="button button-primary" onclick="openChat(${request.id})">Open Chat</button>
                        <button class="button button-secondary" onclick="solveRequest(${request.id})">Solve</button>
                    </div>
                `;
                
                requestList.appendChild(card);
            });
        }
    } catch (err) {
        error.textContent = err.message;
        error.style.display = 'block';
    }
}
```

### 4. Telegram WebApp Integration

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

### 3. Message Polling Sequence (Updated)

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│            │     │            │     │            │
│  Start     │────▶│ Initialize │────▶│ Validate   │
│  Polling   │     │ Timestamp  │     │ ISO Format │
│            │     │            │     │            │
└────────────┘     └────────────┘     └────────────┘
                                             │
                                             ▼
                                      ┌────────────┐
                                      │            │
                                      │  API Call  │
                                      │  with ISO  │
                                      │  Timestamp │
                                      └────────────┘
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
                                      ┌────────────┐     ┌────────────┐
                                      │            │     │            │
                                      │  Update UI │────▶│ Update ISO │
                                      │  If Needed │     │ Timestamp  │
                                      │            │     │            │
                                      └────────────┘     └────────────┘
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
    const endpoints = [
        `${API_BASE_URL}/api/chat/${requestId}`,
        `${API_BASE_URL}/api/support/chat/${requestId}`,
        `${API_BASE_URL}/debug/chat/${requestId}`,
        `${API_BASE_URL}/fixed-chat/${requestId}`
    ];

    let lastError = null;
    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint);
            if (response.ok) {
                const data = await response.json();
                return data;
            }
        } catch (error) {
            lastError = error;
            logWebAppEvent('error', `Failed to load chat from ${endpoint}`, {
                requestId,
                error: error.message
            });
        }
    }
    
    throw lastError || new Error('Failed to load chat history from all endpoints');
}
```

### 3. Message Polling Implementation

```javascript
async function startPolling(requestId) {
    let lastTimestamp = new Date().toISOString();
    
    setInterval(async () => {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/chat/${requestId}/messages?since=${lastTimestamp}`
            );
            
            if (response.ok) {
                const messages = await response.json();
                if (messages && messages.length > 0) {
                    messages.forEach(msg => addMessage(msg));
                    lastTimestamp = messages[messages.length - 1].timestamp;
                }
            } else {
                // Handle empty response gracefully
                logWebAppEvent('info', 'No new messages in polling', {
                    requestId,
                    timestamp: lastTimestamp
                });
            }
        } catch (error) {
            logWebAppEvent('error', 'Error polling messages', {
                requestId,
                error: error.message
            });
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
        await fetch(`${API_BASE_URL}/api/logs/webapp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                level,
                message,
                context: {
                    ...context,
                    platform: tg.platform,
                    colorScheme: tg.colorScheme,
                    viewportHeight: tg.viewportHeight
                }
            })
        });
    } catch (error) {
        console.error('Failed to log event:', error);
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

## Message Handling and Display (Updated in v1.2.1)

The WebApp implements a robust message handling system with recent improvements to fix visibility issues:

### Enhanced Message Rendering (v1.2.1)

The message rendering logic was updated to properly handle messages from both admin and user sides:

```javascript
// Enhanced message rendering with proper visibility for all parties
function addMessage(message) {
    // Prevent duplicate messages (added in v1.2.1)
    if (message.id) {
        const existingMsg = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMsg) {
            console.log(`Message ID ${message.id} already exists, skipping`);
            return;
        }
    }
    
    const isAdmin = message.sender_type === 'admin';
    const isMine = message.sender_id.toString() === currentUserId.toString();
    
    // Create message element with proper styling for visibility
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isAdmin ? 'admin-message' : 'user-message'} ${isMine ? 'my-message' : ''}`;
    
    // Add data attribute for deduplication (added in v1.2.1)
    if (message.id) {
        messageDiv.setAttribute('data-message-id', message.id);
    }

    // Add sender label for clarity (added in v1.2.1)
    const senderLabel = isAdmin ? 'Admin' : 'User';
    
    // Enhanced message structure with sender identification
    messageDiv.innerHTML = `
        <div class="message-sender">${isMine ? 'You' : senderLabel}</div>
        <div class="message-content">${escapeHtml(message.message)}</div>
        <div class="message-time">${time}</div>
        <div class="message-timestamp" style="display: none;">${timestamp}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
}
```

Key improvements in v1.2.1:
1. Fixed message visibility between admin and user
2. Added message deduplication
3. Added clear sender labels
4. Improved message styling for better visibility
5. Fixed ID comparison with string conversion

### CSS Styling Updates

The styling was enhanced to provide better visual differentiation:

```css
/* Styling for user vs admin messages (updated in v1.2.1) */
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

/* Styling for own messages vs others (updated in v1.2.1) */
.my-message {
    align-self: flex-end;
    border-bottom-right-radius: 4px;
    border-bottom-left-radius: var(--message-radius);
}

/* Special styling for own messages by type (added in v1.2.1) */
.my-message.user-message {
    background-color: #e1f5fe;
    color: #0277bd;
}

.my-message.admin-message {
    background-color: #1976d2;
    color: white;
}

/* Sender label styling (added in v1.2.1) */
.message-sender {
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 2px;
    opacity: 0.8;
}
```
