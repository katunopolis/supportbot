from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import time
from datetime import datetime
from sqlalchemy import text
from app.api.routes import router as api_router
from app.database.session import init_db, engine, POOL_SIZE, MAX_OVERFLOW
from app.logging.setup import setup_logging
from app.bot.bot import initialize_bot, setup_webhook, remove_webhook, process_update
import os
import httpx

# WebApp service URL from environment (with fallback to localhost)
WEBAPP_SERVICE_URL = os.getenv("WEBAPP_SERVICE_URL", "http://localhost:3000")

# Global metrics
request_times = []
webhook_times = []
last_errors = []
start_time = time.time()

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

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
static_path = Path(__file__).parent / "monitoring" / "static"
templates_path = Path(__file__).parent / "monitoring" / "templates"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers with response caching
app.include_router(api_router)

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
    """Health check endpoint for Railway."""
    try:
        # Check database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()  # Add explicit commit
            
        # Get system metrics if psutil is available
        system_metrics = {}
        try:
            import psutil
            system_metrics = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent
            }
        except ImportError:
            logging.warning("psutil not available - system metrics will be limited")
            system_metrics = {
                "note": "System metrics unavailable - psutil not installed"
            }
            
        # Get bot status dynamically to avoid circular import
        from app.bot.bot import bot_app
        bot_status = "running" if bot_app else "not_initialized"
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "bot": bot_status,
            "version": "1.2.0",
            "system": system_metrics
        }
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }

@app.post("/webapp-log")
@app.options("/webapp-log")  # Handle CORS preflight
async def webapp_log(request: Request):
    """Handle Railway's webapp logging requests."""
    # For OPTIONS request, return 200 OK
    if request.method == "OPTIONS":
        return {"status": "ok"}
        
    try:
        body = await request.json()
        logging.info(f"Webapp log: {body}")
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error processing webapp log: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log errors and return appropriate response."""
    error_info = {
        "timestamp": datetime.now().isoformat(),
        "path": str(request.url),
        "method": request.method,
        "error": str(exc)
    }
    
    # Add to error tracking
    last_errors.append(error_info)
    if len(last_errors) > 100:  # Keep only last 100 errors
        last_errors.pop(0)
        
    logging.error(f"Global error handler: {error_info}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

# Add this new route to proxy requests to the webapp service
@app.get("/{path:path}")
async def proxy_webapp(path: str, request: Request):
    """Proxy requests to the webapp service"""
    target_url = f"{WEBAPP_SERVICE_URL}/{path}"
    
    # Get query parameters from the original request
    params = dict(request.query_params)
    
    # Create httpx client for forwarding the request
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request with the original query parameters
            response = await client.request(
                method=request.method,
                url=target_url,
                params=params,
                headers={key: value for key, value in request.headers.items() if key != "host"},
                content=await request.body(),
                follow_redirects=True
            )
            
            # Return the response from the webapp service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except Exception as e:
            logging.error(f"Error proxying request to webapp: {e}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            ) 