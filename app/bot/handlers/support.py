import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database.models import Request, Message
from app.database.session import get_db
from app.config import ADMIN_GROUP_ID

# Remove global import of bot
# from app.bot.bot import bot

async def notify_admin_group(request_id: int, user_id: int, issue_text: str):
    """Notify admin group about new support request."""
    try:
        # Import bot inside function to avoid circular import
        from app.bot.bot import bot
        
        if not bot:
            logging.warning("Bot not initialized, can't notify admin group")
            return False
            
        # Format message
        message = (
            f"🆕 New support request #{request_id}\n"
            f"👤 User ID: {user_id}\n"
            f"📝 Issue: {issue_text[:100]}{'...' if len(issue_text) > 100 else ''}\n\n"
            f"Use /view_{request_id} to see details"
        )
        
        # Send message to admin group
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=message
        )
        
        logging.info(f"Notified admin group about request #{request_id}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to notify admin group: {e}")
        return False

async def collect_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect issue from user and create support request."""
    user_id = update.message.from_user.id
    
    # Check if user is in the middle of creating a request
    if not context.user_data.get(f"requesting_support_{user_id}"):
        return False
        
    # Get issue text
    issue_text = update.message.text
    
    # Create new support request in the database
    db = next(get_db())
    try:
        new_request = Request(
            user_id=user_id,
            issue=issue_text,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        # Add initial message
        new_message = Message(
            request_id=new_request.id,
            sender_id=user_id,
            sender_type="user",
            message=issue_text
        )
        db.add(new_message)
        db.commit()
        
        # Clean up user data
        context.user_data.pop(f"requesting_support_{user_id}", None)
        
        # Send confirmation to user
        await update.message.reply_text(
            f"Thank you! Your support request #{new_request.id} has been created. "
            f"An admin will review it shortly."
        )
        
        # Notify admin group about new request
        await notify_admin_group(new_request.id, user_id, issue_text)
        
        return True
        
    except Exception as e:
        logging.error(f"Error creating support request: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your request. Please try again later."
        )
        return True
    finally:
        db.close()

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