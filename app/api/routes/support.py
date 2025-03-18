from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
from app.database.session import get_db
from app.database.models import Request, Message
from pydantic import BaseModel
from app.bot.handlers.support import notify_admin_group

# Configure logger
logger = logging.getLogger(__name__)

# Add prefix to the router
router = APIRouter(prefix="/support")

# Add this new route for direct chat access (as a workaround)
@router.get("/chat/{request_id}")
async def get_chat_direct(request_id: int, db: Session = Depends(get_db)):
    """Get chat data directly without going through the chat.py router"""
    try:
        # Enhanced logging
        logging.info(f"Direct chat endpoint called for request ID: {request_id}")
        
        # Check if request exists
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            logging.error(f"Support request with ID {request_id} not found")
            raise HTTPException(status_code=404, detail=f"Support request with ID {request_id} not found")
        
        # Get all messages for this request
        messages = db.query(Message).filter(Message.request_id == request_id).all()
        logging.info(f"Found {len(messages)} messages for request ID {request_id}")
        
        # Create response object with request and messages
        response = {
            "request_id": request.id,
            "user_id": request.user_id,
            "status": request.status,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "issue": request.issue,
            "solution": request.solution,
            "messages": [
                {
                    "id": msg.id,
                    "request_id": msg.request_id,
                    "sender_id": msg.sender_id,
                    "sender_type": msg.sender_type,
                    "message": msg.message,
                    "timestamp": msg.timestamp
                } for msg in messages
            ]
        }
        
        logging.info(f"Retrieved chat for request ID {request_id}: {len(messages)} messages")
        return response
    except Exception as e:
        logging.error(f"Error retrieving chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chat: {str(e)}")

# Add a simple test endpoint to check if routing works
@router.get("/test")
async def test_route():
    logging.info("Support test route called")
    try:
        # Try database connection to verify it's working
        from app.database.session import get_db, SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            # Test a simple query
            result = db.execute(text("SELECT 1")).fetchone()
            db_result = f"Database test: {result[0]}"
            
            # Test a query to the requests table
            count = db.execute(text("SELECT COUNT(*) FROM requests")).fetchone()
            requests_count = f"Request count: {count[0]}"
            
            return {
                "status": "ok",
                "message": "Support router is working",
                "database_test": db_result,
                "requests_info": requests_count
            }
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Support test route error: {str(e)}")
        return {
            "status": "error",
            "message": f"Support router test failed: {str(e)}"
        }

class RequestCreate(BaseModel):
    user_id: int
    issue: str
    platform: Optional[str] = None
    isWebApp: Optional[bool] = None

class RequestUpdate(BaseModel):
    status: Optional[str] = None
    assigned_admin: Optional[int] = None
    solution: Optional[str] = None

class MessageCreate(BaseModel):
    sender_id: int
    sender_type: str
    message: str

class WebAppLog(BaseModel):
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None

@router.post("/support-request")
async def create_request(
    data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new support request from the web app.
    This function can be called directly or via HTTP request.
    """
    try:
        logging.info(f"Processing support request: {data}")
        
        user_id = data.get("user_id")
        issue = data.get("issue")
        
        if not user_id or not issue:
            logging.error("Missing required fields: user_id or issue")
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        # Create new request
        new_request = Request(
            user_id=user_id,
            issue=issue,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        logging.info(f"Created new support request with ID: {new_request.id}")
        
        # Add the first message from user
        message = Message(
            request_id=new_request.id,
            sender_id=user_id,
            sender_type="user",
            message=issue
        )
        db.add(message)
        db.commit()
        
        # Notify admin group in the background
        background_tasks.add_task(
            notify_admin_group,
            new_request.id,
            user_id,
            issue
        )
        
        # Return a minimal response with just the request ID
        # This helps avoid Telegram WebApp issues with complex responses
        return {"request_id": new_request.id}
        
    except Exception as e:
        logging.error(f"Error creating support request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webapp-log")
async def log_webapp_event(log_data: WebAppLog, background_tasks: BackgroundTasks):
    """Logs events from the WebApp."""
    try:
        log_level = getattr(logging, log_data.level.upper(), logging.INFO)
        logging.log(log_level, f"WebApp: {log_data.message} | Context: {log_data.context}")
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error logging webapp event: {e}")
        return {"status": "error", "message": str(e)}

@router.put("/requests/{request_id}")
async def update_request(
    request_id: int,
    update_data: RequestUpdate,
    db: Session = Depends(get_db)
):
    """Updates a support request."""
    try:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
            
        # Update fields if provided
        if update_data.status is not None:
            request.status = update_data.status
        if update_data.assigned_admin is not None:
            request.assigned_admin = update_data.assigned_admin
        if update_data.solution is not None:
            request.solution = update_data.solution
            
        request.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(request)
        
        return {
            "request_id": request.id,
            "status": request.status,
            "assigned_admin": request.assigned_admin,
            "solution": request.solution,
            "updated_at": request.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/{request_id}/messages")
async def add_message(
    request_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Adds a new message to a support request."""
    try:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
            
        new_message = Message(
            request_id=request_id,
            sender_id=message.sender_id,
            sender_type=message.sender_type,
            message=message.message,
            timestamp=datetime.utcnow()
        )
        db.add(new_message)
        
        # Update request timestamp
        request.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message_id": new_message.id,
            "request_id": request_id,
            "timestamp": new_message.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add an endpoint to get messages
@router.get("/chat/{request_id}/messages", response_model=List[dict])
async def get_messages_direct(
    request_id: int, 
    since: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get messages for a request since a specific timestamp"""
    try:
        # Enhanced logging
        logging.info(f"Direct messages endpoint called for request ID: {request_id}, since: {since}")
        
        # Check if request exists
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            logging.error(f"Support request with ID {request_id} not found")
            raise HTTPException(status_code=404, detail=f"Support request with ID {request_id} not found")
        
        # Build query for messages
        query = db.query(Message).filter(Message.request_id == request_id)
        
        # Filter by timestamp if provided
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                query = query.filter(Message.timestamp > since_dt)
                logging.info(f"Filtering messages since {since_dt}")
            except ValueError:
                logging.error(f"Invalid timestamp format: {since}")
                raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format.")
        
        # Get messages ordered by timestamp
        messages = query.order_by(Message.timestamp.asc()).all()
        
        # Convert to dict for JSON response
        result = [
            {
                "id": msg.id,
                "request_id": msg.request_id,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "message": msg.message,
                "timestamp": msg.timestamp
            } for msg in messages
        ]
        
        logging.info(f"Retrieved {len(messages)} messages for request ID {request_id}")
        return result
    except Exception as e:
        logging.error(f"Error retrieving messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

# Add an endpoint to add messages
@router.post("/chat/{request_id}/messages")
async def add_message_direct(
    request_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Add a new message to the chat"""
    try:
        # Enhanced logging
        logging.info(f"Direct add message endpoint called for request ID: {request_id}")
        
        # Check if request exists
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            logging.error(f"Support request with ID {request_id} not found")
            raise HTTPException(status_code=404, detail=f"Support request with ID {request_id} not found")
        
        # Create new message
        new_message = Message(
            request_id=request_id,
            sender_id=message.sender_id,
            sender_type=message.sender_type,
            message=message.message,
            timestamp=datetime.utcnow()
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Update the request's updated_at timestamp
        request.updated_at = new_message.timestamp
        db.commit()
        
        logging.info(f"Added new message ID {new_message.id} to request ID {request_id}")
        
        return {
            "id": new_message.id,
            "request_id": new_message.request_id,
            "sender_id": new_message.sender_id,
            "sender_type": new_message.sender_type,
            "message": new_message.message,
            "timestamp": new_message.timestamp
        }
    except Exception as e:
        logging.error(f"Error adding message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding message: {str(e)}") 