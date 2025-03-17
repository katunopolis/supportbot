from fastapi import APIRouter
from .support import router as support_router
from .chat import router as chat_router
from .logs import router as logs_router

# Create a main API router
router = APIRouter()

# Include our specific routers
router.include_router(support_router, tags=["support"])
router.include_router(chat_router, tags=["chat"])
router.include_router(logs_router, tags=["logs"]) 