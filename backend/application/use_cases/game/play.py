"""
Use case for playing pieces during a turn.

This use case handles the core game mechanic of playing pieces
and determining turn winners.
"""

import logging
from typing import Optional, List, Dict

from application.base import UseCase
from application.dto.game import PlayRequest, PlayResponse
from application.dto.common import PlayInfo, PieceInfo
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    ConflictException,
)
from domain.entities.game import GamePhase
from domain.value_objects.piece import Piece
from domain.services.game_rules import GameRules
from domain.services.turn_resolution import TurnResolutionService
from domain.events.game_events import (
    TurnCompleted,
    RoundCompleted,
    GameEnded,
    PhaseChanged,
)
from domain.events.game_events import PiecesPlayed
from domain.events.base import EventMetadata
from application.utils import PropertyMapper

logger = logging.getLogger(__name__)


class PlayUseCase(UseCase[PlayRequest, PlayResponse]):
    """
    Handles playing pieces during a turn.

    This use case:
    1. Validates it's the player's turn
    2. Validates the play is legal
    3. Records the play
    4. Determines turn winner when all play
    5. Handles round and game completion
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None,
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

    async def execute(self, request: PlayRequest) -> PlayResponse:
        """
        Play pieces in a turn.

        Args:
            request: The play request

        Returns:
            Response with play result

        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If play invalid
            ConflictException: If not player's turn
        """
        # Validate pieces provided
        if not request.pieces:
            raise ValidationException({"pieces": "Must play at least one piece"})

        if len(request.pieces) > 6:
            raise ValidationException({"pieces": "Cannot play more than 6 pieces"})

        async with self._uow:
            # Get the game
            game = await self._uow.games.get_by_id(request.game_id)
            if not game:
                raise ResourceNotFoundException("Game", request.game_id)

            # Get the room for context
            room = await self._uow.rooms.get_by_id(game.room_id)
            if not room:
                raise ResourceNotFoundException("Room", game.room_id)

            # Verify it's turn phase
            if game.phase != GamePhase.TURN:
                raise ConflictException(
                    "play pieces", f"Game is in {game.phase} phase, not turn"
                )

            # Verify it's player's turn
            current_player_id = PropertyMapper.get_safe(game, "current_player_id")
            if current_player_id != request.player_id:
                raise ConflictException(
                    "play pieces", f"It's not your turn (current: {current_player_id})"
                )

            # Get player
            player = None
            for p in game.players:
                if p.id == request.player_id:
                    player = p
                    break

            if not player:
                raise ValidationException({"player_id": "Player not in this game"})

            # Convert PieceInfo to domain Pieces
            pieces = []
            for piece_info in request.pieces:
                piece = Piece(value=piece_info.value, kind=piece_info.kind)
                pieces.append(piece)

            # Validate player has these pieces
            if not self._player_has_pieces(player, pieces):
                raise ValidationException(
                    {"pieces": "Player doesn't have these pieces"}
                )

            # Validate play is legal
            play_type = GameRules.identify_play_type(pieces)
            if not GameRules.is_valid_play(pieces, play_type):
                raise ValidationException({"pieces": f"Invalid {play_type} play"})

            # Check if play beats current requirement
            current_plays = getattr(game, "current_turn_plays", [])
            if current_plays:
                last_play = current_plays[-1]
                if not GameRules.beats_play(pieces, last_play["pieces"], play_type):
                    raise ValidationException(
                        {"pieces": "Play doesn't beat the current play"}
                    )

            # Make the play
            game.play_turn(request.player_id, pieces)

            # Create play info
            play_info = PlayInfo(
                player_id=request.player_id,
                pieces=[PieceInfo(p.value, p.kind) for p in pieces],
                play_type=play_type,
                is_valid=True,
            )

            # Check if turn is complete
            turn_complete = len(game.current_turn_plays) == len(game.players)
            turn_winner_id = None
            next_player_id = None

            if turn_complete:
                # Determine turn winner
                turn_winner = TurnResolutionService.determine_winner(
                    game.current_turn_plays, game.players
                )
                turn_winner_id = turn_winner.winner_id

                # Process turn completion
                game.complete_turn(turn_winner_id)

                # Check if round/game complete
                if game.is_round_complete():
                    game.complete_round()

                    if game.is_game_complete():
                        game.end_game()
                    else:
                        # Start next round
                        game.start_new_round()
                else:
                    # Continue to next turn
                    next_player_id = PropertyMapper.get_safe(game, "current_player_id")
            else:
                # Find next player
                current_index = game.players.index(player)
                next_index = (current_index + 1) % len(game.players)
                next_player_id = game.players[next_index].id
                game.current_player_id = next_player_id

            # Save the game
            await self._uow.games.save(game)

            # Emit PiecesPlayed event
            play_event = PiecesPlayed(
                metadata=EventMetadata(user_id=request.user_id),
                room_id=room.room_id,
                game_id=game.game_id,
                player_id=request.player_id,
                player_name=player.name,
                pieces_played=len(pieces),
                play_type=play_type,
                turn_number=game.turn_number,
                pieces_remaining=len(player.hand),
            )
            await self._event_publisher.publish(play_event)

            # Emit TurnCompleted if turn done
            if turn_complete:
                turn_event = TurnCompleted(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.room_id,
                    game_id=game.game_id,
                    turn_number=game.turn_number - 1,  # Already incremented
                    winner_id=turn_winner_id,
                    winner_name=next(
                        p.name for p in game.players if p.id == turn_winner_id
                    ),
                    pieces_won=sum(
                        len(play["pieces"]) for play in game.current_turn_plays
                    ),
                    next_player_id=next_player_id,
                )
                await self._event_publisher.publish(turn_event)

            # Handle round completion
            round_complete = game.is_round_complete()
            if round_complete:
                round_event = RoundCompleted(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.room_id,
                    game_id=game.game_id,
                    round_number=(
                        game.round_number - 1
                        if not game.is_game_complete()
                        else game.round_number
                    ),
                    round_scores={p.id: p.current_round_score for p in game.players},
                    total_scores={p.id: p.score for p in game.players},
                    next_round_starting=not game.is_game_complete(),
                )
                await self._event_publisher.publish(round_event)

            # Handle game completion
            game_complete = game.is_game_complete()
            if game_complete:
                winner = max(game.players, key=lambda p: p.score)
                game_event = GameEnded(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.room_id,
                    game_id=game.game_id,
                    winner_id=winner.id,
                    winner_name=winner.name,
                    final_scores={p.id: p.score for p in game.players},
                    rounds_played=game.round_number,
                    end_condition=(
                        "score"
                        if winner.score >= game.win_condition_value
                        else "rounds"
                    ),
                )
                await self._event_publisher.publish(game_event)

            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.pieces_played",
                    value=len(pieces),
                    tags={
                        "play_type": play_type,
                        "turn_complete": str(turn_complete).lower(),
                        "round_complete": str(round_complete).lower(),
                        "game_complete": str(game_complete).lower(),
                    },
                )

            # Create response
            response = PlayResponse(
                success=True,
                request_id=request.request_id,
                play_info=play_info,
                turn_winner_id=turn_winner_id,
                turn_complete=turn_complete,
                next_player_id=next_player_id,
                round_complete=round_complete,
                game_complete=game_complete,
                scores=(
                    {p.id: p.score for p in game.players} if round_complete else None
                ),
            )

            logger.info(
                f"Player {player.name} played {len(pieces)} pieces",
                extra={
                    "game_id": game.game_id,
                    "player_id": request.player_id,
                    "pieces_count": len(pieces),
                    "play_type": play_type,
                    "turn_complete": turn_complete,
                },
            )

            self._log_execution(request, response)
            return response

    def _player_has_pieces(self, player, pieces: List[Piece]) -> bool:
        """Check if player has the specified pieces."""
        player_pieces = list(player.hand)

        for piece in pieces:
            found = False
            for i, p in enumerate(player_pieces):
                if p.point == piece.point and p.kind == piece.kind:
                    player_pieces.pop(i)
                    found = True
                    break

            if not found:
                return False

        return True
