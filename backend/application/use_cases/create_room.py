# application/use_cases/create_room.py
"""
Use case for creating a new game room.
"""

from typing import Optional
import logging

from domain.entities.player import Player
from domain.events.player_events import RoomCreatedEvent
from domain.interfaces.event_publisher import EventPublisher

from ..commands.room_commands import CreateRoomCommand
from ..commands.base import CommandHandler, CommandResult
from ..interfaces.authentication_service import AuthenticationService
from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class RoomCreationResult:
    """Result of room creation."""
    def __init__(self, room_id: str, join_code: str):
        self.room_id = room_id
        self.join_code = join_code


class CreateRoomUseCase(CommandHandler[RoomCreationResult]):
    """
    Use case for creating a new game room.
    
    This orchestrates:
    1. Authenticating the player
    2. Creating the room in the repository
    3. Publishing events
    4. Sending notifications
    """
    
    def __init__(
        self,
        room_repository,  # Will be defined in infrastructure
        auth_service: AuthenticationService,
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._room_repository = room_repository
        self._auth_service = auth_service
        self._event_publisher = event_publisher
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        """Check if this handler can handle the command."""
        return isinstance(command, CreateRoomCommand)
    
    async def handle(self, command: CreateRoomCommand) -> CommandResult[RoomCreationResult]:
        """
        Create a new room.
        
        Args:
            command: CreateRoomCommand with host name and settings
            
        Returns:
            CommandResult with room ID and join code on success
        """
        try:
            # Authenticate the player
            player_identity = await self._auth_service.authenticate_player(
                command.host_name
            )
            if not player_identity:
                player_identity = await self._auth_service.create_guest_player(
                    command.host_name
                )
            
            # Check if player can create a room
            can_create = await self._auth_service.can_perform_action(
                player_identity,
                "create_room"
            )
            if not can_create:
                return CommandResult.fail(
                    "You are not authorized to create a room"
                )
            
            # Create the room
            room = await self._room_repository.create_room(
                host_id=player_identity.player_id,
                host_name=command.host_name,
                settings=command.room_settings
            )
            
            # Create host player
            host_player = Player(command.host_name)
            room.add_player(host_player)
            
            # Save the room
            await self._room_repository.save(room)
            
            # Publish room created event
            event = RoomCreatedEvent(
                room_id=room.id,
                host_name=command.host_name,
                settings=command.room_settings
            )
            await self._event_publisher.publish(event)
            
            # Notify the lobby about the new room
            await self._notification_service.notify_room(
                "lobby",  # Special room ID for lobby
                "room_created",
                {
                    "room_id": room.id,
                    "join_code": room.join_code,
                    "host_name": command.host_name,
                    "player_count": 1,
                    "max_players": 4
                }
            )
            
            logger.info(
                f"Room created: {room.id} by {command.host_name}"
            )
            
            return CommandResult.ok(
                RoomCreationResult(
                    room_id=room.id,
                    join_code=room.join_code
                )
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create room: {str(e)}",
                exc_info=True
            )
            return CommandResult.fail(
                f"Failed to create room: {str(e)}"
            )