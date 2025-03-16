import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database.models import Request, Message
from app.database.session import get_db

async def collect_issue(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session):
    """Collects issue description from user and creates a support request."""
    user_id = update.message.from_user.id
    issue_text = update.message.text
    
    try:
        # Create new support request
        request = Request(
            user_id=user_id,
            issue=issue_text,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        
        # Store initial message
        message = Message(
            request_id=request.id,
            sender_id=user_id,
            sender_type="user",
            message=issue_text,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        
        # Clear user state
        context.user_data.pop(f"requesting_support_{user_id}", None)
        
        await update.message.reply_text(
            "Thank you for submitting your issue. An admin will review it shortly."
        )
        
        logging.info(f"Created support request {request.id} for user {user_id}")
        return request.id
        
    except Exception as e:
        logging.error(f"Error creating support request: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your request. Please try again later."
        )
        return None

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, db: Session):
    """Handles messages from users in an ongoing support conversation."""
    user_id = update.message.from_user.id
    message_text = update.message.text
    
    try:
        # Store the message
        message = Message(
            request_id=request_id,
            sender_id=user_id,
            sender_type="user",
            message=message_text,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        
        # Update request timestamp
        request = db.query(Request).filter(Request.id == request_id).first()
        if request:
            request.updated_at = datetime.utcnow()
            db.commit()
            
        logging.info(f"Stored user message for request {request_id}")
        
    except Exception as e:
        logging.error(f"Error storing user message: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your message. Please try again."
        )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, db: Session):
    """Handles messages from admins in an ongoing support conversation."""
    admin_id = update.message.from_user.id
    message_text = update.message.text
    
    try:
        # Store the message
        message = Message(
            request_id=request_id,
            sender_id=admin_id,
            sender_type="admin",
            message=message_text,
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        
        # Update request timestamp
        request = db.query(Request).filter(Request.id == request_id).first()
        if request:
            request.updated_at = datetime.utcnow()
            db.commit()
            
        logging.info(f"Stored admin message for request {request_id}")
        
    except Exception as e:
        logging.error(f"Error storing admin message: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your message. Please try again."
        ) 