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

router = APIRouter()

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
    """
    try:
        user_id = data.get("user_id")
        issue = data.get("issue")
        
        if not user_id or not issue:
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
        logger.error(f"Error creating support request: {str(e)}")
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