# src/utils/logfire_config.py
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def logfire_trace(name: str = None):
    """
    Simple trace decorator for logging function calls
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            trace_name = name or func.__name__
            logger.info(f"🔍 {trace_name} started")
            try:
                result = await func(*args, **kwargs)
                logger.info(f"✅ {trace_name} completed")
                return result
            except Exception as e:
                logger.error(f"❌ {trace_name} failed: {e}")
                raise
        return wrapper
    return decorator

# Create a mock client for compatibility
class LogfireClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)

logfire = LogfireClient()