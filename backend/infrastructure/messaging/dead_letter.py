"""
Dead letter queue implementation for failed message handling.

Provides mechanisms for handling messages that cannot be processed.
"""

from typing import Dict, Optional, List, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

from .base import Message, MessageStatus, IMessageQueue, MessageHandler, RetryPolicy, T
from .memory_queue import InMemoryQueue


logger = logging.getLogger(__name__)


class DeadLetterReason(Enum):
    """Reasons for sending message to dead letter queue."""

    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    TTL_EXPIRED = "ttl_expired"
    PROCESSING_FAILED = "processing_failed"
    VALIDATION_FAILED = "validation_failed"
    NO_HANDLER = "no_handler"
    MANUAL = "manual"


@dataclass
class DeadLetterPolicy:
    """Policy for dead letter queue behavior."""

    max_retries: int = 3
    ttl: Optional[timedelta] = None
    retry_delay: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    exponential_backoff: bool = True
    backoff_multiplier: float = 2.0
    max_retry_delay: timedelta = field(default_factory=lambda: timedelta(hours=1))
    store_original_metadata: bool = True

    def should_dead_letter(
        self, message: Message[Any], error: Optional[Exception] = None
    ) -> bool:
        """Check if message should be sent to dead letter queue."""
        # Check retry count
        if message.metadata.attempts >= self.max_retries:
            return True

        # Check TTL
        if message.is_expired():
            return True

        # Check for permanent failures
        if error and isinstance(error, (ValueError, TypeError, KeyError)):
            return True

        return False

    def calculate_retry_delay(self, attempts: int) -> timedelta:
        """Calculate delay before retry."""
        if not self.exponential_backoff:
            return self.retry_delay

        delay_seconds = self.retry_delay.total_seconds() * (
            self.backoff_multiplier ** (attempts - 1)
        )
        max_seconds = self.max_retry_delay.total_seconds()

        return timedelta(seconds=min(delay_seconds, max_seconds))


@dataclass
class DeadLetterEntry:
    """Entry in dead letter queue with additional metadata."""

    message: Message[Any]
    reason: DeadLetterReason
    error_message: Optional[str] = None
    original_queue: Optional[str] = None
    dead_lettered_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message.metadata.message_id,
            "reason": self.reason.value,
            "error_message": self.error_message,
            "original_queue": self.original_queue,
            "dead_lettered_at": self.dead_lettered_at.isoformat(),
            "retry_count": self.retry_count,
            "last_retry_at": (
                self.last_retry_at.isoformat() if self.last_retry_at else None
            ),
            "message": self.message.to_dict(),
        }


class DeadLetterQueue:
    """
    Dead letter queue for failed messages.

    Features:
    - Failed message storage
    - Retry management
    - Inspection and recovery
    - Metrics tracking
    """

    def __init__(
        self,
        name: str = "dead_letter",
        policy: Optional[DeadLetterPolicy] = None,
        storage: Optional[IMessageQueue[DeadLetterEntry]] = None,
    ):
        """Initialize dead letter queue."""
        self.name = name
        self.policy = policy or DeadLetterPolicy()
        self._storage = storage or InMemoryQueue(f"{name}_dlq")
        self._entries: Dict[str, DeadLetterEntry] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "total_entries": 0,
            "retried": 0,
            "recovered": 0,
            "expired": 0,
            "by_reason": {},
        }

    async def add(
        self,
        message: Message[Any],
        reason: DeadLetterReason,
        error: Optional[Exception] = None,
        original_queue: Optional[str] = None,
    ) -> str:
        """Add message to dead letter queue."""
        async with self._lock:
            # Create dead letter entry
            entry = DeadLetterEntry(
                message=message,
                reason=reason,
                error_message=str(error) if error else None,
                original_queue=original_queue,
            )

            # Store entry
            self._entries[message.metadata.message_id] = entry

            # Create wrapped message for storage
            wrapped = Message(payload=entry, metadata=message.metadata)

            # Enqueue
            await self._storage.enqueue(wrapped)

            # Update stats
            self._stats["total_entries"] += 1
            reason_key = reason.value
            self._stats["by_reason"][reason_key] = (
                self._stats["by_reason"].get(reason_key, 0) + 1
            )

            logger.warning(
                f"Message {message.metadata.message_id} sent to DLQ. "
                f"Reason: {reason.value}, Error: {error}"
            )

            return message.metadata.message_id

    async def retry(
        self, message_id: str, target_queue: Optional[IMessageQueue[Any]] = None
    ) -> bool:
        """Retry a dead letter message."""
        async with self._lock:
            entry = self._entries.get(message_id)
            if not entry:
                return False

            # Update retry metadata
            entry.retry_count += 1
            entry.last_retry_at = datetime.utcnow()

            # Check if should retry
            if entry.retry_count > self.policy.max_retries:
                logger.error(f"Message {message_id} exceeded max retries in DLQ")
                return False

            # Reset message status
            entry.message.status = MessageStatus.PENDING
            entry.message.metadata.attempts = 0

            # Send to target queue if provided
            if target_queue:
                await target_queue.enqueue(entry.message)

                # Remove from DLQ
                del self._entries[message_id]
                self._stats["retried"] += 1

                return True

            return False

    async def recover(self, message_id: str) -> Optional[Message[Any]]:
        """Recover message from dead letter queue."""
        async with self._lock:
            entry = self._entries.get(message_id)
            if not entry:
                return None

            # Remove from entries
            del self._entries[message_id]
            self._stats["recovered"] += 1

            return entry.message

    async def inspect(
        self, limit: int = 100, reason: Optional[DeadLetterReason] = None
    ) -> List[DeadLetterEntry]:
        """Inspect dead letter entries."""
        async with self._lock:
            entries = list(self._entries.values())

            # Filter by reason if specified
            if reason:
                entries = [e for e in entries if e.reason == reason]

            # Sort by dead letter time
            entries.sort(key=lambda e: e.dead_lettered_at, reverse=True)

            return entries[:limit]

    async def purge(
        self,
        older_than: Optional[timedelta] = None,
        reason: Optional[DeadLetterReason] = None,
    ) -> int:
        """Purge old entries from dead letter queue."""
        async with self._lock:
            to_remove = []
            cutoff = datetime.utcnow() - older_than if older_than else None

            for message_id, entry in self._entries.items():
                should_remove = False

                # Check age
                if cutoff and entry.dead_lettered_at < cutoff:
                    should_remove = True

                # Check reason
                if reason and entry.reason != reason:
                    should_remove = False

                if should_remove:
                    to_remove.append(message_id)

            # Remove entries
            for message_id in to_remove:
                del self._entries[message_id]
                self._stats["expired"] += 1

            return len(to_remove)

    async def size(self) -> int:
        """Get number of entries in dead letter queue."""
        async with self._lock:
            return len(self._entries)

    def get_stats(self) -> Dict[str, Any]:
        """Get dead letter queue statistics."""
        return {**self._stats, "current_size": len(self._entries)}


class DeadLetterHandler(MessageHandler[T]):
    """
    Message handler that sends failures to dead letter queue.

    Wraps another handler and catches failures.
    """

    def __init__(
        self,
        handler: MessageHandler[T],
        dlq: DeadLetterQueue,
        policy: Optional[DeadLetterPolicy] = None,
        original_queue_name: Optional[str] = None,
    ):
        """Initialize dead letter handler."""
        self.handler = handler
        self.dlq = dlq
        self.policy = policy or DeadLetterPolicy()
        self.original_queue_name = original_queue_name

    async def handle(self, message: Message[T]) -> None:
        """Handle message with dead letter support."""
        try:
            # Attempt normal handling
            await self.handler.handle(message)

        except Exception as e:
            # Increment attempts
            message.metadata.attempts += 1
            message.metadata.last_error = str(e)

            # Check if should dead letter
            if self.policy.should_dead_letter(message, e):
                await self.dlq.add(
                    message,
                    DeadLetterReason.PROCESSING_FAILED,
                    e,
                    self.original_queue_name,
                )
                message.status = MessageStatus.DEAD_LETTER
            else:
                # Re-raise for retry
                raise

    def can_handle(self, message: Message[T]) -> bool:
        """Check if can handle message."""
        return self.handler.can_handle(message)


class RetryableDeadLetterQueue(DeadLetterQueue):
    """
    Dead letter queue with automatic retry capabilities.

    Features:
    - Scheduled retries
    - Exponential backoff
    - Selective retry patterns
    """

    def __init__(
        self,
        name: str = "retryable_dlq",
        policy: Optional[DeadLetterPolicy] = None,
        storage: Optional[IMessageQueue[DeadLetterEntry]] = None,
    ):
        """Initialize retryable dead letter queue."""
        super().__init__(name, policy, storage)
        self._retry_tasks: Dict[str, asyncio.Task] = {}
        self._retry_queues: Dict[str, IMessageQueue[Any]] = {}

    def register_retry_queue(self, queue_name: str, queue: IMessageQueue[Any]) -> None:
        """Register queue for automatic retries."""
        self._retry_queues[queue_name] = queue

    async def add(
        self,
        message: Message[Any],
        reason: DeadLetterReason,
        error: Optional[Exception] = None,
        original_queue: Optional[str] = None,
    ) -> str:
        """Add message with automatic retry scheduling."""
        message_id = await super().add(message, reason, error, original_queue)

        # Schedule retry if applicable
        if (
            original_queue
            and original_queue in self._retry_queues
            and reason
            in (DeadLetterReason.PROCESSING_FAILED, DeadLetterReason.TTL_EXPIRED)
        ):

            # Calculate retry delay
            delay = self.policy.calculate_retry_delay(message.metadata.attempts)

            # Schedule retry task
            task = asyncio.create_task(
                self._scheduled_retry(message_id, original_queue, delay)
            )
            self._retry_tasks[message_id] = task

        return message_id

    async def _scheduled_retry(
        self, message_id: str, queue_name: str, delay: timedelta
    ) -> None:
        """Perform scheduled retry after delay."""
        try:
            # Wait for delay
            await asyncio.sleep(delay.total_seconds())

            # Get target queue
            target_queue = self._retry_queues.get(queue_name)
            if not target_queue:
                return

            # Attempt retry
            success = await self.retry(message_id, target_queue)

            if success:
                logger.info(
                    f"Successfully retried message {message_id} to queue {queue_name}"
                )
            else:
                logger.error(f"Failed to retry message {message_id}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in scheduled retry: {e}")
        finally:
            # Clean up task
            self._retry_tasks.pop(message_id, None)

    async def cancel_retry(self, message_id: str) -> bool:
        """Cancel scheduled retry for message."""
        task = self._retry_tasks.get(message_id)
        if task and not task.done():
            task.cancel()
            self._retry_tasks.pop(message_id, None)
            return True
        return False

    async def shutdown(self) -> None:
        """Shutdown retryable queue and cancel pending retries."""
        # Cancel all retry tasks
        for task in self._retry_tasks.values():
            if not task.done():
                task.cancel()

        # Wait for cancellations
        if self._retry_tasks:
            await asyncio.gather(*self._retry_tasks.values(), return_exceptions=True)

        self._retry_tasks.clear()
