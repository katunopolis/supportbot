import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database.models import Request, Message
from app.database.session import get_db
from app.config import ADMIN_GROUP_ID, BASE_WEBAPP_URL

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

async def view_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /view_REQUEST_ID command to show request details"""
    try:
        # Extract the request ID from the command
        text = update.message.text
        match = re.match(r'/view_(\d+)', text)
        
        if not match:
            await update.message.reply_text(
                "Invalid format. Use /view_REQUEST_ID to view a specific request."
            )
            return
            
        request_id = int(match.group(1))
        
        # Get database session
        with next(get_db()) as db:
            # Fetch the request
            request = db.query(Request).filter(Request.id == request_id).first()
            
            if not request:
                await update.message.reply_text(f"Request #{request_id} not found.")
                return
                
            # Get the latest messages (limited to 5)
            messages = db.query(Message).filter(
                Message.request_id == request_id
            ).order_by(Message.timestamp.desc()).limit(5).all()
            
            # Format request details
            user_id = request.user_id
            created_at = request.created_at.strftime("%Y-%m-%d %H:%M")
            updated_at = request.updated_at.strftime("%Y-%m-%d %H:%M")
            status = request.status
            assigned_admin = request.assigned_admin if request.assigned_admin else "None"
            issue = request.issue
            solution = request.solution if request.solution else "Not resolved yet"
            
            # Create a formatted message
            response = (
                f"📝 <b>Request #{request_id}</b>\n\n"
                f"👤 <b>User ID:</b> {user_id}\n"
                f"📅 <b>Created:</b> {created_at}\n"
                f"🔄 <b>Updated:</b> {updated_at}\n"
                f"📊 <b>Status:</b> {status}\n"
                f"👨‍💼 <b>Assigned Admin:</b> {assigned_admin}\n\n"
                f"❓ <b>Issue:</b>\n{issue}\n\n"
            )
            
            if status == "resolved":
                response += f"✅ <b>Solution:</b>\n{solution}\n\n"
                
            # Add recent messages if there are any
            if messages:
                response += "<b>Recent Messages (newest first):</b>\n"
                for msg in messages:
                    sender_type = "Admin" if msg.sender_type == "admin" else "User"
                    msg_time = msg.timestamp.strftime("%H:%M:%S")
                    response += f"[{msg_time}] <b>{sender_type}:</b> {msg.message}\n"
            else:
                response += "<i>No messages yet.</i>\n"
            
            # Create appropriate buttons based on the status
            keyboard = []
            
            # Check if request is pending
            if status == "pending":
                # Get current admin ID
                admin_id = update.effective_user.id
                
                # Add button to assign the request to the current admin
                keyboard.append([
                    InlineKeyboardButton(
                        "Assign to me", 
                        callback_data=f"assign_{request_id}_{admin_id}"
                    )
                ])
                
                # Add button to open chat interface
                keyboard.append([
                    InlineKeyboardButton(
                        "Open Support Chat", 
                        web_app=WebAppInfo(
                            url=f"{BASE_WEBAPP_URL}/chat.html?requestId={request_id}&adminId={admin_id}"
                        )
                    )
                ])
            
            # Check if request is in progress and assigned to current admin
            elif status == "in_progress":
                admin_id = update.effective_user.id
                
                # Add button to open chat interface
                keyboard.append([
                    InlineKeyboardButton(
                        "Open Support Chat", 
                        web_app=WebAppInfo(
                            url=f"{BASE_WEBAPP_URL}/chat.html?requestId={request_id}&adminId={admin_id}"
                        )
                    )
                ])
                
                # Add button to mark as resolved only if assigned to current admin
                if assigned_admin and int(assigned_admin) == admin_id:
                    keyboard.append([
                        InlineKeyboardButton(
                            "Mark as resolved", 
                            callback_data=f"resolve_{request_id}"
                        )
                    ])
            
            # Create the reply markup with the appropriate buttons
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            # Send the response
            await update.message.reply_text(
                response,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            
    except Exception as e:
        logging.error(f"Error viewing request: {str(e)}")
        await update.message.reply_text(
            "An error occurred while retrieving the request details."
        )

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from admin buttons"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Get the callback data
        data = query.data
        
        # Handle assignment callback
        if data.startswith("assign_"):
            parts = data.split("_")
            if len(parts) < 3:
                await query.edit_message_text("Invalid callback data format.")
                return
                
            request_id = int(parts[1])
            admin_id = int(parts[2])
            
            # Assign the request to the admin
            with next(get_db()) as db:
                request = db.query(Request).filter(Request.id == request_id).first()
                
                if not request:
                    await query.edit_message_text(f"Request #{request_id} not found.")
                    return
                    
                if request.status != "pending":
                    await query.edit_message_text(f"Request #{request_id} is already {request.status}.")
                    return
                    
                # Update the request status and assigned admin
                request.status = "in_progress"
                request.assigned_admin = str(admin_id)
                request.updated_at = datetime.now()
                db.commit()
                
                # Create a new message in the system
                new_message = Message(
                    request_id=request_id,
                    sender_id=admin_id,
                    sender_type="admin",
                    message="I have taken ownership of this request and will assist you shortly."
                )
                db.add(new_message)
                db.commit()
                
                # Notify the user that an admin has taken their request
                try:
                    # Assuming bot is available in context
                    await context.bot.send_message(
                        chat_id=request.user_id,
                        text="Good news! An admin has taken your support request and will assist you shortly."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user about admin assignment: {e}")
                
                # Update the admin message
                admin_id = update.effective_user.id
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Open Support Chat", 
                            web_app=WebAppInfo(
                                url=f"{BASE_WEBAPP_URL}/chat.html?requestId={request_id}&adminId={admin_id}"
                            )
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Mark as resolved", 
                            callback_data=f"resolve_{request_id}"
                        )
                    ]
                ]
                
                await query.edit_message_text(
                    f"✅ You have been assigned to request #{request_id}.\n\n"
                    f"You can now chat with the user to provide support.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        # Handle resolve callback
        elif data.startswith("resolve_"):
            parts = data.split("_")
            if len(parts) < 2:
                await query.edit_message_text("Invalid callback data format.")
                return
                
            request_id = int(parts[1])
            admin_id = update.effective_user.id
            
            # Ask for resolution message
            context.user_data["resolving_request"] = request_id
            await query.edit_message_text(
                f"Please provide a solution for request #{request_id}.\n\n"
                "Reply to this message with your solution."
            )
            
    except Exception as e:
        logger.error(f"Error handling admin callback: {str(e)}")
        await query.edit_message_text("An error occurred while processing your request.")
        
async def handle_resolution_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle resolution message from admin"""
    # Check if the admin is in resolution mode
    resolving_request_id = context.user_data.get("resolving_request")
    if not resolving_request_id:
        return False  # Not handling resolution
        
    # Get the solution text
    solution_text = update.message.text
    admin_id = update.effective_user.id
    
    try:
        # Update the request in the database
        with next(get_db()) as db:
            request = db.query(Request).filter(Request.id == resolving_request_id).first()
            
            if not request:
                await update.message.reply_text(f"Request #{resolving_request_id} not found.")
                del context.user_data["resolving_request"]
                return True
                
            if request.status != "in_progress" or request.assigned_admin != str(admin_id):
                await update.message.reply_text(
                    f"You are not assigned to request #{resolving_request_id} or it's not in progress."
                )
                del context.user_data["resolving_request"]
                return True
                
            # Update the request
            request.status = "resolved"
            request.solution = solution_text
            request.updated_at = datetime.now()
            db.commit()
            
            # Add the resolution message to the chat
            new_message = Message(
                request_id=resolving_request_id,
                sender_id=admin_id,
                sender_type="admin",
                message=f"This request has been marked as resolved with solution: {solution_text}"
            )
            db.add(new_message)
            db.commit()
            
            # Notify the user
            try:
                # Assuming bot is available in context
                await context.bot.send_message(
                    chat_id=request.user_id,
                    text=(
                        f"Your support request has been resolved!\n\n"
                        f"Solution: {solution_text}\n\n"
                        "Thank you for using our support service."
                    )
                )
            except Exception as e:
                logger.error(f"Failed to notify user about resolution: {e}")
            
            # Send confirmation to admin
            await update.message.reply_text(
                f"✅ Request #{resolving_request_id} has been marked as resolved."
            )
            
            # Clear the resolution state
            del context.user_data["resolving_request"]
            return True
            
    except Exception as e:
        logger.error(f"Error handling resolution: {str(e)}")
        await update.message.reply_text("An error occurred while resolving the request.")
        del context.user_data["resolving_request"]
        return True
        
    return False  # Not handling resolution 