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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information about the bot."""
    help_text = (
        "🤖 *Support Bot Help* 🤖\n\n"
        "I'm a bot that helps you manage support requests. Here are the available commands:\n\n"
        "👤 *User Commands*:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/request - Create a new support request\n\n"
        "👨‍💼 *Admin Commands*:\n"
        "/list - List all support requests\n"
        "/view_ID - View details of a specific request (replace ID with request number)\n\n"
        "📱 *WebApp Features*:\n"
        "- Request form to submit support issues\n"
        "- Chat interface for admins to communicate with users\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown") 