import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from app.config import get_webapp_url

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command in private chat."""
    user_id = update.message.from_user.id
    if context.user_data.get(f"pending_request_{user_id}"):
        await update.message.reply_text("Welcome back! Please describe your issue:")
        context.user_data[f"requesting_support_{user_id}"] = True
        context.user_data.pop(f"pending_request_{user_id}", None)
    else:
        await update.message.reply_text("Welcome! Use /request in the group to get support.")

async def request_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /request command from the public group by opening a Web App."""
    user_id = update.message.from_user.id
    logging.info(f"User {user_id} requested support")
    
    try:
        # Use the versioned web app URL
        keyboard = [[
            InlineKeyboardButton(
                text="Open Support Form",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the message with the Web App button
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )
        context.user_data[f"requesting_support_{user_id}"] = True
    except Exception as e:
        logging.error(f"Error creating WebApp button: {e}")
        # Fallback to URL button if WebApp fails
        keyboard = [[InlineKeyboardButton("Open Support Form", url=get_webapp_url())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        ) 