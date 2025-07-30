"""
Handle player reconnect use case.

This use case manages the complete flow when a player reconnects,
including bot deactivation and queued message delivery.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from application.interfaces import UnitOfWork
from application.interfaces.services import EventPublisher, MetricsCollector
from application.dto.connection import (
    HandlePlayerReconnectRequest,
    HandlePlayerReconnectResponse,
)
from application.exceptions import ApplicationException
from domain.value_objects import RoomId


class HandlePlayerReconnectUseCase:
    """
    Handle player reconnection.

    This use case:
    1. Marks the player as reconnected
    2. Deactivates bot if it was activated
    3. Retrieves queued messages
    4. Clears the message queue
    5. Cancels room cleanup if needed
    6. Publishes appropriate events
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None,
    ):
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._metrics = metrics

    async def execute(
        self, request: HandlePlayerReconnectRequest
    ) -> HandlePlayerReconnectResponse:
        """Execute the use case."""
        try:
            async with self._uow:
                # Get the room
                room = await self._uow.rooms.get_by_id(request.room_id)
                if not room:
                    return HandlePlayerReconnectResponse(
                        success=False, error="Room not found"
                    )

                # Get the player
                player = room.get_player(request.player_name)
                if not player:
                    return HandlePlayerReconnectResponse(
                        success=False, error="Player not found in room"
                    )

                # Get queued messages before reconnecting
                queue = await self._uow.message_queues.get_queue(
                    request.room_id, request.player_name
                )

                queued_messages = []
                if queue:
                    # Convert messages to dictionaries
                    queued_messages = [
                        {
                            "event_type": msg.event_type,
                            "data": msg.data,
                            "timestamp": msg.timestamp.isoformat(),
                            "is_critical": msg.is_critical,
                        }
                        for msg in queue.get_all_messages()
                    ]

                    # Get oldest message age for metrics
                    oldest_age = queue.oldest_message_age()

                # Check if bot will be deactivated
                was_bot = player.is_bot and not player.original_is_bot

                # Handle reconnection
                player.reconnect(request.room_id, len(queued_messages))

                # Room cleanup cancellation not implemented yet
                room_cleanup_cancelled = False

                # Update connection tracking
                connection = await self._uow.connections.get(
                    request.room_id, request.player_name
                )
                if connection:
                    connection.reconnect(request.websocket_id)
                    await self._uow.connections.save(connection)

                # Clear message queue
                if queue:
                    await self._uow.message_queues.clear_queue(
                        request.room_id, request.player_name
                    )

                # Save changes
                await self._uow.rooms.save(room)
                await self._uow.commit()

                # Publish events from player
                for event in player.events:
                    await self._event_publisher.publish(event)
                player.clear_events()

                # Publish events from queue if any
                if queue:
                    for event in queue.events:
                        await self._event_publisher.publish(event)
                    queue.clear_events()

                # Record metrics
                if self._metrics:
                    self._metrics.increment(
                        "player.reconnected",
                        tags={
                            "bot_deactivated": str(not player.is_bot).lower(),
                            "messages_queued": str(len(queued_messages)),
                        },
                    )

                    if queue and oldest_age is not None:
                        self._metrics.gauge(
                            "message_queue.oldest_message_age", oldest_age
                        )

                # Get current game state
                game = await self._uow.games.get_by_room_id(request.room_id)
                current_state = game.to_dict() if game else None

                # Bot was deactivated during reconnect if player was bot before

                return HandlePlayerReconnectResponse(
                    success=True,
                    bot_deactivated=was_bot,
                    messages_restored=len(queued_messages),
                    queued_messages=queued_messages,
                    current_state=current_state,
                    room_cleanup_cancelled=room_cleanup_cancelled,
                )

        except Exception as e:
            if self._metrics:
                self._metrics.increment("player.reconnect.error")

            raise ApplicationException(
                f"Failed to handle player reconnect: {str(e)}", code="RECONNECT_FAILED"
            )
