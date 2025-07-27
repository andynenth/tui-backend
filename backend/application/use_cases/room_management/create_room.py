"""
Use case for creating a new room.

This use case handles the creation of game rooms where players
can gather before starting a game.
"""

import logging
from typing import Optional
from datetime import datetime
import random
import string

from application.base import UseCase
from application.dto.room_management import CreateRoomRequest, CreateRoomResponse
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import ValidationException, ConflictException
from domain.entities.room import Room, RoomCreated
from domain.entities.player import Player
from domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class CreateRoomUseCase(UseCase[CreateRoomRequest, CreateRoomResponse]):
    """
    Creates a new game room.
    
    This use case:
    1. Validates room parameters
    2. Creates a new Room aggregate
    3. Adds the host player
    4. Generates a unique join code
    5. Emits RoomCreated event
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
    
    async def execute(self, request: CreateRoomRequest) -> CreateRoomResponse:
        """
        Create a new room.
        
        Args:
            request: The room creation request
            
        Returns:
            Response with room info and join code
            
        Raises:
            ValidationException: If request is invalid
            ConflictException: If player already in a room
        """
        # Validate request
        self._validate_request(request)
        
        async with self._uow:
            # Check if player already in a room
            existing_room = await self._uow.rooms.find_by_player(request.host_player_id)
            if existing_room:
                raise ConflictException(
                    "create room",
                    f"Player is already in room {existing_room.code}"
                )
            
            # Generate unique room code
            room_code = await self._generate_unique_code()
            
            # Create the room using a simple constructor
            room_name = request.room_name or f"{request.host_player_name}'s Room"
            room = Room(
                room_id=room_code,  # Use code as ID for simplicity
                host_name=request.host_player_name,
                max_slots=request.max_players or 4
            )
            
            # Host is already added in Room's __post_init__
            # Just create a Player object for the response
            host_player = Player(
                name=request.host_player_name,
                is_bot=False
            )
            
            # Save the room
            await self._uow.rooms.save(room)
            
            # Create room info for response
            room_info = self._create_room_info(room, host_player)
            
            # Emit RoomCreated event
            event = RoomCreated(
                metadata=EventMetadata(user_id=getattr(request, 'user_id', None)),
                room_id=room.room_id,
                host_name=request.host_player_name,
                total_slots=request.max_players or 4
            )
            await self._event_publisher.publish(event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "room.created",
                    tags={
                        "win_condition": request.win_condition_type,
                        "max_players": str(request.max_players),
                        "is_private": str(request.is_private).lower()
                    }
                )
            
            # Create response
            response = CreateRoomResponse(
                success=True,
                request_id=getattr(request, 'request_id', None),
                room_info=room_info,
                join_code=room_code
            )
            
            logger.info(
                f"Room {room_code} created by {request.host_player_name}",
                extra={
                    "room_id": room.room_id,
                    "room_code": room_code,
                    "host_id": request.host_player_id
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _validate_request(self, request: CreateRoomRequest) -> None:
        """Validate the room creation request."""
        errors = {}
        
        if not request.host_player_id:
            errors["host_player_id"] = "Host player ID is required"
        
        if not request.host_player_name:
            errors["host_player_name"] = "Host player name is required"
        
        if request.max_players < 2 or request.max_players > 8:
            errors["max_players"] = "Max players must be between 2 and 8"
        
        if request.win_condition_type not in ["score", "rounds"]:
            errors["win_condition_type"] = "Win condition must be 'score' or 'rounds'"
        
        if request.win_condition_value <= 0:
            errors["win_condition_value"] = "Win condition value must be positive"
        
        if errors:
            raise ValidationException(errors)
    
    async def _generate_unique_code(self) -> str:
        """Generate a unique room code."""
        max_attempts = 10
        
        for _ in range(max_attempts):
            # Generate 6-character code
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            ))
            
            # Check if code exists
            existing = await self._uow.rooms.get_by_code(code)
            if not existing:
                return code
        
        # Fallback - add timestamp
        import time
        return f"{code}{int(time.time()) % 1000}"
    
    def _create_room_info(self, room: Room, host_player: Player) -> RoomInfo:
        """Create RoomInfo DTO from domain entities."""
        # Create player info for all slots
        players = []
        for i, slot in enumerate(room.slots):
            if slot:
                player_info = PlayerInfo(
                    player_id=f"{room.room_id}_p{i}",
                    player_name=slot.name,
                    is_bot=slot.is_bot,
                    is_host=(i == 0),  # First slot is host
                    status=PlayerStatus.CONNECTED,
                    seat_position=i,
                    score=0,
                    games_played=0,
                    games_won=0
                )
                players.append(player_info)
        
        return RoomInfo(
            room_id=room.room_id,
            room_code=room.room_id,  # Using room_id as code
            room_name=f"{room.host_name}'s Room",
            host_id=f"{room.room_id}_p0",
            status=RoomStatus.WAITING,
            players=players,
            max_players=room.max_slots,
            created_at=datetime.utcnow(),
            game_in_progress=False,
            current_game_id=None
        )