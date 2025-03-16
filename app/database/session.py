import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.database.models import Base

# Load environment variables
load_dotenv()

# Get PostgreSQL URL from Railway environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable found")

# Create SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logging.info("Database engine created successfully")
except Exception as e:
    logging.error(f"Error creating database engine: {e}")
    raise

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise 