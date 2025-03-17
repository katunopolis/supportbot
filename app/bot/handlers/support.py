import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from app.database.models import Request, Message
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
        
        # Create inline keyboard with buttons for admin actions
        keyboard = [
            [
                InlineKeyboardButton("📋 Assign", callback_data=f"assign_{request_id}"),
                InlineKeyboardButton("💬 Open Chat", callback_data=f"chat_{request_id}")
            ],
            [
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
    await query.answer()  # Answer to stop the loading state
    
    # Extract the action and request_id from callback data
    # Format is "{action}_{request_id}" (e.g., "assign_123")
    callback_data = query.data
    
    try:
        # Split callback_data and handle potential format issues
        if '_' not in callback_data:
            await query.edit_message_text(text=f"❌ Invalid callback data format: {callback_data}")
            return
            
        action, request_id_str = callback_data.split('_', 1)
        
        try:
            request_id = int(request_id_str)
        except ValueError:
            await query.edit_message_text(text=f"❌ Invalid request ID: {request_id_str}")
            return
        
        # Get admin info
        admin_id = update.effective_user.id
        admin_name = update.effective_user.full_name
        
        # Create database session
        db = next(get_db())
        
        try:
            # Check if request exists
            request = db.query(Request).filter(Request.id == request_id).first()
            if not request:
                await query.edit_message_text(text=f"❌ Request #{request_id} not found")
                return
            
            # Handle different actions
            if action == "assign":
                # Assign the request to this admin
                request.assigned_admin = admin_id
                db.commit()
                
                # Update message text with assignment info
                original_text = query.message.text
                new_text = original_text + f"\n\n👤 Assigned to: {admin_name}"
                
                # Create updated keyboard (remove assign button)
                keyboard = [
                    [
                        InlineKeyboardButton("💬 Open Chat", callback_data=f"chat_{request_id}")
                    ],
                    [
                        InlineKeyboardButton("✅ Solve", callback_data=f"solve_{request_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(text=new_text, reply_markup=reply_markup)
                
            elif action == "chat":
                # Import config for webapp URLs
                from app.config import WEB_APP_URL, BASE_WEBAPP_URL
                
                # Generate proper WebApp chat URL
                chat_url = f"{BASE_WEBAPP_URL}/chat/{request_id}"
                
                # Create inline keyboard with WebApp button
                chat_button = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Open Chat Interface",
                        web_app=WebAppInfo(url=chat_url)
                    )]
                ])
                
                # Send WebApp button to admin
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"Open chat interface for request #{request_id}:",
                    reply_markup=chat_button
                )
                
                # Acknowledge in the group
                await query.edit_message_text(
                    text=query.message.text + f"\n\n💬 Chat opened by: {admin_name}",
                    reply_markup=query.message.reply_markup
                )
                
            elif action == "solve":
                # Mark the request as solved
                request.status = "solved"
                request.updated_at = datetime.now()
                db.commit()
                
                # Update message
                await query.edit_message_text(
                    text=query.message.text + f"\n\n✅ Solved by: {admin_name}",
                    reply_markup=None  # Remove buttons
                )
                
                # Notify the user that their request was solved
                try:
                    await context.bot.send_message(
                        chat_id=request.user_id,
                        text=f"✅ Your support request (#{request_id}) has been resolved. Thank you for using our support service!"
                    )
                except Exception as e:
                    logging.error(f"Failed to notify user about solved request: {e}")
            
            else:
                await query.edit_message_text(text=f"❌ Unknown action: {action}")
            
        except Exception as e:
            logging.error(f"Error handling callback query: {e}")
            await query.edit_message_text(text=f"❌ Error processing action: {str(e)}")
        finally:
            db.close()
        
    except Exception as e:
        logging.error(f"Error handling callback query: {e}")
        await query.edit_message_text(text=f"❌ Error processing callback query: {str(e)}") 