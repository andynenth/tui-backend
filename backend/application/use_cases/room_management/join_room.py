"""
Use case for joining an existing room.

This use case handles players joining rooms using either a room code
or direct room ID.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.room_management import JoinRoomRequest, JoinRoomResponse
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    ConflictException
)
from domain.entities.player import Player
from backend.domain.events.room_events import PlayerJoinedRoom, HostChanged
from backend.domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class JoinRoomUseCase(UseCase[JoinRoomRequest, JoinRoomResponse]):
    """
    Handles players joining rooms.
    
    This use case:
    1. Validates the room exists and has space
    2. Ensures player not already in a room
    3. Adds player to the room
    4. Handles host migration if needed
    5. Emits PlayerJoined event
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
    
    async def execute(self, request: JoinRoomRequest) -> JoinRoomResponse:
        """
        Join a room.
        
        Args:
            request: The join request
            
        Returns:
            Response with room info and seat position
            
        Raises:
            ValidationException: If request is invalid
            ResourceNotFoundException: If room not found
            ConflictException: If room full or player in another room
        """
        # Validate request
        self._validate_request(request)
        
        async with self._uow:
            # Check if player already in a room
            existing_room = await self._uow.rooms.find_by_player(request.player_id)
            if existing_room:
                if request.room_id and existing_room.id == request.room_id:
                    # Already in the requested room
                    room_info = self._create_room_info(existing_room)
                    seat_position = self._get_player_seat(existing_room, request.player_id)
                    
                    return JoinRoomResponse(
                        success=True,
                        request_id=request.request_id,
                        room_info=room_info,
                        seat_position=seat_position,
                        is_host=existing_room.host_id == request.player_id
                    )
                else:
                    raise ConflictException(
                        "join room",
                        f"Player is already in room {existing_room.code}"
                    )
            
            # Find the room
            room = None
            if request.room_code:
                room = await self._uow.rooms.get_by_code(request.room_code)
            elif request.room_id:
                room = await self._uow.rooms.get_by_id(request.room_id)
            
            if not room:
                raise ResourceNotFoundException(
                    "Room",
                    request.room_code or request.room_id
                )
            
            # Check if room is joinable
            # Count non-None slots
            filled_slots = sum(1 for slot in room.slots if slot is not None)
            if filled_slots >= room.max_slots:
                raise ConflictException("join room", "Room is full")
            
            if room.game:
                raise ConflictException("join room", "Game in progress")
            
            # Add player to room using room's add_player method
            seat_position = room.add_player(
                name=request.player_name,
                is_bot=False,
                slot=request.seat_preference
            )
            
            # Check if we need host migration
            host_migrated = False
            new_host_id = None
            # Room handles host migration automatically in its methods
            
            # Save the room
            await self._uow.rooms.save(room)
            
            # Create room info
            room_info = self._create_room_info(room)
            is_host = room.host_name == request.player_name
            
            # Emit PlayerJoinedRoom event
            event = PlayerJoinedRoom(
                metadata=EventMetadata(user_id=request.user_id),
                game_id=room.room_id,  # GameEvent uses game_id
                room_id=room.room_id,
                player_id=request.player_id,
                player_name=request.player_name,
                player_slot=f"P{seat_position + 1}",  # Convert to P1, P2, etc.
                is_bot=False
            )
            await self._event_publisher.publish(event)
            
            # Emit HostChanged if needed
            if host_migrated:
                host_event = HostChanged(
                    metadata=EventMetadata(user_id=request.user_id),
                    game_id=room.room_id,  # GameEvent uses game_id
                    room_id=room.room_id,
                    old_host_id="unknown",  # Previous host left
                    old_host_name="Previous Host",
                    new_host_id=new_host_id,
                    new_host_name=request.player_name,
                    reason="Previous host disconnected"
                )
                await self._event_publisher.publish(host_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "room.joined",
                    tags={
                        "room_full": str(room.is_full()).lower(),
                        "host_migrated": str(host_migrated).lower()
                    }
                )
            
            # Create response
            response = JoinRoomResponse(
                success=True,
                request_id=request.request_id,
                room_info=room_info,
                seat_position=seat_position,
                is_host=is_host
            )
            
            logger.info(
                f"Player {request.player_name} joined room {room.room_id}",
                extra={
                    "player_id": request.player_id,
                    "room_id": room.room_id,
                    "seat_position": seat_position,
                    "is_host": is_host
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _validate_request(self, request: JoinRoomRequest) -> None:
        """Validate the join request."""
        errors = {}
        
        if not request.player_id:
            errors["player_id"] = "Player ID is required"
        
        if not request.player_name:
            errors["player_name"] = "Player name is required"
        
        if not request.room_code and not request.room_id:
            errors["room"] = "Either room code or room ID is required"
        
        if request.seat_preference is not None:
            if request.seat_preference < 0 or request.seat_preference > 7:
                errors["seat_preference"] = "Seat preference must be 0-7"
        
        if errors:
            raise ValidationException(errors)
    
    def _is_host_active(self, room) -> bool:
        """Check if the current host is active."""
        for slot in room.slots:
            if slot and slot.name == room.host_name:
                return getattr(slot, 'is_connected', True)
        return False
    
    def _get_player_seat(self, room, player_id: str) -> int:
        """Get player's seat position."""
        for i, slot in enumerate(room.slots):
            if slot and hasattr(slot, 'name') and slot.name == player_id:
                return i
        return -1
    
    def _create_room_info(self, room) -> RoomInfo:
        """Create RoomInfo DTO from room aggregate."""
        players = []
        
        for i, slot in enumerate(room.slots):
            if slot:
                players.append(PlayerInfo(
                    player_id=slot.id,
                    player_name=slot.name,
                    is_bot=slot.is_bot,
                    is_host=slot.id == room.host_id,
                    status=PlayerStatus.CONNECTED if getattr(slot, 'is_connected', True) else PlayerStatus.DISCONNECTED,
                    seat_position=i,
                    score=slot.score,
                    games_played=slot.games_played,
                    games_won=slot.games_won
                ))
        
        return RoomInfo(
            room_id=room.id,
            room_code=room.code,
            room_name=room.name,
            host_id=room.host_id,
            status=RoomStatus.IN_GAME if room.current_game else RoomStatus.WAITING,
            players=players,
            max_players=room.settings.max_players,
            created_at=room.created_at,
            game_in_progress=room.current_game is not None,
            current_game_id=room.current_game.id if room.current_game else None
        )