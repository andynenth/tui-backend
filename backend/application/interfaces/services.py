"""
Service interfaces for the application layer.

These interfaces define external services that the application layer
depends on. Implementations will be provided by the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from domain.events.base import DomainEvent


class EventPublisher(ABC):
    """Interface for publishing domain events."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event.

        Args:
            event: The event to publish
        """
        pass

    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events.

        Args:
            events: List of events to publish
        """
        pass


class NotificationService(ABC):
    """Interface for sending notifications to users."""

    @abstractmethod
    async def notify_player(
        self, player_id: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification to a specific player.

        Args:
            player_id: Target player's ID
            message: Notification message
            data: Additional notification data
        """
        pass

    @abstractmethod
    async def notify_room(
        self, room_id: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification to all players in a room.

        Args:
            room_id: Target room's ID
            message: Notification message
            data: Additional notification data
        """
        pass


class BotService(ABC):
    """Interface for bot player operations."""

    @abstractmethod
    async def create_bot(self, difficulty: str = "medium") -> str:
        """
        Create a new bot player.

        Args:
            difficulty: Bot difficulty level

        Returns:
            The bot's player ID
        """
        pass

    @abstractmethod
    async def get_bot_action(
        self, game_state: Dict[str, Any], player_id: str
    ) -> Dict[str, Any]:
        """
        Get the next action for a bot player.

        Args:
            game_state: Current game state
            player_id: Bot's player ID

        Returns:
            The action the bot wants to take
        """
        pass

    @abstractmethod
    async def is_bot(self, player_id: str) -> bool:
        """
        Check if a player is a bot.

        Args:
            player_id: Player's ID to check

        Returns:
            True if player is a bot
        """
        pass


class MetricsCollector(ABC):
    """Interface for collecting application metrics."""

    @abstractmethod
    def increment(
        self, metric: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.

        Args:
            metric: Metric name
            value: Amount to increment
            tags: Optional metric tags
        """
        pass

    @abstractmethod
    def gauge(
        self, metric: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric.

        Args:
            metric: Metric name
            value: Gauge value
            tags: Optional metric tags
        """
        pass

    @abstractmethod
    def timing(
        self, metric: str, duration_ms: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timing metric.

        Args:
            metric: Metric name
            duration_ms: Duration in milliseconds
            tags: Optional metric tags
        """
        pass


class CacheService(ABC):
    """Interface for caching service."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass


class Logger(ABC):
    """Interface for structured logging."""

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass

    @abstractmethod
    def error(
        self, message: str, exception: Optional[Exception] = None, **kwargs
    ) -> None:
        """Log an error message."""
        pass
