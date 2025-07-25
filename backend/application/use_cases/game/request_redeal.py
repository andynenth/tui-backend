"""
Use case for requesting a redeal due to weak hand.

This use case handles players initiating a redeal vote when they
have a weak hand at the start of a round.
"""

import logging
from typing import Optional, List
import uuid

from application.base import UseCase
from application.dto.game import RequestRedealRequest, RequestRedealResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException
)
from domain.entities.game import GamePhase
from domain.services.game_rules import GameRules
from backend.domain.events.game_events import RedealRequested, RedealVoteStarted
from backend.domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class RequestRedealUseCase(UseCase[RequestRedealRequest, RequestRedealResponse]):
    """
    Handles redeal requests for weak hands.
    
    This use case:
    1. Validates player has a weak hand
    2. Creates a redeal voting session
    3. Auto-accepts for other weak hand players
    4. Sets timeout for voting
    5. Emits redeal events
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None,
        vote_timeout_seconds: int = 30
    ):
        """
        Initialize the use case.
        
        Args:
            unit_of_work: Unit of work for data access
            event_publisher: Publisher for domain events
            metrics: Optional metrics collector
            vote_timeout_seconds: Timeout for redeal voting
        """
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._metrics = metrics
        self._vote_timeout = vote_timeout_seconds
    
    async def execute(self, request: RequestRedealRequest) -> RequestRedealResponse:
        """
        Request a redeal.
        
        Args:
            request: The redeal request
            
        Returns:
            Response with redeal voting information
            
        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If player doesn't have weak hand
            ConflictException: If not in preparation phase
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
            
            # Verify preparation phase
            if game.phase != GamePhase.PREPARATION:
                raise ConflictException(
                    "request redeal",
                    f"Can only request redeal in preparation phase, not {game.phase}"
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
            
            # Check if redeal already in progress
            if hasattr(game, 'active_redeal_id') and game.active_redeal_id:
                raise ConflictException(
                    "request redeal",
                    "Redeal vote already in progress"
                )
            
            # Verify player has weak hand
            if not GameRules.has_weak_hand(player.hand):
                raise ValidationException({
                    "hand": "Player does not have a weak hand (no piece > 9)"
                })
            
            # Calculate hand strength if not provided
            hand_strength = request.hand_strength_score
            if hand_strength is None:
                hand_strength = sum(p.value for p in player.hand if p.value > 9)
            
            # Create redeal session
            redeal_id = str(uuid.uuid4())
            game.active_redeal_id = redeal_id
            game.redeal_votes = {request.player_id: True}  # Requester auto-accepts
            game.redeal_timeout = self._vote_timeout
            
            # Find other players with weak hands who auto-accept
            auto_accept_players = []
            for p in game.players:
                if p.id != request.player_id and GameRules.has_weak_hand(p.hand):
                    game.redeal_votes[p.id] = True
                    auto_accept_players.append(p.id)
            
            # Calculate votes required (all players must vote)
            votes_required = len(game.players)
            
            # Save game state
            await self._uow.games.save(game)
            
            # Emit RedealRequested event
            redeal_requested = RedealRequested(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                requesting_player_id=request.player_id,
                requesting_player_name=player.name,
                redeal_id=redeal_id,
                hand_strength=hand_strength,
                round_number=game.round_number
            )
            await self._event_publisher.publish(redeal_requested)
            
            # Emit RedealVoteStarted event
            vote_started = RedealVoteStarted(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                redeal_id=redeal_id,
                timeout_seconds=self._vote_timeout,
                votes_required=votes_required,
                auto_accepted_players=auto_accept_players + [request.player_id],
                players_to_vote=[
                    p.id for p in game.players 
                    if p.id not in game.redeal_votes
                ]
            )
            await self._event_publisher.publish(vote_started)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.redeal_requested",
                    tags={
                        "round_number": str(game.round_number),
                        "hand_strength": str(hand_strength),
                        "auto_accepts": str(len(auto_accept_players))
                    }
                )
            
            # Create response
            response = RequestRedealResponse(
                success=True,
                request_id=request.request_id,
                redeal_id=redeal_id,
                requesting_player_id=request.player_id,
                votes_required=votes_required,
                timeout_seconds=self._vote_timeout,
                auto_accept_players=auto_accept_players
            )
            
            logger.info(
                f"Player {player.name} requested redeal",
                extra={
                    "game_id": game.id,
                    "player_id": request.player_id,
                    "redeal_id": redeal_id,
                    "auto_accepts": len(auto_accept_players),
                    "votes_required": votes_required
                }
            )
            
            self._log_execution(request, response)
            return response