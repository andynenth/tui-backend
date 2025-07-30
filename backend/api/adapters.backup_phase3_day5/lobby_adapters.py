"""
Lobby operation WebSocket adapters using minimal intervention pattern.
Handles room list requests and updates.
"""

from typing import Dict, Any, Optional, Callable, List
import logging

from infrastructure.dependencies import get_unit_of_work, get_metrics_collector
from application.use_cases.lobby.get_room_list import GetRoomListUseCase
from application.dto.lobby import GetRoomListRequest

logger = logging.getLogger(__name__)

# Actions that need lobby adapter handling
LOBBY_ADAPTER_ACTIONS = {"request_room_list", "get_rooms"}


async def handle_lobby_messages(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Minimal intervention handler for lobby-related messages.
    Only intercepts messages that need clean architecture adaptation.
    """
    action = message.get("action")

    # Fast path - pass through non-lobby messages
    if action not in LOBBY_ADAPTER_ACTIONS:
        return await legacy_handler(websocket, message)

    # Handle lobby actions with minimal overhead
    if action == "request_room_list":
        return await _handle_request_room_list(
            websocket, message, room_state, broadcast_func
        )
    elif action == "get_rooms":
        return await _handle_get_rooms(websocket, message, room_state, broadcast_func)

    # Fallback (shouldn't reach here)
    return await legacy_handler(websocket, message)


async def _handle_request_room_list(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle request_room_list - client requesting current room list.
    This returns the room list immediately (same as get_rooms).
    """
    # Delegate to get_rooms handler
    return await _handle_get_rooms(websocket, message, room_state, broadcast_func)


async def _handle_get_rooms(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable],
) -> Dict[str, Any]:
    """
    Handle get_rooms - direct request for room list (no broadcast).
    Returns the current list of rooms to the requester only.
    """
    data = message.get("data", {})
    filter_options = data.get("filter", {})

    try:
        # Get dependencies
        uow = get_unit_of_work()
        metrics = get_metrics_collector()
        use_case = GetRoomListUseCase(uow, metrics)

        # Create request
        request = GetRoomListRequest(
            player_id=data.get("player_id"),
            include_private=filter_options.get("include_private", False),
            include_full=not filter_options.get("available_only", False),
            include_in_game=not filter_options.get("not_in_game", False),
            sort_by="created_at",
            sort_order="desc",
            page=1,
            page_size=50,
        )

        # Execute use case
        response_dto = await use_case.execute(request)

        # Format rooms for WebSocket response
        rooms = []
        for room_summary in response_dto.rooms:
            rooms.append(
                {
                    "room_id": room_summary.room_id,
                    "room_code": room_summary.room_code,
                    "host_name": room_summary.host_name,
                    "player_count": room_summary.player_count,
                    "max_players": room_summary.max_players,
                    "game_active": room_summary.game_in_progress,
                    "is_public": not room_summary.is_private,
                }
            )

        response = {
            "event": "room_list",
            "data": {
                "rooms": rooms,
                "total_count": response_dto.total_items,
                "filter_applied": bool(filter_options),
                "page": response_dto.page,
                "total_pages": response_dto.total_pages,
            },
        }

        logger.info(f"Returning {len(rooms)} rooms from clean architecture")

    except Exception as e:
        logger.error(f"Error getting room list: {e}")
        # Fallback to empty list on error
        response = {
            "event": "room_list",
            "data": {
                "rooms": [],
                "total_count": 0,
                "filter_applied": bool(filter_options),
                "error": str(e),
            },
        }

    return response


def format_room_for_lobby(room_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format room data for lobby display.
    Extracts only the information needed by lobby clients.
    """
    return {
        "room_id": room_data.get("room_id"),
        "host_name": room_data.get("host_name"),
        "player_count": len(room_data.get("players", [])),
        "max_players": 4,  # Game constant
        "game_active": room_data.get("game_active", False),
        "is_public": room_data.get("is_public", True),
    }


class LobbyAdapterIntegration:
    """
    Integration point for lobby adapters.
    Maintains compatibility with existing system while enabling clean architecture.
    """

    def __init__(self, legacy_handler: Callable):
        self.legacy_handler = legacy_handler
        self._enabled = True

    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """Main entry point for lobby message handling"""
        if not self._enabled:
            return await self.legacy_handler(websocket, message)

        return await handle_lobby_messages(
            websocket, message, self.legacy_handler, room_state, broadcast_func
        )

    def enable(self):
        """Enable lobby adapters"""
        self._enabled = True
        logger.info("Lobby adapters enabled")

    def disable(self):
        """Disable lobby adapters (fallback to legacy)"""
        self._enabled = False
        logger.info("Lobby adapters disabled - using legacy handlers")
