from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Request(Base):
    """Model for support requests."""
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger)
    issue = Column(Text)
    assigned_admin = Column(BigInteger, nullable=True)
    status = Column(String(50), default="pending")
    solution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    messages = relationship("Message", back_populates="request")

class Message(Base):
    """Model for chat messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"))
    sender_id = Column(BigInteger)
    sender_type = Column(String(10))  # 'user' or 'admin'
    message = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    request = relationship("Request", back_populates="messages")

class Log(Base):
    """Model for application logs."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    level = Column(String(20))
    message = Column(Text)
    context = Column(Text)

class Admin(Base):
    """Model for admin users."""
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True)
    name = Column(String(100))
    role = Column(String(50), default="admin")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) 