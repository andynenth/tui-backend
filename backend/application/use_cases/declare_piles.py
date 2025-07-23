# application/use_cases/declare_piles.py
"""
Use case for declaring pile count in declaration phase.
"""

import logging

from domain.events.game_events import DeclarationMadeEvent
from domain.interfaces.event_publisher import EventPublisher

from ..commands.game_commands import DeclareCommand
from ..commands.base import CommandHandler, CommandResult
from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class DeclareResult:
    """Result of making a declaration."""
    def __init__(
        self,
        declaration: int,
        declarations_complete: bool,
        remaining_players: list
    ):
        self.declaration = declaration
        self.declarations_complete = declarations_complete
        self.remaining_players = remaining_players


class DeclarePilesUseCase(CommandHandler[DeclareResult]):
    """
    Use case for declaring pile count.
    
    This orchestrates:
    1. Validating it's the player's turn to declare
    2. Validating the declaration is valid
    3. Recording the declaration
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
        return isinstance(command, DeclareCommand)
    
    async def handle(self, command: DeclareCommand) -> CommandResult[DeclareResult]:
        """
        Make a pile count declaration.
        
        Args:
            command: DeclareCommand with room ID, player, and declaration
            
        Returns:
            CommandResult with declaration info on success
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
            
            # Validate it's in declaration phase
            if game.current_phase.value != "DECLARATION":
                return CommandResult.fail(
                    f"Cannot declare in {game.current_phase.value} phase"
                )
            
            # Get current declarer from state machine
            current_declarer = state_machine.get_current_declarer()
            if current_declarer != command.player_name:
                return CommandResult.fail(
                    f"It's not your turn to declare. Current: {current_declarer}"
                )
            
            # Validate declaration value
            if not 0 <= command.declaration <= 8:
                return CommandResult.fail(
                    "Declaration must be between 0 and 8"
                )
            
            # Execute the declaration through state machine
            result = await state_machine.process_action(
                "declare",
                {
                    "player": command.player_name,
                    "value": command.declaration
                }
            )
            
            if not result.success:
                return CommandResult.fail(
                    result.error or "Failed to make declaration"
                )
            
            # Update the game state
            await self._game_repository.save(game)
            
            # Get remaining players who need to declare
            remaining_players = state_machine.get_remaining_declarers()
            declarations_complete = len(remaining_players) == 0
            
            # Publish declaration made event
            event = DeclarationMadeEvent(
                game_id=room.game_id,
                room_id=command.room_id,
                player_name=command.player_name,
                declaration=command.declaration,
                round_number=game.round_number
            )
            await self._event_publisher.publish(event)
            
            # Notify all players
            notification_data = {
                "player": command.player_name,
                "declaration": command.declaration,
                "declarations_complete": declarations_complete
            }
            
            if not declarations_complete:
                notification_data["next_declarer"] = state_machine.get_current_declarer()
                notification_data["remaining_players"] = remaining_players
            
            await self._notification_service.notify_room(
                command.room_id,
                "declaration_made",
                notification_data
            )
            
            logger.info(
                f"Player {command.player_name} declared {command.declaration} "
                f"in room {command.room_id}"
            )
            
            return CommandResult.ok(
                DeclareResult(
                    declaration=command.declaration,
                    declarations_complete=declarations_complete,
                    remaining_players=remaining_players
                )
            )
            
        except Exception as e:
            logger.error(
                f"Failed to make declaration: {str(e)}",
                exc_info=True
            )
            return CommandResult.fail(
                f"Failed to make declaration: {str(e)}"
            )