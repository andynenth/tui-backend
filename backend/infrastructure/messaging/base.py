"""
Base abstractions for message queue infrastructure.

Provides core interfaces and data types for message handling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable, Awaitable, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


T = TypeVar("T")


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class MessageStatus(Enum):
    """Message processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    DEAD_LETTER = "dead_letter"


@dataclass
class RetryPolicy:
    """Policy for message retry behavior."""

    max_retries: int = 3
    initial_delay: timedelta = field(default_factory=lambda: timedelta(seconds=1))
    max_delay: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    exponential_backoff: bool = True
    backoff_multiplier: float = 2.0
    retry_on_errors: Optional[List[type]] = None

    def calculate_delay(self, attempt: int) -> timedelta:
        """Calculate delay for retry attempt."""
        if not self.exponential_backoff:
            return self.initial_delay

        delay = self.initial_delay.total_seconds() * (
            self.backoff_multiplier ** (attempt - 1)
        )
        max_seconds = self.max_delay.total_seconds()

        return timedelta(seconds=min(delay, max_seconds))


@dataclass
class DeliveryOptions:
    """Options for message delivery."""

    ttl: Optional[timedelta] = None
    delay: Optional[timedelta] = None
    priority: MessagePriority = MessagePriority.NORMAL
    persistent: bool = False
    exclusive: bool = False
    correlation_id: Optional[str] = None


@dataclass
class MessageMetadata:
    """Metadata for a message."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    destination: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    content_type: str = "application/json"
    headers: Dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    last_error: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class Message(Generic[T]):
    """
    Generic message container.

    Represents a message in the queue system with payload and metadata.
    """

    payload: T
    metadata: MessageMetadata = field(default_factory=MessageMetadata)
    status: MessageStatus = MessageStatus.PENDING
    priority: MessagePriority = MessagePriority.NORMAL

    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.metadata.expires_at:
            return datetime.utcnow() > self.metadata.expires_at
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.metadata.message_id,
            "payload": self.payload,
            "status": self.status.value,
            "priority": self.priority.value,
            "metadata": {
                "timestamp": self.metadata.timestamp.isoformat(),
                "source": self.metadata.source,
                "destination": self.metadata.destination,
                "correlation_id": self.metadata.correlation_id,
                "reply_to": self.metadata.reply_to,
                "content_type": self.metadata.content_type,
                "headers": self.metadata.headers,
                "attempts": self.metadata.attempts,
                "last_error": self.metadata.last_error,
                "expires_at": (
                    self.metadata.expires_at.isoformat()
                    if self.metadata.expires_at
                    else None
                ),
            },
        }


class MessageHandler(ABC, Generic[T]):
    """Base class for message handlers."""

    @abstractmethod
    async def handle(self, message: Message[T]) -> None:
        """
        Handle a message.

        Args:
            message: Message to handle

        Raises:
            Exception: If message handling fails
        """
        pass

    @abstractmethod
    def can_handle(self, message: Message[T]) -> bool:
        """
        Check if handler can process message.

        Args:
            message: Message to check

        Returns:
            True if handler can process message
        """
        pass


class IMessageQueue(ABC, Generic[T]):
    """Interface for message queue operations."""

    @abstractmethod
    async def enqueue(
        self, message: Message[T], options: Optional[DeliveryOptions] = None
    ) -> str:
        """
        Add message to queue.

        Args:
            message: Message to enqueue
            options: Delivery options

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Message[T]]:
        """
        Remove and return message from queue.

        Args:
            timeout: Wait timeout in seconds

        Returns:
            Message if available, None otherwise
        """
        pass

    @abstractmethod
    async def peek(self, count: int = 1) -> List[Message[T]]:
        """
        Peek at messages without removing.

        Args:
            count: Number of messages to peek

        Returns:
            List of messages
        """
        pass

    @abstractmethod
    async def acknowledge(self, message_id: str) -> bool:
        """
        Acknowledge message processing.

        Args:
            message_id: ID of message to acknowledge

        Returns:
            True if acknowledged
        """
        pass

    @abstractmethod
    async def reject(self, message_id: str, requeue: bool = False) -> bool:
        """
        Reject message.

        Args:
            message_id: ID of message to reject
            requeue: Whether to requeue message

        Returns:
            True if rejected
        """
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get queue size."""
        pass

    @abstractmethod
    async def clear(self) -> int:
        """
        Clear all messages.

        Returns:
            Number of messages cleared
        """
        pass


class IMessageRouter(ABC):
    """Interface for message routing."""

    @abstractmethod
    async def route(
        self, message: Message[Any], routing_key: Optional[str] = None
    ) -> List[str]:
        """
        Route message to destinations.

        Args:
            message: Message to route
            routing_key: Optional routing key

        Returns:
            List of destination queue names
        """
        pass

    @abstractmethod
    def register_route(
        self,
        pattern: str,
        destination: str,
        filter_func: Optional[Callable[[Message[Any]], bool]] = None,
    ) -> None:
        """
        Register a routing rule.

        Args:
            pattern: Route pattern
            destination: Destination queue name
            filter_func: Optional filter function
        """
        pass

    @abstractmethod
    def unregister_route(self, pattern: str, destination: Optional[str] = None) -> bool:
        """
        Unregister routing rule.

        Args:
            pattern: Route pattern
            destination: Specific destination or all if None

        Returns:
            True if unregistered
        """
        pass


class IMessageSerializer(ABC, Generic[T]):
    """Interface for message serialization."""

    @abstractmethod
    def serialize(self, message: Message[T]) -> bytes:
        """
        Serialize message to bytes.

        Args:
            message: Message to serialize

        Returns:
            Serialized bytes
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Message[T]:
        """
        Deserialize bytes to message.

        Args:
            data: Serialized data

        Returns:
            Deserialized message
        """
        pass

    @abstractmethod
    def content_type(self) -> str:
        """Get content type for serialized data."""
        pass
