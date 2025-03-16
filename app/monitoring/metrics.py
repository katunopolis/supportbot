import time
import psutil
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from sqlalchemy import text

@dataclass
class RequestMetric:
    path: str
    method: str
    time: float
    timestamp: str

@dataclass
class ErrorMetric:
    timestamp: str
    path: str
    method: str
    error: str
    error_id: str

class MetricsManager:
    def __init__(self, max_history: int = 1000):
        self.request_times: List[RequestMetric] = []
        self.webhook_times: List[float] = []
        self.last_errors: List[ErrorMetric] = []
        self.start_time = time.time()
        self.max_history = max_history

    def add_request_metric(self, path: str, method: str, process_time: float):
        """Add a new request metric."""
        metric = RequestMetric(
            path=path,
            method=method,
            time=process_time,
            timestamp=datetime.now().isoformat()
        )
        self.request_times.append(metric)
        if len(self.request_times) > self.max_history:
            self.request_times.pop(0)

    def add_webhook_time(self, process_time: float):
        """Add a new webhook processing time."""
        self.webhook_times.append(process_time)
        if len(self.webhook_times) > self.max_history:
            self.webhook_times.pop(0)

    def add_error(self, path: str, method: str, error: str, error_id: str):
        """Add a new error metric."""
        error_metric = ErrorMetric(
            timestamp=datetime.now().isoformat(),
            path=path,
            method=method,
            error=error,
            error_id=error_id
        )
        self.last_errors.append(error_metric)
        if len(self.last_errors) > self.max_history:
            self.last_errors.pop(0)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics."""
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": memory.percent,
            "memory_available": memory.available,
            "uptime_seconds": time.time() - self.start_time
        }

    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics."""
        avg_response_time = (
            sum(r.time for r in self.request_times) / len(self.request_times)
            if self.request_times else 0
        )
        webhook_avg_time = (
            sum(self.webhook_times) / len(self.webhook_times)
            if self.webhook_times else 0
        )
        return {
            "average_response_time": avg_response_time,
            "webhook_average_time": webhook_avg_time,
            "total_requests": len(self.request_times),
            "recent_errors": [asdict(error) for error in self.last_errors[-10:]]
        }

    def get_request_metrics(self, limit: int = 100) -> Dict[str, Any]:
        """Get detailed request metrics."""
        return {
            "request_count": len(self.request_times),
            "recent_requests": [asdict(req) for req in self.request_times[-limit:]]
        }

    def get_error_metrics(self, limit: int = 50) -> Dict[str, Any]:
        """Get error metrics."""
        return {
            "error_count": len(self.last_errors),
            "recent_errors": [asdict(error) for error in self.last_errors[-limit:]]
        }

# Global metrics manager instance
metrics_manager = MetricsManager() 