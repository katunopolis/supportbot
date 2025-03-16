from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database.session import get_db
from app.database.models import Request, Message

router = APIRouter()

@router.get("/chat/{request_id}")
async def get_chat_history(request_id: int, db: Session = Depends(get_db)):
    """Retrieves chat history for a specific support request."""
    try:
        # Get request details
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
            
        # Get messages
        messages = db.query(Message).filter(
            Message.request_id == request_id
        ).order_by(Message.timestamp.asc()).all()
        
        # Format response
        chat_history = {
            "request_id": request.id,
            "status": request.status,
            "issue": request.issue,
            "created_at": request.created_at.isoformat(),
            "updated_at": request.updated_at.isoformat(),
            "assigned_admin": request.assigned_admin,
            "solution": request.solution,
            "messages": [
                {
                    "sender_id": msg.sender_id,
                    "sender_type": msg.sender_type,
                    "message": msg.message,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ]
        }
        
        return chat_history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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