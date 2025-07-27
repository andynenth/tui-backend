"""
Use case for removing a player from a room.

This use case handles hosts removing players (including bots) from their room.
"""

import logging
from typing import Optional
from datetime import datetime

from application.base import UseCase
from application.dto.room_management import RemovePlayerRequest, RemovePlayerResponse
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    AuthorizationException,
    ConflictException,
    ValidationException
)
from domain.events.room_events import PlayerRemoved
from domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class RemovePlayerUseCase(UseCase[RemovePlayerRequest, RemovePlayerResponse]):
    """
    Removes a player from a room.
    
    This use case:
    1. Validates requester is host
    2. Ensures target player exists
    3. Prevents removal during active game
    4. Removes player from room
    5. Emits appropriate event
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
    
    async def execute(self, request: RemovePlayerRequest) -> RemovePlayerResponse:
        """
        Remove a player from the room.
        
        Args:
            request: The removal request
            
        Returns:
            Response with removal details
            
        Raises:
            ResourceNotFoundException: If room or player not found
            AuthorizationException: If requester not host
            ConflictException: If cannot remove player
            ValidationException: If request invalid
        """
        # Validate request
        self._validate_request(request)
        
        async with self._uow:
            # Get the room
            room = await self._uow.rooms.get_by_id(request.room_id)
            if not room:
                raise ResourceNotFoundException("Room", request.room_id)
            
            # Check authorization - must be host
            if room.host_name != request.requesting_player_id:
                raise AuthorizationException(
                    "remove player",
                    f"room {request.room_id}"
                )
            
            # Cannot remove self (host)
            if request.target_player_id == request.requesting_player_id:
                raise ConflictException(
                    "remove player",
                    "Host cannot remove themselves"
                )
            
            # Check if game in progress
            if room.game:
                raise ConflictException(
                    "remove player",
                    "Cannot remove players while game is in progress"
                )
            
            # Find target player
            target_slot = None
            slot_index = None
            for i, slot in enumerate(room.slots):
                if slot and hasattr(slot, 'name') and slot.name == request.target_player_id:
                    target_slot = slot
                    slot_index = i
                    break
            
            if not target_slot:
                raise ResourceNotFoundException("Player", request.target_player_id)
            
            # Store player info before removal
            was_bot = target_slot.is_bot
            player_name = target_slot.name
            
            # Remove player from room
            room.remove_player(request.target_player_id)
            
            # Save the room
            await self._uow.rooms.save(room)
            
            # Create updated room info
            room_info = self._create_room_info(room)
            
            # Emit PlayerRemoved event for both bots and players
            event = PlayerRemoved(
                metadata=EventMetadata(user_id=request.user_id),
                game_id=room.room_id,  # GameEvent uses game_id
                room_id=room.room_id,
                removed_player_id=request.target_player_id,
                removed_player_name=player_name,
                removed_player_slot=f"P{slot_index + 1}",
                removed_by_id=request.requesting_player_id,
                removed_by_name=room.host_name  # Assuming host is removing
            )
            
            await self._event_publisher.publish(event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "player.removed",
                    tags={
                        "was_bot": str(was_bot).lower(),
                        "reason": "host_action"
                    }
                )
            
            # Create response
            response = RemovePlayerResponse(
                success=True,
                request_id=request.request_id,
                removed_player_id=request.target_player_id,
                room_info=room_info,
                was_bot=was_bot
            )
            
            logger.info(
                f"Player {player_name} removed from room {room.room_id} by host",
                extra={
                    "removed_player_id": request.target_player_id,
                    "room_id": room.room_id,
                    "was_bot": was_bot,
                    "removed_by": request.requesting_player_id
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _validate_request(self, request: RemovePlayerRequest) -> None:
        """Validate the removal request."""
        errors = {}
        
        if not request.room_id:
            errors["room_id"] = "Room ID is required"
        
        if not request.requesting_player_id:
            errors["requesting_player_id"] = "Requesting player ID is required"
        
        if not request.target_player_id:
            errors["target_player_id"] = "Target player ID is required"
        
        if errors:
            raise ValidationException(errors)
    
    def _create_room_info(self, room) -> RoomInfo:
        """Create RoomInfo DTO from room aggregate."""
        players = []
        
        for i, slot in enumerate(room.slots):
            if slot:
                players.append(PlayerInfo(
                    player_id=f"{room.room_id}_p{i}",
                    player_name=slot.name,
                    is_bot=slot.is_bot,
                    is_host=slot.name == room.host_name,
                    status=PlayerStatus.CONNECTED if getattr(slot, 'is_connected', True) else PlayerStatus.DISCONNECTED,
                    seat_position=i,
                    score=0,
                    games_played=0,
                    games_won=0
                ))
        
        return RoomInfo(
            room_id=room.room_id,
            room_code=room.room_id,
            room_name=f"{room.host_name}'s Room",
            host_id=f"{room.room_id}_p0",
            status=RoomStatus.WAITING,
            players=players,
            max_players=room.max_slots,
            created_at=datetime.utcnow(),
            game_in_progress=False,
            current_game_id=None
        )