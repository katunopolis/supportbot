from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.api.routes import chat, support, logs
from app.database.session import init_db
from app.logging.setup import setup_logging
from app.bot.bot import initialize_bot, setup_webhook, remove_webhook, process_update

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    try:
        # Initialize database
        init_db()
        logging.info("Database initialized successfully")
        
        # Setup logging
        setup_logging()
        logging.info("Logging system initialized successfully")
        
        # Initialize bot and set webhook
        await initialize_bot()
        await setup_webhook()
        logging.info("Bot initialized and webhook set")
        
    except Exception as e:
        logging.error(f"Error during startup: {e}")
        raise
        
    yield
    
    try:
        # Remove webhook on shutdown
        await remove_webhook()
        logging.info("Webhook removed on shutdown")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Support Bot API",
    description="API for managing support requests and chat interactions",
    version="1.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(support.router, prefix="/api", tags=["support"])
app.include_router(logs.router, prefix="/api", tags=["logs"])

@app.post("/webhook")
async def webhook(update: dict):
    """Handle incoming updates from Telegram."""
    try:
        success = await process_update(update)
        if success:
            return {"status": "ok"}
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Failed to process update"}
            )
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.2.0"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    error_id = logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error_id": error_id
        }
    ) 