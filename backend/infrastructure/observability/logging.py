"""
Structured logging infrastructure with context support.

Provides flexible logging with structured output, contextual information,
and multiple output formats.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Union
from datetime import datetime
from enum import Enum
import json
import sys
import asyncio
from pathlib import Path
from contextlib import contextmanager
from functools import wraps
import traceback
from dataclasses import dataclass, field
import threading
from queue import Queue
import logging


class LogLevel(Enum):
    """Log levels in increasing severity."""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __ge__(self, other):
        return self.value >= other.value

    def __gt__(self, other):
        return self.value > other.value

    def __le__(self, other):
        return self.value <= other.value

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value


class LogFormat(Enum):
    """Supported log output formats."""

    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"
    CONSOLE = "console"


@dataclass
class LogConfig:
    """Configuration for logging system."""

    level: LogLevel = field(default_factory=lambda: LogLevel.INFO)
    format: LogFormat = field(default_factory=lambda: LogFormat.JSON)
    app_name: Optional[str] = None
    output: Optional[str] = None  # stdout, stderr, or file path
    buffer_size: int = 1000
    async_mode: bool = True
    include_stacktrace: bool = True
    context_fields: List[str] = field(default_factory=list)
    filters: List[Callable[[Dict[str, Any]], bool]] = field(default_factory=list)


@dataclass
class LogContext:
    """Contextual information for log entries."""

    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    room_id: Optional[str] = None
    player_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.user_id:
            result["user_id"] = self.user_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.request_id:
            result["request_id"] = self.request_id
        if self.room_id:
            result["room_id"] = self.room_id
        if self.player_id:
            result["player_id"] = self.player_id
        result.update(self.extra)
        return result


# Thread-local storage for log context
_context_storage = threading.local()


class ILogger(ABC):
    """Interface for loggers."""

    @abstractmethod
    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Log a message at the specified level."""
        pass

    @abstractmethod
    def with_context(self, **kwargs: Any) -> "ILogger":
        """Create a child logger with additional context."""
        pass

    def trace(self, message: str, **kwargs: Any) -> None:
        """Log at TRACE level."""
        self.log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log at CRITICAL level."""
        self.log(LogLevel.CRITICAL, message, **kwargs)


class ILoggerFactory(ABC):
    """Interface for creating loggers."""

    @abstractmethod
    def create_logger(self, name: str) -> ILogger:
        """Create a logger with the given name."""
        pass


class StructuredLogger(ILogger):
    """
    Base structured logger implementation.

    Features:
    - Structured output with context
    - Multiple output formats
    - Filtering support
    - Performance optimization
    """

    def __init__(
        self,
        name: str,
        config: LogConfig,
        formatter: Optional[Callable[[Dict[str, Any]], str]] = None,
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            config: Logger configuration
            formatter: Custom formatter function
        """
        self.name = name
        self.config = config
        self.formatter = formatter or self._default_formatter
        self.context = {}
        self._filters = config.filters.copy()

    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Log a structured message."""
        if level < self.config.level:
            return

        # Build log entry
        entry = self._build_entry(level, message, kwargs)

        # Apply filters
        if not self._apply_filters(entry):
            return

        # Format and output
        formatted = self.formatter(entry)
        self._output(formatted)

    def with_context(self, **kwargs: Any) -> "StructuredLogger":
        """Create a child logger with additional context."""
        child = StructuredLogger(self.name, self.config, self.formatter)
        child.context = {**self.context, **kwargs}
        child._filters = self._filters.copy()
        return child

    def _build_entry(
        self, level: LogLevel, message: str, fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a complete log entry."""
        # Get thread-local context
        local_context = getattr(_context_storage, "context", {})

        # Build entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.name,
            "logger": self.name,
            "message": message,
            **self.context,
            **local_context,
            **fields,
        }

        # Add app name if configured
        if self.config.app_name:
            entry["app"] = self.config.app_name

        # Add stack trace for errors
        if level >= LogLevel.ERROR and self.config.include_stacktrace:
            entry["stacktrace"] = traceback.format_exc()

        return entry

    def _apply_filters(self, entry: Dict[str, Any]) -> bool:
        """Apply all filters to the log entry."""
        for filter_func in self._filters:
            if not filter_func(entry):
                return False
        return True

    def _default_formatter(self, entry: Dict[str, Any]) -> str:
        """Default formatter based on configured format."""
        if self.config.format == LogFormat.JSON:
            return json.dumps(entry, default=str)

        elif self.config.format == LogFormat.TEXT:
            return (
                f"{entry['timestamp']} [{entry['level']}] "
                f"{entry['logger']}: {entry['message']}"
            )

        elif self.config.format == LogFormat.STRUCTURED:
            # Key=value format
            items = []
            for key, value in entry.items():
                if isinstance(value, str) and " " in value:
                    items.append(f'{key}="{value}"')
                else:
                    items.append(f"{key}={value}")
            return " ".join(items)

        else:  # CONSOLE
            level_colors = {
                "TRACE": "\033[37m",  # White
                "DEBUG": "\033[36m",  # Cyan
                "INFO": "\033[32m",  # Green
                "WARNING": "\033[33m",  # Yellow
                "ERROR": "\033[31m",  # Red
                "CRITICAL": "\033[35m",  # Magenta
            }
            reset = "\033[0m"
            color = level_colors.get(entry["level"], "")

            return (
                f"{color}{entry['timestamp']} [{entry['level']}]{reset} "
                f"{entry['logger']}: {entry['message']}"
            )

    def _output(self, formatted: str) -> None:
        """Output the formatted log entry."""
        if self.config.output is None or self.config.output == "stdout":
            print(formatted, file=sys.stdout, flush=True)
        elif self.config.output == "stderr":
            print(formatted, file=sys.stderr, flush=True)
        else:
            # File output
            with open(self.config.output, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")


class AsyncLogger(StructuredLogger):
    """
    Asynchronous logger for high-performance logging.

    Features:
    - Non-blocking log writes
    - Buffering for batch writes
    - Graceful shutdown
    """

    def __init__(
        self,
        name: str,
        config: LogConfig,
        formatter: Optional[Callable[[Dict[str, Any]], str]] = None,
    ):
        """Initialize async logger."""
        super().__init__(name, config, formatter)
        self._queue: Queue = Queue(maxsize=config.buffer_size)
        self._running = False
        self._worker_thread = None

        if config.async_mode:
            self._start_worker()

    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Queue log message for async processing."""
        if level < self.config.level:
            return

        entry = self._build_entry(level, message, kwargs)

        if not self._apply_filters(entry):
            return

        if self.config.async_mode and self._running:
            try:
                self._queue.put_nowait(entry)
            except:
                # Queue full, fall back to sync
                formatted = self.formatter(entry)
                self._output(formatted)
        else:
            # Sync mode
            formatted = self.formatter(entry)
            self._output(formatted)

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Background worker for processing log entries."""
        batch = []

        while self._running:
            try:
                # Get entries with timeout for periodic flush
                entry = self._queue.get(timeout=0.1)
                batch.append(entry)

                # Batch write
                if len(batch) >= 10:
                    self._flush_batch(batch)
                    batch = []

            except:
                # Timeout - flush any pending
                if batch:
                    self._flush_batch(batch)
                    batch = []

        # Final flush
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Flush a batch of log entries."""
        for entry in batch:
            formatted = self.formatter(entry)
            self._output(formatted)

    def shutdown(self) -> None:
        """Gracefully shutdown the logger."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)


# Global logger factory
_logger_factory: Optional[ILoggerFactory] = None
_loggers: Dict[str, ILogger] = {}


class DefaultLoggerFactory(ILoggerFactory):
    """Default logger factory implementation."""

    def __init__(self, config: LogConfig):
        """Initialize factory with configuration."""
        self.config = config

    def create_logger(self, name: str) -> ILogger:
        """Create a logger instance."""
        if self.config.async_mode:
            return AsyncLogger(name, self.config)
        else:
            return StructuredLogger(name, self.config)


def configure_logging(config: LogConfig) -> None:
    """
    Configure the global logging system.

    Args:
        config: Logging configuration
    """
    global _logger_factory
    _logger_factory = DefaultLoggerFactory(config)


def get_logger(name: str) -> ILogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if name not in _loggers:
        if _logger_factory is None:
            # Auto-configure with defaults
            configure_logging(LogConfig())

        _loggers[name] = _logger_factory.create_logger(name)

    return _loggers[name]


@contextmanager
def log_context(**kwargs: Any):
    """
    Context manager for adding contextual information to logs.

    Example:
        with log_context(user_id="123", request_id="abc"):
            logger.info("Processing request")
    """
    # Get existing context
    old_context = getattr(_context_storage, "context", {})

    # Merge with new context
    new_context = {**old_context, **kwargs}
    _context_storage.context = new_context

    try:
        yield
    finally:
        # Restore old context
        _context_storage.context = old_context


def log_performance(
    logger: ILogger, operation: str, level: LogLevel = LogLevel.INFO
) -> Callable:
    """
    Decorator for logging function performance.

    Args:
        logger: Logger to use
        operation: Operation name
        level: Log level

    Example:
        @log_performance(logger, "database_query")
        async def query_users():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = datetime.utcnow()

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start).total_seconds()

                logger.log(
                    level,
                    f"{operation} completed",
                    duration_seconds=duration,
                    status="success",
                )

                return result

            except Exception as e:
                duration = (datetime.utcnow() - start).total_seconds()

                logger.error(
                    f"{operation} failed",
                    duration_seconds=duration,
                    status="error",
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = datetime.utcnow()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start).total_seconds()

                logger.log(
                    level,
                    f"{operation} completed",
                    duration_seconds=duration,
                    status="success",
                )

                return result

            except Exception as e:
                duration = (datetime.utcnow() - start).total_seconds()

                logger.error(
                    f"{operation} failed",
                    duration_seconds=duration,
                    status="error",
                    error=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience loggers for specific formats


class ConsoleLogger(StructuredLogger):
    """Logger optimized for console output."""

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        """Initialize console logger."""
        config = LogConfig(level=level, format=LogFormat.CONSOLE, async_mode=False)
        super().__init__(name, config)


class JsonLogger(StructuredLogger):
    """Logger that outputs JSON."""

    def __init__(
        self, name: str, level: LogLevel = LogLevel.INFO, output: Optional[str] = None
    ):
        """Initialize JSON logger."""
        config = LogConfig(
            level=level, format=LogFormat.JSON, output=output, async_mode=True
        )
        super().__init__(name, config)


class FileLogger(AsyncLogger):
    """Logger that writes to files with rotation support."""

    def __init__(
        self,
        name: str,
        file_path: Union[str, Path],
        level: LogLevel = LogLevel.INFO,
        max_size_mb: int = 100,
        max_files: int = 5,
    ):
        """Initialize file logger with rotation."""
        config = LogConfig(
            level=level, format=LogFormat.JSON, output=str(file_path), async_mode=True
        )
        super().__init__(name, config)

        self.file_path = Path(file_path)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files

    def _output(self, formatted: str) -> None:
        """Output with file rotation."""
        # Check file size
        if (
            self.file_path.exists()
            and self.file_path.stat().st_size > self.max_size_bytes
        ):
            self._rotate_files()

        # Write to file
        super()._output(formatted)

    def _rotate_files(self) -> None:
        """Rotate log files."""
        # Rename existing files
        for i in range(self.max_files - 1, 0, -1):
            old_path = self.file_path.with_suffix(f".{i}")
            new_path = self.file_path.with_suffix(f".{i + 1}")

            if old_path.exists():
                if new_path.exists():
                    new_path.unlink()
                old_path.rename(new_path)

        # Rename current file
        if self.file_path.exists():
            self.file_path.rename(self.file_path.with_suffix(".1"))
