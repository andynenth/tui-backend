# backend/api/services/log_buffer.py

import logging
import json
import time
from collections import deque
from threading import Lock
from typing import Dict, List, Optional, Any
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration for filtering"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class InMemoryLogBuffer:
    """Thread-safe circular buffer for storing log entries"""
    
    def __init__(self, max_size: int = 2000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = Lock()
    
    def add_entry(self, entry: Dict[str, Any]):
        """Add a log entry to the buffer"""
        with self.lock:
            self.buffer.append(entry)
    
    def get_entries(
        self,
        limit: Optional[int] = None,
        level: Optional[LogLevel] = None,
        logger_filter: Optional[str] = None,
        since_minutes: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered log entries from the buffer"""
        with self.lock:
            entries = list(self.buffer)
        
        # Filter by time
        if since_minutes:
            cutoff_time = time.time() - (since_minutes * 60)
            entries = [e for e in entries if e.get('timestamp', 0) >= cutoff_time]
        
        # Filter by level
        if level:
            entries = [e for e in entries if e.get('level') == level.value]
        
        # Filter by logger name
        if logger_filter:
            entries = [e for e in entries if logger_filter.lower() in e.get('logger', '').lower()]
        
        # Search in message content
        if search:
            search_lower = search.lower()
            entries = [e for e in entries if search_lower in e.get('message', '').lower()]
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Apply limit
        if limit:
            entries = entries[:limit]
        
        return entries
    
    def clear(self):
        """Clear all log entries"""
        with self.lock:
            self.buffer.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        with self.lock:
            total_entries = len(self.buffer)
            if not self.buffer:
                return {
                    'total_entries': 0,
                    'oldest_entry': None,
                    'newest_entry': None,
                    'level_counts': {},
                    'max_size': self.max_size
                }
            
            # Count entries by level
            level_counts = {}
            for entry in self.buffer:
                level = entry.get('level', 'UNKNOWN')
                level_counts[level] = level_counts.get(level, 0) + 1
            
            return {
                'total_entries': total_entries,
                'oldest_entry': self.buffer[0].get('timestamp'),
                'newest_entry': self.buffer[-1].get('timestamp'),
                'level_counts': level_counts,
                'max_size': self.max_size
            }


class LogBufferHandler(logging.Handler):
    """Custom logging handler that captures logs to the buffer"""
    
    def __init__(self, log_buffer: InMemoryLogBuffer):
        super().__init__()
        self.log_buffer = log_buffer
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record to the buffer"""
        try:
            # Create structured log entry
            entry = {
                'timestamp': record.created,
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'thread_name': record.threadName,
            }
            
            # Add exception info if present
            if record.exc_info:
                entry['exception'] = self.format(record)
            
            # Add to buffer
            self.log_buffer.add_entry(entry)
            
        except Exception:
            # Don't let logging errors break the application
            self.handleError(record)


# Global log buffer instance
log_buffer = InMemoryLogBuffer(max_size=2000)
log_buffer_handler = LogBufferHandler(log_buffer)
log_buffer_handler.setLevel(logging.DEBUG)

# JSON formatter for structured logging
formatter = logging.Formatter(
    '{"timestamp": %(created)f, "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
)
log_buffer_handler.setFormatter(formatter)