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
            
            # Format the message safely
            try:
                message = record.getMessage()
            except Exception as e:
                message = f"Error formatting message: {str(e)}"
            
            # Create context without circular references
            context = {
                'name': record.name,
                'levelno': record.levelno,
                'pathname': record.pathname,
                'lineno': record.lineno,
                'exc_info': record.exc_info,
                'func': record.funcName
            }
            
            log_entry = Log(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                message=message,
                context=str(context)
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            # If we can't log to the database, at least try to print the error
            print(f"Error in DatabaseLogHandler: {e}")
            self.handleError(record) 