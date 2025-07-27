"""
Use case for starting a new game.

This use case handles the initialization of a new game within a room,
including dealing pieces and detecting weak hands.
"""

import logging
from typing import Optional, List, Dict

from application.base import UseCase
from application.dto.game import StartGameRequest, StartGameResponse
from application.dto.common import GameStateInfo, PieceInfo
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    AuthorizationException,
    ConflictException,
    ValidationException
)
from domain.entities.game import Game, GamePhase
from domain.entities.player import Player
from domain.services.game_rules import GameRules
from domain.events.game_events import (
    GameStarted,
    RoundStarted,
    PiecesDealt,
    WeakHandDetected
)
from domain.events.base import EventMetadata

logger = logging.getLogger(__name__)


class StartGameUseCase(UseCase[StartGameRequest, StartGameResponse]):
    """
    Starts a new game in a room.
    
    This use case:
    1. Validates the room is ready for a game
    2. Creates a new Game entity
    3. Deals initial pieces
    4. Detects weak hands
    5. Emits game start events
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
    
    async def execute(self, request: StartGameRequest) -> StartGameResponse:
        """
        Start a new game.
        
        Args:
            request: The start game request
            
        Returns:
            Response with game initialization data
            
        Raises:
            ResourceNotFoundException: If room not found
            AuthorizationException: If requester not host
            ConflictException: If game already in progress
            ValidationException: If room not ready
        """
        async with self._uow:
            # Get the room
            room = await self._uow.rooms.get_by_id(request.room_id)
            if not room:
                raise ResourceNotFoundException("Room", request.room_id)
            
            # Verify requester is host
            if room.host_id != request.requesting_player_id:
                raise AuthorizationException(
                    "start game",
                    f"room {request.room_id}"
                )
            
            # Check if game already in progress
            if room.current_game:
                raise ConflictException(
                    "start game",
                    "Game already in progress"
                )
            
            # Validate room is ready
            if room.player_count < 2:
                raise ValidationException({
                    "players": "Need at least 2 players to start"
                })
            
            # Create game players from room slots
            game_players = []
            for i, slot in enumerate(room.slots):
                if slot:
                    game_player = Player(
                        id=slot.id,
                        name=slot.name,
                        is_bot=slot.is_bot
                    )
                    game_player.seat_position = i
                    game_players.append(game_player)
            
            # Shuffle seats if requested
            if request.shuffle_seats:
                import random
                random.shuffle(game_players)
                for i, player in enumerate(game_players):
                    player.seat_position = i
            
            # Determine starting player
            starting_player = game_players[0]
            if request.use_previous_starter and hasattr(room, 'last_starter_id'):
                for player in game_players:
                    if player.id == room.last_starter_id:
                        starting_player = player
                        break
            
            # Create the game
            game = Game.create(
                game_id=None,  # Will be generated
                players=game_players,
                win_condition_type=room.settings.win_condition_type,
                win_condition_value=room.settings.win_condition_value
            )
            
            # Start the game (deals pieces)
            game.start_game(starting_player_id=starting_player.id)
            
            # Save the game
            await self._uow.games.save(game)
            
            # Update room with game reference
            room.current_game = game
            room.last_starter_id = starting_player.id
            await self._uow.rooms.save(room)
            
            # Prepare response data
            game_state = self._create_game_state_info(game, room.id)
            player_hands = self._get_player_hands(game)
            weak_hands = self._detect_weak_hands(game)
            
            # Emit GameStarted event
            game_started = GameStarted(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                players=[{
                    "id": p.id,
                    "name": p.name,
                    "seat_position": p.seat_position
                } for p in game_players],
                starting_player_id=starting_player.id,
                win_condition={
                    "type": room.settings.win_condition_type,
                    "value": room.settings.win_condition_value
                }
            )
            await self._event_publisher.publish(game_started)
            
            # Emit RoundStarted event
            round_started = RoundStarted(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                round_number=1,
                starting_player_id=starting_player.id,
                pieces_per_player=8
            )
            await self._event_publisher.publish(round_started)
            
            # Emit PiecesDealt event
            pieces_dealt = PiecesDealt(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.id,
                game_id=game.id,
                round_number=1,
                dealer_id=starting_player.id,
                piece_counts={p.id: len(p.hand) for p in game.players}
            )
            await self._event_publisher.publish(pieces_dealt)
            
            # Emit WeakHandDetected events if any
            for player_id in weak_hands:
                weak_hand_event = WeakHandDetected(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.id,
                    game_id=game.id,
                    player_id=player_id,
                    player_name=next(p.name for p in game.players if p.id == player_id),
                    hand_strength=self._calculate_hand_strength(game, player_id),
                    can_request_redeal=True
                )
                await self._event_publisher.publish(weak_hand_event)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.started",
                    tags={
                        "player_count": str(len(game_players)),
                        "has_bots": str(any(p.is_bot for p in game_players)).lower(),
                        "win_condition": room.settings.win_condition_type,
                        "weak_hands": str(len(weak_hands))
                    }
                )
            
            # Create response
            response = StartGameResponse(
                success=True,
                request_id=request.request_id,
                game_id=game.id,
                room_id=room.id,
                initial_state=game_state,
                player_hands=player_hands,
                starting_player_id=starting_player.id,
                weak_hands_detected=weak_hands
            )
            
            logger.info(
                f"Game {game.id} started in room {room.code}",
                extra={
                    "game_id": game.id,
                    "room_id": room.id,
                    "player_count": len(game_players),
                    "starting_player": starting_player.id,
                    "weak_hands": len(weak_hands)
                }
            )
            
            self._log_execution(request, response)
            return response
    
    def _create_game_state_info(self, game: Game, room_id: str) -> GameStateInfo:
        """Create GameStateInfo from game entity."""
        return GameStateInfo(
            game_id=game.id,
            room_id=room_id,
            round_number=game.round_number,
            turn_number=game.turn_number,
            phase=game.phase.value if hasattr(game.phase, 'value') else str(game.phase),
            current_player_id=game.current_player_id,
            player_scores={p.id: p.score for p in game.players},
            pieces_remaining={p.id: len(p.hand) for p in game.players}
        )
    
    def _get_player_hands(self, game: Game) -> Dict[str, List[PieceInfo]]:
        """Get all player hands as PieceInfo objects."""
        hands = {}
        for player in game.players:
            hands[player.id] = [
                PieceInfo(value=piece.value, kind=piece.kind)
                for piece in player.hand
            ]
        return hands
    
    def _detect_weak_hands(self, game: Game) -> List[str]:
        """Detect players with weak hands."""
        weak_players = []
        
        for player in game.players:
            if GameRules.has_weak_hand(player.hand):
                weak_players.append(player.id)
        
        return weak_players
    
    def _calculate_hand_strength(self, game: Game, player_id: str) -> int:
        """Calculate hand strength score for a player."""
        for player in game.players:
            if player.id == player_id:
                return sum(p.value for p in player.hand if p.value > 9)
        return 0