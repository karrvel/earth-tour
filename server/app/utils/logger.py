import os
import sys
from loguru import logger

# Configure Loguru
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Remove default handler
logger.remove()

# Add stdout handler with custom format
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Add file handler for error logs
logger.add(
    "logs/error.log",
    level="ERROR",
    rotation="10 MB",
    retention="1 week",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Create a function to get the logger
def get_logger(name):
    """
    Return a logger instance with the specified name.
    
    Args:
        name (str): The name of the logger, typically the module name
        
    Returns:
        logger: A configured logger instance
    """
    return logger.bind(name=name)
