"""
Centralized Logging Service for Liap Tui Game
Provides structured JSON logging with correlation IDs and context
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading

@dataclass
class LogContext:
    """Context information for structured logging"""
    correlation_id: str
    room_id: Optional[str] = None
    player_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName', 
                          'process', 'stack_info', 'exc_info', 'exc_text', 'context']:
                log_entry[key] = value
                
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

class GameLogger:
    """Centralized logging service with structured output and correlation IDs"""
    
    def __init__(self):
        self._context_storage = threading.local()
        self.setup_loggers()
        
    def setup_loggers(self):
        """Set up specialized loggers with JSON formatting"""
        import os
        from logging.handlers import RotatingFileHandler
        
        # Create formatters
        json_formatter = JsonFormatter()
        
        # Determine if we're in production or development
        log_to_files = os.getenv("LOG_TO_FILES", "false").lower() == "true"
        log_directory = os.getenv("LOG_DIRECTORY", "logs")
        
        # Create log directory if it doesn't exist
        if log_to_files:
            os.makedirs(log_directory, exist_ok=True)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Create handlers list (always include console for now)
        handlers = [console_handler]
        
        # Add file handlers for production
        if log_to_files:
            # Game events log file
            game_file_handler = RotatingFileHandler(
                os.path.join(log_directory, "game_events.log"),
                maxBytes=50*1024*1024,  # 50MB
                backupCount=5
            )
            game_file_handler.setFormatter(json_formatter)
            game_file_handler.setLevel(logging.INFO)
            
            # WebSocket events log file
            websocket_file_handler = RotatingFileHandler(
                os.path.join(log_directory, "websocket.log"),
                maxBytes=50*1024*1024,
                backupCount=5
            )
            websocket_file_handler.setFormatter(json_formatter)
            websocket_file_handler.setLevel(logging.INFO)
            
            # Performance log file
            performance_file_handler = RotatingFileHandler(
                os.path.join(log_directory, "performance.log"),
                maxBytes=50*1024*1024,
                backupCount=5
            )
            performance_file_handler.setFormatter(json_formatter)
            performance_file_handler.setLevel(logging.INFO)
            
            # Security log file
            security_file_handler = RotatingFileHandler(
                os.path.join(log_directory, "security.log"),
                maxBytes=50*1024*1024,
                backupCount=5
            )
            security_file_handler.setFormatter(json_formatter)
            security_file_handler.setLevel(logging.WARNING)
            
            # Error log file
            error_file_handler = RotatingFileHandler(
                os.path.join(log_directory, "errors.log"),
                maxBytes=50*1024*1024,
                backupCount=5
            )
            error_file_handler.setFormatter(json_formatter)
            error_file_handler.setLevel(logging.ERROR)
            
            # Create specialized loggers with both console and file handlers
            self.game_logger = self._create_logger('game', [console_handler, game_file_handler])
            self.websocket_logger = self._create_logger('websocket', [console_handler, websocket_file_handler])
            self.performance_logger = self._create_logger('performance', [console_handler, performance_file_handler])
            self.security_logger = self._create_logger('security', [console_handler, security_file_handler])
            self.error_logger = self._create_logger('error', [console_handler, error_file_handler])
            
            print(f"📁 LOGGING: File logging enabled - logs saved to {log_directory}/")
        else:
            # Development mode - console only
            self.game_logger = self._create_logger('game', [console_handler])
            self.websocket_logger = self._create_logger('websocket', [console_handler])
            self.performance_logger = self._create_logger('performance', [console_handler])
            self.security_logger = self._create_logger('security', [console_handler])
            self.error_logger = self._create_logger('error', [console_handler])
            
            print("📺 LOGGING: Console logging only (set LOG_TO_FILES=true for file logging)")
        
        # Set levels
        self.game_logger.setLevel(logging.INFO)
        self.websocket_logger.setLevel(logging.INFO)
        self.performance_logger.setLevel(logging.INFO)
        self.security_logger.setLevel(logging.WARNING)
        self.error_logger.setLevel(logging.ERROR)
        
    def _create_logger(self, name: str, handlers) -> logging.Logger:
        """Create a logger with the specified handler(s)"""
        from typing import List
        
        logger = logging.getLogger(name)
        logger.handlers.clear()  # Remove existing handlers
        
        # Handle both single handler and list of handlers
        if isinstance(handlers, list):
            for handler in handlers:
                logger.addHandler(handler)
        else:
            logger.addHandler(handlers)
            
        logger.propagate = False
        return logger
    
    @contextmanager
    def log_context(self, **context_kwargs):
        """Context manager for setting log context"""
        old_context = getattr(self._context_storage, 'context', None)
        
        # Generate correlation ID if not provided
        if 'correlation_id' not in context_kwargs:
            context_kwargs['correlation_id'] = str(uuid.uuid4())[:8]
            
        self._context_storage.context = LogContext(**context_kwargs)
        try:
            yield self._context_storage.context
        finally:
            self._context_storage.context = old_context
    
    def _get_context(self) -> Optional[Dict[str, Any]]:
        """Get current log context"""
        context = getattr(self._context_storage, 'context', None)
        return context.to_dict() if context else None
    
    def _log_with_context(self, logger: logging.Logger, level: int, message: str, **extra):
        """Log message with current context"""
        context = self._get_context()
        if context:
            extra['context'] = context
        logger.log(level, message, extra=extra)
    
    # Game-specific logging methods
    def log_game_event(self, event: str, room_id: str = None, player_id: str = None, **extra):
        """Log game-specific events with context"""
        self._log_with_context(
            self.game_logger, 
            logging.INFO, 
            f"Game event: {event}",
            event_type=event,
            room_id=room_id,
            player_id=player_id,
            **extra
        )
    
    def log_phase_change(self, room_id: str, old_phase: str, new_phase: str, **extra):
        """Log phase transitions"""
        self._log_with_context(
            self.game_logger,
            logging.INFO,
            f"Phase transition: {old_phase} -> {new_phase}",
            event_type="phase_change",
            room_id=room_id,
            old_phase=old_phase,
            new_phase=new_phase,
            **extra
        )
    
    def log_player_action(self, room_id: str, player_id: str, action: str, **extra):
        """Log player actions"""
        self._log_with_context(
            self.game_logger,
            logging.INFO,
            f"Player action: {player_id} performed {action}",
            event_type="player_action",
            room_id=room_id,
            player_id=player_id,
            action=action,
            **extra
        )
    
    # WebSocket logging methods
    def log_websocket_event(self, room_id: str, action: str, connection_id: str = None, **extra):
        """Log WebSocket events with connection context"""
        self._log_with_context(
            self.websocket_logger,
            logging.INFO,
            f"WebSocket {action}",
            event_type="websocket",
            room_id=room_id,
            connection_id=connection_id,
            action=action,
            **extra
        )
    
    def log_message_delivery(self, room_id: str, sequence: int, status: str, latency_ms: float = None, **extra):
        """Log message delivery events"""
        self._log_with_context(
            self.websocket_logger,
            logging.INFO,
            f"Message delivery: seq {sequence} {status}",
            event_type="message_delivery",
            room_id=room_id,
            sequence=sequence,
            status=status,
            latency_ms=latency_ms,
            **extra
        )
    
    def log_connection_event(self, room_id: str, event: str, client_info: dict = None, **extra):
        """Log connection events"""
        self._log_with_context(
            self.websocket_logger,
            logging.INFO,
            f"Connection {event}",
            event_type="connection",
            room_id=room_id,
            connection_event=event,
            client_info=client_info,
            **extra
        )
    
    # Performance logging methods
    def log_performance(self, operation: str, duration_ms: float, **extra):
        """Log performance metrics"""
        self._log_with_context(
            self.performance_logger,
            logging.INFO,
            f"Performance: {operation} took {duration_ms:.2f}ms",
            event_type="performance",
            operation=operation,
            duration_ms=duration_ms,
            **extra
        )
    
    def log_slow_operation(self, operation: str, duration_ms: float, threshold_ms: float = 1000, **extra):
        """Log slow operations that exceed threshold"""
        if duration_ms > threshold_ms:
            self._log_with_context(
                self.performance_logger,
                logging.WARNING,
                f"Slow operation: {operation} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)",
                event_type="slow_operation",
                operation=operation,
                duration_ms=duration_ms,
                threshold_ms=threshold_ms,
                **extra
            )
    
    # Security logging methods
    def log_security_event(self, event: str, severity: str = "medium", **extra):
        """Log security-related events"""
        level = logging.WARNING if severity == "medium" else logging.ERROR
        self._log_with_context(
            self.security_logger,
            level,
            f"Security event: {event}",
            event_type="security",
            security_event=event,
            severity=severity,
            **extra
        )
    
    def log_authentication_event(self, player_id: str, event: str, success: bool, **extra):
        """Log authentication events"""
        self._log_with_context(
            self.security_logger,
            logging.INFO,
            f"Authentication: {player_id} {event} ({'success' if success else 'failed'})",
            event_type="authentication",
            player_id=player_id,
            auth_event=event,
            success=success,
            **extra
        )
    
    # Error logging methods
    def log_error(self, error: Exception, context: str = None, **extra):
        """Log errors with full context"""
        self._log_with_context(
            self.error_logger,
            logging.ERROR,
            f"Error in {context}: {str(error)}",
            event_type="error",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            **extra
        )
    
    def log_critical_error(self, error: Exception, context: str = None, **extra):
        """Log critical errors that affect system stability"""
        self._log_with_context(
            self.error_logger,
            logging.CRITICAL,
            f"Critical error in {context}: {str(error)}",
            event_type="critical_error",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            **extra
        )
    
    # Utility methods
    @contextmanager
    def timed_operation(self, operation: str, **context):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.log_performance(operation, duration_ms, **context)
            self.log_slow_operation(operation, duration_ms, **context)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a specific logger by name"""
        loggers = {
            'game': self.game_logger,
            'websocket': self.websocket_logger,
            'performance': self.performance_logger,
            'security': self.security_logger,
            'error': self.error_logger
        }
        return loggers.get(name, self.game_logger)

# Global logger instance
game_logger = GameLogger()

# Convenience functions for easy importing
def log_game_event(event: str, **kwargs):
    """Convenience function for logging game events"""
    game_logger.log_game_event(event, **kwargs)

def log_websocket_event(room_id: str, action: str, **kwargs):
    """Convenience function for logging WebSocket events"""
    game_logger.log_websocket_event(room_id, action, **kwargs)

def log_performance(operation: str, duration_ms: float, **kwargs):
    """Convenience function for logging performance"""
    game_logger.log_performance(operation, duration_ms, **kwargs)

def log_error(error: Exception, context: str = None, **kwargs):
    """Convenience function for logging errors"""
    game_logger.log_error(error, context, **kwargs)

# Export for easy importing
__all__ = [
    'GameLogger', 'LogContext', 'JsonFormatter', 'game_logger',
    'log_game_event', 'log_websocket_event', 'log_performance', 'log_error'
]