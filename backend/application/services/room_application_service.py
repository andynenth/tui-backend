"""
Room application service.

This service provides high-level orchestration of room-related use cases
and manages room lifecycle operations.
"""

import logging
from typing import Optional, Dict, Any, List

from application.base import ApplicationService
from application.interfaces import (
    UnitOfWork,
    EventPublisher,
    BotService,
    MetricsCollector,
)
from application.use_cases.room_management import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    LeaveRoomUseCase,
    GetRoomStateUseCase,
    AddBotUseCase,
    RemovePlayerUseCase,
)
from application.dto.room_management import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    AddBotRequest,
)
from application.dto.common import RoomInfo
from application.exceptions import ApplicationException, ResourceNotFoundException

logger = logging.getLogger(__name__)


class RoomApplicationService(ApplicationService):
    """
    High-level service for room operations.

    This service:
    1. Orchestrates room lifecycle operations
    2. Manages player capacity and bot filling
    3. Handles room cleanup and maintenance
    4. Provides room analytics
    5. Coordinates complex room workflows
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        bot_service: BotService,
        metrics: Optional[MetricsCollector] = None,
    ):
        """
        Initialize the service.

        Args:
            unit_of_work: Unit of work for transactions
            event_publisher: Event publishing service
            bot_service: Bot management service
            metrics: Optional metrics collector
        """
        super().__init__()
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._bot_service = bot_service
        self._metrics = metrics

        # Initialize use cases
        self._create_room_use_case = CreateRoomUseCase(
            unit_of_work, event_publisher, metrics
        )
        self._join_room_use_case = JoinRoomUseCase(
            unit_of_work, event_publisher, metrics
        )
        self._leave_room_use_case = LeaveRoomUseCase(
            unit_of_work, event_publisher, metrics
        )
        self._get_room_state_use_case = GetRoomStateUseCase(unit_of_work, metrics)
        self._add_bot_use_case = AddBotUseCase(
            unit_of_work, event_publisher, bot_service, metrics
        )
        self._remove_player_use_case = RemovePlayerUseCase(
            unit_of_work, event_publisher, metrics
        )

    async def create_room_and_fill_bots(
        self,
        host_player_id: str,
        host_player_name: str,
        room_name: Optional[str] = None,
        bot_count: int = 0,
        bot_difficulty: str = "medium",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a room and optionally fill with bots.

        Args:
            host_player_id: Host player ID
            host_player_name: Host player name
            room_name: Optional room name
            bot_count: Number of bots to add
            bot_difficulty: Bot difficulty level
            user_id: User ID for tracking

        Returns:
            Room creation result with bot details
        """
        try:
            # Create the room
            create_request = CreateRoomRequest(
                host_player_id=host_player_id,
                host_player_name=host_player_name,
                room_name=room_name,
                user_id=user_id,
            )
            create_response = await self._create_room_use_case.execute(create_request)

            if not create_response.success:
                raise ApplicationException(
                    "Failed to create room", code="ROOM_CREATION_FAILED"
                )

            room_info = create_response.room_info
            bots_added = []

            # Add requested bots
            for i in range(min(bot_count, room_info.max_players - 1)):
                bot_request = AddBotRequest(
                    room_id=room_info.room_id,
                    requesting_player_id=host_player_id,
                    bot_difficulty=bot_difficulty,
                    user_id=user_id,
                )

                try:
                    bot_response = await self._add_bot_use_case.execute(bot_request)
                    if bot_response.success:
                        bots_added.append(bot_response.bot_info)
                        room_info = bot_response.room_info
                except Exception as e:
                    self._logger.warning(f"Failed to add bot {i+1}: {e}")
                    break

            self._logger.info(
                f"Room created with {len(bots_added)} bots",
                extra={
                    "room_id": room_info.room_id,
                    "room_code": room_info.room_code,
                    "bot_count": len(bots_added),
                },
            )

            return {
                "room_info": room_info,
                "join_code": create_response.join_code,
                "bots_added": bots_added,
            }

        except Exception as e:
            self._logger.error(f"Failed to create room with bots: {e}", exception=e)
            raise

    async def quick_join(
        self,
        player_id: str,
        player_name: str,
        preferences: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> JoinRoomResponse:
        """
        Quick join - find and join a suitable room.

        Args:
            player_id: Player ID
            player_name: Player name
            preferences: Join preferences (max_players, etc.)
            user_id: User ID for tracking

        Returns:
            Join room response
        """
        preferences = preferences or {}

        async with self._uow:
            # Find suitable rooms
            all_rooms = await self._uow.rooms.list_active(limit=100)

            suitable_rooms = []
            for room in all_rooms:
                # Skip if full or game in progress
                if room.is_full() or room.current_game:
                    continue

                # Skip private rooms
                if room.settings.is_private:
                    continue

                # Check preferences
                if "max_players" in preferences:
                    if room.settings.max_players != preferences["max_players"]:
                        continue

                if "min_players" in preferences:
                    if room.player_count < preferences["min_players"]:
                        continue

                suitable_rooms.append(room)

            # Sort by player count (prefer fuller rooms)
            suitable_rooms.sort(key=lambda r: r.player_count, reverse=True)

            if not suitable_rooms:
                # No suitable room - create one
                create_response = await self.create_room_and_fill_bots(
                    host_player_id=player_id,
                    host_player_name=player_name,
                    room_name=f"{player_name}'s Room",
                    bot_count=preferences.get("preferred_bot_count", 0),
                    user_id=user_id,
                )

                return JoinRoomResponse(
                    success=True,
                    room_info=create_response["room_info"],
                    seat_position=0,
                    is_host=True,
                )

            # Join the best room
            best_room = suitable_rooms[0]
            join_request = JoinRoomRequest(
                player_id=player_id,
                player_name=player_name,
                room_id=best_room.id,
                user_id=user_id,
            )

            return await self._join_room_use_case.execute(join_request)

    async def cleanup_inactive_rooms(
        self, inactive_threshold_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Clean up inactive rooms.

        Args:
            inactive_threshold_minutes: Minutes of inactivity before cleanup

        Returns:
            Cleanup statistics
        """
        from datetime import datetime, timedelta

        threshold = datetime.utcnow() - timedelta(minutes=inactive_threshold_minutes)
        cleaned_rooms = []

        async with self._uow:
            rooms = await self._uow.rooms.list_active(limit=1000)

            for room in rooms:
                # Skip rooms with active games
                if room.current_game:
                    continue

                # Check last activity
                last_activity = room.created_at
                for slot in room.slots:
                    if slot and hasattr(slot, "last_activity"):
                        if slot.last_activity > last_activity:
                            last_activity = slot.last_activity

                # Clean up if inactive
                if last_activity < threshold:
                    # Check if only bots remain
                    human_count = sum(
                        1 for slot in room.slots if slot and not slot.is_bot
                    )

                    if human_count == 0:
                        await self._uow.rooms.delete(room.id)
                        cleaned_rooms.append(
                            {
                                "room_id": room.id,
                                "room_code": room.code,
                                "reason": "no_humans",
                            }
                        )
                    elif last_activity < threshold - timedelta(minutes=60):
                        # Extra old with humans - also clean
                        await self._uow.rooms.delete(room.id)
                        cleaned_rooms.append(
                            {
                                "room_id": room.id,
                                "room_code": room.code,
                                "reason": "timeout",
                            }
                        )

        if self._metrics:
            self._metrics.gauge(
                "rooms.cleaned_up",
                len(cleaned_rooms),
                tags={"threshold_minutes": str(inactive_threshold_minutes)},
            )

        return {"rooms_cleaned": len(cleaned_rooms), "cleaned_rooms": cleaned_rooms}

    async def get_room_analytics(self, room_id: str) -> Dict[str, Any]:
        """
        Get detailed room analytics.

        Args:
            room_id: Room ID

        Returns:
            Room analytics data
        """
        async with self._uow:
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                raise ResourceNotFoundException("Room", room_id)

            # Calculate analytics
            human_players = sum(1 for slot in room.slots if slot and not slot.is_bot)
            bot_players = sum(1 for slot in room.slots if slot and slot.is_bot)

            # Get connection status
            connected_players = sum(
                1 for slot in room.slots if slot and getattr(slot, "is_connected", True)
            )

            # Room age
            from datetime import datetime

            room_age_minutes = (
                datetime.utcnow() - room.created_at
            ).total_seconds() / 60

            analytics = {
                "room_id": room_id,
                "room_code": room.code,
                "player_composition": {
                    "human_players": human_players,
                    "bot_players": bot_players,
                    "total_players": room.player_count,
                    "max_players": room.settings.max_players,
                },
                "connection_status": {
                    "connected": connected_players,
                    "disconnected": room.player_count - connected_players,
                },
                "room_metrics": {
                    "age_minutes": round(room_age_minutes, 2),
                    "games_played": getattr(room, "games_played", 0),
                    "host_changes": getattr(room, "host_change_count", 0),
                },
                "settings": {
                    "win_condition": f"{room.settings.win_condition_type} {room.settings.win_condition_value}",
                    "allow_bots": room.settings.allow_bots,
                    "is_private": room.settings.is_private,
                },
            }

            # Add game info if active
            if room.current_game:
                game = await self._uow.games.get_by_id(room.current_game.id)
                if game:
                    analytics["active_game"] = {
                        "game_id": game.id,
                        "round_number": game.round_number,
                        "phase": game.phase.value,
                        "duration_minutes": getattr(game, "duration_minutes", 0),
                    }

            return analytics

    async def balance_room_with_bots(
        self, room_id: str, target_players: int = 4, bot_difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Balance room by adding/removing bots to reach target player count.

        Args:
            room_id: Room ID
            target_players: Target number of players
            bot_difficulty: Difficulty for new bots

        Returns:
            List of balance actions taken
        """
        actions = []

        async with self._uow:
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                raise ResourceNotFoundException("Room", room_id)

            # Can't balance during active game
            if room.current_game:
                raise ApplicationException(
                    "Cannot balance room during active game", code="GAME_IN_PROGRESS"
                )

            current_players = room.player_count
            target_players = min(target_players, room.settings.max_players)

            # Add bots if needed
            if current_players < target_players:
                bots_to_add = target_players - current_players
                host_id = room.host_id

                for i in range(bots_to_add):
                    try:
                        bot_request = AddBotRequest(
                            room_id=room_id,
                            requesting_player_id=host_id,
                            bot_difficulty=bot_difficulty,
                        )
                        bot_response = await self._add_bot_use_case.execute(bot_request)

                        if bot_response.success:
                            actions.append(
                                {
                                    "action": "added_bot",
                                    "bot_id": bot_response.bot_info.player_id,
                                    "bot_name": bot_response.bot_info.player_name,
                                }
                            )
                    except Exception as e:
                        self._logger.warning(f"Failed to add bot: {e}")
                        break

            # Remove bots if needed
            elif current_players > target_players:
                bots_to_remove = current_players - target_players
                bot_slots = [slot for slot in room.slots if slot and slot.is_bot]

                host_id = room.host_id
                for i in range(min(bots_to_remove, len(bot_slots))):
                    bot = bot_slots[i]
                    try:
                        remove_request = RemovePlayerRequest(
                            room_id=room_id,
                            requesting_player_id=host_id,
                            target_player_id=bot.id,
                        )
                        remove_response = await self._remove_player_use_case.execute(
                            remove_request
                        )

                        if remove_response.success:
                            actions.append(
                                {
                                    "action": "removed_bot",
                                    "bot_id": bot.id,
                                    "bot_name": bot.name,
                                }
                            )
                    except Exception as e:
                        self._logger.warning(f"Failed to remove bot: {e}")
                        break

        return actions
