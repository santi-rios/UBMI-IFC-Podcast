"""
Logging configuration for the podcast pipeline
"""

import logging
import sys
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "INFO", log_file: str = None) -> None:
    """
    Setup logging configuration using loguru
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file. If None, only logs to console
    """
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file logger if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="1 month"
        )


def get_logger(name: str):
    """Get a logger instance for a specific module"""
    return logger.bind(name=name)
