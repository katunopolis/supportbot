import logging
from app.config import LOG_LEVEL, LOG_FORMAT
from app.logging.handlers import DatabaseLogHandler

class LogFilter(logging.Filter):
    """Filter out noisy debug messages."""
    def filter(self, record):
        try:
            # Filter out httpcore debug messages
            if record.name.startswith('httpcore'):
                return False
                
            # Filter out httpx debug messages unless they're actual requests
            if record.name == 'httpx':
                msg = record.getMessage()
                if not any(s in msg for s in ['HTTP Request:', 'HTTP Response']):
                    return False
                    
            # Filter out telegram debug messages unless they're important
            if record.name == 'telegram.Bot':
                msg = record.getMessage()
                if any(s in msg for s in ['Entering:', 'Exiting:', 'True']):
                    return False
                    
            return True
            
        except Exception as e:
            # If there's any error in filtering, let the message through
            logging.error(f"Error in LogFilter: {e}")
            return True

def setup_logging():
    """Set up logging with console and database handlers."""
    try:
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Set up console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(LogFilter())
        
        # Database handler
        db_handler = DatabaseLogHandler()
        db_handler.setFormatter(formatter)
        db_handler.addFilter(LogFilter())
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Add our handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(db_handler)
        
        # Configure specific loggers
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.INFO)
        logging.getLogger('telegram').setLevel(logging.INFO)
        
        # Log startup with a cleaner format
        logging.info('Bot Service Started')
        logging.info('Initializing components...')
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Set up basic console logging as fallback
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT
        )
        logging.warning("Falling back to basic console logging")