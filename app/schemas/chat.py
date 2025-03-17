from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MessageBase(BaseModel):
    """Base message schema"""
    message: str
    sender_id: int
    sender_type: str  # 'user' or 'admin'


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    pass


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: int
    request_id: int
    timestamp: datetime

    class Config:
        orm_mode = True


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