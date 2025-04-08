"""
XCA-Bot Logger Module

This module sets up structured logging for the entire application using Loguru.
It provides consistent logging format, rotation, and severity levels.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configure main application logger
def setup_logger():
    """Configure the application logger with console and file handlers."""
    # Remove default handlers
    logger.remove()
    
    # Add console handler for INFO and above
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    
    # Add file handler for all logs
    logger.add(
        logs_dir / "xca-bot.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
    )
    
    # Add file handler for errors only
    logger.add(
        logs_dir / "xca-bot-errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="1 month",
        compression="zip",
    )
    
    logger.debug("Logger initialized")
    return logger

# Development log to track project progress
def dev_log(message, status="INFO"):
    """Log development progress with special formatting.
    
    Args:
        message: The development log message
        status: Status indicator (INFO, DONE, TODO, NOTE)
    """
    status_colors = {
        "INFO": "blue",
        "DONE": "green",
        "TODO": "yellow",
        "NOTE": "magenta",
    }
    color = status_colors.get(status, "white")
    
    logger.opt(colors=True).info(
        f"<{color}>[DEV-{status}]</{color}> {message}"
    )

# Initialize logger
app_logger = setup_logger()

# Export logger and developer logging function
__all__ = ["logger", "dev_log"] 