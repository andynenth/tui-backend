"""
Base middleware infrastructure for cross-cutting concerns.

Provides a flexible middleware pipeline for request/response processing.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, List, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
from contextlib import contextmanager
import uuid


logger = logging.getLogger(__name__)


# Type variables
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")
TContext = TypeVar("TContext")


@dataclass
class MiddlewareContext:
    """Context passed through middleware pipeline."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to context."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from context."""
        return self.metadata.get(key, default)

    def add_error(self, error: Exception) -> None:
        """Add error to context."""
        self.errors.append(error)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()


class IMiddleware(ABC, Generic[TRequest, TResponse]):
    """
    Interface for middleware components.

    Middleware can process requests before and after
    the main handler execution.
    """

    @abstractmethod
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse],
    ) -> TResponse:
        """
        Process request through middleware.

        Args:
            request: The request being processed
            context: Middleware context
            next_handler: Next handler in pipeline

        Returns:
            Response from pipeline
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}()"


class MiddlewarePipeline(Generic[TRequest, TResponse]):
    """
    Pipeline for executing middleware in sequence.

    Middleware is executed in order for requests and
    reverse order for responses (onion architecture).
    """

    def __init__(self, handler: Callable[[TRequest, MiddlewareContext], TResponse]):
        """
        Initialize pipeline with final handler.

        Args:
            handler: Final request handler
        """
        self._handler = handler
        self._middleware: List[IMiddleware[TRequest, TResponse]] = []
        self._is_async = asyncio.iscoroutinefunction(handler)

    def add(self, middleware: IMiddleware[TRequest, TResponse]) -> "MiddlewarePipeline":
        """
        Add middleware to pipeline.

        Args:
            middleware: Middleware to add

        Returns:
            Self for chaining
        """
        self._middleware.append(middleware)
        return self

    def add_multiple(
        self, *middleware: IMiddleware[TRequest, TResponse]
    ) -> "MiddlewarePipeline":
        """
        Add multiple middleware to pipeline.

        Args:
            *middleware: Middleware components to add

        Returns:
            Self for chaining
        """
        self._middleware.extend(middleware)
        return self

    async def execute_async(
        self, request: TRequest, context: Optional[MiddlewareContext] = None
    ) -> TResponse:
        """
        Execute pipeline asynchronously.

        Args:
            request: Request to process
            context: Optional context (created if not provided)

        Returns:
            Response from pipeline
        """
        if context is None:
            context = MiddlewareContext()

        # Build the pipeline from inside out
        handler = self._handler

        # Wrap handler in middleware (reverse order)
        for middleware in reversed(self._middleware):
            handler = self._wrap_handler(middleware, handler)

        # Execute pipeline
        if self._is_async:
            return await handler(request, context)
        else:
            # Run sync handler in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, handler, request, context)

    def execute(
        self, request: TRequest, context: Optional[MiddlewareContext] = None
    ) -> TResponse:
        """
        Execute pipeline synchronously.

        Args:
            request: Request to process
            context: Optional context (created if not provided)

        Returns:
            Response from pipeline
        """
        if self._is_async:
            raise RuntimeError("Cannot execute async pipeline synchronously")

        if context is None:
            context = MiddlewareContext()

        # Build the pipeline
        handler = self._handler

        # Wrap handler in middleware (reverse order)
        for middleware in reversed(self._middleware):
            handler = self._wrap_handler_sync(middleware, handler)

        # Execute pipeline
        return handler(request, context)

    def _wrap_handler(
        self, middleware: IMiddleware[TRequest, TResponse], next_handler: Callable
    ) -> Callable:
        """Wrap handler with middleware for async execution."""

        async def wrapped(request: TRequest, context: MiddlewareContext) -> TResponse:
            return await middleware.process(request, context, next_handler)

        return wrapped

    def _wrap_handler_sync(
        self, middleware: IMiddleware[TRequest, TResponse], next_handler: Callable
    ) -> Callable:
        """Wrap handler with middleware for sync execution."""

        def wrapped(request: TRequest, context: MiddlewareContext) -> TResponse:
            # Convert sync middleware to async for consistency
            async def async_next(req: TRequest, ctx: MiddlewareContext) -> TResponse:
                return next_handler(req, ctx)

            # Run async middleware in new event loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    middleware.process(request, context, async_next)
                )
            finally:
                loop.close()

        return wrapped

    @property
    def middleware_count(self) -> int:
        """Get number of middleware in pipeline."""
        return len(self._middleware)

    def get_middleware(self) -> List[IMiddleware[TRequest, TResponse]]:
        """Get list of middleware in pipeline."""
        return self._middleware.copy()


# Common middleware base classes


class LoggingMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Base middleware for logging requests and responses.

    Override log methods to customize logging.
    """

    def __init__(self, logger_name: Optional[str] = None):
        """Initialize logging middleware."""
        self.logger = logging.getLogger(logger_name or __name__)

    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse],
    ) -> TResponse:
        """Process request with logging."""
        # Log request
        self.log_request(request, context)

        try:
            # Process request
            response = await next_handler(request, context)

            # Log response
            self.log_response(response, context)

            return response

        except Exception as e:
            # Log error
            self.log_error(e, context)
            raise

    def log_request(self, request: TRequest, context: MiddlewareContext) -> None:
        """Log incoming request."""
        self.logger.info(
            f"Request {context.request_id}: {request}",
            extra={"correlation_id": context.correlation_id},
        )

    def log_response(self, response: TResponse, context: MiddlewareContext) -> None:
        """Log outgoing response."""
        self.logger.info(
            f"Response {context.request_id}: {response} "
            f"(took {context.elapsed_time:.3f}s)",
            extra={"correlation_id": context.correlation_id},
        )

    def log_error(self, error: Exception, context: MiddlewareContext) -> None:
        """Log error."""
        self.logger.error(
            f"Error in request {context.request_id}: {error}",
            extra={"correlation_id": context.correlation_id},
            exc_info=True,
        )


class TimingMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for timing request processing.

    Adds timing information to context metadata.
    """

    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse],
    ) -> TResponse:
        """Process request with timing."""
        start_time = datetime.utcnow()

        try:
            response = await next_handler(request, context)

            # Add timing metadata
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            context.add_metadata("processing_time", elapsed)
            context.add_metadata("processing_time_ms", elapsed * 1000)

            return response

        except Exception:
            # Still record timing on error
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            context.add_metadata("processing_time", elapsed)
            context.add_metadata("processing_time_ms", elapsed * 1000)
            raise


class ErrorHandlingMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Base middleware for error handling.

    Override handle_error to customize error handling.
    """

    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse],
    ) -> TResponse:
        """Process request with error handling."""
        try:
            return await next_handler(request, context)

        except Exception as e:
            # Add error to context
            context.add_error(e)

            # Handle error
            return await self.handle_error(e, request, context)

    async def handle_error(
        self, error: Exception, request: TRequest, context: MiddlewareContext
    ) -> TResponse:
        """
        Handle error.

        Override to customize error handling.
        Default behavior is to re-raise.
        """
        raise error


# Middleware factory


class MiddlewareFactory:
    """Factory for creating common middleware configurations."""

    @staticmethod
    def create_default_pipeline(
        handler: Callable[[TRequest, MiddlewareContext], TResponse],
        include_logging: bool = True,
        include_timing: bool = True,
        include_error_handling: bool = True,
    ) -> MiddlewarePipeline[TRequest, TResponse]:
        """
        Create pipeline with default middleware.

        Args:
            handler: Request handler
            include_logging: Include logging middleware
            include_timing: Include timing middleware
            include_error_handling: Include error handling

        Returns:
            Configured pipeline
        """
        pipeline = MiddlewarePipeline(handler)

        if include_error_handling:
            pipeline.add(ErrorHandlingMiddleware())

        if include_timing:
            pipeline.add(TimingMiddleware())

        if include_logging:
            pipeline.add(LoggingMiddleware())

        return pipeline


# Context manager for middleware execution


@contextmanager
def middleware_context(**metadata):
    """
    Context manager for middleware execution.

    Example:
        with middleware_context(user_id=123) as context:
            response = pipeline.execute(request, context)
    """
    context = MiddlewareContext(metadata=metadata)
    try:
        yield context
    finally:
        # Log final context state if needed
        if context.errors:
            logger.warning(
                f"Request {context.request_id} had {len(context.errors)} errors"
            )
