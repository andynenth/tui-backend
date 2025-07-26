"""
Use case for making pile declarations.

This use case handles players declaring how many piles they expect
to capture during the round.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.game import DeclareRequest, DeclareResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException
)
from domain.entities.game import GamePhase
from domain.events.player_events import PlayerDeclaredPiles
from domain.events.game_events import PhaseChanged
from domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class DeclareUseCase(UseCase[DeclareRequest, DeclareResponse]):
    """
    Handles player pile declarations.
    
    This use case:
    1. Validates it's the declaration phase
    2. Validates the declaration is legal
    3. Records the player's declaration
    4. Checks if all players have declared
    5. Transitions to turn phase if complete
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
    
    async def execute(self, request: DeclareRequest) -> DeclareResponse:
        """
        Make a pile declaration.
        
        Args:
            request: The declaration request
            
        Returns:
            Response with declaration result
            
        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If declaration invalid
            ConflictException: If not player's turn or wrong phase
        """
        # Validate pile count
        if request.pile_count < 0 or request.pile_count > 8:
            raise ValidationException({
                "pile_count": "Pile count must be between 0 and 8"
            })
        
        async with self._uow:
            # Get the game
            game = await self._uow.games.get_by_id(request.game_id)
            if not game:
                raise ResourceNotFoundException("Game", request.game_id)
            
            # Get the room for context
            room = await self._uow.rooms.get_by_id(game.room_id)
            if not room:
                raise ResourceNotFoundException("Room", game.room_id)
            
            # Verify player is in the game
            player = None
            for p in game.players:
                if p.id == request.player_id:
                    player = p
                    break
            
            if not player:
                raise ValidationException({
                    "player_id": "Player not in this game"
                })
            
            # Verify it's declaration phase
            if game.phase != GamePhase.DECLARATION:
                raise ConflictException(
                    "make declaration",
                    f"Game is in {game.phase} phase, not declaration"
                )
            
            # Check if player already declared
            if hasattr(game, 'declarations') and request.player_id in game.declarations:
                raise ConflictException(
                    "make declaration",
                    "Player has already declared"
                )
            
            # Apply declaration rules
            existing_declarations = getattr(game, 'declarations', {})
            total_declared = sum(existing_declarations.values())
            remaining_players = len(game.players) - len(existing_declarations)
            
            # If last player to declare, ensure total ≠ 8
            if remaining_players == 1:
                if total_declared + request.pile_count == 8:
                    raise ValidationException({
                        "pile_count": f"Total declarations cannot equal 8. Current total: {total_declared}"
                    })
            
            # Record declaration
            game.declare_piles(request.player_id, request.pile_count)
            
            # Check if all players have declared
            all_declared = len(game.declarations) == len(game.players)
            next_player_id = None
            
            if not all_declared:
                # Find next player to declare
                for p in game.players:
                    if p.id not in game.declarations:
                        next_player_id = p.id
                        break
            else:
                # All declared - transition to turn phase
                game.start_turn_phase()
                next_player_id = game.current_player_id
            
            # Save the game
            await self._uow.games.save(game)
            
            # Calculate total declarations
            total_declared = sum(game.declarations.values())
            
            # Emit PlayerDeclaredPiles event
            declare_event = PlayerDeclaredPiles(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                player_id=request.player_id,
                player_name=player.name,
                declared_piles=request.pile_count,
                declarations_complete=all_declared,
                total_declared=total_declared if all_declared else None
            )
            await self._event_publisher.publish(declare_event)
            
            # If all declared, emit phase change
            if all_declared:
                phase_event = PhaseChanged(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    old_phase=GamePhase.DECLARATION.value,
                    new_phase=GamePhase.TURN.value,
                    round_number=game.round_number,
                    current_player_id=game.current_player_id
                )
                await self._event_publisher.publish(phase_event)
                
                # TODO: emit AllPlayersReady event when it's created
                # ready_event = AllPlayersReady(
                #     metadata=EventMetadata(user_id=request.user_id),
                #     room_id=room.id,
                #     game_id=game.id,
                #     phase=GamePhase.DECLARATION.value,
                #     next_phase=GamePhase.TURN.value
                # )
                # await self._event_publisher.publish(ready_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.declaration_made",
                    tags={
                        "pile_count": str(request.pile_count),
                        "all_declared": str(all_declared).lower(),
                        "is_last_player": str(remaining_players == 1).lower()
                    }
                )
            
            # Create response
            response = DeclareResponse(
                success=True,
                request_id=request.request_id,
                player_id=request.player_id,
                declared_piles=request.pile_count,
                all_declared=all_declared,
                next_player_id=next_player_id,
                total_declared=total_declared if all_declared else None
            )
            
            logger.info(
                f"Player {player.name} declared {request.pile_count} piles",
                extra={
                    "game_id": game.id,
                    "player_id": request.player_id,
                    "pile_count": request.pile_count,
                    "all_declared": all_declared,
                    "total_declared": total_declared
                }
            )
            
            self._log_execution(request, response)
            return response