# Chat API Endpoints

This document outlines the Chat API endpoints implemented for the Telegram Support Bot.

## Overview

The Chat API enables seamless communication between users and admins by providing endpoints to retrieve conversation history and send messages.

## API Routes

All chat endpoints are prefixed with `/api/chat` and defined in `app/api/routes/chat.py`.

### Timestamp Handling

All timestamp fields in the API use ISO 8601 format in UTC timezone (e.g., `2025-03-17T10:30:00Z`). 
When filtering messages by timestamp, the API properly handles various timestamp formats:

- ISO 8601 with Z suffix (`2025-03-17T10:30:00Z`)
- ISO 8601 with timezone offset (`2025-03-17T10:30:00+00:00`)
- ISO 8601 without timezone info (assumed as UTC)

Clients should include timezone information in request headers to help with time synchronization:

```
X-Client-Timezone: America/New_York
X-Client-Time: 2025-03-17T10:30:00Z
X-Client-Time-Ms: 1710550200000
```

The server may return a timestamp in response headers for synchronization:

```
X-Server-Time: 2025-03-17T10:30:05Z
```

### Get Chat History

Retrieves the complete conversation history for a specific support request.

**Endpoint:** `GET /api/chat/{request_id}`

**Response Headers:**
- `X-Server-Time`: Current server time in ISO 8601 format

**Response Model:** `ChatResponse`

**Sample Response:**
```json
{
  "request_id": 123,
  "user_id": 456789012,
  "status": "in_progress",
  "created_at": "2025-03-17T10:30:00Z",
  "updated_at": "2025-03-17T11:45:00Z",
  "issue": "I'm having trouble with logging in",
  "solution": null,
  "messages": [
    {
      "id": 1,
      "request_id": 123,
      "sender_id": 456789012,
      "sender_type": "user",
      "message": "I'm having trouble with logging in",
      "timestamp": "2025-03-17T10:30:00Z"
    },
    {
      "id": 2,
      "request_id": 123,
      "sender_id": 987654321,
      "sender_type": "admin",
      "message": "I'll help you with that. What happens when you try to log in?",
      "timestamp": "2025-03-17T10:40:00Z"
    }
  ],
  "server_time": "2025-03-17T11:46:05Z"
}
```

### Add Message

Adds a new message to the conversation.

**Endpoint:** `POST /api/chat/{request_id}/messages`

**Request Headers:**
- `X-Client-Timestamp`: Client's current time in ISO 8601 format
- `X-Timezone-Offset`: Client's timezone offset in minutes
- `X-Client-Time-Ms`: Client's current time in milliseconds since epoch

**Request Body:** `MessageCreate`
```json
{
  "sender_id": 987654321,
  "sender_type": "admin",
  "message": "Have you tried resetting your password?",
  "timestamp": "2025-03-17T11:50:00Z"
}
```

**Response Headers:**
- `X-Server-Time`: Current server time in ISO 8601 format

**Response Model:** `MessageResponse`

**Sample Response:**
```json
{
  "id": 3,
  "request_id": 123,
  "sender_id": 987654321,
  "sender_type": "admin",
  "message": "Have you tried resetting your password?",
  "timestamp": "2025-03-17T11:50:00Z"
}
```

### Get Chat List

Retrieves a list of all support requests with their latest messages.

**Endpoint:** `GET /api/chat/chats`

**Sample Response:**
```json
[
  {
    "request_id": 123,
    "status": "in_progress",
    "issue": "I'm having trouble with logging in",
    "created_at": "2025-03-17T10:30:00",
    "updated_at": "2025-03-17T11:45:00",
    "assigned_admin": "987654321",
    "solution": null,
    "latest_message": {
      "sender_id": 987654321,
      "sender_type": "admin",
      "message": "Have you tried resetting your password?",
      "timestamp": "2025-03-17T11:45:00"
    }
  }
]
```

### Get Messages Since Timestamp

Retrieves messages for a specific support request that were created after a given timestamp.

**Endpoint:** `GET /api/chat/{request_id}/messages?since={timestamp}`

**Parameters:**
- `request_id`: The ID of the support request
- `since`: (Optional) ISO format timestamp (UTC) to filter messages created after this time

**Request Headers:**
- `X-Last-Timestamp`: Last received message timestamp for more precise filtering
- `X-User-ID`: Current user ID for message attribution
- `X-User-Type`: Current user type ('user' or 'admin')

**Response Headers:**
- `X-Server-Time`: Current server time in ISO 8601 format

**Response Model:** List of `MessageResponse`

**Sample Response:**
```json
[
  {
    "id": 3,
    "request_id": 123,
    "sender_id": 987654321,
    "sender_type": "admin",
    "message": "Have you tried resetting your password?",
    "timestamp": "2025-03-17T11:50:00Z"
  },
  {
    "id": 4,
    "request_id": 123,
    "sender_id": 456789012,
    "sender_type": "user",
    "message": "Yes, I tried that but it didn't work",
    "timestamp": "2025-03-17T11:55:00Z"
  }
]
```

### Reliability Endpoints

The system includes several reliability endpoints to ensure chat functionality continues to work even in case of issues.

#### Fixed Chat Response

Provides a reliable chat response that always works, even when database access fails.

**Endpoint:** `GET /fixed-chat/{request_id}`

**Parameters:**
- `request_id`: The ID of the support request

**Response:** A valid chat structure with fixed data

```json
{
  "request_id": 123,
  "user_id": 12345,
  "status": "pending",
  "created_at": "2025-03-18T10:16:08.308399",
  "updated_at": "2025-03-18T10:16:08.308414",
  "issue": "Your support request is being processed.",
  "solution": null,
  "messages": [
    {
      "id": 1,
      "request_id": 123,
      "sender_id": 12345,
      "sender_type": "user",
      "message": "I need help with my support request.",
      "timestamp": "2025-03-18T10:16:08.308399"
    },
    {
      "id": 2,
      "request_id": 123,
      "sender_id": 0,
      "sender_type": "system",
      "message": "Your request has been submitted. An admin will respond shortly.",
      "timestamp": "2025-03-18T10:16:08.308399"
    }
  ]
}
```

#### Debug Chat Endpoint

Provides debug information and a fallback response for chats.

**Endpoint:** `GET /debug/chat/{request_id}`

**Parameters:**
- `request_id`: The ID of the support request

**Response:** Detailed chat information with additional logging

## Data Models

The API uses the following Pydantic models for request and response validation:

### MessageBase
```python
class MessageBase(BaseModel):
    """Base message schema"""
    message: str
    sender_id: int
    sender_type: str  # 'user' or 'admin'
```

### MessageCreate
```python
class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    pass
```

### MessageResponse
```python
class MessageResponse(MessageBase):
    """Schema for message response"""
    id: int
    request_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
```

### ChatResponse
```python
class ChatResponse(BaseModel):
    """Schema for chat response with request details and messages"""
    request_id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    issue: str
    solution: Optional[str] = None
    messages: List[MessageResponse]

    class Config:
        orm_mode = True
```

## Integration with WebApp

These API endpoints are consumed by the Telegram WebApp chat interface to provide a seamless chat experience between users and administrators. The WebApp is configured to poll the chat endpoint periodically to check for new messages, ensuring near real-time communication.

## Error Handling

All endpoints include enhanced error handling with graceful degradation:

- For the `/api/chat/{request_id}/messages` endpoint, an empty array is returned instead of a 404 error when no messages are found
- The `/fixed-chat/{request_id}` endpoint always returns a valid response structure even if the request doesn't exist
- The main chat loading system tries multiple endpoints in sequence to ensure at least one succeeds

## Frontend Integration

The WebApp implements a multi-tiered fallback system for chat data loading:

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

## Authentication

Currently, these endpoints do not implement authentication. In a production environment, appropriate authentication and authorization mechanisms should be implemented to secure these endpoints. 

## Timestamp Processing in the Backend

The backend API implements careful handling of timestamps for chat functionality:

1. **Standardization**: All timestamps are standardized to ISO 8601 format with UTC timezone.
2. **Parsing**: The API carefully parses incoming timestamp strings with multiple fallback mechanisms.
3. **Timezone Awareness**: When converting to database timestamps, timezone information is preserved.
4. **Filtering Logic**: Messages are filtered using proper timestamp comparisons to ensure no messages are missed.

Example of timestamp processing in the API:

```python
# Convert the UTC timestamp to datetime - be more lenient with format
try:
    # First try standard ISO format with Z suffix
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

## Best Practices for Using the Chat API

1. **Always Include Timezone Info**: Always send timestamps with UTC timezone indicator (Z suffix).
2. **Handle Time Synchronization**: Implement client-server time synchronization using the `X-Server-Time` header.
3. **Time Drift Handling**: Check for significant time differences between client and server.
4. **Proper Timestamp Display**: Display times in the user's local timezone with appropriate context.
5. **Reliable Polling**: Implement reliable polling with exponential backoff for errors.
6. **Multiple Endpoint Fallbacks**: Use multiple API endpoints for redundancy in critical operations. 