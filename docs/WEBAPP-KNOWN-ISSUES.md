# WebApp Known Issues and Solutions

This document tracks significant issues identified in the WebApp components of the Support Bot project, along with their solutions.

## Resolved Issues

### Message Visibility in Chat Interface (Resolved in v1.2.1)

#### Issue Description
Users and admins were only able to see their own messages in the chat interface, despite messages being properly stored in the database. This created a poor user experience where neither party could see the other's responses.

#### Root Cause
The issue was traced to the message rendering logic in `chat.html`. The `addMessage` function was applying styles in a way that made messages from the other party effectively invisible or incorrectly positioned.

Key problematic code:
```javascript
// Original problematic code
function addMessage(message) {
    const isAdmin = message.sender_type === 'admin';
    const isMine = message.sender_id === (adminIdFromQuery || tg.initDataUnsafe?.user?.id);

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isAdmin ? 'admin-message' : 'user-message'} ${isMine ? 'my-message' : ''}`;
    
    // ...rest of code...
}
```

Additional issues:
1. String vs. number type mismatch when comparing user IDs
2. Lack of visual indication of message sender
3. No deduplication when reconnecting or reloading the chat
4. CSS styling issues in message bubbles

#### Solution
The fix included several key improvements:

1. **Fixed message rendering logic**: Updated the display logic to properly show all messages regardless of sender.
2. **String type comparison**: Changed ID comparison to use `.toString()` to avoid type mismatch issues.
3. **Added sender labels**: Added clear "You" vs "Admin/User" labels to improve readability.
4. **Message deduplication**: Added checks to prevent duplicate messages from appearing.
5. **Enhanced styling**: Updated CSS to properly differentiate messages and improve visual clarity.
6. **Debug logging**: Added extensive console logging to help identify and diagnose issues.

Key fixed code:
```javascript
function addMessage(message) {
    // Don't process duplicate messages
    if (message.id) {
        const existingMsg = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMsg) return;
    }
    
    const isAdmin = message.sender_type === 'admin';
    const isMine = message.sender_id.toString() === currentUserId.toString();
    
    // Create and style message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isAdmin ? 'admin-message' : 'user-message'} ${isMine ? 'my-message' : ''}`;
    
    if (message.id) {
        messageDiv.setAttribute('data-message-id', message.id);
    }

    // Add sender label for clarity
    const senderLabel = isAdmin ? 'Admin' : 'User';
    
    messageDiv.innerHTML = `
        <div class="message-sender">${isMine ? 'You' : senderLabel}</div>
        <div class="message-content">${escapeHtml(message.message)}</div>
        <div class="message-time">${time}</div>
        <div class="message-timestamp" style="display: none;">${timestamp}</div>
    `;
}
```

#### Verification
This issue has been successfully resolved in version 1.2.1 (released 2025-03-20). The fix can be verified by:
1. Opening the chat from both user and admin sides
2. Checking that both parties can see each other's messages
3. Verifying that messages are properly styled and labeled

### Timestamp Handling Issues (Resolved in v1.2.1)

#### Issue Description
Messages were being displayed out of order due to inconsistent handling of timestamps between frontend and backend. In some cases, messages would not appear at all because of timezone differences.

#### Root Cause
The WebApp was not properly handling ISO 8601 format timestamps with timezone information, leading to comparison issues. The backend was also inconsistent in how it processed timestamps with different timezone information.

#### Solution
1. **Frontend**: Implemented the `ensureISOTimestamp` function to standardize all timestamp handling:

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

2. **Backend**: Enhanced the timestamp handling in API endpoints to properly process various timestamp formats and always return ISO 8601 format with UTC timezone:

```python
# Convert the UTC timestamp to datetime - be more lenient with format
try:
    # First try standard ISO format with Z suffix
    try:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
    except ValueError:
        # Try parsing as a datetime without timezone info
        try:
            since_dt = datetime.fromisoformat(since)
            # Add UTC timezone if missing
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            # Last resort: try standard datetime parsing
            since_dt = datetime.strptime(since, "%Y-%m-%dT%H:%M:%S.%f")
            since_dt = since_dt.replace(tzinfo=timezone.utc)
    
    # Ensure we have timezone info
    if since_dt.tzinfo is None:
        since_dt = since_dt.replace(tzinfo=timezone.utc)
```

3. **API Route Handling**: Fixed the API route handling in `main.py` to properly direct timestamp-related requests to the appropriate endpoint handlers.

#### Verification
This issue has been successfully resolved in version 1.2.1. The fix can be verified by:
1. Testing the chat between users with different local time zones
2. Confirming messages appear in the correct chronological order
3. Verifying that all timestamps are properly formatted in the logs

## Future Planned Improvements

1. **WebSocket Support**: Implementing WebSocket communication for real-time message delivery.
2. **Typing Indicators**: Adding typing status indicators to improve chat experience.
3. **Media Message Support**: Enhancing the chat to support image and file sharing.
4. **Offline Message Queue**: Adding support for offline message queuing. 