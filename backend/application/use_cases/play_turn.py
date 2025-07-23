# application/use_cases/play_turn.py
"""
Use case for playing a turn in the game.
"""

import logging
from typing import List

from domain.value_objects.turn_play import TurnPlay
from domain.events.game_events import TurnPlayedEvent
from domain.interfaces.event_publisher import EventPublisher

from ..commands.game_commands import PlayTurnCommand
from ..commands.base import CommandHandler, CommandResult
from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class PlayTurnResult:
    """Result of playing a turn."""
    def __init__(
        self,
        success: bool,
        turn_number: int,
        pieces_played: List[int],
        play_type: str
    ):
        self.success = success
        self.turn_number = turn_number
        self.pieces_played = pieces_played
        self.play_type = play_type


class PlayTurnUseCase(CommandHandler[PlayTurnResult]):
    """
    Use case for playing pieces in a turn.
    
    This orchestrates:
    1. Validating it's the player's turn
    2. Validating the pieces can be played
    3. Executing the play through the state machine
    4. Publishing events
    5. Notifying all players
    """
    
    def __init__(
        self,
        room_repository,  # Will be defined in infrastructure
        game_repository,  # Will be defined in infrastructure
        state_machine_repository,  # Will be defined in infrastructure
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._room_repository = room_repository
        self._game_repository = game_repository
        self._state_machine_repository = state_machine_repository
        self._event_publisher = event_publisher
        self._notification_service = notification_service
    
    def can_handle(self, command) -> bool:
        """Check if this handler can handle the command."""
        return isinstance(command, PlayTurnCommand)
    
    async def handle(self, command: PlayTurnCommand) -> CommandResult[PlayTurnResult]:
        """
        Play pieces in a turn.
        
        Args:
            command: PlayTurnCommand with room ID, player, and pieces
            
        Returns:
            CommandResult with turn info on success
        """
        try:
            # Get the room
            room = await self._room_repository.get(command.room_id)
            if not room:
                return CommandResult.fail("Room not found")
            
            # Check if game is in progress
            if not room.game_id or room.is_game_finished:
                return CommandResult.fail("No game in progress")
            
            # Get the game
            game = await self._game_repository.get(room.game_id)
            if not game:
                return CommandResult.fail("Game not found")
            
            # Get the state machine
            state_machine = await self._state_machine_repository.get(
                command.room_id
            )
            if not state_machine:
                return CommandResult.fail("Game state not found")
            
            # Validate it's in turn phase
            if game.current_phase.value != "TURN":
                return CommandResult.fail(
                    f"Cannot play turn in {game.current_phase.value} phase"
                )
            
            # Get current player from state machine
            current_player = state_machine.get_current_player()
            if current_player != command.player_name:
                return CommandResult.fail(
                    f"It's not your turn. Current player: {current_player}"
                )
            
            # Validate pieces exist
            player = game.get_player(command.player_name)
            if not player:
                return CommandResult.fail("Player not found in game")
            
            # Convert indices to pieces
            try:
                pieces_to_play = [
                    player.pieces[idx] for idx in command.piece_indices
                ]
            except IndexError:
                return CommandResult.fail("Invalid piece indices")
            
            # Execute the play through state machine
            result = await state_machine.process_action(
                "play",
                {
                    "player": command.player_name,
                    "pieces": command.piece_indices
                }
            )
            
            if not result.success:
                return CommandResult.fail(result.error or "Failed to play turn")
            
            # Update the game state
            await self._game_repository.save(game)
            
            # Create turn play value object
            turn_play = TurnPlay(
                player_name=command.player_name,
                pieces=pieces_to_play,
                turn_number=game.turn_number
            )
            
            # Publish turn played event
            event = TurnPlayedEvent(
                game_id=room.game_id,
                room_id=command.room_id,
                player_name=command.player_name,
                pieces_played=[p.value for p in pieces_to_play],
                play_type=turn_play.play_type,
                turn_number=game.turn_number
            )
            await self._event_publisher.publish(event)
            
            # Notify all players
            await self._notification_service.notify_room(
                command.room_id,
                "turn_played",
                {
                    "player": command.player_name,
                    "pieces": [p.value for p in pieces_to_play],
                    "play_type": turn_play.play_type,
                    "turn_number": game.turn_number,
                    "next_player": state_machine.get_current_player()
                }
            )
            
            logger.info(
                f"Player {command.player_name} played {len(pieces_to_play)} "
                f"pieces in room {command.room_id}"
            )
            
            return CommandResult.ok(
                PlayTurnResult(
                    success=True,
                    turn_number=game.turn_number,
                    pieces_played=[p.value for p in pieces_to_play],
                    play_type=turn_play.play_type
                )
            )
            
        except Exception as e:
            logger.error(
                f"Failed to play turn: {str(e)}",
                exc_info=True
            )
            return CommandResult.fail(
                f"Failed to play turn: {str(e)}"
            )