"""
API routes for the admin panel module.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.database.models import Request
from app.admin_panel.config import is_admin_panel_enabled

router = APIRouter()

@router.get("/api/support/requests")
async def get_support_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get support requests with optional filtering by status."""
    if not is_admin_panel_enabled():
        raise HTTPException(status_code=404, detail="Admin panel is disabled")
        
    try:
        query = db.query(Request)
        
        # Filter by status if provided
        if status:
            if status.lower() == "open":
                # Open requests are those that are pending or in_progress
                query = query.filter(Request.status.in_(["pending", "in_progress"]))
            else:
                query = query.filter(Request.status == status)
                
        requests = query.all()
        
        return [
            {
                "id": req.id,
                "user_id": req.user_id,
                "issue": req.issue,
                "status": req.status,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "updated_at": req.updated_at.isoformat() if req.updated_at else None,
                "assigned_admin": req.assigned_admin
            }
            for req in requests
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/support/requests/{request_id}/solve")
async def solve_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Mark a request as solved."""
    if not is_admin_panel_enabled():
        raise HTTPException(status_code=404, detail="Admin panel is disabled")
        
    try:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
            
        # Just mark as solved, actual solution will be provided via bot
        request.status = "solved"
        request.updated_at = datetime.now()
        db.commit()
        
        return {"status": "success", "message": "Request marked as solved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 