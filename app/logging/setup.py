import logging
from app.config import LOG_LEVEL, LOG_FORMAT
from app.logging.handlers import DatabaseLogHandler

def setup_logging():
    """Set up logging with console and database handlers."""
    try:
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Set up console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Database handler
        db_handler = DatabaseLogHandler()
        db_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL))
        root_logger.addHandler(console_handler)
        root_logger.addHandler(db_handler)
        
        # Log startup
        logging.info('='*80)
        logging.info('Bot started')
        logging.info('='*80)
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Set up basic console logging as fallback
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT
        )
        logging.warning("Falling back to basic console logging") 