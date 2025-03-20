from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
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


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    message: str
    sender_id: int
    sender_type: str


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
        
        # Serialize messages to dictionary with proper ISO 8601 formatting
        serialized_messages = []
        for msg in messages:
            if msg.timestamp:
                timestamp = msg.timestamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            else:
                timestamp = None
                
            serialized_messages.append({
                "id": msg.id,
                "request_id": msg.request_id,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "message": msg.message,
                "timestamp": timestamp
            })
        
        # Create response object with request and messages
        # Format timestamps as ISO 8601 with Z suffix for UTC
        response = {
            "request_id": request.id,
            "user_id": request.user_id,
            "status": request.status,
            "created_at": request.created_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "updated_at": request.updated_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
            
            # Format timestamps as ISO 8601 with Z suffix for UTC
            created_at = request.created_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            updated_at = request.updated_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            # Format latest message if available
            latest_message_data = None
            if latest_message:
                latest_timestamp = latest_message.timestamp
                if latest_timestamp:
                    latest_timestamp = latest_timestamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
                    
                latest_message_data = {
                    "sender_id": latest_message.sender_id,
                    "sender_type": latest_message.sender_type,
                    "message": latest_message.message,
                    "timestamp": latest_timestamp
                }
            
            chat_info = {
                "request_id": request.id,
                "status": request.status,
                "issue": request.issue,
                "created_at": created_at,
                "updated_at": updated_at,
                "assigned_admin": request.assigned_admin,
                "solution": request.solution,
                "latest_message": latest_message_data
            }
            chat_list.append(chat_info)
            
        return chat_list
        
    except Exception as e:
        logging.error(f"Error in get_chat_list: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
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
            return []
            
        # Query for messages
        query = db.query(DbMessage).filter(DbMessage.request_id == request_id)
        
        # Handle timestamp filtering if provided
        if since == 'undefined' or not since:
            since = datetime.now(timezone.utc).isoformat()
            logging.info(f"Using current timestamp for undefined since value: {since}")
        
        try:
            # Convert the UTC timestamp to datetime - be more lenient with format
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
            
            # Debug log the parsed time
            logging.info(f"Parsed timestamp {since} as {since_dt} (UTC)")
            
            # For SQLite compatibility: convert to naive datetime but ensure UTC
            naive_dt = since_dt.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.filter(DbMessage.timestamp > naive_dt)
            logging.info(f"Filtering messages after {since_dt}")
        except Exception as e:
            logging.error(f"Error parsing timestamp {since}: {str(e)}")
            # Use current time if parsing fails, but ensure it's UTC
            since_dt = datetime.now(timezone.utc)
            naive_dt = since_dt.replace(tzinfo=None)
            query = query.filter(DbMessage.timestamp > naive_dt)
            logging.info(f"Using fallback timestamp: {since_dt}")
        
        # Get all matching messages and order by timestamp
        messages = query.order_by(DbMessage.timestamp.asc()).all()
        logging.info(f"Found {len(messages)} messages for request {request_id}")
        
        # Convert to response format with proper UTC timestamps
        message_responses = []
        for msg in messages:
            if msg.timestamp:
                # Ensure timestamp is treated as UTC and format in ISO 8601
                utc_time = datetime.combine(msg.timestamp.date(), msg.timestamp.time(), tzinfo=timezone.utc)
                timestamp = utc_time.isoformat().replace('+00:00', 'Z')
            else:
                timestamp = None
                
            message_responses.append({
                "id": msg.id,
                "request_id": msg.request_id,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "message": msg.message,
                "timestamp": timestamp
            })
            
        return message_responses
    except Exception as e:
        logging.error(f"Error getting messages: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return []

@router.post("/{request_id}/messages")
async def send_message(
    request_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Send a new message to a chat."""
    try:
        request = db.query(DbRequest).filter(DbRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        # Always use UTC time
        current_time = datetime.now(timezone.utc)
        logging.info(f"Creating new message at time: {current_time.isoformat()}")
        
        # Create a new message
        new_message = DbMessage(
            request_id=request_id,
            sender_id=message_data.sender_id,
            sender_type=message_data.sender_type,
            message=message_data.message,
            timestamp=current_time
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Update request timestamp
        request.updated_at = current_time
        db.commit()
        
        logging.info(f"Created new message in request {request_id} from {message_data.sender_type} (ID: {new_message.id})")
        
        # Return the created message with proper ISO 8601 formatting
        timestamp = new_message.timestamp.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        logging.info(f"Message timestamp: {timestamp}")
        
        # Return the created message
        result = {
            "id": new_message.id,
            "request_id": new_message.request_id,
            "sender_id": new_message.sender_id,
            "sender_type": new_message.sender_type,
            "message": new_message.message,
            "timestamp": timestamp
        }
        logging.info(f"Returning message response: {result}")
        return result
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))