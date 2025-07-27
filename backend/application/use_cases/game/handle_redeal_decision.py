"""
Use case for handling redeal decision timeout or forced completion.

This use case processes the final redeal decision when voting times out
or when the system needs to force a decision.
"""

import logging
from typing import Optional, List

from application.base import UseCase
from application.dto.game import HandleRedealDecisionRequest, HandleRedealDecisionResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException
)
from domain.entities.game import GamePhase
from domain.events.game_events import (
    RedealTimedOut,
    RedealApproved,
    RedealCancelled,
    RedealExecuted,
    PiecesDealt
)
from domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class HandleRedealDecisionUseCase(UseCase[HandleRedealDecisionRequest, HandleRedealDecisionResponse]):
    """
    Handles final redeal decision after timeout or forced completion.
    
    This use case:
    1. Checks voting status
    2. Applies timeout rules (non-voters = decline)
    3. Executes or cancels redeal
    4. Transitions game phase
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
    
    async def execute(self, request: HandleRedealDecisionRequest) -> HandleRedealDecisionResponse:
        """
        Handle redeal decision after timeout or forced completion.
        
        Args:
            request: The decision request
            
        Returns:
            Response with final decision result
            
        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If invalid redeal ID
            ConflictException: If no active redeal
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
                    "handle redeal decision",
                    "No active redeal vote"
                )
            
            # Verify redeal ID matches
            if game.active_redeal_id != request.redeal_id:
                raise ValidationException({
                    "redeal_id": "Invalid or expired redeal ID"
                })
            
            # Find players who haven't voted
            missing_votes = []
            for player in game.players:
                if player.id not in game.redeal_votes:
                    missing_votes.append(player.id)
            
            # If forcing decision or timeout, treat missing votes as declines
            if request.force_decision or missing_votes:
                for player_id in missing_votes:
                    game.redeal_votes[player_id] = False
            
            # Count votes
            accept_votes = sum(1 for vote in game.redeal_votes.values() if vote)
            total_votes = len(game.redeal_votes)
            all_voted = total_votes == len(game.players)
            
            # Determine decision
            decision = "timeout" if missing_votes else "voted"
            redeal_approved = accept_votes == len(game.players)
            new_hands_dealt = False
            
            # Handle timeout first
            if missing_votes:
                # Emit RedealTimedOut event
                timeout_event = RedealTimedOut(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    redeal_id=request.redeal_id,
                    missing_voters=missing_votes,
                    accept_votes=accept_votes,
                    total_players=len(game.players)
                )
                await self._event_publisher.publish(timeout_event)
                decision = "timeout"
            
            # Process decision
            if redeal_approved:
                decision = "approved"
                
                # Execute redeal
                game.execute_redeal()
                new_hands_dealt = True
                
                # Move to declaration phase
                game.phase = GamePhase.DECLARATION
                
                # Emit RedealApproved
                approved_event = RedealApproved(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    redeal_id=request.redeal_id,
                    total_votes=len(game.players),
                    accept_votes=accept_votes
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
                
                # Emit PiecesDealt
                pieces_event = PiecesDealt(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    round_number=game.round_number,
                    dealer_id=game.current_player_id,
                    piece_counts={p.id: len(p.hand) for p in game.players}
                )
                await self._event_publisher.publish(pieces_event)
            else:
                decision = "declined" if not missing_votes else "timeout"
                
                # Find first decliner to become starter
                new_starter_id = game.current_player_id
                for player_id, vote in game.redeal_votes.items():
                    if not vote:
                        new_starter_id = player_id
                        break
                
                game.current_player_id = new_starter_id
                game.starting_player_id = new_starter_id
                
                # Move to declaration phase
                game.phase = GamePhase.DECLARATION
                
                # Emit RedealCancelled
                cancelled_event = RedealCancelled(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    redeal_id=request.redeal_id,
                    cancelled_by="timeout" if missing_votes else "vote",
                    reason=f"Redeal {decision}: {accept_votes}/{len(game.players)} accepted"
                )
                await self._event_publisher.publish(cancelled_event)
            
            # Clear redeal state
            game.active_redeal_id = None
            game.redeal_votes = {}
            
            # Save game state
            await self._uow.games.save(game)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.redeal_decision",
                    tags={
                        "decision": decision,
                        "missing_votes": str(len(missing_votes)),
                        "accept_votes": str(accept_votes)
                    }
                )
            
            # Create response
            response = HandleRedealDecisionResponse(
                success=True,
                request_id=request.request_id,
                redeal_id=request.redeal_id,
                decision=decision,
                new_hands_dealt=new_hands_dealt,
                starting_player_id=game.current_player_id,
                missing_votes=missing_votes
            )
            
            logger.info(
                f"Redeal decision: {decision}",
                extra={
                    "game_id": game.id,
                    "redeal_id": request.redeal_id,
                    "decision": decision,
                    "accept_votes": accept_votes,
                    "missing_votes": len(missing_votes)
                }
            )
            
            self._log_execution(request, response)
            return response