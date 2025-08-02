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
    ValidationException,
)
from domain.entities.game import Game, GamePhase, WinConditionType
from domain.entities.player import Player
from domain.entities.room import RoomStatus
from domain.services.game_rules import GameRules
from domain.events.game_events import (
    GameStarted,
    RoundStarted,
    PiecesDealt,
    WeakHandDetected,
    PhaseChanged,
)
from domain.events.base import EventMetadata
from application.adapters.state_management_adapter import StateManagementAdapter

# PropertyMapper import removed - using direct attribute access

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
        state_adapter: Optional[StateManagementAdapter] = None,
        metrics: Optional[MetricsCollector] = None,
    ):
        """
        Initialize the use case.

        Args:
            unit_of_work: Unit of work for data access
            event_publisher: Publisher for domain events
            state_adapter: Optional state management adapter
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._state_adapter = state_adapter
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
                raise AuthorizationException("start game", f"room {request.room_id}")

            # Check if game already in progress
            if room.game:
                raise ConflictException("start game", "Game already in progress")

            # Validate room is ready
            # Count actual players in room
            occupied_slots = sum(1 for slot in room.slots if slot is not None)
            if occupied_slots < 2:
                raise ValidationException(
                    {"players": "Need at least 2 players to start"}
                )

            # Create game players from room slots
            game_players = []
            for i, slot in enumerate(room.slots):
                if slot:
                    game_player = Player(
                        name=slot.name,
                        is_bot=slot.is_bot,
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
            if request.use_previous_starter and hasattr(room, "last_starter_id"):
                for player in game_players:
                    if player.id == room.last_starter_id:
                        starting_player = player
                        break

            # Create the game
            game = Game(
                room_id=room.room_id,
                players=game_players,
                # Using defaults for win condition as they are set in the dataclass
            )

            # Track game start if adapter available
            if self._state_adapter:
                await self._state_adapter.track_game_start(
                    game_id=game.room_id,
                    room_id=room.room_id,
                    players=[p.name for p in game_players],
                    starting_player=starting_player.name
                )

            # Start the game and first round using domain methods
            logger.info(f"Starting game for room {room.room_id}")
            
            # Start the game (sets phase to PREPARATION)
            game.start_game()
            
            # Start the first round (deals cards to players)
            logger.info(
                f"🎯 [PHASE_TRANSITION_DEBUG] Starting round 1, dealing cards to {len(game.players)} players"
            )
            game.start_round()
            
            logger.info(f"🎯 [PHASE_TRANSITION_DEBUG] Game phase after start_round: {game.current_phase}")
            
            # Track phase change if adapter available
            if self._state_adapter:
                context = self._state_adapter.create_context(
                    game_id=game.room_id,
                    room_id=room.room_id,
                    current_phase=str(GamePhase.NOT_STARTED)
                )
                await self._state_adapter.track_phase_change(
                    context=context,
                    from_phase=GamePhase.NOT_STARTED,
                    to_phase=game.current_phase,
                    trigger="start_game",
                    payload={"player_count": len(game_players), "round": game.round_number}
                )

            # Publish all domain events from the game
            logger.info(
                f"[START_GAME_DEBUG] Publishing {len(game.events)} domain events"
            )
            event_failures = []
            for i, event in enumerate(game.events):
                try:
                    await self._event_publisher.publish(event)
                except Exception as e:
                    logger.error(
                        f"Error publishing {type(event).__name__}: {e}",
                        exc_info=True
                    )
                    event_failures.append((type(event).__name__, str(e)))
            
            # Clear events even if some failed to prevent re-processing
            game.clear_events()
            
            # If any critical events failed, raise an error
            if event_failures:
                failure_details = "; ".join([f"{name}: {error}" for name, error in event_failures])
                logger.error(f"[START_GAME_DEBUG] {len(event_failures)} events failed: {failure_details}")
                # Only raise if PiecesDealt-type events failed, as these are critical for phase transitions
                critical_failures = [name for name, _ in event_failures if "Pieces" in name or "Phase" in name]
                if critical_failures:
                    raise ValidationException(
                        {"domain_events": f"Critical events failed: {', '.join(critical_failures)}"}
                    )

            # Update room status to IN_GAME and set game reference
            room.status = RoomStatus.IN_GAME
            room.game = game
            room.last_starter_id = starting_player.id

            # Save the game and room
            await self._uow.games.save(game)
            await self._uow.rooms.save(room)

            # Prepare response data
            game_state = self._create_game_state_info(game, room.room_id)
            player_hands = self._get_player_hands(game)
            weak_hands = self._detect_weak_hands(game)

            # Emit GameStarted event
            try:
                game_started = GameStarted(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.room_id,
                    round_number=game.round_number,
                    player_names=[p.name for p in game_players],
                    win_condition="first_to_reach_50",
                    max_score=game.max_score,
                    max_rounds=game.max_rounds,
                )
                logger.info(
                    f"[START_GAME_DEBUG] Created GameStarted event for {len(game_started.player_names)} players"
                )
                await self._event_publisher.publish(game_started)
                logger.info(f"[START_GAME_DEBUG] Successfully published GameStarted event")
            except Exception as e:
                logger.error(
                    f"[START_GAME_DEBUG] Error creating/publishing GameStarted event: {e}",
                    exc_info=True
                )
                raise ValidationException(
                    {"game_started": f"Failed to create game started event: {str(e)}"}
                )

            # Emit RoundStarted event
            try:
                round_started = RoundStarted(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.room_id,
                    round_number=1,
                    starter_name=starting_player.name,
                    player_hands={
                        p.name: [piece.kind for piece in p.hand] for p in game.players
                    },
                )
                logger.info(
                    f"[START_GAME_DEBUG] Created RoundStarted event with starter: {starting_player.name}"
                )
                await self._event_publisher.publish(round_started)
                logger.info(f"[START_GAME_DEBUG] Successfully published RoundStarted event")
            except Exception as e:
                logger.error(
                    f"[START_GAME_DEBUG] Error creating/publishing RoundStarted event: {e}",
                    exc_info=True
                )
                raise ValidationException(
                    {"round_started": f"Failed to create round started event: {str(e)}"}
                )

            # Emit PiecesDealt event
            try:
                pieces_dealt = PiecesDealt(
                    metadata=EventMetadata(user_id=request.user_id),
                    room_id=room.room_id,
                    round_number=1,
                    player_pieces={
                        p.name: [piece.kind for piece in p.hand] for p in game.players
                    },
                )
                logger.info(
                    f"[START_GAME_DEBUG] Created PiecesDealt event with {len(pieces_dealt.player_pieces)} players"
                )
                await self._event_publisher.publish(pieces_dealt)
                logger.info(f"[START_GAME_DEBUG] Successfully published PiecesDealt event")
            except Exception as e:
                logger.error(
                    f"[START_GAME_DEBUG] Error creating/publishing PiecesDealt event: {e}",
                    exc_info=True
                )
                raise ValidationException(
                    {"pieces_dealt": f"Failed to create pieces dealt event: {str(e)}"}
                )

            # COMMENTED OUT: PhaseChanged event is now handled by the state machine's auto-broadcast
            # The state machine will automatically broadcast phase changes with the correct hand data
            # from base_state.py when the preparation phase is entered

            # # Emit PhaseChanged event to trigger frontend phase transition
            # phase_changed = PhaseChanged(
            #     metadata=EventMetadata(user_id=request.user_id),
            #     room_id=room.room_id,
            #     old_phase="waiting",
            #     new_phase=game.current_phase.value if hasattr(game.current_phase, "value") else str(game.current_phase),
            #     round_number=game.round_number,
            #     turn_number=game.turn_number,
            #     phase_data={
            #         "players": [{"name": p.name, "id": p.id, "score": p.score, "hand_size": len(p.hand)} for p in game.players],
            #         "my_hand": {p.id: [{"value": piece.value, "kind": piece.kind} for piece in p.hand] for p in game.players},
            #         "current_player": starting_player.name,
            #         "game_settings": {
            #             "max_score": game.max_score,
            #             "max_rounds": game.max_rounds,
            #             "win_condition": "first_to_reach_50"
            #         }
            #     }
            # )
            # await self._event_publisher.publish(phase_changed)

            # Emit WeakHandDetected event if any weak hands
            if weak_hands:
                try:
                    weak_hand_players = [
                        next(p.name for p in game.players if p.id == player_id)
                        for player_id in weak_hands
                    ]
                    weak_hand_event = WeakHandDetected(
                        metadata=EventMetadata(user_id=request.user_id),
                        room_id=room.room_id,
                        round_number=1,
                        weak_hand_players=weak_hand_players,
                    )
                    logger.info(
                        f"[START_GAME_DEBUG] Created WeakHandDetected event for {len(weak_hand_players)} players"
                    )
                    await self._event_publisher.publish(weak_hand_event)
                    logger.info(f"[START_GAME_DEBUG] Successfully published WeakHandDetected event")
                except Exception as e:
                    logger.error(
                        f"[START_GAME_DEBUG] Error creating/publishing WeakHandDetected event: {e}",
                        exc_info=True
                    )
                    # Don't raise here - weak hand detection is not critical for game start
                    logger.warning(f"[START_GAME_DEBUG] Continuing game start despite weak hand event error")

            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.started",
                    tags={
                        "player_count": str(len(game_players)),
                        "has_bots": str(any(p.is_bot for p in game_players)).lower(),
                        "win_condition": (
                            getattr(room.settings, "win_condition_type", "pile_count")
                            if hasattr(room, "settings")
                            else "pile_count"
                        ),
                        "weak_hands": str(len(weak_hands)),
                    },
                )

            # Create response
            response = StartGameResponse(
                game_id=game.room_id,
                room_id=room.room_id,
                initial_state=game_state,
                player_hands=player_hands,
                starting_player_id=starting_player.id,
                weak_hands_detected=weak_hands,
            )

            logger.info(
                f"Game {game.room_id} started in room {room.room_id}",
                extra={
                    "game_id": game.room_id,
                    "room_id": room.room_id,
                    "player_count": len(game_players),
                    "starting_player": starting_player.id,
                    "weak_hands": len(weak_hands),
                },
            )

            self._log_execution(request, response)
            return response

    def _create_game_state_info(self, game: Game, room_id: str) -> GameStateInfo:
        """Create GameStateInfo from game entity."""
        return GameStateInfo(
            game_id=game.room_id,
            room_id=room_id,
            round_number=game.round_number,
            turn_number=game.turn_number,
            phase=(
                game.current_phase.value
                if hasattr(game.current_phase, "value")
                else str(game.current_phase)
            ),
            current_player_id=getattr(game, "current_player_id", None),
            player_scores={p.id: p.score for p in game.players},
            pieces_remaining={p.id: len(p.hand) for p in game.players},
        )

    def _get_player_hands(self, game: Game) -> Dict[str, List[PieceInfo]]:
        """Get all player hands as PieceInfo objects."""
        hands = {}
        for player in game.players:
            hands[player.id] = [
                PieceInfo(value=piece.point, kind=piece.kind) for piece in player.hand
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
