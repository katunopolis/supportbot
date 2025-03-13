from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import sqlite3
from typing import Optional

app = FastAPI()

# Models
class SupportRequest(BaseModel):
    user_id: int
    issue: str

class ChatMessage(BaseModel):
    sender_id: int
    sender_type: str
    message: str

# Database setup
def init_db():
    """Initialize SQLite database for storing support requests and messages."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Create requests table
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
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER,
                    sender_id INTEGER,
                    sender_type TEXT,  -- 'user' or 'admin'
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES requests(id)
                )
            """)
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")

# Initialize database on startup
init_db()

# Routes
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Support Bot API is running"}

@app.post("/support-request")
async def create_request(request: SupportRequest):
    """Handle new support requests."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Save request
            cursor.execute("""
                INSERT INTO requests (user_id, issue)
                VALUES (?, ?)
            """, (request.user_id, request.issue))
            conn.commit()
            request_id = cursor.lastrowid
            
            # Save initial message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, 'user', ?)
            """, (request_id, request.user_id, request.issue))
            conn.commit()
            
            # Return the web app URL for the chat
            webapp_url = f"https://webapp-support-bot-production.up.railway.app/chat/{request_id}"
            
            return JSONResponse(content={
                "message": "Support request submitted successfully",
                "request_id": request_id,
                "chat_url": webapp_url
            })
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/{request_id}")
async def get_chat_messages(request_id: int):
    """Get all messages for a specific support request."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, r.user_id, r.assigned_admin
                FROM messages m
                JOIN requests r ON m.request_id = r.id
                WHERE m.request_id = ?
                ORDER BY m.timestamp ASC
            """, (request_id,))
            messages = cursor.fetchall()
            
            if not messages:
                raise HTTPException(status_code=404, detail="Request not found")
                
            # Format messages for frontend
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg[0],
                    "request_id": msg[1],
                    "sender_id": msg[2],
                    "sender_type": msg[3],
                    "message": msg[4],
                    "timestamp": msg[5],
                    "user_id": msg[6],
                    "assigned_admin": msg[7]
                })
            
            return JSONResponse(content={"messages": formatted_messages})
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/{request_id}/message")
async def send_message(request_id: int, message: ChatMessage):
    """Send a new message in the support chat."""
    try:
        with sqlite3.connect("support_requests.db") as conn:
            cursor = conn.cursor()
            # Save message
            cursor.execute("""
                INSERT INTO messages (request_id, sender_id, sender_type, message)
                VALUES (?, ?, ?, ?)
            """, (request_id, message.sender_id, message.sender_type, message.message))
            conn.commit()
            
            return JSONResponse(content={"message": "Message sent successfully"})
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint that verifies webhook status."""
    try:
        from telegram import Bot
        bot = Bot(token=TOKEN)
        webhook_info = await bot.get_webhook_info()
        return {
            "status": "healthy",
            "webhook_url": webhook_info.url,
            "webhook_set": webhook_info.url == WEBHOOK_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
