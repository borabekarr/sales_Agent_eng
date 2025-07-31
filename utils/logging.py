import logging
import sys
from typing import Dict, Any
import structlog
from pythonjsonlogger import jsonlogger


def setup_logging():
    """Setup structured logging configuration"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities"""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, **kwargs) 