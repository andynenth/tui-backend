"""
Use case for declining a redeal request.

This use case handles players voting to decline a redeal, which
immediately cancels the redeal and makes the declining player
the starting player for the round.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.game import DeclineRedealRequest, DeclineRedealResponse
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException
)
from domain.entities.game import GamePhase
from domain.events.game_events import (
    RedealDeclined,
    RedealCancelled,
    StartingPlayerChanged
)
from domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class DeclineRedealUseCase(UseCase[DeclineRedealRequest, DeclineRedealResponse]):
    """
    Handles declining a redeal vote.
    
    This use case:
    1. Records the decline vote
    2. Immediately cancels the redeal
    3. Makes declining player the starter
    4. Transitions to declaration phase
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
    
    async def execute(self, request: DeclineRedealRequest) -> DeclineRedealResponse:
        """
        Decline a redeal vote.
        
        Args:
            request: The decline request
            
        Returns:
            Response with decline result
            
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
                    "decline redeal",
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
                    "decline redeal",
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
            
            # Record decline vote (false)
            game.redeal_votes[request.player_id] = False
            
            # Declining immediately cancels redeal
            previous_starter = game.current_player_id
            game.current_player_id = request.player_id
            game.starting_player_id = request.player_id
            
            # Clear redeal state
            cancelled_redeal_id = game.active_redeal_id
            game.active_redeal_id = None
            game.redeal_votes = {}
            
            # Move to declaration phase
            game.phase = GamePhase.DECLARATION
            
            # Save game state
            await self._uow.games.save(game)
            
            # Emit RedealDeclined event
            decline_event = RedealDeclined(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                redeal_id=request.redeal_id,
                player_id=request.player_id,
                player_name=player.name,
                becomes_starter=True
            )
            await self._event_publisher.publish(decline_event)
            
            # Emit RedealCancelled event
            cancelled_event = RedealCancelled(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                redeal_id=cancelled_redeal_id,
                cancelled_by=request.player_id,
                reason="Player declined redeal"
            )
            await self._event_publisher.publish(cancelled_event)
            
            # Emit StartingPlayerChanged event
            starter_event = StartingPlayerChanged(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                old_starter_id=previous_starter,
                new_starter_id=request.player_id,
                new_starter_name=player.name,
                reason="Declined redeal"
            )
            await self._event_publisher.publish(starter_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.redeal_declined",
                    tags={
                        "round_number": str(game.round_number),
                        "becomes_starter": "true"
                    }
                )
            
            # Create response
            response = DeclineRedealResponse(
                success=True,
                request_id=request.request_id,
                redeal_id=request.redeal_id,
                player_id=request.player_id,
                redeal_cancelled=True,
                declining_player_becomes_starter=True,
                new_starting_player_id=request.player_id
            )
            
            logger.info(
                f"Player {player.name} declined redeal and becomes starter",
                extra={
                    "game_id": game.id,
                    "player_id": request.player_id,
                    "redeal_id": request.redeal_id,
                    "previous_starter": previous_starter,
                    "new_starter": request.player_id
                }
            )
            
            self._log_execution(request, response)
            return response