import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.database.models import Log

class DatabaseLogHandler(logging.Handler):
    """Custom logging handler that stores logs in the database."""
    
    def emit(self, record):
        try:
            engine = create_engine(DATABASE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()
            
            log_entry = Log(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                message=record.getMessage(),
                context=str(record.__dict__)
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception:
            self.handleError(record) 