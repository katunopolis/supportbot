"""
Handlers for the Admin Panel module.
"""

import logging
from typing import Optional
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
import os

from app.database.models import Request
from app.database.session import get_db
from app.admin_panel.config import is_admin_panel_enabled, get_admin_panel_url

logger = logging.getLogger(__name__)

# Get admin group ID from environment variables
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /panel command to open the admin panel."""
    if not is_admin_panel_enabled():
        await update.message.reply_text("The admin panel is currently disabled.")
        return
        
    # Verify if the user is in the admin group
    if ADMIN_GROUP_ID and str(update.effective_chat.id) != ADMIN_GROUP_ID:
        await update.message.reply_text("This command is only available in the admin group.")
        return
        
    # Create keyboard with WebApp button
    keyboard = [
        [
            InlineKeyboardButton(
                "Open Admin Panel",
                web_app=WebAppInfo(url=get_admin_panel_url())
            )
        ]
    ]
    
    await update.message.reply_text(
        "Click below to open the admin panel:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register_admin_panel_handlers(application):
    """Register handlers for the admin panel module."""
    if not is_admin_panel_enabled():
        logger.info("Admin panel module is disabled. Skipping handler registration.")
        return
        
    # Register the /panel command handler
    application.add_handler(CommandHandler("panel", admin_panel_command))
    logger.info("Admin panel handlers registered successfully.") 