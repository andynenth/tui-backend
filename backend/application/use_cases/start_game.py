# application/use_cases/start_game.py
"""
Use case for starting a game in a room.
"""

import logging
from typing import List

from domain.entities.game import Game
from domain.entities.player import Player
from domain.events.game_events import GameStartedEvent
from domain.interfaces.event_publisher import EventPublisher

from ..commands.game_commands import StartGameCommand
from ..commands.base import CommandHandler, CommandResult
from ..interfaces.authentication_service import AuthenticationService
from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class StartGameResult:
    """Result of starting a game."""
    def __init__(self, game_id: str, players: List[str]):
        self.game_id = game_id
        self.players = players


class StartGameUseCase(CommandHandler[StartGameResult]):
    """
    Use case for starting a game in a room.
    
    This orchestrates:
    1. Validating the room is ready for a game
    2. Creating a new game instance
    3. Transitioning to the first phase
    4. Publishing events
    5. Notifying all players
    """
    
    def __init__(
        self,
        room_repository,  # Will be defined in infrastructure
        game_repository,  # Will be defined in infrastructure
        auth_service: AuthenticationService,
        event_publisher: EventPublisher,
        notification_service: NotificationService,
        state_machine_factory  # Will be defined in infrastructure
    ):
        self._room_repository = room_repository
        self._game_repository = game_repository
        self._auth_service = auth_service
        self._event_publisher = event_publisher
        self._notification_service = notification_service
        self._state_machine_factory = state_machine_factory
    
    def can_handle(self, command) -> bool:
        """Check if this handler can handle the command."""
        return isinstance(command, StartGameCommand)
    
    async def handle(self, command: StartGameCommand) -> CommandResult[StartGameResult]:
        """
        Start a game in a room.
        
        Args:
            command: StartGameCommand with room ID and requesting player
            
        Returns:
            CommandResult with game info on success
        """
        try:
            # Get the room
            room = await self._room_repository.get(command.room_id)
            if not room:
                return CommandResult.fail("Room not found")
            
            # Verify the requesting player is the host
            if room.host_name != command.requesting_player:
                return CommandResult.fail("Only the host can start the game")
            
            # Check if game is already in progress
            if room.game_id and not room.is_game_finished:
                return CommandResult.fail("Game is already in progress")
            
            # Validate room has enough players
            if room.player_count() < 2:  # Minimum 2 players
                return CommandResult.fail(
                    f"Need at least 2 players to start. Currently have {room.player_count()}"
                )
            
            # Create game with players from room
            game_players = [
                Player(name) for name in room.get_player_names()
            ]
            
            game = Game(
                players=game_players,
                max_score=room.settings.get("max_score", 50)
            )
            
            # Save the game
            game_id = await self._game_repository.create(game)
            game.id = game_id
            
            # Update room with game ID
            room.game_id = game_id
            room.is_game_finished = False
            await self._room_repository.save(room)
            
            # Create and start state machine
            state_machine = self._state_machine_factory.create(
                game=game,
                room_id=command.room_id
            )
            await state_machine.start()
            
            # Publish game started event
            event = GameStartedEvent(
                game_id=game_id,
                room_id=command.room_id,
                players=[p.name for p in game_players],
                max_score=game.max_score
            )
            await self._event_publisher.publish(event)
            
            # Notify all players
            await self._notification_service.notify_room(
                command.room_id,
                "game_started",
                {
                    "game_id": game_id,
                    "players": [p.name for p in game_players],
                    "max_score": game.max_score,
                    "current_phase": game.current_phase.value
                }
            )
            
            logger.info(
                f"Game {game_id} started in room {command.room_id} "
                f"with {len(game_players)} players"
            )
            
            return CommandResult.ok(
                StartGameResult(
                    game_id=game_id,
                    players=[p.name for p in game_players]
                )
            )
            
        except Exception as e:
            logger.error(
                f"Failed to start game: {str(e)}",
                exc_info=True
            )
            return CommandResult.fail(
                f"Failed to start game: {str(e)}"
            )