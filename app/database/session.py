import os
import logging
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
from app.database.models import Base

# Load environment variables
load_dotenv()

# Get PostgreSQL URL from Railway environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable found")

# Database connection pool settings
POOL_SIZE = 20  # Maximum number of persistent connections
MAX_OVERFLOW = 10  # Maximum number of connections that can be created beyond pool_size
POOL_TIMEOUT = 30  # Timeout for getting a connection from the pool
POOL_RECYCLE = 1800  # Recycle connections after 30 minutes

# Create SQLAlchemy engine with optimized settings
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Enable connection health checks
        echo_pool=True  # Log pool events for monitoring
    )
    
    # Configure connection pool event listeners
    @event.listens_for(engine, 'checkout')
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logging.debug("Database connection checked out from pool")

    @event.listens_for(engine, 'checkin')
    def receive_checkin(dbapi_connection, connection_record):
        logging.debug("Database connection returned to pool")

    # Create session factory with optimized settings
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False  # Prevent unnecessary database queries
    )
    
    logging.info("Database engine and connection pool created successfully")
except Exception as e:
    logging.error(f"Error creating database engine: {e}")
    raise

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
                logging.warning(f"Database initialization attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                raise 