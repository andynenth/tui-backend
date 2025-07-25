"""
Use case for marking a player ready for the next phase.

This use case handles players signaling readiness to proceed,
commonly used between phases or after viewing results.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.game import MarkPlayerReadyRequest, MarkPlayerReadyResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException
)
from domain.entities.game import GamePhase
from domain.events.player_events import PlayerReady
from backend.domain.events.game_events import AllPlayersReady, PhaseChanged
from backend.domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class MarkPlayerReadyUseCase(UseCase[MarkPlayerReadyRequest, MarkPlayerReadyResponse]):
    """
    Handles marking players ready for phase transitions.
    
    This use case:
    1. Records player readiness
    2. Checks if all players ready
    3. Triggers phase transitions
    4. Handles round transitions
    5. Emits appropriate events
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
    
    async def execute(self, request: MarkPlayerReadyRequest) -> MarkPlayerReadyResponse:
        """
        Mark player ready for next phase.
        
        Args:
            request: The ready request
            
        Returns:
            Response with readiness status
            
        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If invalid phase
            ConflictException: If already ready
        """
        async with self._uow:
            # Get the game
            game = await self._uow.games.get_by_id(request.game_id)
            if not game:
                raise ResourceNotFoundException("Game", request.game_id)
            
            # Get the room for context
            room = await self._uow.rooms.get_by_id(game.room_id)
            if not room:
                raise ResourceNotFoundException("Room", game.room_id)
            
            # Verify player is in game
            player = None
            for p in game.players:
                if p.id == request.player_id:
                    player = p
                    break
            
            if not player:
                raise ValidationException({
                    "player_id": "Player not in this game"
                })
            
            # Verify valid phase for readiness
            if request.ready_for_phase not in [p.value for p in GamePhase]:
                raise ValidationException({
                    "ready_for_phase": f"Invalid phase: {request.ready_for_phase}"
                })
            
            # Initialize ready tracking if needed
            if not hasattr(game, 'ready_players'):
                game.ready_players = {}
            
            # Check if already ready
            phase_key = f"{game.phase.value}_to_{request.ready_for_phase}"
            if phase_key not in game.ready_players:
                game.ready_players[phase_key] = set()
            
            if request.player_id in game.ready_players[phase_key]:
                raise ConflictException(
                    "mark ready",
                    "Player already marked ready for this transition"
                )
            
            # Mark player ready
            game.ready_players[phase_key].add(request.player_id)
            ready_count = len(game.ready_players[phase_key])
            total_players = len(game.players)
            all_ready = ready_count == total_players
            
            # Determine next phase
            next_phase = None
            if all_ready:
                # Handle phase transitions
                if game.phase == GamePhase.PREPARATION and request.ready_for_phase == "DECLARATION":
                    game.phase = GamePhase.DECLARATION
                    next_phase = GamePhase.DECLARATION.value
                elif game.phase == GamePhase.SCORING and request.ready_for_phase == "PREPARATION":
                    # Start next round
                    if not game.is_game_complete():
                        game.start_new_round()
                        next_phase = GamePhase.PREPARATION.value
                elif game.phase == GamePhase.SCORING and request.ready_for_phase == "ENDED":
                    # Game is complete
                    next_phase = "ENDED"
                
                # Clear ready state for this transition
                game.ready_players[phase_key] = set()
            
            # Save game state
            await self._uow.games.save(game)
            
            # Emit PlayerReady event
            ready_event = PlayerReady(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                player_id=request.player_id,
                player_name=player.name,
                ready_for_phase=request.ready_for_phase,
                ready_count=ready_count,
                total_players=total_players,
                all_players_ready=all_ready
            )
            await self._event_publisher.publish(ready_event)
            
            # If all ready, emit additional events
            if all_ready:
                # Emit AllPlayersReady
                all_ready_event = AllPlayersReady(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    phase=game.phase.value,
                    next_phase=next_phase
                )
                await self._event_publisher.publish(all_ready_event)
                
                # Emit PhaseChanged if phase changed
                if next_phase and next_phase != game.phase.value:
                    phase_event = PhaseChanged(
                        metadata=EventMetadata(user_id=request.user_id),
                        room_id=room.id,
                        game_id=game.id,
                        old_phase=phase_key.split('_to_')[0],
                        new_phase=next_phase,
                        round_number=game.round_number,
                        current_player_id=game.current_player_id
                    )
                    await self._event_publisher.publish(phase_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.player_ready",
                    tags={
                        "current_phase": game.phase.value,
                        "ready_for": request.ready_for_phase,
                        "all_ready": str(all_ready).lower()
                    }
                )
            
            # Create response
            response = MarkPlayerReadyResponse(
                success=True,
                request_id=request.request_id,
                player_id=request.player_id,
                ready_count=ready_count,
                total_players=total_players,
                all_ready=all_ready,
                next_phase=next_phase
            )
            
            logger.info(
                f"Player {player.name} marked ready",
                extra={
                    "game_id": game.id,
                    "player_id": request.player_id,
                    "ready_for": request.ready_for_phase,
                    "ready_count": f"{ready_count}/{total_players}",
                    "all_ready": all_ready
                }
            )
            
            self._log_execution(request, response)
            return response