# Chat API Endpoints

This document outlines the Chat API endpoints implemented for the Telegram Support Bot.

## Overview

The Chat API enables seamless communication between users and admins by providing endpoints to retrieve conversation history and send messages.

## API Routes

All chat endpoints are prefixed with `/api/chat` and defined in `app/api/routes/chat.py`.

### Get Chat History

Retrieves the complete conversation history for a specific support request.

**Endpoint:** `GET /api/chat/{request_id}`

**Response Model:** `ChatResponse`

**Sample Response:**
```json
{
  "request_id": 123,
  "user_id": 456789012,
  "status": "in_progress",
  "created_at": "2025-03-17T10:30:00",
  "updated_at": "2025-03-17T11:45:00",
  "issue": "I'm having trouble with logging in",
  "solution": null,
  "messages": [
    {
      "id": 1,
      "request_id": 123,
      "sender_id": 456789012,
      "sender_type": "user",
      "message": "I'm having trouble with logging in",
      "timestamp": "2025-03-17T10:30:00"
    },
    {
      "id": 2,
      "request_id": 123,
      "sender_id": 987654321,
      "sender_type": "admin",
      "message": "I'll help you with that. What happens when you try to log in?",
      "timestamp": "2025-03-17T10:40:00"
    }
  ]
}
```

### Add Message

Adds a new message to the conversation.

**Endpoint:** `POST /api/chat/{request_id}/messages`

**Request Body:** `MessageCreate`
```json
{
  "sender_id": 987654321,
  "sender_type": "admin",
  "message": "Have you tried resetting your password?"
}
```

**Response Model:** `MessageResponse`

**Sample Response:**
```json
{
  "id": 3,
  "request_id": 123,
  "sender_id": 987654321,
  "sender_type": "admin",
  "message": "Have you tried resetting your password?",
  "timestamp": "2025-03-17T11:50:00"
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

All endpoints include proper error handling:

- `404 Not Found`: Returned when the specified request ID doesn't exist
- `500 Internal Server Error`: Returned for unexpected server-side errors

## Authentication

Currently, these endpoints do not implement authentication. In a production environment, appropriate authentication and authorization mechanisms should be implemented to secure these endpoints. 