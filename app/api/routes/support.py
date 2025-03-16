from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database.session import get_db
from app.database.models import Request, Message
from pydantic import BaseModel

router = APIRouter()

class RequestCreate(BaseModel):
    user_id: int
    issue: str

class RequestUpdate(BaseModel):
    status: Optional[str] = None
    assigned_admin: Optional[int] = None
    solution: Optional[str] = None

class MessageCreate(BaseModel):
    sender_id: int
    sender_type: str
    message: str

@router.post("/support-request")
async def create_request(request: RequestCreate, db: Session = Depends(get_db)):
    """Creates a new support request."""
    try:
        new_request = Request(
            user_id=request.user_id,
            issue=request.issue,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        # Create initial message
        message = Message(
            request_id=new_request.id,
            sender_id=request.user_id,
            sender_type="user",
            message=request.issue,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        
        return {
            "request_id": new_request.id,
            "status": new_request.status,
            "created_at": new_request.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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