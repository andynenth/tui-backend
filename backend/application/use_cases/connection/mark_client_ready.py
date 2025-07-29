"""
Use case for marking a client as ready.

When a client connects or reconnects, it needs to signal that it's
ready to receive game updates. This use case handles that signal.
"""

from typing import Optional
import logging
from datetime import datetime

from application.base import UseCase
from application.dto.connection import MarkClientReadyRequest, MarkClientReadyResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import ResourceNotFoundException, ConflictException
from domain.events.connection_events import ClientReady
from domain.events.base import EventMetadata
from application.utils import PropertyMapper

logger = logging.getLogger(__name__)


class MarkClientReadyUseCase(UseCase[MarkClientReadyRequest, MarkClientReadyResponse]):
    """
    Marks a client as ready to receive updates.
    
    This use case:
    1. Validates the player exists in the room
    2. Updates the player's ready status
    3. Emits a PlayerReady event
    4. Triggers game start if all players ready
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the use case.
        
        Args:
            unit_of_work: Unit of work for data access
            event_publisher: Publisher for domain events
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._metrics = metrics
    
    async def execute(self, request: MarkClientReadyRequest) -> MarkClientReadyResponse:
        """
        Mark a client as ready.
        
        Args:
            request: The ready request
            
        Returns:
            Response indicating success
            
        Raises:
            ResourceNotFoundException: If room or player not found
            ConflictException: If player already ready
        """
        # Special handling for lobby connections
        if request.room_id == "lobby":
            logger.info(
                f"Client ready for lobby connection: player_id={request.player_id}"
            )
            
            # Record metrics for lobby
            if self._metrics:
                self._metrics.increment(
                    "player.ready",
                    tags={
                        "room_id": "lobby",
                        "client_version": request.client_version or "unknown"
                    }
                )
            
            # Return success response for lobby
            return MarkClientReadyResponse(
                success=True,
                request_id=request.request_id,
                player_id=request.player_id,
                is_ready=True,
                room_state_provided=False
            )
        
        async with self._uow:
            # Get the room
            room = await self._uow.rooms.get_by_id(request.room_id)
            if not room:
                raise ResourceNotFoundException("Room", request.room_id)
            
            # Find the player in the room
            player_slot = None
            slot_index = None
            for i, slot in enumerate(room.slots):
                if slot and PropertyMapper.generate_player_id(room.room_id, i) == request.player_id:
                    player_slot = slot
                    slot_index = i
                    break
            
            if not player_slot:
                raise ResourceNotFoundException("Player", request.player_id)
            
            # Check if already ready
            if hasattr(player_slot, 'is_ready') and player_slot.is_ready:
                raise ConflictException(
                    "mark player ready",
                    "Player is already marked as ready"
                )
            
            # Mark player as ready
            player_slot.is_ready = True
            player_slot.is_connected = True
            
            # Store client capabilities if provided
            if request.client_capabilities:
                player_slot.client_capabilities = request.client_capabilities
            
            # Save the room
            await self._uow.rooms.save(room)
            
            # Emit ClientReady event
            event = ClientReady(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=request.room_id,
                player_id=request.player_id,
                player_name=player_slot.name,
                ready_time=datetime.utcnow(),
                client_version=request.client_version
            )
            await self._event_publisher.publish(event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "player.ready",
                    tags={
                        "room_id": request.room_id,
                        "client_version": request.client_version or "unknown"
                    }
                )
            
            # Create response
            response = MarkClientReadyResponse(
                success=True,
                request_id=request.request_id,
                player_id=request.player_id,
                is_ready=True,
                room_state_provided=True
            )
            
            logger.info(
                f"Player {request.player_id} marked as ready in room {request.room_id}",
                extra={
                    "player_id": request.player_id,
                    "room_id": request.room_id,
                    "all_ready": self._check_all_ready(room)
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _check_all_ready(self, room) -> bool:
        """Check if all players in the room are ready."""
        for slot in room.slots:
            if slot and (not hasattr(slot, 'is_ready') or not slot.is_ready):
                return False
        return True