import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database.models import Request, Message
from app.database.session import get_db
from app.config import ADMIN_GROUP_ID

async def assign_request(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, admin_id: int, db: Session):
    """Assigns a support request to an admin."""
    try:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            await update.message.reply_text("Request not found.")
            return False
            
        if request.assigned_admin:
            await update.message.reply_text("This request is already assigned.")
            return False
            
        request.assigned_admin = admin_id
        request.status = "in_progress"
        request.updated_at = datetime.utcnow()
        db.commit()
        
        # Log assignment
        message = Message(
            request_id=request_id,
            sender_id=admin_id,
            sender_type="admin",
            message=f"Request assigned to admin {admin_id}",
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        
        logging.info(f"Request {request_id} assigned to admin {admin_id}")
        await update.message.reply_text(f"Request {request_id} has been assigned to you.")
        return True
        
    except Exception as e:
        logging.error(f"Error assigning request: {e}")
        await update.message.reply_text("Error assigning request. Please try again.")
        return False

async def close_request(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, solution: str, db: Session):
    """Closes a support request with a solution."""
    try:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            await update.message.reply_text("Request not found.")
            return False
            
        request.status = "resolved"
        request.solution = solution
        request.updated_at = datetime.utcnow()
        db.commit()
        
        # Log closure
        message = Message(
            request_id=request_id,
            sender_id=update.message.from_user.id,
            sender_type="admin",
            message=f"Request closed with solution: {solution}",
            timestamp=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        
        logging.info(f"Request {request_id} closed with solution")
        await update.message.reply_text(f"Request {request_id} has been closed.")
        return True
        
    except Exception as e:
        logging.error(f"Error closing request: {e}")
        await update.message.reply_text("Error closing request. Please try again.")
        return False

async def list_requests(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Session, status: str = None):
    """Lists support requests with optional status filter."""
    try:
        query = db.query(Request)
        if status:
            query = query.filter(Request.status == status)
        requests = query.order_by(Request.created_at.desc()).all()
        
        if not requests:
            await update.message.reply_text("No requests found.")
            return
            
        for request in requests:
            keyboard = []
            if request.status == "pending":
                keyboard.append([
                    InlineKeyboardButton("Assign to me", callback_data=f"assign_{request.id}")
                ])
            elif request.status == "in_progress":
                keyboard.append([
                    InlineKeyboardButton("Close request", callback_data=f"close_{request.id}")
                ])
                
            message = (
                f"Request #{request.id}\n"
                f"Status: {request.status}\n"
                f"User: {request.user_id}\n"
                f"Created: {request.created_at}\n"
                f"Issue: {request.issue}\n"
            )
            
            if request.assigned_admin:
                message += f"Assigned to: {request.assigned_admin}\n"
                
            if request.solution:
                message += f"Solution: {request.solution}\n"
                
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            await update.message.reply_text(message, reply_markup=reply_markup)
            
    except Exception as e:
        logging.error(f"Error listing requests: {e}")
        await update.message.reply_text("Error retrieving requests. Please try again.") 