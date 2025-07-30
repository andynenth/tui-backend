"""
Message handler implementations with various processing patterns.

Provides reusable handlers for common message processing scenarios.
"""

import asyncio
from typing import List, Optional, Callable, Any, Dict, Set
from datetime import datetime, timedelta
import logging
from functools import wraps

from .base import Message, MessageHandler, MessageStatus, RetryPolicy, T


logger = logging.getLogger(__name__)


class AsyncMessageHandler(MessageHandler[T]):
    """
    Async message handler with concurrent processing.

    Features:
    - Configurable concurrency
    - Task management
    - Graceful shutdown
    """

    def __init__(
        self,
        handler_func: Callable[[Message[T]], Any],
        max_concurrent: int = 10,
        name: Optional[str] = None,
    ):
        """Initialize async handler."""
        self.handler_func = handler_func
        self.max_concurrent = max_concurrent
        self.name = name or f"async_handler_{id(self)}"
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: Set[asyncio.Task] = set()
        self._shutdown = False

    async def handle(self, message: Message[T]) -> None:
        """Handle message asynchronously."""
        if self._shutdown:
            raise RuntimeError("Handler is shutting down")

        async with self._semaphore:
            # Create task for handling
            task = asyncio.create_task(self._handle_message(message))
            self._active_tasks.add(task)

            try:
                await task
            finally:
                self._active_tasks.discard(task)

    async def _handle_message(self, message: Message[T]) -> None:
        """Handle individual message."""
        try:
            # Check if handler is async
            if asyncio.iscoroutinefunction(self.handler_func):
                await self.handler_func(message)
            else:
                # Run sync handler in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.handler_func, message)

            message.status = MessageStatus.COMPLETED

        except Exception as e:
            message.status = MessageStatus.FAILED
            message.metadata.last_error = str(e)
            logger.error(f"Handler {self.name} failed: {e}")
            raise

    def can_handle(self, message: Message[T]) -> bool:
        """Check if can handle message."""
        return not self._shutdown

    async def shutdown(self) -> None:
        """Shutdown handler gracefully."""
        self._shutdown = True

        # Wait for active tasks
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} tasks to complete")
            await asyncio.gather(*self._active_tasks, return_exceptions=True)

        logger.info(f"Handler {self.name} shutdown complete")


class BatchMessageHandler(MessageHandler[T]):
    """
    Batch message handler for processing multiple messages together.

    Features:
    - Configurable batch size and timeout
    - Efficient bulk processing
    - Automatic flushing
    """

    def __init__(
        self,
        batch_func: Callable[[List[Message[T]]], Any],
        batch_size: int = 100,
        batch_timeout: timedelta = timedelta(seconds=5),
        name: Optional[str] = None,
    ):
        """Initialize batch handler."""
        self.batch_func = batch_func
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.name = name or f"batch_handler_{id(self)}"

        self._batch: List[Message[T]] = []
        self._batch_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def handle(self, message: Message[T]) -> None:
        """Add message to batch."""
        if self._shutdown:
            raise RuntimeError("Handler is shutting down")

        async with self._batch_lock:
            self._batch.append(message)

            # Check if should flush
            if len(self._batch) >= self.batch_size:
                await self._flush_batch()
            elif not self._flush_task or self._flush_task.done():
                # Schedule flush
                self._flush_task = asyncio.create_task(self._scheduled_flush())

    async def _scheduled_flush(self) -> None:
        """Flush batch after timeout."""
        await asyncio.sleep(self.batch_timeout.total_seconds())

        async with self._batch_lock:
            if self._batch:
                await self._flush_batch()

    async def _flush_batch(self) -> None:
        """Process current batch."""
        if not self._batch:
            return

        batch = self._batch
        self._batch = []

        try:
            # Process batch
            if asyncio.iscoroutinefunction(self.batch_func):
                await self.batch_func(batch)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.batch_func, batch)

            # Mark messages as completed
            for msg in batch:
                msg.status = MessageStatus.COMPLETED

            logger.info(f"Processed batch of {len(batch)} messages")

        except Exception as e:
            # Mark messages as failed
            for msg in batch:
                msg.status = MessageStatus.FAILED
                msg.metadata.last_error = str(e)

            logger.error(f"Batch processing failed: {e}")
            raise

    def can_handle(self, message: Message[T]) -> bool:
        """Check if can handle message."""
        return not self._shutdown

    async def shutdown(self) -> None:
        """Shutdown handler and flush remaining messages."""
        self._shutdown = True

        # Cancel scheduled flush
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()

        # Flush remaining messages
        async with self._batch_lock:
            if self._batch:
                await self._flush_batch()


class ChainedMessageHandler(MessageHandler[T]):
    """
    Chains multiple handlers together.

    Features:
    - Sequential processing
    - Conditional chaining
    - Error propagation
    """

    def __init__(
        self,
        handlers: List[MessageHandler[T]],
        stop_on_error: bool = True,
        name: Optional[str] = None,
    ):
        """Initialize chained handler."""
        self.handlers = handlers
        self.stop_on_error = stop_on_error
        self.name = name or f"chain_{id(self)}"

    async def handle(self, message: Message[T]) -> None:
        """Handle message through chain."""
        for i, handler in enumerate(self.handlers):
            try:
                if handler.can_handle(message):
                    await handler.handle(message)
                else:
                    logger.debug(f"Handler {i} cannot handle message")

            except Exception as e:
                logger.error(f"Handler {i} in chain failed: {e}")

                if self.stop_on_error:
                    raise

    def can_handle(self, message: Message[T]) -> bool:
        """Check if any handler can handle message."""
        return any(h.can_handle(message) for h in self.handlers)


class ErrorHandlingWrapper(MessageHandler[T]):
    """
    Wraps a handler with error handling logic.

    Features:
    - Exception catching
    - Error logging
    - Fallback handling
    """

    def __init__(
        self,
        handler: MessageHandler[T],
        error_handler: Optional[Callable[[Message[T], Exception], Any]] = None,
        reraise: bool = True,
        name: Optional[str] = None,
    ):
        """Initialize error handling wrapper."""
        self.handler = handler
        self.error_handler = error_handler
        self.reraise = reraise
        self.name = name or f"error_wrapper_{id(self)}"
        self._error_count = 0

    async def handle(self, message: Message[T]) -> None:
        """Handle message with error handling."""
        try:
            await self.handler.handle(message)

        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in handler {self.name}: {e}", exc_info=True)

            # Call error handler if provided
            if self.error_handler:
                try:
                    if asyncio.iscoroutinefunction(self.error_handler):
                        await self.error_handler(message, e)
                    else:
                        self.error_handler(message, e)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")

            # Update message status
            message.status = MessageStatus.FAILED
            message.metadata.last_error = str(e)

            if self.reraise:
                raise

    def can_handle(self, message: Message[T]) -> bool:
        """Check if wrapped handler can handle message."""
        return self.handler.can_handle(message)

    def get_error_count(self) -> int:
        """Get total error count."""
        return self._error_count


class RetryingHandler(MessageHandler[T]):
    """
    Handler with retry logic.

    Features:
    - Configurable retry policy
    - Exponential backoff
    - Dead letter support
    """

    def __init__(
        self,
        handler: MessageHandler[T],
        retry_policy: Optional[RetryPolicy] = None,
        name: Optional[str] = None,
    ):
        """Initialize retrying handler."""
        self.handler = handler
        self.retry_policy = retry_policy or RetryPolicy()
        self.name = name or f"retry_{id(self)}"
        self._retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_after_retries": 0,
        }

    async def handle(self, message: Message[T]) -> None:
        """Handle message with retries."""
        last_error = None

        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                await self.handler.handle(message)

                # Success
                if attempt > 0:
                    self._retry_stats["successful_retries"] += 1

                return

            except Exception as e:
                last_error = e
                message.metadata.attempts = attempt + 1

                # Check if should retry
                if attempt >= self.retry_policy.max_retries:
                    break

                # Check if error type is retryable
                if self.retry_policy.retry_on_errors:
                    if not any(
                        isinstance(e, err_type)
                        for err_type in self.retry_policy.retry_on_errors
                    ):
                        break

                # Calculate delay
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.calculate_delay(attempt + 1)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.retry_policy.max_retries} "
                        f"after {delay.total_seconds()}s for message {message.metadata.message_id}"
                    )

                    self._retry_stats["total_retries"] += 1
                    await asyncio.sleep(delay.total_seconds())

        # All retries failed
        self._retry_stats["failed_after_retries"] += 1
        message.status = MessageStatus.FAILED
        message.metadata.last_error = str(last_error)

        raise last_error

    def can_handle(self, message: Message[T]) -> bool:
        """Check if handler can handle message."""
        return self.handler.can_handle(message)

    def get_stats(self) -> Dict[str, int]:
        """Get retry statistics."""
        return self._retry_stats.copy()


class TimeoutHandler(MessageHandler[T]):
    """
    Handler with timeout enforcement.

    Features:
    - Processing timeout
    - Graceful cancellation
    - Timeout statistics
    """

    def __init__(
        self, handler: MessageHandler[T], timeout: timedelta, name: Optional[str] = None
    ):
        """Initialize timeout handler."""
        self.handler = handler
        self.timeout = timeout
        self.name = name or f"timeout_{id(self)}"
        self._timeout_count = 0

    async def handle(self, message: Message[T]) -> None:
        """Handle message with timeout."""
        try:
            await asyncio.wait_for(
                self.handler.handle(message), timeout=self.timeout.total_seconds()
            )

        except asyncio.TimeoutError:
            self._timeout_count += 1
            message.status = MessageStatus.FAILED
            message.metadata.last_error = (
                f"Timeout after {self.timeout.total_seconds()}s"
            )

            logger.error(
                f"Handler timeout for message {message.metadata.message_id} "
                f"after {self.timeout.total_seconds()}s"
            )

            raise

    def can_handle(self, message: Message[T]) -> bool:
        """Check if handler can handle message."""
        return self.handler.can_handle(message)

    def get_timeout_count(self) -> int:
        """Get number of timeouts."""
        return self._timeout_count


class FilteringHandler(MessageHandler[T]):
    """
    Handler that filters messages based on criteria.

    Features:
    - Flexible filtering
    - Filter chaining
    - Statistics
    """

    def __init__(
        self,
        handler: MessageHandler[T],
        filter_func: Callable[[Message[T]], bool],
        name: Optional[str] = None,
    ):
        """Initialize filtering handler."""
        self.handler = handler
        self.filter_func = filter_func
        self.name = name or f"filter_{id(self)}"
        self._filtered_count = 0
        self._passed_count = 0

    async def handle(self, message: Message[T]) -> None:
        """Handle message if it passes filter."""
        if self.filter_func(message):
            self._passed_count += 1
            await self.handler.handle(message)
        else:
            self._filtered_count += 1
            logger.debug(f"Message {message.metadata.message_id} filtered out")

    def can_handle(self, message: Message[T]) -> bool:
        """Check if can handle message after filtering."""
        return self.filter_func(message) and self.handler.can_handle(message)

    def get_stats(self) -> Dict[str, int]:
        """Get filter statistics."""
        return {
            "filtered": self._filtered_count,
            "passed": self._passed_count,
            "total": self._filtered_count + self._passed_count,
        }
