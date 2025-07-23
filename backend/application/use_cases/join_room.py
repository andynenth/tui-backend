# application/use_cases/join_room.py
"""
Use case for joining an existing game room.
"""

from typing import Optional
import logging

from domain.entities.player import Player
from domain.events.player_events import PlayerJoinedEvent
from domain.interfaces.event_publisher import EventPublisher

from ..commands.room_commands import JoinRoomCommand
from ..commands.base import CommandHandler, CommandResult
from ..interfaces.authentication_service import AuthenticationService
from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class JoinRoomResult:
    """Result of joining a room."""
    def __init__(self, room_id: str, player_count: int, game_in_progress: bool):
        self.room_id = room_id
        self.player_count = player_count
        self.game_in_progress = game_in_progress


class JoinRoomUseCase(CommandHandler[JoinRoomResult]):
    """
    Use case for joining an existing game room.
    
    This orchestrates:
    1. Authenticating the player
    2. Validating the room exists and has space
    3. Adding the player to the room
    4. Publishing events
    5. Notifying other players
    """
    
    def __init__(
        self,
        room_repository,  # Will be defined in infrastructure
        game_repository,  # Will be defined in infrastructure
        auth_service: AuthenticationService,
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._room_repository = room_repository
        self._game_repository = game_repository
        self._auth_service = auth_service
        self._event_publisher = event_publisher
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        """Check if this handler can handle the command."""
        return isinstance(command, JoinRoomCommand)
    
    async def handle(self, command: JoinRoomCommand) -> CommandResult[JoinRoomResult]:
        """
        Join an existing room.
        
        Args:
            command: JoinRoomCommand with room ID and player name
            
        Returns:
            CommandResult with room info on success
        """
        try:
            # Get the room
            room = await self._room_repository.get(command.room_id)
            if not room:
                return CommandResult.fail("Room not found")
            
            # Check if room is full
            if room.is_full():
                return CommandResult.fail("Room is full")
            
            # Check if player name is already taken
            if room.has_player(command.player_name):
                return CommandResult.fail(
                    f"Player name '{command.player_name}' is already taken"
                )
            
            # Authenticate the player
            player_identity = None
            if command.player_token:
                player_identity = await self._auth_service.validate_token(
                    command.player_token
                )
            
            if not player_identity:
                player_identity = await self._auth_service.create_guest_player(
                    command.player_name
                )
            
            # Check if player can join this room
            can_join = await self._auth_service.can_join_room(
                player_identity,
                command.room_id
            )
            if not can_join:
                return CommandResult.fail(
                    "You are not authorized to join this room"
                )
            
            # Create and add the player
            player = Player(command.player_name)
            room.add_player(player)
            
            # Save the updated room
            await self._room_repository.save(room)
            
            # Get game state if game is in progress
            game_in_progress = False
            if room.game_id:
                game = await self._game_repository.get(room.game_id)
                if game:
                    game_in_progress = not game.is_finished()
            
            # Publish player joined event
            event = PlayerJoinedEvent(
                room_id=command.room_id,
                player_name=command.player_name,
                player_count=room.player_count()
            )
            await self._event_publisher.publish(event)
            
            # Notify other players in the room
            await self._notification_service.notify_room(
                command.room_id,
                "player_joined",
                {
                    "player_name": command.player_name,
                    "player_count": room.player_count(),
                    "players": [p.name for p in room.get_players()]
                },
                exclude_players=[player_identity.player_id]
            )
            
            logger.info(
                f"Player {command.player_name} joined room {command.room_id}"
            )
            
            return CommandResult.ok(
                JoinRoomResult(
                    room_id=command.room_id,
                    player_count=room.player_count(),
                    game_in_progress=game_in_progress
                )
            )
            
        except Exception as e:
            logger.error(
                f"Failed to join room: {str(e)}",
                exc_info=True
            )
            return CommandResult.fail(
                f"Failed to join room: {str(e)}"
            )