from fastapi import APIRouter
from .support import router as support_router
from .chat import router as chat_router, chat_router as chat_router_duplicate
from .logs import router as logs_router

# Create a main API router
router = APIRouter()

# Include our specific routers with explicit prefixes
router.include_router(support_router, prefix="/support", tags=["support"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(chat_router_duplicate, prefix="/chat_api", tags=["chat"])  # Add duplicate router for compatibility
router.include_router(logs_router, prefix="/logs", tags=["logs"]) 