"""
Use case for accepting a redeal request.

This use case handles players voting to accept a redeal when
another player has requested it due to a weak hand.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.game import AcceptRedealRequest, AcceptRedealResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException
)
from domain.entities.game import GamePhase
from backend.domain.events.game_events import (
    RedealAccepted,
    RedealApproved,
    RedealExecuted,
    PiecesDealt
)
from backend.domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class AcceptRedealUseCase(UseCase[AcceptRedealRequest, AcceptRedealResponse]):
    """
    Handles accepting a redeal vote.
    
    This use case:
    1. Records the acceptance vote
    2. Checks if all players have voted
    3. Executes redeal if approved
    4. Transitions to appropriate phase
    5. Emits relevant events
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
    
    async def execute(self, request: AcceptRedealRequest) -> AcceptRedealResponse:
        """
        Accept a redeal vote.
        
        Args:
            request: The acceptance request
            
        Returns:
            Response with voting status
            
        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If invalid redeal ID
            ConflictException: If already voted or no active redeal
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
            
            # Verify there's an active redeal
            if not hasattr(game, 'active_redeal_id') or not game.active_redeal_id:
                raise ConflictException(
                    "accept redeal",
                    "No active redeal vote"
                )
            
            # Verify redeal ID matches
            if game.active_redeal_id != request.redeal_id:
                raise ValidationException({
                    "redeal_id": "Invalid or expired redeal ID"
                })
            
            # Verify player hasn't already voted
            if request.player_id in game.redeal_votes:
                raise ConflictException(
                    "accept redeal",
                    "Player has already voted"
                )
            
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
            
            # Record acceptance vote
            game.redeal_votes[request.player_id] = True
            votes_collected = len(game.redeal_votes)
            votes_required = len(game.players)
            
            # Check if all have voted and all accepted
            redeal_approved = False
            new_hands_dealt = False
            
            if votes_collected == votes_required:
                # Check if all votes are accepts
                all_accepted = all(game.redeal_votes.values())
                
                if all_accepted:
                    redeal_approved = True
                    
                    # Execute redeal
                    game.execute_redeal()
                    new_hands_dealt = True
                    
                    # Clear redeal state
                    game.active_redeal_id = None
                    game.redeal_votes = {}
                    
                    # Move to declaration phase
                    game.phase = GamePhase.DECLARATION
            
            # Save game state
            await self._uow.games.save(game)
            
            # Emit RedealAccepted event
            accept_event = RedealAccepted(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                redeal_id=request.redeal_id,
                player_id=request.player_id,
                player_name=player.name,
                votes_collected=votes_collected,
                votes_required=votes_required
            )
            await self._event_publisher.publish(accept_event)
            
            # If redeal approved, emit additional events
            if redeal_approved:
                # Emit RedealApproved
                approved_event = RedealApproved(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    redeal_id=request.redeal_id,
                    total_votes=votes_required,
                    accept_votes=votes_collected
                )
                await self._event_publisher.publish(approved_event)
                
                # Emit RedealExecuted
                executed_event = RedealExecuted(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    redeal_id=request.redeal_id,
                    round_number=game.round_number,
                    new_starting_player_id=game.current_player_id
                )
                await self._event_publisher.publish(executed_event)
                
                # Emit PiecesDealt for new hands
                pieces_event = PiecesDealt(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    round_number=game.round_number,
                    dealer_id=game.current_player_id,
                    piece_counts={p.id: len(p.hand) for p in game.players}
                )
                await self._event_publisher.publish(pieces_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.redeal_accepted",
                    tags={
                        "votes_collected": str(votes_collected),
                        "votes_required": str(votes_required),
                        "redeal_approved": str(redeal_approved).lower()
                    }
                )
            
            # Create response
            response = AcceptRedealResponse(
                success=True,
                request_id=request.request_id,
                redeal_id=request.redeal_id,
                player_id=request.player_id,
                votes_collected=votes_collected,
                votes_required=votes_required,
                redeal_approved=redeal_approved,
                new_hands_dealt=new_hands_dealt
            )
            
            logger.info(
                f"Player {player.name} accepted redeal",
                extra={
                    "game_id": game.id,
                    "player_id": request.player_id,
                    "redeal_id": request.redeal_id,
                    "votes": f"{votes_collected}/{votes_required}",
                    "approved": redeal_approved
                }
            )
            
            self._log_execution(request, response)
            return response