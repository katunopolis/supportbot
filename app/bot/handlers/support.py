import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database.models import Request, Message, Admin
from app.database.session import get_db
from app.config import ADMIN_GROUP_ID, WEB_APP_URL, BASE_WEBAPP_URL

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
        
        # Create simplified keyboard with just two buttons: Open Chat and Solve
        # For group messages, we need to use simple callback buttons, not WebApp buttons directly
        keyboard = [
            [
                InlineKeyboardButton("💬 Open Chat", callback_data=f"chat_{request_id}"),
                InlineKeyboardButton("✅ Solve", callback_data=f"solve_{request_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send message to admin group with inline keyboard
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=message,
            reply_markup=reply_markup
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

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    
    # Parse the callback data
    callback_data = query.data
    
    # Log the callback data for debugging
    logging.info(f"Received callback query: {callback_data}")
    
    # Parse the callback data (format: action_request_id)
    parts = callback_data.split("_")
    
    if len(parts) < 2:
        await query.answer("Invalid action")
        return
        
    action = parts[0]
    request_id = int(parts[1])
    
    # Get admin information
    admin_id = update.effective_user.id
    admin_name = update.effective_user.full_name
    
    # Use a database session
    with next(get_db()) as db:
        # Get the request
        request = db.query(Request).filter(Request.id == request_id).first()
        
        if not request:
            await query.answer("Request not found")
            return
            
        # Handle different actions
        if action == "assign":
            # Extract admin ID from callback if available
            admin_id_from_callback = int(parts[2]) if len(parts) > 2 else admin_id
            
            # Make sure callback admin ID matches current user
            if admin_id_from_callback != admin_id:
                await query.answer(f"Invalid admin ID in callback")
                return
                
            # Check if already assigned
            if request.assigned_admin is not None:
                await query.answer("This request is already assigned")
                return
                
            # Assign the request
            request.assigned_admin = str(admin_id)
            request.status = "assigned"
            request.updated_at = datetime.now()
            db.commit()
            
            # Add system message about assignment
            system_message = Message(
                request_id=request_id,
                sender_id=admin_id,
                sender_type="system",
                message=f"Request assigned to admin {admin_name}",
                timestamp=datetime.now()
            )
            db.add(system_message)
            db.commit()
            
            # Update the group message
            keyboard = query.message.reply_markup.inline_keyboard
            new_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("💬 Open Chat", callback_data=f"chat_{request_id}"),
                    InlineKeyboardButton("✅ Solve", callback_data=f"solve_{request_id}")
                ]
            ])
            
            try:
                # Import bot inside function to avoid circular import
                from app.bot.bot import bot
                await bot.edit_message_reply_markup(
                    chat_id=ADMIN_GROUP_ID,
                    message_id=query.message.message_id,
                    reply_markup=new_keyboard
                )
            except Exception as e:
                logging.error(f"Error updating message keyboard: {e}")
            
            await query.answer("Request assigned successfully")
            
        elif action == "view":
            # Send private message to admin with details and proper WebApp button
            # First, get full request details
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
            
            # Create appropriate buttons based on the status
            private_keyboard = []
            
            # Add WebApp button only in private message to admin
            if status in ["pending", "in_progress"]:
                private_keyboard.append([
                    InlineKeyboardButton(
                        "Open Support Chat", 
                        web_app=WebAppInfo(
                            url=f"{BASE_WEBAPP_URL}/chat.html?request_id={request_id}&admin_id={admin_id}"
                        )
                    )
                ])
            
            # Add appropriate action button based on status
            if status == "pending":
                private_keyboard.append([
                    InlineKeyboardButton(
                        "Assign to me", 
                        callback_data=f"assign_{request_id}_{admin_id}"
                    )
                ])
            elif status == "in_progress" and request.assigned_admin == str(admin_id):
                private_keyboard.append([
                    InlineKeyboardButton(
                        "Mark as resolved", 
                        callback_data=f"resolve_{request_id}"
                    )
                ])
            
            # Send detailed view to admin as private message
            private_reply_markup = InlineKeyboardMarkup(private_keyboard)
            await context.bot.send_message(
                chat_id=admin_id,
                text=response,
                reply_markup=private_reply_markup,
                parse_mode="HTML"
            )
            
            # Acknowledge in the group
            await query.edit_message_text(
                text=query.message.text + f"\n\n👁️ Details viewed by: {admin_name}",
                reply_markup=query.message.reply_markup
            )
            
        elif action == "chat":
            # Admin wants to open chat with this user
            if request.assigned_admin != str(admin_id) and request.assigned_admin is not None:
                assigned_admin = db.query(Admin).filter(Admin.id == request.assigned_admin).first()
                if assigned_admin:
                    await query.answer(f"This request is assigned to {assigned_admin.name}")
                    return
            
            # If not assigned to anyone, assign it to this admin
            if request.assigned_admin is None:
                request.assigned_admin = str(admin_id)
                request.updated_at = datetime.now()
                request.status = "assigned"
                db.commit()
                
                # Add system message about assignment to chat
                system_message = Message(
                    request_id=request_id,
                    sender_id=admin_id,
                    sender_type="system", 
                    message=f"This request has been assigned to {admin_name}",
                    timestamp=datetime.now()
                )
                db.add(system_message)
                db.commit()
            
            # Import bot inside function to avoid circular import
            from app.bot.bot import bot
            
            # Create a WebApp URL for the chat interface with proper Telegram init parameter
            # Use a clear format that's easier to parse
            chat_url = f"{BASE_WEBAPP_URL}/chat.html?request_id={request_id}&admin_id={admin_id}"
            
            # Create a WebApp button for the chat
            keyboard = [[
                InlineKeyboardButton(
                    "📱 Open Chat Interface",
                    web_app=WebAppInfo(url=chat_url)
                )
            ]]
            
            # Send private message to admin with WebApp button
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"Click below to open the chat interface for request #{request_id}:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await query.answer("Opening chat interface...")
            except Exception as e:
                logging.error(f"Error sending chat message to admin: {e}")
                await query.answer("Error opening chat interface")
            
        elif action == "solve" or action == "resolve":
            # Store the request ID in context for the solution message
            context.user_data["solving_request_id"] = request_id
            
            # Update the message in admin group
            try:
                from app.bot.bot import bot
                await bot.edit_message_text(
                    chat_id=ADMIN_GROUP_ID,
                    message_id=query.message.message_id,
                    text=f"✍️ Admin {admin_name} is providing resolution details for request #{request_id}...\n\nPlease wait."
                )
            except Exception as e:
                logging.error(f"Error updating admin group message: {e}")
            
            # Ask admin for solution details in private message
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"Please provide a brief description of the solution for request #{request_id}:"
                )
                await query.answer("Please provide solution details in our private chat")
            except Exception as e:
                logging.error(f"Error sending solution prompt to admin: {e}")
                await query.answer("Error requesting solution details")
        else:
            await query.answer("Unknown action") 