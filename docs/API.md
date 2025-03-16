## Monitoring API Endpoints

### System Metrics
```http
GET /monitoring/api/metrics
```

Returns system-wide metrics including CPU, memory, database, and application statistics.

**Response**
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

### Request Metrics
```http
GET /monitoring/api/requests?limit=100
```

Returns detailed request timing information.

**Parameters**
- `limit` (optional): Number of recent requests to return (default: 100)

**Response**
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

### Error Metrics
```http
GET /monitoring/api/errors
```

Returns recent error information.

**Response**
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

## Performance Optimizations

### Response Compression
All API responses are now compressed using GZip for responses larger than 1000 bytes.

```python
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### CORS Configuration
CORS is now restricted to specific origins for better security:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://webapp-support-bot-production.up.railway.app",
        "https://supportbot-production-b784.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Background Tasks
Long-running operations are now processed in the background:

```python
@app.post("/webhook")
async def webhook(update: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_update_background, update)
    return {"status": "ok"}
```

### Performance Headers
All responses now include processing time information:

```
X-Process-Time: 0.123 # Time in seconds
```

### API Documentation
API documentation is now available at more secure endpoints:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

## Error Handling

### Enhanced Error Responses
All error responses now include additional context:

```json
{
    "detail": "An unexpected error occurred",
    "error_id": "unique_error_id",
    "path": "/api/endpoint"
}
```

### Rate Limiting
API endpoints are now rate-limited to prevent abuse:

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Rate limiting logic
    pass
```

## Monitoring Dashboard

The monitoring dashboard is available at `/monitoring/dashboard` and provides:
1. Real-time system metrics
2. Application performance data
3. Database connection stats
4. Error tracking visualization

## Best Practices

1. **Error Handling**
   - Always check response status codes
   - Handle rate limiting appropriately
   - Implement exponential backoff for retries

2. **Performance**
   - Use compression for large responses
   - Implement client-side caching
   - Handle background tasks appropriately

3. **Security**
   - Use HTTPS for all requests
   - Include appropriate authentication
   - Validate all input data 