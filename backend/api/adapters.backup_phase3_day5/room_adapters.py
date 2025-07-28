"""
Room management WebSocket adapters using minimal intervention pattern.
Optimized for <50% overhead while maintaining clean architecture boundaries.
"""

from typing import Dict, Any, Optional, Callable
import uuid
import logging

# Import clean architecture dependencies
from infrastructure.dependencies import (
    get_unit_of_work,
    get_event_publisher,
    get_metrics_collector,
    get_bot_service
)
from application.use_cases.room_management import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    LeaveRoomUseCase,
    GetRoomStateUseCase,
    AddBotUseCase,
    RemovePlayerUseCase
)
from application.dto.room_management import (
    CreateRoomRequest,
    JoinRoomRequest,
    LeaveRoomRequest,
    GetRoomStateRequest,
    AddBotRequest,
    RemovePlayerRequest
)

logger = logging.getLogger(__name__)

# Define a function that imports and calls the bridge
async def ensure_room_visible_to_legacy(room_id: str) -> None:
    """Import and call the legacy bridge sync function."""
    try:
        # Import inside function to avoid circular imports
        from infrastructure.adapters.legacy_repository_bridge import ensure_room_visible_to_legacy as sync_func
        logger.info(f"[ROOM_CREATE_DEBUG] Legacy bridge imported successfully for room {room_id}")
        await sync_func(room_id)
    except ImportError as e:
        logger.error(f"[ROOM_CREATE_DEBUG] Failed to import legacy bridge: {e}", exc_info=True)
        logger.warning(f"[ROOM_CREATE_DEBUG] Using no-op sync for room {room_id} - import failed")
    except Exception as e:
        logger.error(f"[ROOM_CREATE_DEBUG] Error during import/sync: {e}", exc_info=True)

# Actions that need room adapter handling
ROOM_ADAPTER_ACTIONS = {
    "create_room", "join_room", "leave_room", 
    "get_room_state", "add_bot", "remove_player"
}


async def handle_room_messages(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None
) -> Optional[Dict[str, Any]]:
    """
    Minimal intervention handler for room-related messages.
    Only intercepts messages that need clean architecture adaptation.
    """
    action = message.get("action")
    
    # Fast path - pass through non-room messages
    if action not in ROOM_ADAPTER_ACTIONS:
        return await legacy_handler(websocket, message)
    
    # Handle room actions with minimal overhead
    if action == "create_room":
        return await _handle_create_room(websocket, message, room_state, broadcast_func)
    elif action == "join_room":
        return await _handle_join_room(websocket, message, room_state, broadcast_func)
    elif action == "leave_room":
        return await _handle_leave_room(websocket, message, room_state, broadcast_func)
    elif action == "get_room_state":
        return await _handle_get_room_state(websocket, message, room_state, broadcast_func)
    elif action == "add_bot":
        return await _handle_add_bot(websocket, message, room_state, broadcast_func)
    elif action == "remove_player":
        return await _handle_remove_player(websocket, message, room_state, broadcast_func)
    
    # Fallback (shouldn't reach here)
    return await legacy_handler(websocket, message)


async def _handle_create_room(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """
    Handle create_room with clean architecture principles.
    Maps WebSocket message to use case and back to response.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")
    
    logger.debug(f"[ROOM_CREATE_DEBUG] Starting room creation for player: {player_name}")
    logger.debug(f"[ROOM_CREATE_DEBUG] Full message data: {data}")
    
    if not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Player name is required",
                "type": "validation_error"
            }
        }
    
    try:
        # Generate a player ID if not provided
        player_id = data.get("player_id", f"player_{uuid.uuid4().hex[:8]}")
        
        # Create the request DTO
        request = CreateRoomRequest(
            host_player_id=player_id,
            host_player_name=player_name,
            room_name=data.get("room_name"),
            max_players=data.get("max_players", 4),
            win_condition_type=data.get("win_condition_type", "score"),
            win_condition_value=data.get("win_condition_value", 50),
            allow_bots=data.get("allow_bots", True),
            is_private=data.get("is_private", False)
        )
        
        # Get dependencies and create use case
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        metrics = get_metrics_collector()
        use_case = CreateRoomUseCase(uow, event_publisher, metrics)
        
        # Execute the use case
        logger.debug(f"[ROOM_CREATE_DEBUG] Executing CreateRoomUseCase for player: {player_name}")
        response_dto = await use_case.execute(request)
        
        # Map the response DTO to WebSocket response format
        response = {
            "event": "room_created",
            "data": {
                "room_id": response_dto.room_info.room_id,
                "room_code": response_dto.join_code,
                "host_name": player_name,
                "success": response_dto.success,
                "room_info": {
                    "room_id": response_dto.room_info.room_id,
                    "room_code": response_dto.room_info.room_code,
                    "room_name": response_dto.room_info.room_name,
                    "host_id": response_dto.room_info.host_id,
                    "players": [
                        {
                            "player_id": p.player_id,
                            "name": p.player_name,  # Frontend expects "name" not "player_name"
                            "is_bot": p.is_bot,
                            "is_host": p.is_host,
                            "seat_position": p.seat_position,
                            "avatar_color": getattr(p, 'avatar_color', None)  # Include avatar color if available
                        }
                        for p in response_dto.room_info.players
                    ],
                    "max_players": response_dto.room_info.max_players,
                    "game_in_progress": response_dto.room_info.game_in_progress
                }
            }
        }
        
        # Log for monitoring
        logger.info(f"Room created: {response_dto.room_info.room_id} by {player_name}")
        logger.debug(f"[ROOM_CREATE_DEBUG] Room successfully stored in repository")
        
        # Sync to legacy manager to prevent "Room not found" warnings
        logger.info(f"[ROOM_CREATE_DEBUG] About to sync room {response_dto.room_info.room_id} to legacy")
        logger.info(f"[ROOM_CREATE_DEBUG] Room has {len(response_dto.room_info.players)} players")
        for p in response_dto.room_info.players:
            logger.info(f"[ROOM_CREATE_DEBUG]   - {p.player_name} (bot={p.is_bot}, seat={p.seat_position})")
        
        try:
            await ensure_room_visible_to_legacy(response_dto.room_info.room_id)
            logger.info(f"[ROOM_CREATE_DEBUG] Room sync completed successfully")
        except Exception as sync_error:
            # Don't fail the request if sync fails
            logger.error(f"Failed to sync room to legacy: {sync_error}", exc_info=True)
        
        logger.debug(f"[ROOM_CREATE_DEBUG] Response being sent: {response}")
        
        return response
        
    except Exception as e:
        logger.error(f"[ROOM_CREATE_DEBUG] Error creating room: {e}", exc_info=True)
        return {
            "event": "error",
            "data": {
                "message": f"Failed to create room: {str(e)}",
                "type": "room_creation_error"
            }
        }


async def _handle_join_room(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle join_room request"""
    data = message.get("data", {})
    room_id = data.get("room_id")
    room_code = data.get("room_code")
    player_name = data.get("player_name")
    
    if not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Player name is required",
                "type": "validation_error"
            }
        }
    
    if not room_id and not room_code:
        return {
            "event": "error",
            "data": {
                "message": "Room ID or room code is required",
                "type": "validation_error"
            }
        }
    
    try:
        # Generate a player ID if not provided
        player_id = data.get("player_id", f"player_{uuid.uuid4().hex[:8]}")
        
        # Create the request DTO
        request = JoinRoomRequest(
            player_id=player_id,
            player_name=player_name,
            room_id=room_id,
            room_code=room_code,
            seat_preference=data.get("seat_preference")
        )
        
        # Get dependencies and create use case
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        metrics = get_metrics_collector()
        use_case = JoinRoomUseCase(uow, event_publisher, metrics)
        
        # Execute the use case
        logger.debug(f"[ROOM_JOIN_DEBUG] Executing JoinRoomUseCase for player: {player_name}")
        response_dto = await use_case.execute(request)
        
        # Map the response DTO to WebSocket response format
        response = {
            "event": "joined_room",
            "data": {
                "room_id": response_dto.room_info.room_id,
                "room_code": response_dto.room_info.room_code,
                "player_name": player_name,
                "success": response_dto.success,
                "seat_position": response_dto.seat_position,
                "is_host": response_dto.is_host,
                "room_info": {
                    "room_id": response_dto.room_info.room_id,
                    "room_code": response_dto.room_info.room_code,
                    "room_name": response_dto.room_info.room_name,
                    "host_id": response_dto.room_info.host_id,
                    "players": [
                        {
                            "player_id": p.player_id,
                            "name": p.player_name,  # Frontend expects "name" not "player_name"
                            "is_bot": p.is_bot,
                            "is_host": p.is_host,
                            "seat_position": p.seat_position,
                            "avatar_color": getattr(p, 'avatar_color', None)  # Include avatar color if available
                        }
                        for p in response_dto.room_info.players
                    ],
                    "max_players": response_dto.room_info.max_players,
                    "game_in_progress": response_dto.room_info.game_in_progress
                }
            }
        }
        
        # Log for monitoring
        logger.info(f"Player {player_name} joined room: {response_dto.room_info.room_id}")
        
        # Sync to legacy manager
        try:
            await ensure_room_visible_to_legacy(response_dto.room_info.room_id)
        except Exception as sync_error:
            logger.warning(f"Failed to sync room to legacy after join: {sync_error}")
        
        return response
        
    except Exception as e:
        logger.error(f"[ROOM_JOIN_DEBUG] Error joining room: {e}", exc_info=True)
        return {
            "event": "error",
            "data": {
                "message": f"Failed to join room: {str(e)}",
                "type": "room_join_error"
            }
        }


async def _handle_leave_room(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle leave_room request"""
    data = message.get("data", {})
    player_name = data.get("player_name")
    room_id = data.get("room_id")
    
    if not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Player name is required",
                "type": "validation_error"
            }
        }
    
    if not room_id:
        return {
            "event": "error",
            "data": {
                "message": "Room ID is required",
                "type": "validation_error"
            }
        }
    
    try:
        # Generate a player ID if not provided
        player_id = data.get("player_id", f"player_{uuid.uuid4().hex[:8]}")
        
        # Create the request DTO
        request = LeaveRoomRequest(
            player_id=player_id,
            room_id=room_id,
            reason=data.get("reason", "Player left")
        )
        
        # Get dependencies and create use case
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        metrics = get_metrics_collector()
        use_case = LeaveRoomUseCase(uow, event_publisher, metrics)
        
        # Execute the use case
        logger.debug(f"[ROOM_LEAVE_DEBUG] Executing LeaveRoomUseCase for player: {player_name}")
        response_dto = await use_case.execute(request)
        
        # Map the response DTO to WebSocket response format
        response = {
            "event": "left_room",
            "data": {
                "player_name": player_name,
                "room_id": room_id,
                "success": response_dto.success,
                "removed_player_id": response_dto.removed_player_id
            }
        }
        
        # Log for monitoring
        logger.info(f"Player {player_name} left room: {room_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"[ROOM_LEAVE_DEBUG] Error leaving room: {e}", exc_info=True)
        return {
            "event": "error",
            "data": {
                "message": f"Failed to leave room: {str(e)}",
                "type": "room_leave_error"
            }
        }


async def _handle_get_room_state(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle get_room_state request"""
    data = message.get("data", {})
    room_id = data.get("room_id")
    
    if not room_id:
        return {
            "event": "error",
            "data": {
                "message": "Room ID is required",
                "type": "validation_error"
            }
        }
    
    try:
        # Create the request DTO
        request = GetRoomStateRequest(
            room_id=room_id,
            requesting_player_id=data.get("player_id")
        )
        
        # Get dependencies and create use case
        uow = get_unit_of_work()
        metrics = get_metrics_collector()
        use_case = GetRoomStateUseCase(uow, metrics)
        
        # Execute the use case
        logger.debug(f"[ROOM_STATE_DEBUG] Executing GetRoomStateUseCase for room: {room_id}")
        response_dto = await use_case.execute(request)
        
        # Log the players found
        logger.info(f"[ROOM_STATE_DEBUG] Found {len(response_dto.room_info.players)} players in room {room_id}:")
        for p in response_dto.room_info.players:
            logger.info(f"[ROOM_STATE_DEBUG]   - {p.player_name} (bot={p.is_bot}, seat={p.seat_position})")
        
        # Map the response DTO to WebSocket response format
        response = {
            "event": "room_state",
            "data": {
                "room_id": response_dto.room_info.room_id,
                "room_code": response_dto.room_info.room_code,
                "room_name": response_dto.room_info.room_name,
                "host_id": response_dto.room_info.host_id,
                "players": [
                    {
                        "player_id": p.player_id,
                        "name": p.player_name,  # Frontend expects "name" not "player_name"
                        "is_bot": p.is_bot,
                        "is_host": p.is_host,
                        "seat_position": p.seat_position,
                        "avatar_color": getattr(p, 'avatar_color', None)  # Include avatar color if available
                    }
                    for p in response_dto.room_info.players
                ],
                "max_players": response_dto.room_info.max_players,
                "game_in_progress": response_dto.room_info.game_in_progress,
                "current_game_id": response_dto.room_info.current_game_id
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"[ROOM_STATE_DEBUG] Error getting room state: {e}", exc_info=True)
        return {
            "event": "error",
            "data": {
                "message": f"Failed to get room state: {str(e)}",
                "type": "room_state_error"
            }
        }


async def _handle_add_bot(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle add_bot request"""
    data = message.get("data", {})
    room_id = data.get("room_id")
    difficulty = data.get("difficulty", "medium")
    
    if not room_id:
        return {
            "event": "error",
            "data": {
                "message": "Room ID is required",
                "type": "validation_error"
            }
        }
    
    try:
        # Create the request DTO
        request = AddBotRequest(
            room_id=room_id,
            requesting_player_id=data.get("player_id", "host"),
            bot_difficulty=difficulty,
            bot_name=data.get("bot_name")  # Optional custom name
        )
        
        # Get dependencies and create use case
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        bot_service = get_bot_service()
        metrics = get_metrics_collector()
        use_case = AddBotUseCase(uow, event_publisher, bot_service, metrics)
        
        # Execute the use case
        logger.debug(f"[BOT_ADD_DEBUG] Executing AddBotUseCase for room: {room_id}")
        response_dto = await use_case.execute(request)
        
        # Map the response DTO to WebSocket response format
        response = {
            "event": "bot_added",
            "data": {
                "bot_id": response_dto.bot_info.player_id,
                "bot_name": response_dto.bot_info.player_name,
                "difficulty": difficulty,
                "seat_position": response_dto.bot_info.seat_position,
                "success": response_dto.success,
                "room_info": {
                    "room_id": response_dto.room_info.room_id,
                    "players": [
                        {
                            "player_id": p.player_id,
                            "name": p.player_name,  # Frontend expects "name" not "player_name"
                            "is_bot": p.is_bot,
                            "is_host": p.is_host,
                            "seat_position": p.seat_position,
                            "avatar_color": getattr(p, 'avatar_color', None)  # Include avatar color if available
                        }
                        for p in response_dto.room_info.players
                    ]
                }
            }
        }
        
        # Log for monitoring
        logger.info(f"Bot added to room {room_id}: {response_dto.bot_info.player_name}")
        
        return response
        
    except Exception as e:
        logger.error(f"[BOT_ADD_DEBUG] Error adding bot: {e}", exc_info=True)
        return {
            "event": "error",
            "data": {
                "message": f"Failed to add bot: {str(e)}",
                "type": "bot_add_error"
            }
        }


async def _handle_remove_player(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle remove_player request (host removing a player)"""
    data = message.get("data", {})
    room_id = data.get("room_id")
    target_player_id = data.get("target_player_id")
    requesting_player_id = data.get("requesting_player_id")
    
    if not room_id:
        return {
            "event": "error",
            "data": {
                "message": "Room ID is required",
                "type": "validation_error"
            }
        }
    
    if not target_player_id:
        return {
            "event": "error",
            "data": {
                "message": "Target player ID is required",
                "type": "validation_error"
            }
        }
    
    if not requesting_player_id:
        return {
            "event": "error",
            "data": {
                "message": "Requesting player ID is required",
                "type": "validation_error"
            }
        }
    
    try:
        # Create the request DTO
        request = RemovePlayerRequest(
            room_id=room_id,
            requesting_player_id=requesting_player_id,
            target_player_id=target_player_id,
            reason=data.get("reason", "Removed by host")
        )
        
        # Get dependencies and create use case
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        metrics = get_metrics_collector()
        use_case = RemovePlayerUseCase(uow, event_publisher, metrics)
        
        # Execute the use case
        logger.debug(f"[PLAYER_REMOVE_DEBUG] Executing RemovePlayerUseCase for player: {target_player_id}")
        response_dto = await use_case.execute(request)
        
        # Map the response DTO to WebSocket response format
        response = {
            "event": "player_removed",
            "data": {
                "removed_player_id": response_dto.removed_player_id,
                "removed_by": requesting_player_id,
                "success": response_dto.success,
                "room_info": {
                    "room_id": response_dto.room_info.room_id,
                    "players": [
                        {
                            "player_id": p.player_id,
                            "name": p.player_name,  # Frontend expects "name" not "player_name"
                            "is_bot": p.is_bot,
                            "is_host": p.is_host,
                            "seat_position": p.seat_position,
                            "avatar_color": getattr(p, 'avatar_color', None)  # Include avatar color if available
                        }
                        for p in response_dto.room_info.players
                    ]
                }
            }
        }
        
        # Log for monitoring
        logger.info(f"Player {target_player_id} removed from room {room_id} by {requesting_player_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"[PLAYER_REMOVE_DEBUG] Error removing player: {e}", exc_info=True)
        return {
            "event": "error",
            "data": {
                "message": f"Failed to remove player: {str(e)}",
                "type": "player_remove_error"
            }
        }


class RoomAdapterIntegration:
    """
    Integration point for room adapters.
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
        broadcast_func: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """Main entry point for room message handling"""
        if not self._enabled:
            return await self.legacy_handler(websocket, message)
        
        return await handle_room_messages(
            websocket, message, self.legacy_handler, room_state, broadcast_func
        )
    
    def enable(self):
        """Enable room adapters"""
        self._enabled = True
        logger.info("Room adapters enabled")
    
    def disable(self):
        """Disable room adapters (fallback to legacy)"""
        self._enabled = False
        logger.info("Room adapters disabled - using legacy handlers")