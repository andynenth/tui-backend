"""
Message queue service for managing messages to disconnected players.

This service handles queueing and delivering messages to players who
are temporarily disconnected, ensuring they don't miss important game events.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from domain.entities.message_queue import PlayerQueue, QueuedMessage
from domain.value_objects import PlayerId, RoomId
from domain.events import MessageQueued, MessageQueueOverflow, QueuedMessagesDelivered
from application.interfaces import UnitOfWork
from application.interfaces.services import EventPublisher, Logger
from application.exceptions import ApplicationException


class MessageQueueService:
    """
    Service for managing message queues.

    This service handles:
    - Queueing messages for disconnected players
    - Managing queue size limits
    - Prioritizing critical messages
    - Delivering queued messages on reconnection
    """

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        logger: Optional[Logger] = None,
    ):
        self._uow = uow
        self._event_publisher = event_publisher
        self._logger = logger or logging.getLogger(__name__)

    async def queue_message(
        self,
        room_id: str,
        player_name: str,
        event_type: str,
        event_data: Dict[str, Any],
        is_critical: bool = False,
    ) -> bool:
        """
        Queue a message for a disconnected player.

        Args:
            room_id: The room ID
            player_name: The player name
            event_type: Type of event to queue
            event_data: Event data
            is_critical: Whether this is a critical message

        Returns:
            True if message was queued, False if queue is full
        """
        async with self._uow:
            # Get or create queue
            queue = await self._uow.message_queues.get_queue(room_id, player_name)
            if not queue:
                # Player might not have a queue yet
                await self._uow.message_queues.create_queue(room_id, player_name)
                queue = PlayerQueue(
                    player_id=PlayerId(player_name), room_id=RoomId(room_id)
                )

            # Create message
            message = QueuedMessage(
                event_type=event_type,
                data=event_data,
                timestamp=datetime.utcnow(),
                is_critical=is_critical,
            )

            # Try to add message
            if queue.add_message(message):
                # Save updated queue
                await self._uow.message_queues.save_queue(queue)

                # Publish event
                event = MessageQueued(
                    room_id=room_id,
                    player_name=player_name,
                    event_type_queued=event_type,
                    is_critical=is_critical,
                    queue_size=len(queue.messages),
                )
                await self._event_publisher.publish_batch([event])

                self._logger.debug(
                    f"Queued {event_type} for {player_name} in room {room_id}. "
                    f"Queue size: {len(queue.messages)}"
                )

                return True
            else:
                # Queue is full
                overflow_event = MessageQueueOverflow(
                    room_id=room_id,
                    player_name=player_name,
                    dropped_count=1,
                    retained_critical_count=sum(
                        1 for msg in queue.messages if msg.is_critical
                    ),
                    queue_capacity=queue.max_size,
                )
                await self._event_publisher.publish_batch([overflow_event])

                self._logger.warning(
                    f"Queue overflow for {player_name} in room {room_id}. "
                    f"Dropped {event_type} event"
                )

                return False

    async def get_queued_messages(
        self, room_id: str, player_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get all queued messages for a player.

        Args:
            room_id: The room ID
            player_name: The player name

        Returns:
            List of queued messages
        """
        async with self._uow:
            queue = await self._uow.message_queues.get_queue(room_id, player_name)
            if not queue:
                return []

            return [msg.to_dict() for msg in queue.messages]

    async def deliver_messages(
        self, room_id: str, player_name: str
    ) -> List[Dict[str, Any]]:
        """
        Deliver and clear queued messages.

        Args:
            room_id: The room ID
            player_name: The player name

        Returns:
            List of delivered messages
        """
        async with self._uow:
            queue = await self._uow.message_queues.get_queue(room_id, player_name)
            if not queue:
                return []

            # Get messages before clearing
            messages = [msg.to_dict() for msg in queue.messages]

            # Clear queue
            await self._uow.message_queues.clear_queue(room_id, player_name)

            # Publish event
            if messages:
                event = QueuedMessagesDelivered(
                    room_id=room_id,
                    player_name=player_name,
                    message_count=len(messages),
                    oldest_message_age_seconds=(
                        (
                            datetime.utcnow() - queue.messages[0].timestamp
                        ).total_seconds()
                        if queue.messages
                        else 0
                    ),
                    critical_message_count=sum(
                        1 for msg in queue.messages if msg.is_critical
                    ),
                )
                await self._event_publisher.publish_batch([event])

                self._logger.info(
                    f"Delivered {len(messages)} messages to {player_name} in room {room_id}"
                )

            return messages

    async def get_queue_stats(self, room_id: str) -> Dict[str, Any]:
        """
        Get statistics about message queues in a room.

        Args:
            room_id: The room ID

        Returns:
            Queue statistics
        """
        async with self._uow:
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                raise ApplicationException(
                    f"Room {room_id} not found", code="ROOM_NOT_FOUND"
                )

            stats = {
                "room_id": room_id,
                "total_queues": 0,
                "total_messages": 0,
                "players": [],
            }

            for player in room.players:
                queue = await self._uow.message_queues.get_queue(room_id, player.name)
                if queue:
                    player_stats = {
                        "player_name": player.name,
                        "queue_size": len(queue.messages),
                        "critical_messages": sum(
                            1 for msg in queue.messages if msg.is_critical
                        ),
                        "oldest_message_age": (
                            (
                                datetime.utcnow() - queue.messages[0].timestamp
                            ).total_seconds()
                            if queue.messages
                            else 0
                        ),
                    }
                    stats["players"].append(player_stats)
                    stats["total_queues"] += 1
                    stats["total_messages"] += len(queue.messages)

            return stats

    async def cleanup_old_messages(
        self, room_id: str, max_age_minutes: int = 30
    ) -> int:
        """
        Clean up old messages from queues.

        Args:
            room_id: The room ID
            max_age_minutes: Maximum age for messages

        Returns:
            Number of messages cleaned up
        """
        async with self._uow:
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                return 0

            total_cleaned = 0
            cutoff_time = datetime.utcnow()

            for player in room.players:
                queue = await self._uow.message_queues.get_queue(room_id, player.name)
                if queue:
                    # Remove old messages
                    original_count = len(queue.messages)
                    queue.messages = [
                        msg
                        for msg in queue.messages
                        if (cutoff_time - msg.timestamp).total_seconds()
                        < max_age_minutes * 60
                    ]

                    cleaned = original_count - len(queue.messages)
                    if cleaned > 0:
                        await self._uow.message_queues.save_queue(queue)
                        total_cleaned += cleaned

                        self._logger.info(
                            f"Cleaned {cleaned} old messages from {player.name}'s queue "
                            f"in room {room_id}"
                        )

            return total_cleaned

    async def prioritize_critical_messages(
        self, room_id: str, player_name: str
    ) -> None:
        """
        Reorder queue to prioritize critical messages.

        Args:
            room_id: The room ID
            player_name: The player name
        """
        async with self._uow:
            queue = await self._uow.message_queues.get_queue(room_id, player_name)
            if not queue or len(queue.messages) <= 1:
                return

            # Separate critical and non-critical messages
            critical = [msg for msg in queue.messages if msg.is_critical]
            non_critical = [msg for msg in queue.messages if not msg.is_critical]

            # Reorder: critical first, maintaining timestamp order within each group
            queue.messages = critical + non_critical

            await self._uow.message_queues.save_queue(queue)

            self._logger.debug(
                f"Prioritized {len(critical)} critical messages for {player_name} "
                f"in room {room_id}"
            )
