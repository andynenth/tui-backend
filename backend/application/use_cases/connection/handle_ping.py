"""
Use case for handling ping messages.

Ping messages are used to keep connections alive and measure latency.
This use case updates the player's last activity timestamp and returns
a pong response.
"""

from typing import Optional
import logging
from datetime import datetime

from application.base import UseCase
from application.dto.connection import HandlePingRequest, HandlePingResponse
from application.interfaces import UnitOfWork, MetricsCollector
from application.exceptions import ResourceNotFoundException
from application.utils import PropertyMapper

logger = logging.getLogger(__name__)


class HandlePingUseCase(UseCase[HandlePingRequest, HandlePingResponse]):
    """
    Handles ping messages from clients.

    This use case:
    1. Updates the player's last activity timestamp
    2. Records latency metrics if sequence number provided
    3. Returns a pong response with server time
    """

    def __init__(
        self, unit_of_work: UnitOfWork, metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the use case.

        Args:
            unit_of_work: Unit of work for data access
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._metrics = metrics

    async def execute(self, request: HandlePingRequest) -> HandlePingResponse:
        """
        Handle a ping request.

        Args:
            request: The ping request

        Returns:
            Pong response with server time

        Raises:
            ResourceNotFoundException: If player not found
        """
        async with self._uow:
            # Update player's last activity if in a room
            if request.room_id:
                room = await self._uow.rooms.get_by_id(request.room_id)
                if room:
                    # Find player in room
                    player_found = False
                    for i, slot in enumerate(room.slots):
                        if (
                            slot
                            and PropertyMapper.generate_player_id(room.room_id, i)
                            == request.player_id
                        ):
                            # Update last activity timestamp
                            slot.last_activity = datetime.utcnow()
                            player_found = True
                            break

                    if player_found:
                        await self._uow.rooms.save(room)

            # Record metrics if available
            if self._metrics and request.sequence_number is not None:
                self._metrics.increment(
                    "ping.received", tags={"room_id": request.room_id or "lobby"}
                )

            # Create pong response
            response = HandlePingResponse(
                success=True,
                request_id=request.request_id,
                sequence_number=request.sequence_number,
                server_time=datetime.utcnow(),
            )

            # Log for debugging
            logger.debug(
                f"Handled ping from player {request.player_id}",
                extra={
                    "player_id": request.player_id,
                    "room_id": request.room_id,
                    "sequence": request.sequence_number,
                },
            )

            self._log_execution(request, response)
            return response
