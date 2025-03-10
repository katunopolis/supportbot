from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from fastapi import FastAPI
import telegram  # for catching Forbidden
import sqlite3
import os
import uvicorn

# Create FastAPI instance
fastapi_app = FastAPI()

# Create Telegram bot instance
bot_app = Application.builder().token(TOKEN).build()

# Webhook URL
WEBHOOK_URL = "https://supportbot-production-b784.up.railway.app/webhook"

async def set_webhook():
    """Set the webhook for the bot."""
    from telegram import Bot
    bot = Bot(token=TOKEN)
    await bot.set_webhook(WEBHOOK_URL)

# Telegram Bot Token
TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Error: SUPPORT_BOT_TOKEN is not set. Please set it in your environment variables.")

print(f"Bot Token Loaded: {TOKEN[:5]}********")  # Prints only part of the token for security

# Admin Group Chat ID
ADMIN_GROUP_ID = -4771220922

# Database setup
def init_db():
    conn = sqlite3.connect("support_requests.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            issue TEXT,
            assigned_admin INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'Open',
            solution TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

# Test sending a message manually
async def test_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(ADMIN_GROUP_ID, "Test message from bot!")
        print("[DEBUG] Successfully sent test message to Admin Group")
        await update.message.reply_text("Test message sent to admin group. Check if it arrived!")
    except Exception as e:
        print(f"[ERROR] Failed to send test message: {e}")
        await update.message.reply_text(f"Failed to send test message: {e}")

# Get the Admin Group Chat ID
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID: {chat_id}")
    print(f"[DEBUG] Admin Group ID: {chat_id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start in private chat. If user had pending request, skip /request."""
    user_id = update.message.from_user.id
    if context.user_data.get(f"pending_request_{user_id}"):
        await update.message.reply_text("Welcome back! Please describe the issue you're facing:")
        context.user_data[f"requesting_support_{user_id}"] = True
        context.user_data.pop(f"pending_request_{user_id}", None)
    else:
        await update.message.reply_text("Welcome! Use /request in the group to get support.")

async def request_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /request command from a public group"""
    user_id = update.message.from_user.id

    if update.message.chat.type != "private":
        # Attempt to DM the user.
        try:
            await context.bot.send_message(
                user_id,
                "I see you need support! Please describe the issue you're facing:"
            )
            context.user_data[f"requesting_support_{user_id}"] = True

            # Notify user in the group
            await context.bot.send_message(
                update.message.chat_id,
                f"@{update.message.from_user.username}, I've sent you a private message."
            )

        except telegram.error.Forbidden:
            # Bot can't message user, so store a pending_request flag.
            context.user_data[f"pending_request_{user_id}"] = True
            keyboard = [[InlineKeyboardButton("Start Chat with Bot", url=f"https://t.me/{context.bot.username}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"@{update.message.from_user.username}, please start a private chat with the bot first by clicking below. Once you click 'Start' in private chat, I'll automatically ask for your issue.",
                reply_markup=reply_markup
            )
    else:
        # If user typed /request in private chat
        await update.message.reply_text("Please describe the issue you're facing:")
        context.user_data[f"requesting_support_{user_id}"] = True

async def collect_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user responses to collect issue details"""
    user_id = update.message.from_user.id

    if context.user_data.get(f"requesting_support_{user_id}"):
        issue_description = update.message.text
        print(f"[DEBUG] Received issue from user {user_id}: {issue_description}")

        conn = sqlite3.connect("support_requests.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO requests (user_id, issue) VALUES (?, ?)", (user_id, issue_description))
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()
        print(f"[DEBUG] Saved request #{request_id} to the database")

        # Build the keyboard with three buttons: Assign, Open Chat (if any), Solve.
        buttons = []
        row1 = [InlineKeyboardButton("Assign to me", callback_data=f"assign_{request_id}")]

        if update.message.from_user.username:
            row2 = [InlineKeyboardButton("Open User Chat", url=f"https://t.me/{update.message.from_user.username}")]
            buttons.append(row2)
        # "Solve" button.
        row3 = [InlineKeyboardButton("Solve", callback_data=f"solve_{request_id}")]

        buttons.insert(0, row1)  # Put "Assign to me" at top row
        buttons.append(row3)     # Solve button as last row

        reply_markup = InlineKeyboardMarkup(buttons)

        try:
            await context.bot.send_message(
                ADMIN_GROUP_ID,
                f"📌 **New Support Request #{request_id}**\n\n"
                f"🔹 **User ID:** `{user_id}`\n"
                f"📄 **Issue:** {issue_description}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            print(f"[DEBUG] Sent request #{request_id} to Admin Group")
        except Exception as e:
            print(f"[ERROR] Failed to send message to Admin Group: {e}")

        await update.message.reply_text("✅ Your request has been submitted. A support admin will reach out soon.")
        context.user_data[f"requesting_support_{user_id}"] = False

async def assign_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id
    request_id = int(query.data.split("_")[1])

    conn = sqlite3.connect("support_requests.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET assigned_admin = ?, status = 'Assigned' WHERE id = ?", (admin_id, request_id))
    conn.commit()

    cursor.execute("SELECT user_id FROM requests WHERE id = ?", (request_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id = user[0]
        assigned_username = query.from_user.username  # or None
        if not assigned_username:
            # Hard-code the admin’s ID if you know it
            # (Here you said your admin user ID is 839475704)
            # We'll build tg:// link
            assigned_username = None
            admin_id_hardcoded = 839475704
            admin_link = f"tg://user?id={admin_id_hardcoded}"
        else:
            admin_link = f"https://t.me/{assigned_username}"

        # Replace 'Assign to me' with 'Assigned to X'
        original_markup = query.message.reply_markup
        assigned_label = f"Assigned to {assigned_username or 'unknown'}"
        assigned_button = InlineKeyboardButton(assigned_label, callback_data="noop")

        new_keyboard = []
        for row in original_markup.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("assign_"):
                    new_row.append(assigned_button)
                else:
                    new_row.append(btn)
            new_keyboard.append(new_row)

        # Update the Admin Group message
        await query.edit_message_reply_markup(InlineKeyboardMarkup(new_keyboard))
        await query.answer("You have been assigned to this request.")

        # Provide user with a button to open the admin chat
        user_keyboard = [[InlineKeyboardButton("Open Admin Chat", url=admin_link)]]
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"A support admin (@{assigned_username or 'unknown'}) "
                f"has been assigned to your request.\n\n"
                "Click below to open a direct chat with them."
            ),
            reply_markup=InlineKeyboardMarkup(user_keyboard)
        )
    else:
        await query.answer("Error: Could not find the request in the database.")

async def solve_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    When admin clicks 'Solve' button in the Admin Group message,
    we simply ask them for a solution description and store
    the request ID for the next text they send.
    """
    query = update.callback_query
    admin_id = query.from_user.id
    request_id = int(query.data.split("_")[1])

    # Let the admin know we are waiting for the solution text
    await query.answer()  # close the loading circle
    await query.message.reply_text(
        f"Admin (@{query.from_user.username}), please provide a short description of the solution for request #{request_id}."
    )

    # We'll store that this admin is solving that request
    # so that the next text from them goes to save_solution.
    context.user_data[f"solving_request_admin_{admin_id}"] = request_id

    # Optionally, remove or disable the Solve button so no one else tries to solve
    # but keep the assigned buttons, etc.
    original_markup = query.message.reply_markup
    new_keyboard = []
    for row in original_markup.inline_keyboard:
        new_row = []
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("solve_"):
                # Show that solve is in progress
                new_row.append(InlineKeyboardButton("Solving…", callback_data="noop"))
            else:
                new_row.append(btn)
        new_keyboard.append(new_row)

    await query.edit_message_reply_markup(InlineKeyboardMarkup(new_keyboard))

async def solved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles marking a request as solved (from user side command)"""
    user_id = update.message.from_user.id

    conn = sqlite3.connect("support_requests.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM requests WHERE user_id = ? AND status = 'Assigned'", (user_id,))
    request = cursor.fetchone()

    if request:
        request_id = request[0]
        await update.message.reply_text("Please provide a short description of the solution:")
        context.user_data["solving_request"] = request_id
    else:
        await update.message.reply_text("No active support requests found.")

async def save_solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the solution description from either:
    - The user side (/solved flow), OR
    - The admin side after clicking 'Solve' in the Admin Group.
    """

    admin_id = update.message.from_user.id
    text_input = update.message.text

    # 1) Admin solving path
    admin_solving_key = f"solving_request_admin_{admin_id}"
    if admin_solving_key in context.user_data:
        request_id = context.user_data[admin_solving_key]

        conn = sqlite3.connect("support_requests.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET status = 'Solved', solution = ? WHERE id = ?",
            (text_input, request_id)
        )
        # Retrieve the user ID so we can message them the solution
        cursor.execute("SELECT user_id FROM requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        user_id = row[0] if row else None  # <-- define user_id here
        conn.commit()
        conn.close()

        # Notify admin group
        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"Request #{request_id} has been marked as **Solved** by admin (@{update.message.from_user.username}).\n"
            f"**Solution:** {text_input}",
            parse_mode="Markdown"
        )

        # Send solution to the user
        if user_id:
            await context.bot.send_message(
                user_id,
                f"Your request #{request_id} has been solved by admin (@{update.message.from_user.username}).\n"
                f"**Solution:** {text_input}",
                parse_mode="Markdown"
            )

        await update.message.reply_text(
            f"Request #{request_id} marked as solved with your solution:\n{text_input}"
        )

        context.user_data.pop(admin_solving_key, None)
        return

    # 2) Otherwise, check if it's the user side solution
    if "solving_request" in context.user_data:
        request_id = context.user_data["solving_request"]
        solution = text_input

        conn = sqlite3.connect("support_requests.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE requests SET status = 'Solved', solution = ? WHERE id = ?",
            (solution, request_id)
        )
        conn.commit()
        conn.close()

        await context.bot.send_message(
            ADMIN_GROUP_ID,
            f"Request #{request_id} has been marked as Solved by the user.\nSolution: {solution}"
        )

        await update.message.reply_text("Your request has been marked as solved. Thank you!")
        context.user_data.pop("solving_request", None)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks"""
    query = update.callback_query

    if query.data.startswith("assign_"):
        await assign_request(update, context)
    elif query.data.startswith("solve_"):
        await solve_request(update, context)


def main():
    init_db()
    
    # Initialize bot application
    bot_app = Application.builder().token(TOKEN).build()

    # Add handlers to bot_app
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("request", request_support))
    bot_app.add_handler(CommandHandler("solved", solved))
    bot_app.add_handler(CommandHandler("get_chat_id", get_chat_id))
    bot_app.add_handler(CommandHandler("test_admin", test_admin_message))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_issue))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_solution))
    bot_app.add_handler(CallbackQueryHandler(button_handler))

    print("Setting webhook...")
    import asyncio
    asyncio.run(set_webhook())  # Set Telegram bot webhook

    print("Bot is running on webhook...")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
