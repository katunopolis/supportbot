from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class RequestBase(BaseModel):
    """Base schema for support requests"""
    user_id: int
    issue: str
    platform: Optional[str] = None
    isWebApp: Optional[bool] = None


class RequestCreate(RequestBase):
    """Schema for creating a new support request"""
    pass


class RequestUpdate(BaseModel):
    """Schema for updating a support request"""
    status: Optional[str] = None
    assigned_admin: Optional[int] = None
    solution: Optional[str] = None


class RequestResponse(RequestBase):
    """Schema for support request response"""
    id: int
    request_id: int
    status: str
    assigned_admin: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    solution: Optional[str] = None

    class Config:
        orm_mode = True


class WebAppLog(BaseModel):
    """Schema for WebApp logging"""
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None 