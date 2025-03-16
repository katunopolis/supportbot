from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.monitoring.metrics import metrics_manager
from app.database.session import engine
from sqlalchemy import text

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@router.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard(request: Request):
    """Render the monitoring dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )

@router.get("/api/metrics")
async def get_metrics():
    """Get all system metrics."""
    try:
        # Get database connection stats
        with engine.connect() as conn:
            active_connections = conn.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar()
            
        return {
            "system": metrics_manager.get_system_metrics(),
            "application": metrics_manager.get_application_metrics(),
            "database": {
                "active_connections": active_connections
            }
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/requests")
async def get_request_metrics(limit: int = 100):
    """Get request metrics."""
    return metrics_manager.get_request_metrics(limit)

@router.get("/api/errors")
async def get_error_metrics():
    """Get error metrics."""
    return metrics_manager.get_error_metrics() 