# Security Implementation

This document describes the security implementations in the Support Bot system, particularly focusing on how we handle public group chat scenarios.

## Group Chat Security

When users activate the support bot from a public group chat, we've implemented several security measures to ensure that only the user who initiated the request can access the support form and chat:

### 1. URL Parameter Security

- When a user sends the `/request` command in a group, the WebApp URL includes their `user_id` as a parameter
- Example: `https://webapp-domain.com/support-form.html?user_id=123456789`
- This parameter is used for verification on both frontend and backend

### 2. Frontend Security Checks

#### Support Form Verification
- The `support-form.html` implements verification that compares the URL's `user_id` parameter against the actual Telegram WebApp user ID
- If they don't match, the form is disabled and an error message is displayed
- This prevents other users from submitting requests through the same button

#### Chat Interface Verification
- Similar verification is implemented in `chat.html`
- The `verifyUserAccess()` function performs the comparison and blocks unauthorized access
- Only the user who initiated the request can view and interact with the chat

### 3. Backend Security Checks

- All API endpoints that handle chat data or message sending include user verification
- The backend compares the `user_id` parameter against the request owner's ID
- Unauthorized attempts result in 403 Forbidden responses
- Double verification ensures that even if frontend verification is bypassed, the backend will still block unauthorized access

### 4. Security Logging

- Comprehensive logging tracks all verification checks and unauthorized attempts
- Log entries include user IDs and request IDs for audit trails
- Failed verification attempts are logged with warning level for monitoring

## Private Chat Security

In private chats (direct messages to the bot), we apply the same security model for consistency, but verification is less critical since the WebApp is already within the user's private conversation with the bot.

## Error Handling

- Security checks include robust error handling to prevent legitimate users from being blocked due to technical issues
- Clear, user-friendly error messages explain access restrictions without revealing sensitive information
- Fallback mechanisms ensure the system remains usable even if parts of the security verification encounter problems

## Implementation Details

### Key Files
- `app/bot/handlers/start.py`: Adds user_id to WebApp URLs
- `webapp-support-bot/support-form.html`: Frontend verification for the support form
- `webapp-support-bot/chat.html`: Frontend verification for the chat interface
- `app/api/routes/support.py`: Backend verification for API endpoints

### Verification Logic

```javascript
// Frontend verification example (simplified)
function verifyUserAccess() {
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    
    if (!userId) return true; // Direct access case
    
    const currentUserId = window.Telegram.WebApp.initDataUnsafe.user.id.toString();
    if (currentUserId !== userId) {
        // Show error and disable interface
        return false;
    }
    
    return true;
}
```

```python
# Backend verification example (simplified)
if user_id:
    requested_user_id = str(user_id)
    request_owner_id = str(request.user_id)
    
    if requested_user_id != request_owner_id:
        logging.warning(f"Unauthorized access attempt: User {user_id} tried to access request {request_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to access this chat")
```

## Security Considerations

- This implementation focuses on preventing casual unauthorized access
- For higher security requirements, additional measures like cryptographic signatures could be implemented
- Regular security audits should review these verification mechanisms 