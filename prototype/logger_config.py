"""Logging configuration for the prototype."""
import logging
import os
import sys
from pathlib import Path


def setup_logging(log_level: str = None, log_file: str = None):
    """Set up logging configuration."""
    # Get log level from environment or use default
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - default to logs directory if not specified
    if log_file is None:
        # Default log file location
        log_file = os.getenv("LOG_FILE", "logs/prototype.log")
    
    # Always write to file for debugging
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use rotating file handler to prevent huge log files
    try:
        from logging.handlers import RotatingFileHandler
        # Max 10MB per file, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
    except ImportError:
        # Fallback to regular FileHandler if RotatingFileHandler not available
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
    
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Log that file logging is enabled
    root_logger.info(f"Logging to file: {log_path.absolute()}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)

