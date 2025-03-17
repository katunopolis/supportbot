from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.database.session import get_db
from app.database.models import Request, Message
from pydantic import BaseModel

# Define our Pydantic models for the API
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

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/{request_id}", response_model=ChatResponse)
async def get_chat(request_id: int, db: Session = Depends(get_db)):
    """Get chat messages for a specific support request"""
    try:
        # Check if request exists
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Support request with ID {request_id} not found"
            )
        
        # Get all messages for this request
        messages = db.query(Message).filter(Message.request_id == request_id).all()
        
        # Create response object with request and messages
        response = {
            "request_id": request.id,
            "user_id": request.user_id,
            "status": request.status,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "issue": request.issue,
            "solution": request.solution,
            "messages": messages
        }
        
        return response
    except Exception as e:
        logging.error(f"Error retrieving chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving chat: {str(e)}"
        )

@router.post("/{request_id}/messages", response_model=MessageResponse)
async def add_message(
    request_id: int, 
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a new message to the chat"""
    # Check if request exists
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support request with ID {request_id} not found"
        )
    
    # Create new message
    new_message = Message(
        request_id=request_id,
        sender_id=message_data.sender_id,
        sender_type=message_data.sender_type,
        message=message_data.message
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Update the request's updated_at timestamp
    request.updated_at = new_message.timestamp
    db.commit()
    
    return new_message

@router.get("/chats")
async def get_chat_list(db: Session = Depends(get_db)):
    """Retrieves a list of all support requests with their latest messages."""
    try:
        requests = db.query(Request).order_by(Request.updated_at.desc()).all()
        
        chat_list = []
        for request in requests:
            # Get latest message
            latest_message = db.query(Message).filter(
                Message.request_id == request.id
            ).order_by(Message.timestamp.desc()).first()
            
            chat_info = {
                "request_id": request.id,
                "status": request.status,
                "issue": request.issue,
                "created_at": request.created_at.isoformat(),
                "updated_at": request.updated_at.isoformat(),
                "assigned_admin": request.assigned_admin,
                "solution": request.solution,
                "latest_message": {
                    "sender_id": latest_message.sender_id,
                    "sender_type": latest_message.sender_type,
                    "message": latest_message.message,
                    "timestamp": latest_message.timestamp.isoformat()
                } if latest_message else None
            }
            chat_list.append(chat_info)
            
        return chat_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{request_id}/messages", response_model=List[MessageResponse])
async def get_messages_since(
    request_id: int, 
    since: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get messages for a request since a specific timestamp"""
    try:
        # Check if request exists
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Support request with ID {request_id} not found"
            )
        
        # Build query for messages
        query = db.query(Message).filter(Message.request_id == request_id)
        
        # Filter by timestamp if provided
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                query = query.filter(Message.timestamp > since_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid timestamp format. Use ISO format."
                )
        
        # Get messages ordered by timestamp
        messages = query.order_by(Message.timestamp.asc()).all()
        
        return messages
    except Exception as e:
        logging.error(f"Error retrieving messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving messages: {str(e)}"
        ) 