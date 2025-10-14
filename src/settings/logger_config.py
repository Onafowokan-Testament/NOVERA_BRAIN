import sys
from pathlib import Path
from loguru import logger


LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure loguru logger
config = {
    "handlers": [
        # Console handler with colors
        {
            "sink": sys.stdout,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "level": "INFO",
        },
        # File handler for all logs
        {
            "sink": LOGS_DIR / "novera.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            "rotation": "500 MB",  # Rotate when file reaches 500MB
            "retention": "7 days",  # Keep logs for 7 days
            "compression": "zip",   # Compress rotated logs
            "level": "DEBUG",
        },
        # Separate file for errors
        {
            "sink": LOGS_DIR / "errors.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            "rotation": "100 MB",
            "retention": "30 days",
            "compression": "zip",
            "level": "ERROR",
        }
    ]
}

def setup_logger():
    """Initialize logger configuration"""
    # Remove default logger
    logger.remove()
    
    # Add handlers from config
    for handler in config["handlers"]:
        logger.add(**handler)
    
    return logger

# Initialize logger
logger = setup_logger()