"""
Correlation ID propagation for request tracking.

Provides correlation ID generation and propagation through
all layers of the application.
"""

import uuid
import asyncio
import threading
from typing import Optional, Dict, Any, Callable, TypeVar, Union
from contextvars import ContextVar
from functools import wraps
from datetime import datetime

# Context variables for correlation
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_metadata_var: ContextVar[Dict[str, Any]] = ContextVar('request_metadata', default={})


class CorrelationContext:
    """
    Manages correlation IDs and request metadata.
    
    Features:
    - Automatic ID generation
    - Context propagation
    - Metadata tracking
    - Cross-service correlation
    """
    
    def __init__(self):
        """Initialize correlation context."""
        self._active_correlations: Dict[str, Dict[str, Any]] = {}
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return f"corr_{uuid.uuid4().hex[:16]}"
    
    def set_correlation_id(
        self,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Set correlation ID in context."""
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
        
        # Set in context
        correlation_id_var.set(correlation_id)
        
        # Set metadata
        if metadata:
            request_metadata_var.set(metadata)
            
        # Track active correlation
        self._active_correlations[correlation_id] = {
            'created_at': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        return correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from context."""
        return correlation_id_var.get()
    
    def get_request_metadata(self) -> Dict[str, Any]:
        """Get current request metadata."""
        return request_metadata_var.get()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to current request context."""
        metadata = request_metadata_var.get().copy()
        metadata[key] = value
        request_metadata_var.set(metadata)
    
    def clear_correlation(self) -> None:
        """Clear current correlation context."""
        correlation_id = correlation_id_var.get()
        if correlation_id:
            self._active_correlations.pop(correlation_id, None)
        
        correlation_id_var.set(None)
        request_metadata_var.set({})
    
    def get_active_correlations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active correlations."""
        return self._active_correlations.copy()
    
    def cleanup_old_correlations(self, max_age_hours: int = 1) -> int:
        """Clean up old correlations."""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_ids = [
            corr_id for corr_id, data in self._active_correlations.items()
            if data['created_at'] < cutoff
        ]
        
        for corr_id in old_ids:
            self._active_correlations.pop(corr_id, None)
        
        return len(old_ids)


# Global correlation context
_correlation_context = CorrelationContext()


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _correlation_context.get_correlation_id()


def set_correlation_id(
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Set correlation ID and return it."""
    return _correlation_context.set_correlation_id(correlation_id, metadata)


def add_correlation_metadata(key: str, value: Any) -> None:
    """Add metadata to current correlation context."""
    _correlation_context.add_metadata(key, value)


def clear_correlation() -> None:
    """Clear current correlation context."""
    _correlation_context.clear_correlation()


# Decorators for correlation

T = TypeVar('T', bound=Callable[..., Any])


def with_correlation(
    generate_new: bool = True,
    propagate: bool = True
) -> Callable[[T], T]:
    """
    Decorator to ensure correlation ID exists.
    
    Args:
        generate_new: Whether to generate new ID if none exists
        propagate: Whether to propagate existing ID
    """
    def decorator(func: T) -> T:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                existing_id = get_correlation_id()
                
                if not existing_id and generate_new:
                    correlation_id = set_correlation_id()
                    try:
                        return await func(*args, **kwargs)
                    finally:
                        if not propagate:
                            clear_correlation()
                else:
                    return await func(*args, **kwargs)
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                existing_id = get_correlation_id()
                
                if not existing_id and generate_new:
                    correlation_id = set_correlation_id()
                    try:
                        return func(*args, **kwargs)
                    finally:
                        if not propagate:
                            clear_correlation()
                else:
                    return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator


def propagate_correlation_to_thread(
    target: Callable,
    *args,
    **kwargs
) -> threading.Thread:
    """
    Create thread that propagates correlation context.
    
    Args:
        target: Thread target function
        *args: Positional arguments for target
        **kwargs: Keyword arguments for target
    """
    # Capture current context
    correlation_id = get_correlation_id()
    metadata = _correlation_context.get_request_metadata()
    
    def wrapped_target(*args, **kwargs):
        # Restore context in new thread
        if correlation_id:
            set_correlation_id(correlation_id, metadata)
        
        try:
            return target(*args, **kwargs)
        finally:
            clear_correlation()
    
    thread = threading.Thread(
        target=wrapped_target,
        args=args,
        kwargs=kwargs
    )
    
    return thread


async def propagate_correlation_to_task(
    coro: Any,
    correlation_id: Optional[str] = None
) -> Any:
    """
    Run coroutine with correlation context.
    
    Args:
        coro: Coroutine to run
        correlation_id: Optional correlation ID to use
    """
    if correlation_id:
        set_correlation_id(correlation_id)
    elif not get_correlation_id():
        set_correlation_id()
    
    try:
        return await coro
    finally:
        # Context vars are automatically propagated in asyncio
        pass


class CorrelationMiddleware:
    """
    Middleware for web frameworks to handle correlation IDs.
    
    Can be adapted for FastAPI, Flask, etc.
    """
    
    def __init__(
        self,
        header_name: str = "X-Correlation-ID",
        generate_if_missing: bool = True
    ):
        """Initialize middleware."""
        self.header_name = header_name
        self.generate_if_missing = generate_if_missing
    
    async def __call__(self, request: Any, call_next: Callable) -> Any:
        """Process request with correlation ID."""
        # Extract correlation ID from headers
        correlation_id = request.headers.get(self.header_name)
        
        if not correlation_id and self.generate_if_missing:
            correlation_id = _correlation_context.generate_correlation_id()
        
        if correlation_id:
            # Set correlation context
            set_correlation_id(correlation_id, {
                'path': str(request.url.path),
                'method': request.method,
                'client': request.client.host if request.client else None
            })
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add correlation ID to response headers
            if correlation_id:
                response.headers[self.header_name] = correlation_id
            
            return response
            
        finally:
            # Clear correlation context
            clear_correlation()


def inject_correlation_header(
    headers: Dict[str, str],
    correlation_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Inject correlation ID into headers.
    
    Args:
        headers: Headers dictionary to update
        correlation_id: Optional correlation ID (uses current if not provided)
    
    Returns:
        Updated headers dictionary
    """
    if correlation_id is None:
        correlation_id = get_correlation_id()
    
    if correlation_id:
        headers['X-Correlation-ID'] = correlation_id
    
    return headers


def extract_correlation_header(
    headers: Dict[str, str],
    header_name: str = "X-Correlation-ID"
) -> Optional[str]:
    """
    Extract correlation ID from headers.
    
    Args:
        headers: Headers dictionary
        header_name: Name of correlation header
    
    Returns:
        Correlation ID if found
    """
    return headers.get(header_name)


class CorrelatedLogger:
    """
    Logger wrapper that includes correlation ID.
    """
    
    def __init__(self, logger: Any):
        """Initialize correlated logger."""
        self.logger = logger
    
    def _add_correlation(self, message: str, extra: Optional[Dict] = None) -> tuple:
        """Add correlation ID to log message."""
        correlation_id = get_correlation_id()
        
        if correlation_id:
            if extra is None:
                extra = {}
            extra['correlation_id'] = correlation_id
            
            # Prepend correlation ID to message
            message = f"[{correlation_id}] {message}"
        
        return message, extra
    
    def debug(self, message: str, *args, extra: Optional[Dict] = None, **kwargs):
        """Log debug message with correlation."""
        message, extra = self._add_correlation(message, extra)
        self.logger.debug(message, *args, extra=extra, **kwargs)
    
    def info(self, message: str, *args, extra: Optional[Dict] = None, **kwargs):
        """Log info message with correlation."""
        message, extra = self._add_correlation(message, extra)
        self.logger.info(message, *args, extra=extra, **kwargs)
    
    def warning(self, message: str, *args, extra: Optional[Dict] = None, **kwargs):
        """Log warning message with correlation."""
        message, extra = self._add_correlation(message, extra)
        self.logger.warning(message, *args, extra=extra, **kwargs)
    
    def error(self, message: str, *args, extra: Optional[Dict] = None, **kwargs):
        """Log error message with correlation."""
        message, extra = self._add_correlation(message, extra)
        self.logger.error(message, *args, extra=extra, **kwargs)
    
    def critical(self, message: str, *args, extra: Optional[Dict] = None, **kwargs):
        """Log critical message with correlation."""
        message, extra = self._add_correlation(message, extra)
        self.logger.critical(message, *args, extra=extra, **kwargs)