# Support Bot API Documentation

## Base URL
```
https://webapp-support-bot-production.up.railway.app
```

## Authentication
All API endpoints require appropriate authentication. Authentication methods vary by endpoint type.

## Support Request Endpoints

### Create Support Request
```http
POST /api/requests
```

**Request Body:**
```json
{
    "user_id": 123456789,
    "issue": "Description of the issue"
}
```

**Response:**
```json
{
    "request_id": 1,
    "status": "pending",
    "created_at": "2025-03-16T17:01:08.191Z"
}
```

### Update Support Request
```http
PUT /api/requests/{request_id}
```

**Request Body:**
```json
{
    "status": "in_progress",
    "assigned_admin": 987654321,
    "solution": "Solution description"
}
```

**Response:**
```json
{
    "request_id": 1,
    "status": "in_progress",
    "assigned_admin": 987654321,
    "solution": "Solution description",
    "updated_at": "2025-03-16T17:01:08.191Z"
}
```

### Add Message to Support Request
```http
POST /api/requests/{request_id}/messages
```

**Request Body:**
```json
{
    "sender_id": 123456789,
    "sender_type": "user",
    "message": "Message content"
}
```

**Response:**
```json
{
    "message_id": 1,
    "request_id": 1,
    "timestamp": "2025-03-16T17:01:08.191Z"
}
```

## Monitoring Endpoints

### Dashboard
```http
GET /monitoring/dashboard
```
Returns the monitoring dashboard HTML page.

### System Metrics
```http
GET /monitoring/api/metrics
```

**Response:**
```json
{
    "system": {
        "cpu_percent": 45.2,
        "memory_percent": 68.7,
        "uptime_seconds": 3600
    },
    "application": {
        "average_response_time": 0.245,
        "webhook_average_time": 0.156,
        "total_requests": 1000,
        "recent_errors": []
    },
    "database": {
        "active_connections": 5
    }
}
```

### Request Metrics
```http
GET /monitoring/api/requests
```

**Query Parameters:**
- `limit` (optional): Number of recent requests to return (default: 100)

### Error Metrics
```http
GET /monitoring/api/errors
```

## Health Check
```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": 1710604868.191,
    "database": "connected",
    "bot": "running",
    "version": "1.2.0",
    "system": {
        "cpu_percent": 45.2,
        "memory_percent": 68.7
    }
}
```

## Webhook Endpoint
```http
POST /webhook
```
Handles incoming updates from Telegram. This endpoint should be configured in your Telegram bot settings.

## Logging Endpoint
```http
POST /webapp-log
```
Internal endpoint for Railway's webapp logging system. Returns 200 OK when logs are successfully processed.

## Error Responses
All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
    "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
    "error": "Error description"
}
```

## Rate Limiting
The API implements rate limiting to prevent abuse. Current limits are:
- 100 requests per minute per IP for general endpoints
- 1000 requests per minute for the webhook endpoint

## Notes
1. All timestamps are in ISO 8601 format and UTC timezone
2. Request IDs are integers and auto-incrementing
3. Status values for support requests can be: "pending", "in_progress", "resolved", "closed"
4. Sender types can be: "user", "admin", "system"

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