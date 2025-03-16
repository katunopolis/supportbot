from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Request(Base):
    """Model for support requests."""
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    issue = Column(Text)
    assigned_admin = Column(Integer, nullable=True)
    status = Column(String(50), default="pending")
    solution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    """Model for chat messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"))
    sender_id = Column(Integer)
    sender_type = Column(String(10))  # 'user' or 'admin'
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    """Model for application logs."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20))
    message = Column(Text)
    context = Column(Text) 