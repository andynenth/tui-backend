"""
Use case for leaving an active game.

This use case handles players leaving during an active game,
converting them to bots to maintain game continuity.
"""

import logging
from typing import Optional

from application.base import UseCase
from application.dto.game import LeaveGameRequest, LeaveGameResponse
from application.interfaces import (
    UnitOfWork,
    EventPublisher,
    BotService,
    MetricsCollector,
)
from application.exceptions import ResourceNotFoundException, ValidationException

# from domain.events.player_events import PlayerLeftGame, PlayerConvertedToBot  # TODO: Create these events
from domain.events.base import EventMetadata
from application.utils import PropertyMapper

logger = logging.getLogger(__name__)


class LeaveGameUseCase(UseCase[LeaveGameRequest, LeaveGameResponse]):
    """
    Handles players leaving during an active game.

    This use case:
    1. Converts leaving player to bot
    2. Maintains game continuity
    3. Updates player statistics
    4. Handles bot takeover
    5. Emits appropriate events
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        bot_service: BotService,
        metrics: Optional[MetricsCollector] = None,
    ):
        """
        Initialize the use case.

        Args:
            unit_of_work: Unit of work for data access
            event_publisher: Publisher for domain events
            bot_service: Service for bot operations
            metrics: Optional metrics collector
        """
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._bot_service = bot_service
        self._metrics = metrics

    async def execute(self, request: LeaveGameRequest) -> LeaveGameResponse:
        """
        Leave an active game.

        Args:
            request: The leave game request

        Returns:
            Response with leave result

        Raises:
            ResourceNotFoundException: If game not found
            ValidationException: If player not in game
        """
        async with self._uow:
            # Get the game
            game = await self._uow.games.get_by_id(request.game_id)
            if not game:
                raise ResourceNotFoundException("Game", request.game_id)

            # Get the room
            room = await self._uow.rooms.get_by_id(game.room_id)
            if not room:
                raise ResourceNotFoundException("Room", game.room_id)

            # Find player in game
            game_player = None
            player_index = None
            for i, p in enumerate(game.players):
                if p.id == request.player_id:
                    game_player = p
                    player_index = i
                    break

            if not game_player:
                raise ValidationException({"player_id": "Player not in this game"})

            # Find player in room
            room_player = None
            for slot in room.slots:
                if (
                    slot
                    and PropertyMapper.generate_player_id(room.room_id, i)
                    == request.player_id
                ):
                    room_player = slot
                    break

            if not room_player:
                raise ValidationException({"player_id": "Player not in room"})

            # Create bot replacement
            bot_id = await self._bot_service.create_bot("medium")
            bot_name = f"Bot ({game_player.name})"

            # Update game player to bot
            game_player.is_bot = True
            game_player.original_id = request.player_id
            game_player.original_name = game_player.name
            game_player.id = bot_id
            game_player.name = bot_name

            # Update room player to bot
            room_player.is_bot = True
            room_player.is_connected = True  # Bots are always "connected"
            room_player.original_id = request.player_id
            room_player.id = bot_id
            room_player.name = bot_name

            # Update current player if it was the leaving player
            if PropertyMapper.get_safe(game, "current_player_id") == request.player_id:
                game.current_player_id = bot_id

            # Update any other game state that references the player
            if hasattr(game, "declarations") and request.player_id in game.declarations:
                game.declarations[bot_id] = game.declarations.pop(request.player_id)

            if hasattr(game, "redeal_votes") and request.player_id in game.redeal_votes:
                game.redeal_votes[bot_id] = game.redeal_votes.pop(request.player_id)

            if hasattr(game, "ready_players"):
                for phase_key, ready_set in game.ready_players.items():
                    if request.player_id in ready_set:
                        ready_set.remove(request.player_id)
                        ready_set.add(bot_id)

            # Save game and room
            await self._uow.games.save(game)
            await self._uow.rooms.save(room)

            # Update player statistics
            try:
                stats = await self._uow.player_stats.get_stats(request.player_id)
                stats["games_abandoned"] = stats.get("games_abandoned", 0) + 1
                await self._uow.player_stats.update_stats(request.player_id, stats)
            except Exception as e:
                logger.warning(f"Failed to update player stats: {e}")

            # TODO: Emit PlayerLeftGame event when it's created
            # left_event = PlayerLeftGame(
            #     metadata=EventMetadata(user_id=request.user_id),
            #     room_id=room.room_id,
            #     game_id=game.game_id,
            #     player_id=request.player_id,
            #     player_name=game_player.original_name,
            #     reason=request.reason or "Player left game",
            #     round_number=game.round_number,
            #     game_phase=game.phase.value
            # )
            # await self._event_publisher.publish(left_event)

            # TODO: Emit PlayerConvertedToBot event when it's created
            # bot_event = PlayerConvertedToBot(
            #     metadata=EventMetadata(user_id=request.user_id),
            #     room_id=room.room_id,
            #     game_id=game.game_id,
            #     original_player_id=request.player_id,
            #     original_player_name=game_player.original_name,
            #     bot_id=bot_id,
            #     bot_name=bot_name,
            #     bot_difficulty="medium"
            # )
            # await self._event_publisher.publish(bot_event)

            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "game.player_left",
                    tags={
                        "round_number": str(game.round_number),
                        "phase": game.phase.value,
                        "reason": request.reason or "voluntary",
                    },
                )

            # Create response
            response = LeaveGameResponse(
                success=True,
                request_id=request.request_id,
                player_id=request.player_id,
                converted_to_bot=True,
                game_continues=True,
                replacement_bot_id=bot_id,
            )

            logger.info(
                f"Player {game_player.original_name} left game and was replaced by bot",
                extra={
                    "game_id": game.game_id,
                    "player_id": request.player_id,
                    "bot_id": bot_id,
                    "round": game.round_number,
                    "phase": game.phase.value,
                },
            )

            self._log_execution(request, response)
            return response
