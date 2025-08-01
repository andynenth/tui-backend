# backend/api/services/log_buffer.py

import logging
import json
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(str, Enum):
    """Log levels for filtering"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger: str
    message: str
    module: str
    funcName: str
    lineno: int
    thread: str
    extra: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class InMemoryLogBuffer:
    """
    Thread-safe in-memory log buffer that captures logs from multiple sources.
    Designed for debugging and monitoring with minimal performance impact.
    """
    
    def __init__(self, max_size: int = 1000, retention_hours: int = 24):
        """
        Initialize the log buffer.
        
        Args:
            max_size: Maximum number of log entries to keep
            retention_hours: How many hours to retain logs
        """
        self.max_size = max_size
        self.retention_hours = retention_hours
        self._lock = threading.RLock()
        self._buffer: deque = deque(maxlen=max_size)
        self._logger = logging.getLogger(__name__)
        
    def add_log(self, record: logging.LogRecord) -> None:
        """
        Add a log record to the buffer.
        
        Args:
            record: The logging record to add
        """
        try:
            # Extract extra data from the record
            extra = {}
            for key, value in record.__dict__.items():
                if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'message', 'exc_info', 'exc_text', 'stack_info'}:
                    try:
                        # Try to serialize the value to ensure it's JSON-safe
                        json.dumps(value)
                        extra[key] = value
                    except (TypeError, ValueError):
                        extra[key] = str(value)
            
            entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                level=record.levelname,
                logger=record.name,
                message=record.getMessage(),
                module=record.module,
                funcName=record.funcName,
                lineno=record.lineno,
                thread=record.threadName or f"Thread-{record.thread}",
                extra=extra if extra else None
            )
            
            with self._lock:
                self._buffer.append(entry)
                
        except Exception as e:
            # Avoid infinite recursion by not logging errors here
            print(f"Error adding log to buffer: {e}")
    
    def get_logs(
        self, 
        limit: Optional[int] = None, 
        level: Optional[LogLevel] = None,
        logger_filter: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs from the buffer with optional filtering.
        
        Args:
            limit: Maximum number of logs to return
            level: Minimum log level to include
            logger_filter: Filter by logger name (substring match)
            since: Only return logs after this timestamp
            
        Returns:
            List of log entries as dictionaries
        """
        with self._lock:
            logs = list(self._buffer)
        
        # Apply filters
        filtered_logs = []
        level_priority = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}
        min_level = level_priority.get(level.value if level else 'DEBUG', 10)
        
        for log_entry in logs:
            # Level filter
            if level_priority.get(log_entry.level, 0) < min_level:
                continue
                
            # Logger filter
            if logger_filter and logger_filter.lower() not in log_entry.logger.lower():
                continue
                
            # Time filter
            if since:
                log_time = datetime.fromisoformat(log_entry.timestamp.replace('Z', '+00:00'))
                if log_time < since:
                    continue
            
            filtered_logs.append(log_entry.to_dict())
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit
        if limit:
            filtered_logs = filtered_logs[:limit]
            
        return filtered_logs
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics.
        
        Returns:
            Dictionary with buffer statistics
        """
        with self._lock:
            logs = list(self._buffer)
        
        if not logs:
            return {
                'total_logs': 0,
                'buffer_size': self.max_size,
                'buffer_usage': 0.0,
                'retention_hours': self.retention_hours,
                'level_counts': {},
                'logger_counts': {},
                'oldest_log': None,
                'newest_log': None
            }
        
        # Count by level
        level_counts = {}
        logger_counts = {}
        
        for log_entry in logs:
            level_counts[log_entry.level] = level_counts.get(log_entry.level, 0) + 1
            logger_counts[log_entry.logger] = logger_counts.get(log_entry.logger, 0) + 1
        
        return {
            'total_logs': len(logs),
            'buffer_size': self.max_size,
            'buffer_usage': len(logs) / self.max_size * 100,
            'retention_hours': self.retention_hours,
            'level_counts': level_counts,
            'logger_counts': dict(sorted(logger_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'oldest_log': logs[0].timestamp if logs else None,
            'newest_log': logs[-1].timestamp if logs else None
        }
    
    def clear(self) -> int:
        """
        Clear all logs from the buffer.
        
        Returns:
            Number of logs cleared
        """
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            return count
    
    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search logs by message content.
        
        Args:
            query: Search query (case-insensitive)
            limit: Maximum results to return
            
        Returns:
            List of matching log entries
        """
        query_lower = query.lower()
        results = []
        
        with self._lock:
            for log_entry in reversed(self._buffer):  # Search newest first
                if (query_lower in log_entry.message.lower() or 
                    query_lower in log_entry.logger.lower() or
                    query_lower in log_entry.funcName.lower()):
                    results.append(log_entry.to_dict())
                    if len(results) >= limit:
                        break
        
        return results


class LogBufferHandler(logging.Handler):
    """
    Custom logging handler that feeds logs into the InMemoryLogBuffer.
    """
    
    def __init__(self, log_buffer: InMemoryLogBuffer):
        super().__init__()
        self.log_buffer = log_buffer
        
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the buffer.
        
        Args:
            record: The log record to emit
        """
        self.log_buffer.add_log(record)


# Global log buffer instance
_log_buffer = InMemoryLogBuffer(max_size=2000, retention_hours=24)


def get_log_buffer() -> InMemoryLogBuffer:
    """Get the global log buffer instance."""
    return _log_buffer


def setup_log_capture():
    """
    Set up log capture for the entire application.
    This should be called once during application startup.
    """
    log_buffer = get_log_buffer()
    
    # Create handler
    handler = LogBufferHandler(log_buffer)
    handler.setLevel(logging.DEBUG)
    
    # Add to root logger to capture all logs
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Also add to specific loggers we care about
    important_loggers = [
        'api',
        'websocket',
        'game',
        'room',
        'use_case',
        'application',
        'engine',
        'uvicorn.access',
        'uvicorn.error'
    ]
    
    for logger_name in important_loggers:
        logger = logging.getLogger(logger_name)
        if handler not in logger.handlers:
            logger.addHandler(handler)
    
    logging.getLogger(__name__).info("Log capture initialized successfully")