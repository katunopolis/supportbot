# Monitoring System Documentation

## Overview
The monitoring system provides real-time insights into the bot's performance, system resources, and application metrics through an interactive dashboard and API endpoints.

## Dashboard

### Access
The monitoring dashboard is available at `/monitoring/dashboard`

### Features
1. **System Metrics**
   - CPU Usage (gauge chart)
   - Memory Usage (gauge chart)
   - System Uptime
   - Database Connections

2. **Application Metrics**
   - Average Response Time
   - Webhook Processing Time
   - Total Request Count
   - Recent Errors List

3. **Real-time Updates**
   - Auto-refresh every 5 seconds
   - Interactive charts
   - Error tracking

## API Endpoints

### 1. System Metrics
```
GET /monitoring/api/metrics
```
Returns:
```json
{
    "system": {
        "cpu_percent": float,
        "memory_percent": float,
        "memory_available": int,
        "uptime_seconds": float
    },
    "application": {
        "average_response_time": float,
        "webhook_average_time": float,
        "total_requests": int,
        "recent_errors": [
            {
                "timestamp": string,
                "path": string,
                "method": string,
                "error": string,
                "error_id": string
            }
        ]
    },
    "database": {
        "active_connections": int
    }
}
```

### 2. Request Metrics
```
GET /monitoring/api/requests?limit=100
```
Returns:
```json
{
    "request_count": int,
    "recent_requests": [
        {
            "path": string,
            "method": string,
            "time": float,
            "timestamp": string
        }
    ]
}
```

### 3. Error Metrics
```
GET /monitoring/api/errors
```
Returns:
```json
{
    "error_count": int,
    "recent_errors": [
        {
            "timestamp": string,
            "path": string,
            "method": string,
            "error": string,
            "error_id": string
        }
    ]
}
```

## Metrics Collection

### System Metrics
- CPU usage via `psutil`
- Memory usage and availability
- System uptime tracking
- Database connection monitoring

### Application Metrics
- Request timing tracking
- Webhook processing time
- Error collection and categorization
- Request count and patterns

### Data Retention
- Maximum 1000 entries for each metric type
- Automatic cleanup of old entries
- Real-time metric updates

## Implementation Details

### MetricsManager Class
The `MetricsManager` class handles all metric collection and storage:

```python
class MetricsManager:
    def __init__(self, max_history: int = 1000):
        self.request_times: List[RequestMetric] = []
        self.webhook_times: List[float] = []
        self.last_errors: List[ErrorMetric] = []
        self.start_time = time.time()
        self.max_history = max_history
```

### Metric Types

1. **RequestMetric**
```python
@dataclass
class RequestMetric:
    path: str
    method: str
    time: float
    timestamp: str
```

2. **ErrorMetric**
```python
@dataclass
class ErrorMetric:
    timestamp: str
    path: str
    method: str
    error: str
    error_id: str
```

## Dashboard Components

### 1. System Metrics Section
- CPU Usage Gauge
- Memory Usage Gauge
- Uptime Display
- Database Connections Counter

### 2. Application Metrics Section
- Response Time Display
- Webhook Time Display
- Request Counter

### 3. Error Tracking Section
- Recent Errors List
- Error Details
- Timestamp Information

## Integration

### Adding Custom Metrics
To add custom metrics:

1. Define metric in `MetricsManager`:
```python
def add_custom_metric(self, name: str, value: Any):
    self.custom_metrics[name] = value
```

2. Update API endpoint:
```python
@router.get("/api/custom-metrics")
async def get_custom_metrics():
    return metrics_manager.get_custom_metrics()
```

3. Add to dashboard:
```javascript
function updateCustomMetrics(data) {
    document.getElementById('custom-metric').textContent = data.value;
}
```

## Best Practices

1. **Performance Impact**
   - Use background tasks for metric collection
   - Implement efficient data structures
   - Regular cleanup of old metrics

2. **Security**
   - Restrict dashboard access
   - Validate metric data
   - Sanitize error messages

3. **Maintenance**
   - Regular metric cleanup
   - Dashboard updates
   - API endpoint monitoring 