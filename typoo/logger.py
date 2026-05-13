"""
Logging system for Typoo application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class Logger:
    """Centralized logging configuration."""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def setup(cls, level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
        """
        Setup logging system.
        
        Args:
            level: Logging level (default: INFO)
            log_file: Optional file path for logging
            
        Returns:
            Configured logger instance
        """
        if cls._instance is not None:
            return cls._instance
        
        logger = logging.getLogger("typoo")
        logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (if log file provided)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._instance = logger
        return logger
    
    @classmethod
    def get(cls) -> logging.Logger:
        """Get logger instance."""
        if cls._instance is None:
            cls.setup()
        return cls._instance
