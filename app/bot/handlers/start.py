import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from app.config import get_webapp_url, BASE_WEBAPP_URL, WEB_APP_URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command in private chat."""
    user_id = update.message.from_user.id
    if context.user_data.get(f"pending_request_{user_id}"):
        await update.message.reply_text("Welcome back! Please describe your issue:")
        context.user_data[f"requesting_support_{user_id}"] = True
        context.user_data.pop(f"pending_request_{user_id}", None)
    else:
        await update.message.reply_text("Welcome! Use /request in the group to get support.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command to verify the bot is working."""
    await update.message.reply_text("✅ Bot is working correctly! Command handling is now fixed.")
    logging.info(f"Test command executed by user {update.message.from_user.id}")

async def request_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /request command by opening the appropriate WebApp based on chat type."""
    user_id = update.message.from_user.id
    chat_type = update.effective_chat.type
    logging.info(f"User {user_id} requested support in {chat_type} chat")
    
    # Use different approaches based on chat type
    if chat_type == "private":
        # In private chats, we can use the full WebApp URL
        return await request_support_private(update, context)
    else:
        # In groups, we need special handling
        return await request_support_group(update, context)

async def request_support_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support request in private chat - can use full WebApp URL."""
    user_id = update.message.from_user.id
    logging.info(f"Private chat support request from user {user_id}")
    
    try:
        # For private chats, we can use the full form URL
        webapp_url = get_webapp_url()
        logging.info(f"Private chat using WebApp URL: {webapp_url}")
        
        keyboard = [[
            InlineKeyboardButton(
                text="Open Support Form",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )
        context.user_data[f"requesting_support_{user_id}"] = True
        return True
    except Exception as e:
        logging.error(f"Error creating private WebApp button: {e}")
        # Fallback to regular message
        await update.message.reply_text(
            "Sorry, there was an error opening the support form. Please try again later."
        )
        return False

async def request_support_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support request in group chat - needs special URL handling."""
    user_id = update.message.from_user.id
    logging.info(f"Group chat support request from user {user_id}")
    
    try:
        # For group chats, we use the simplest possible URL format
        # that Telegram will accept for public groups
        webapp_url = f"{BASE_WEBAPP_URL}"
        if not webapp_url.endswith('/'):
            webapp_url += '/'
            
        logging.info(f"Group chat using WebApp URL: {webapp_url}")
        
        keyboard = [[
            InlineKeyboardButton(
                text="Open Support Form",
                web_app=WebAppInfo(url=webapp_url)
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Click the button below to open our support form:",
            reply_markup=reply_markup
        )
        context.user_data[f"requesting_support_{user_id}"] = True
        return True
    except Exception as e:
        logging.error(f"Error creating group WebApp button: {e}")
        # Fallback to URL button if WebApp fails
        keyboard = [[InlineKeyboardButton("Open Support Form", url=f"{BASE_WEBAPP_URL}/")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Click the button below to open our support form (opens in browser):",
            reply_markup=reply_markup
        )
        return False

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information about the bot."""
    help_text = (
        "🤖 *Support Bot Help* 🤖\n\n"
        "I'm a bot that helps you manage support requests. Here are the available commands:\n\n"
        "👤 *User Commands*:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/request - Create a new support request\n"
        "/test - Test command to verify the bot is working\n\n"
        "👨‍💼 *Admin Commands*:\n"
        "/list - List all support requests\n"
        "/view_ID - View details of a specific request (replace ID with request number)\n\n"
        "📱 *WebApp Features*:\n"
        "- Request form to submit support issues\n"
        "- Chat interface for admins to communicate with users\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown") 