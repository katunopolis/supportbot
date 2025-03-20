# Database Optimization Documentation

## Overview
The database layer is optimized for high concurrency and performance using SQLAlchemy with PostgreSQL, featuring connection pooling, health checks, and automatic connection management.

## Connection Pool Configuration

### Overview
The application uses SQLAlchemy's connection pooling with optimized settings for better performance and stability. The connection pool is configured before the bot initialization to ensure proper resource management.

### Key Settings
```python
POOL_TIMEOUT = 30  # seconds
MAX_CONNECTIONS = 100
```

### Configuration Order
1. Pool timeout configuration
2. Connection pool size setting
3. Database session setup
4. Bot initialization

### Implementation Details

#### Database Session Setup
```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=MAX_CONNECTIONS,
    pool_timeout=POOL_TIMEOUT
)
```

#### Health Check Implementation
```python
async def check_database():
    """Test database connection with proper error handling."""
    try:
        async with Session() as session:
            await session.execute(text("SELECT 1"))
            await session.commit()
            return True
    except Exception as e:
        logging.error(f"Database connection test failed: {e}")
        return False
```

## Connection Management

### Session Factory
```python
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent unnecessary database queries
)
```

### Database Dependency
```python
def get_db():
    """Database session dependency with error handling."""
    db = SessionLocal()
    try:
        # Verify connection is active
        db.execute("SELECT 1")
        yield db
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise
    finally:
        db.close()
```

## Health Checks & Monitoring

### Connection Pool Events
```python
@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logging.debug("Database connection checked out from pool")

@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
    logging.debug("Database connection returned to pool")
```

### Database Initialization
```python
def init_db():
    """Initialize database tables with connection retry logic."""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            logging.info("Database tables created successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Database initialization attempt {attempt + 1} failed")
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to initialize database after {max_retries} attempts")
                raise
```

## Performance Optimizations

### 1. Connection Pooling
- Maintains a pool of reusable connections
- Reduces connection overhead
- Handles connection lifecycle

### 2. Health Checks
- Pre-ping feature enabled
- Automatic connection verification
- Failed connection detection

### 3. Connection Recycling
- Connections recycled after 30 minutes
- Prevents stale connections
- Ensures connection reliability

### 4. Error Handling
- Comprehensive error tracking
- Automatic retries
- Detailed error logging

## Query Optimization

### 1. Session Management
```python
async def perform_database_operation():
    db = next(get_db())
    try:
        # Perform operations
        result = db.query(Model).filter(Model.id == id).first()
        return result
    finally:
        db.close()
```

### 2. Bulk Operations
```python
def bulk_insert_items(items: List[Dict]):
    db = next(get_db())
    try:
        db.bulk_insert_mappings(Model, items)
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
```

### 3. Query Optimization
```python
# Efficient querying with specific columns
db.query(Model.id, Model.name).filter(Model.active == True)

# Using joins effectively
db.query(Model).join(RelatedModel).filter(RelatedModel.status == 'active')
```

## Monitoring & Metrics

### Connection Pool Statistics
```python
def get_pool_stats():
    return {
        "pool_size": MAX_CONNECTIONS,
        "active_connections": engine.pool.checkedin()
    }
```

### Query Performance
```python
def monitor_query_time(query_func):
    start_time = time.time()
    result = query_func()
    duration = time.time() - start_time
    logging.info(f"Query execution time: {duration}s")
    return result
```

## Best Practices

### 1. Connection Management
- Always use the connection pool
- Close connections after use
- Handle connection errors

### 2. Query Optimization
- Use specific column selection
- Implement efficient joins
- Avoid N+1 query problems

### 3. Error Handling
- Implement retry logic
- Log database errors
- Handle connection timeouts

### 4. Monitoring
- Track connection pool usage
- Monitor query performance
- Log database operations

## Security Considerations

### 1. Connection Security
- Use SSL/TLS for database connections
- Implement connection timeouts
- Rotate database credentials

### 2. Query Security
- Use parameterized queries
- Implement query timeouts
- Validate input data

### 3. Access Control
- Implement role-based access
- Use connection pooling
- Monitor database access

## Maintenance

### 1. Regular Tasks
- Monitor connection pool usage
- Clean up stale connections
- Update database statistics

### 2. Performance Tuning
- Adjust pool settings based on load
- Optimize query patterns
- Monitor resource usage

### 3. Troubleshooting
- Check connection pool logs
- Monitor query performance
- Track error patterns

## Database Schema

### Request Model
```python
class Request:
    id: int
    user_id: bigint  # Changed from int to bigint to support large Telegram user IDs
    issue: str
    assigned_admin: Optional[bigint]  # Changed from int to bigint to support large Telegram admin IDs
    status: str
    solution: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### Message Model
```python
class Message:
    id: int
    request_id: int
    sender_id: bigint  # Changed from int to bigint to support large Telegram user IDs
    sender_type: str  # 'user' or 'admin'
    message: str
    timestamp: datetime
```

### Log Model
```python
class Log:
    id: int
    timestamp: datetime
    level: str
    message: str
    context: str
```

## Migration Management

### Alembic Usage
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Recent Schema Changes
1. 2025-03-19: Changed user_id, assigned_admin, and sender_id columns to BIGINT type to support large Telegram IDs
   - Affected tables: requests (user_id, assigned_admin), messages (sender_id)
   - Migration file: fix_bigint_columns.py
   - Reason: Support for Telegram user IDs that exceed 32-bit integer range

### Best Practices
1. Regular backups before migrations
2. Test migrations in staging
3. Document changes
4. Version control migrations
5. Maintain rollback plans 