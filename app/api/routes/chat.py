from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.database.session import get_db
from app.database.models import Request as DbRequest, Message as DbMessage
from pydantic import BaseModel

# Initialize the router with prefix
router = APIRouter(tags=["chat"])

# Add a duplicate router to handle both /chat and /chat_api endpoints
from fastapi import FastAPI
# This will be used in main.py to register the same routes under multiple prefixes
chat_router = router

# Define our Pydantic models for the API
class MessageBase(BaseModel):
    """Base message schema"""
    message: str
    sender_id: int
    sender_type: str  # 'user' or 'admin'


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    pass


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: int
    request_id: int
    sender_id: int
    sender_type: str
    message: str
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

@router.get("/{request_id}", response_model=ChatResponse)
async def get_chat(request_id: int, db: Session = Depends(get_db)):
    """Get chat messages for a specific support request"""
    try:
        # Check if request exists
        request = db.query(DbRequest).filter(DbRequest.id == request_id).first()
        if not request:
            logging.error(f"Support request with ID {request_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Support request with ID {request_id} not found"
            )
        
        # Get all messages for this request
        messages = db.query(DbMessage).filter(DbMessage.request_id == request_id).all()
        
        # Serialize messages to dictionary
        serialized_messages = []
        for msg in messages:
            serialized_messages.append({
                "id": msg.id,
                "request_id": msg.request_id,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "message": msg.message,
                "timestamp": msg.timestamp
            })
        
        # Create response object with request and messages
        response = {
            "request_id": request.id,
            "user_id": request.user_id,
            "status": request.status,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "issue": request.issue,
            "solution": request.solution,
            "messages": serialized_messages
        }
        
        logging.info(f"Retrieved chat for request ID {request_id}: {len(messages)} messages")
        return response
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
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
    request = db.query(DbRequest).filter(DbRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support request with ID {request_id} not found"
        )
    
    # Create new message
    new_message = DbMessage(
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
        requests = db.query(DbRequest).order_by(DbRequest.updated_at.desc()).all()
        
        chat_list = []
        for request in requests:
            # Get latest message
            latest_message = db.query(DbMessage).filter(
                DbMessage.request_id == request.id
            ).order_by(DbMessage.timestamp.desc()).first()
            
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

@router.get("/{request_id}/messages")
async def get_messages(
    request_id: int, 
    since: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get messages for a chat since a specific timestamp."""
    logging.info(f"Getting messages for request {request_id} since {since}")
    
    try:
        request = db.query(DbRequest).filter(DbRequest.id == request_id).first()
        if not request:
            logging.warning(f"Request ID {request_id} not found for messages")
            # Return empty array instead of 404 for smoother UX
            return []
            
        # Query for messages, optionally filtering by timestamp
        query = db.query(DbMessage).filter(DbMessage.request_id == request_id)
        
        # Handle timestamp filtering if provided
        if since:
            try:
                # Try to parse the timestamp in different formats
                try:
                    # Try ISO format (with or without Z suffix)
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                except ValueError:
                    # Try other formats if needed
                    logging.warning(f"Could not parse timestamp {since} as ISO format")
                    since_dt = datetime.now()  # Fallback
                
                query = query.filter(DbMessage.timestamp > since_dt)
                logging.info(f"Filtering messages after {since_dt}")
            except Exception as e:
                logging.error(f"Error parsing timestamp {since}: {str(e)}")
                # Continue without timestamp filtering if parsing fails
        
        # Get all matching messages    
        messages = query.all()
        logging.info(f"Found {len(messages)} messages for request {request_id}")
        
        # Convert to response format
        message_responses = []
        for msg in messages:
            message_responses.append({
                "id": msg.id,
                "request_id": msg.request_id,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "message": msg.message,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })
            
        return message_responses
    except Exception as e:
        logging.error(f"Error getting messages: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        # Return empty array instead of error for smoother UX
        return []

@router.post("/{request_id}/messages")
async def send_message(request_id: int, message: str, sender_id: int, sender_type: str, db: Session = Depends(get_db)):
    """Send a new message to a chat."""
    request = db.query(DbRequest).filter(DbRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    # Create a new message
    new_message = DbMessage(
        request_id=request_id,
        sender_id=sender_id,
        sender_type=sender_type,
        message=message,
        timestamp=datetime.now()
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Return the created message
    return {
        "id": new_message.id,
        "request_id": new_message.request_id,
        "sender_id": new_message.sender_id,
        "sender_type": new_message.sender_type,
        "message": new_message.message,
        "timestamp": new_message.timestamp
    } 