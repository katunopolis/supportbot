from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import time
import psutil
from datetime import datetime
from sqlalchemy import text
from app.api.routes import chat, support, logs
from app.database.session import init_db, engine, POOL_SIZE, MAX_OVERFLOW
from app.logging.setup import setup_logging
from app.bot.bot import initialize_bot, setup_webhook, remove_webhook, process_update, bot_app, bot
from app.monitoring import monitoring_router

# Global metrics
request_times = []
webhook_times = []
last_errors = []
start_time = time.time()

# Performance monitoring middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Store request time for monitoring
    request_times.append({
        'path': request.url.path,
        'method': request.method,
        'time': process_time,
        'timestamp': datetime.now().isoformat()
    })
    # Keep only last 1000 requests
    if len(request_times) > 1000:
        request_times.pop(0)
        
    response.headers["X-Process-Time"] = str(process_time)
    return response

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

# Initialize FastAPI app with optimized settings
app = FastAPI(
    title="Support Bot API",
    description="API for managing support requests and chat interactions",
    version="1.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",  # Move API docs to /api/docs for better security
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://webapp-support-bot-production.up.railway.app",
        "https://supportbot-production-b784.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
static_path = Path(__file__).parent / "monitoring" / "static"
templates_path = Path(__file__).parent / "monitoring" / "templates"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers with response caching
app.include_router(
    chat.router,
    prefix="/api",
    tags=["chat"]
)
app.include_router(
    support.router,
    prefix="/api",
    tags=["support"]
)
app.include_router(
    logs.router,
    prefix="/api",
    tags=["logs"]
)
app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

async def process_update_background(update: dict, background_tasks: BackgroundTasks):
    """Process Telegram update in the background."""
    try:
        await process_update(update)
    except Exception as e:
        logging.error(f"Background update processing error: {e}")

@app.post("/webhook")
async def webhook(update: dict, background_tasks: BackgroundTasks):
    """Handle incoming updates from Telegram with performance monitoring."""
    start_time = time.time()
    try:
        # Add update processing to background tasks
        background_tasks.add_task(process_update_background, update, background_tasks)
        
        # Record webhook processing time
        process_time = time.time() - start_time
        webhook_times.append(process_time)
        # Keep only last 1000 webhook times
        if len(webhook_times) > 1000:
            webhook_times.pop(0)
            
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with system status."""
    return {
        "status": "healthy",
        "version": "1.2.0",
        "database": "connected",
        "bot": "running"
    }

@app.get("/monitoring/metrics")
async def get_metrics():
    """Get detailed system metrics."""
    try:
        # Database connection stats
        with engine.connect() as conn:
            active_connections = conn.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar()
            
        # Calculate average response times
        avg_response_time = sum(r['time'] for r in request_times) / len(request_times) if request_times else 0
        webhook_avg_time = sum(t for t in webhook_times) / len(webhook_times) if webhook_times else 0
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Bot metrics
        bot_info = {
            "concurrent_updates": bot_app.concurrent_updates,
            "connection_pool_size": bot_app.connection_pool_size,
            "running_webhooks": len(webhook_times)
        }
        
        # Database pool metrics
        db_pool_info = {
            "pool_size": POOL_SIZE,
            "max_overflow": MAX_OVERFLOW,
            "active_connections": active_connections
        }
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "uptime_seconds": time.time() - start_time
            },
            "application": {
                "average_response_time": avg_response_time,
                "webhook_average_time": webhook_avg_time,
                "total_requests": len(request_times),
                "recent_errors": last_errors[-10:],  # Last 10 errors
            },
            "database": db_pool_info,
            "bot": bot_info
        }
    except Exception as e:
        logging.error(f"Error collecting metrics: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to collect metrics"}
        )

@app.get("/monitoring/requests")
async def get_request_metrics(limit: int = 100):
    """Get detailed request timing information."""
    return {
        "request_count": len(request_times),
        "recent_requests": request_times[-limit:]
    }

@app.get("/monitoring/errors")
async def get_error_metrics():
    """Get recent error information."""
    return {
        "error_count": len(last_errors),
        "recent_errors": last_errors[-50:]  # Last 50 errors
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with error tracking."""
    error_id = logging.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Store error for monitoring
    error_info = {
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path,
        "method": request.method,
        "error": str(exc),
        "error_id": error_id
    }
    last_errors.append(error_info)
    # Keep only last 1000 errors
    if len(last_errors) > 1000:
        last_errors.pop(0)
        
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error_id": error_id,
            "path": request.url.path
        }
    )

# Initialize bot
@app.on_event("startup")
async def startup_event():
    await bot.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await bot.shutdown() 