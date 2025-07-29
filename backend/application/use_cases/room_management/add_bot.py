"""
Use case for adding a bot player to a room.

This use case handles adding AI-controlled players to fill empty slots
in a room.
"""

import logging
from typing import Optional
import random

from application.base import UseCase
from application.dto.room_management import AddBotRequest, AddBotResponse
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.interfaces import UnitOfWork, EventPublisher, BotService, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    AuthorizationException,
    ConflictException,
    ValidationException
)
from domain.entities.player import Player
from domain.events.room_events import BotAdded
from domain.events.base import EventMetadata
from datetime import datetime

logger = logging.getLogger(__name__)


class AddBotUseCase(UseCase[AddBotRequest, AddBotResponse]):
    """
    Adds a bot player to a room.
    
    This use case:
    1. Validates requester is host
    2. Checks room has space
    3. Creates bot player
    4. Adds bot to room
    5. Emits BotAdded event
    """
    
    # Bot name pool
    BOT_NAMES = [
        "AlphaBot", "BetaBot", "GammaBot", "DeltaBot",
        "EpsilonBot", "ZetaBot", "EtaBot", "ThetaBot",
        "IotaBot", "KappaBot", "LambdaBot", "MuBot",
        "NuBot", "XiBot", "OmicronBot", "PiBot"
    ]
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        bot_service: BotService,
        metrics: Optional[MetricsCollector] = None
    ):
        """
        Initialize the use case.
        
        Args:
            unit_of_work: Unit of work for data access
            event_publisher: Publisher for domain events
            bot_service: Service for bot operations
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._bot_service = bot_service
        self._metrics = metrics
    
    async def execute(self, request: AddBotRequest) -> AddBotResponse:
        """
        Add a bot to the room.
        
        Args:
            request: The add bot request
            
        Returns:
            Response with bot and room info
            
        Raises:
            ResourceNotFoundException: If room not found
            AuthorizationException: If requester not host
            ConflictException: If room full or bots disabled
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
            if room.host_id != request.requesting_player_id:
                raise AuthorizationException(
                    "add bot",
                    f"room {request.room_id}"
                )
            
            # Bots are always allowed in this implementation
            
            # Check if room has space
            if room.is_full():
                raise ConflictException("add bot", "Room is full")
            
            # Check if game in progress
            if room.game:
                raise ConflictException(
                    "add bot",
                    "Cannot add bot while game is in progress"
                )
            
            # Create bot player
            bot_id = await self._bot_service.create_bot(request.bot_difficulty)
            bot_name = request.bot_name or self._generate_bot_name(room)
            
            # Add bot to room
            try:
                seat_position = room.add_player(bot_name, is_bot=True, slot=request.seat_position)
            except ValueError as e:
                # Convert domain exception to application exception
                if "occupied" in str(e).lower():
                    raise ConflictException("add bot", f"Slot {request.seat_position} is already occupied")
                else:
                    raise ConflictException("add bot", str(e))
            
            # Save the room
            await self._uow.rooms.save(room)
            
            # Create bot info
            bot_info = PlayerInfo(
                player_id=bot_id,
                player_name=bot_name,
                is_bot=True,
                is_host=False,
                status=PlayerStatus.CONNECTED,
                seat_position=seat_position,
                score=0,
                games_played=0,
                games_won=0
            )
            
            # Create updated room info
            room_info = self._create_room_info(room)
            
            # Emit BotAdded event
            event = BotAdded(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.room_id,
                bot_id=bot_id,
                bot_name=bot_name,
                player_slot=f"P{seat_position + 1}",
                added_by_id=request.requesting_player_id,
                added_by_name=room.host_name  # Host is adding the bot
            )
            await self._event_publisher.publish(event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "bot.added",
                    tags={
                        "difficulty": request.bot_difficulty,
                        "room_full": str(room.is_full()).lower()
                    }
                )
            
            # Create response
            response = AddBotResponse(
                bot_info=bot_info,
                room_info=room_info
            )
            
            logger.info(
                f"Bot {bot_name} added to room {room.room_id}",
                extra={
                    "bot_id": bot_id,
                    "room_id": room.room_id,
                    "difficulty": request.bot_difficulty,
                    "seat_position": seat_position
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _validate_request(self, request: AddBotRequest) -> None:
        """Validate the add bot request."""
        errors = {}
        
        if not request.room_id:
            errors["room_id"] = "Room ID is required"
        
        if not request.requesting_player_id:
            errors["requesting_player_id"] = "Requesting player ID is required"
        
        if request.bot_difficulty not in ["easy", "medium", "hard"]:
            errors["bot_difficulty"] = "Bot difficulty must be easy, medium, or hard"
        
        if request.seat_position is not None:
            if request.seat_position < 0 or request.seat_position > 7:
                errors["seat_position"] = "Seat position must be 0-7"
        
        if errors:
            raise ValidationException(errors)
    
    def _generate_bot_name(self, room) -> str:
        """Generate a unique bot name for the room."""
        # Get existing bot names in room
        existing_names = set()
        for slot in room.slots:
            if slot and slot.is_bot:
                existing_names.add(slot.name)
        
        # Find available name
        available_names = [
            name for name in self.BOT_NAMES
            if name not in existing_names
        ]
        
        if available_names:
            return random.choice(available_names)
        else:
            # Fallback with number suffix
            import time
            return f"Bot{int(time.time()) % 1000}"
    
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
                    status=PlayerStatus.CONNECTED,
                    seat_position=i,
                    score=slot.score,
                    games_played=0,  # Not tracked in Player entity
                    games_won=0      # Not tracked in Player entity
                ))
        
        return RoomInfo(
            room_id=room.room_id,
            room_code=room.room_id,
            room_name=f"{room.host_name}'s Room",
            host_id=room.host_id,
            status=RoomStatus.WAITING,
            players=players,
            max_players=room.max_slots,
            created_at=datetime.utcnow(),
            game_in_progress=False,
            current_game_id=None
        )