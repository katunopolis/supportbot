from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database.session import get_db
from app.database.models import Log

router = APIRouter()

@router.get("/logs")
async def get_logs(
    level: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """Retrieves application logs with optional filters."""
    try:
        query = db.query(Log)
        
        # Apply filters
        if level:
            query = query.filter(Log.level == level)
        if start_time:
            query = query.filter(Log.timestamp >= start_time)
        if end_time:
            query = query.filter(Log.timestamp <= end_time)
            
        # Order by timestamp descending and limit results
        logs = query.order_by(Log.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "context": log.context
            }
            for log in logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/recent")
async def get_recent_logs(
    hours: int = Query(default=24, ge=1, le=168),
    level: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """Retrieves recent logs from the last N hours."""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(Log).filter(Log.timestamp >= start_time)
        
        if level:
            query = query.filter(Log.level == level)
            
        logs = query.order_by(Log.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "context": log.context
            }
            for log in logs
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/levels")
async def get_log_levels(db: Session = Depends(get_db)):
    """Retrieves available log levels and their counts."""
    try:
        levels = db.query(
            Log.level,
            db.func.count(Log.id).label("count")
        ).group_by(Log.level).all()
        
        return [
            {
                "level": level,
                "count": count
            }
            for level, count in levels
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 