"""
Handle player disconnect use case.

This use case manages the complete flow when a player disconnects,
including bot activation and message queue creation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from application.interfaces import UnitOfWork
from application.interfaces.services import EventPublisher, MetricsCollector
from application.dto.connection import (
    HandlePlayerDisconnectRequest,
    HandlePlayerDisconnectResponse,
)
from application.exceptions import ApplicationException
from domain.value_objects import RoomId


class HandlePlayerDisconnectUseCase:
    """
    Handle player disconnection.

    This use case:
    1. Marks the player as disconnected
    2. Activates bot if game is in progress
    3. Creates message queue for the player
    4. Handles host migration if needed
    5. Publishes appropriate events
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
        self, request: HandlePlayerDisconnectRequest
    ) -> HandlePlayerDisconnectResponse:
        """Execute the use case."""
        try:
            async with self._uow:
                # Get the room
                room = await self._uow.rooms.get_by_id(request.room_id)
                if not room:
                    return HandlePlayerDisconnectResponse(
                        success=False, error="Room not found"
                    )

                # Get the player
                player = room.get_player(request.player_name)
                if not player:
                    return HandlePlayerDisconnectResponse(
                        success=False, error="Player not found in room"
                    )

                # Handle disconnection
                game_in_progress = room.is_game_started()
                player.disconnect(
                    request.room_id,
                    activate_bot=request.activate_bot and game_in_progress,
                )

                # Handle host migration if needed
                host_migrated = False
                new_host_name = None
                if room.is_host(request.player_name):
                    new_host = room.migrate_host()
                    if new_host:
                        host_migrated = True
                        new_host_name = new_host.name

                # Create message queue only if game in progress
                queue_created = False
                if game_in_progress:
                    await self._uow.message_queues.create_queue(
                        request.room_id, request.player_name
                    )
                    queue_created = True

                # Update or create connection tracking
                connection = await self._uow.connections.get(
                    request.room_id, request.player_name
                )
                if connection:
                    connection.disconnect()
                    await self._uow.connections.save(connection)
                else:
                    # Create new disconnected connection
                    from domain.entities.connection import (
                        PlayerConnection,
                        ConnectionStatus,
                    )
                    from domain.value_objects import PlayerId, RoomId

                    connection = PlayerConnection(
                        player_id=PlayerId(request.player_name),
                        room_id=RoomId(request.room_id),
                        status=ConnectionStatus.CONNECTED,
                    )
                    connection.disconnect()
                    await self._uow.connections.save(connection)

                # Save changes
                await self._uow.rooms.save(room)
                await self._uow.commit()

                # Publish events from player
                for event in player.events:
                    await self._event_publisher.publish(event)
                player.clear_events()

                # Record metrics
                if self._metrics:
                    self._metrics.increment(
                        "player.disconnected",
                        tags={
                            "game_in_progress": str(game_in_progress).lower(),
                            "bot_activated": str(player.is_bot).lower(),
                        },
                    )

                return HandlePlayerDisconnectResponse(
                    success=True,
                    bot_activated=player.is_bot and not player.original_is_bot,
                    queue_created=queue_created,
                    host_migrated=host_migrated,
                    new_host_name=new_host_name,
                )

        except Exception as e:
            if self._metrics:
                self._metrics.increment("player.disconnect.error")

            raise ApplicationException(
                f"Failed to handle player disconnect: {str(e)}",
                code="DISCONNECT_FAILED",
            )
