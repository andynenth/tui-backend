"""
WebSocket Use Case Dispatcher
Direct integration between WebSocket messages and clean architecture use cases.
Replaces the adapter layer with direct DTO transformation and use case execution.
"""

from typing import Dict, Any, Optional, Callable, Union
import uuid
import time
import logging
from dataclasses import dataclass

# Import dependencies
from infrastructure.dependencies import (
    get_unit_of_work,
    get_event_publisher,
    get_metrics_collector,
    get_bot_service,
)

# Import all use cases
from application.use_cases.connection import (
    HandlePingUseCase,
    MarkClientReadyUseCase,
    AcknowledgeMessageUseCase,
    SyncClientStateUseCase,
)
from application.use_cases.room_management import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    LeaveRoomUseCase,
    GetRoomStateUseCase,
    AddBotUseCase,
    RemovePlayerUseCase,
)
from application.use_cases.lobby import GetRoomListUseCase, GetRoomDetailsUseCase
from application.use_cases.game import (
    StartGameUseCase,
    DeclareUseCase,
    PlayUseCase,
    RequestRedealUseCase,
    AcceptRedealUseCase,
    DeclineRedealUseCase,
    HandleRedealDecisionUseCase,
    MarkPlayerReadyUseCase,
    LeaveGameUseCase,
)

# Import DTOs
from application.dto.connection import (
    HandlePingRequest,
    HandlePingResponse,
    MarkClientReadyRequest,
    MarkClientReadyResponse,
    AcknowledgeMessageRequest,
    AcknowledgeMessageResponse,
    SyncClientStateRequest,
    SyncClientStateResponse,
)
from application.dto.room_management import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse,
    LeaveRoomRequest,
    LeaveRoomResponse,
    GetRoomStateRequest,
    GetRoomStateResponse,
    AddBotRequest,
    AddBotResponse,
    RemovePlayerRequest,
    RemovePlayerResponse,
)
from application.dto.lobby import GetRoomListRequest, GetRoomDetailsRequest
from application.dto.game import (
    StartGameRequest,
    StartGameResponse,
    DeclareRequest,
    DeclareResponse,
    PlayRequest,
    PlayResponse,
    RequestRedealRequest,
    RequestRedealResponse,
    AcceptRedealRequest,
    AcceptRedealResponse,
    DeclineRedealRequest,
    DeclineRedealResponse,
    MarkPlayerReadyRequest,
    MarkPlayerReadyResponse,
    LeaveGameRequest,
    LeaveGameResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class DispatchContext:
    """Context for use case dispatch"""

    websocket: Any
    room_id: str
    room_state: Optional[Dict[str, Any]] = None
    player_id: Optional[str] = None
    player_name: Optional[str] = None


class UseCaseDispatcher:
    """
    Dispatches WebSocket events directly to use cases.
    Handles DTO transformation and response formatting.
    """

    def __init__(self):
        """Initialize dispatcher with dependencies"""
        self.uow = get_unit_of_work()
        self.event_publisher = get_event_publisher()
        self.metrics = get_metrics_collector()
        self.bot_service = get_bot_service()

        # Game-specific services will be created as needed
        self.game_service = None
        self.game_state_store = None

        # Initialize use cases (could be lazy-loaded for optimization)
        self._init_use_cases()

        # Map events to handler methods
        self.event_handlers = {
            # Connection events
            "ping": self._handle_ping,
            "client_ready": self._handle_client_ready,
            "ack": self._handle_ack,
            "sync_request": self._handle_sync_request,
            # Room management events
            "create_room": self._handle_create_room,
            "join_room": self._handle_join_room,
            "leave_room": self._handle_leave_room,
            "get_room_state": self._handle_get_room_state,
            "add_bot": self._handle_add_bot,
            "remove_player": self._handle_remove_player,
            # Lobby events
            "request_room_list": self._handle_request_room_list,
            "get_rooms": self._handle_get_rooms,  # Alias for request_room_list
            # Game events
            "start_game": self._handle_start_game,
            "declare": self._handle_declare,
            "play": self._handle_play,
            "play_pieces": self._handle_play,  # Alias for play
            "request_redeal": self._handle_request_redeal,
            "accept_redeal": self._handle_accept_redeal,
            "decline_redeal": self._handle_decline_redeal,
            "redeal_decision": self._handle_redeal_decision,
            "player_ready": self._handle_player_ready,
            "leave_game": self._handle_leave_game,
        }

    def _init_use_cases(self):
        """Initialize all use cases"""
        # Connection use cases
        self.ping_use_case = HandlePingUseCase(self.uow, self.metrics)
        self.client_ready_use_case = MarkClientReadyUseCase(
            self.uow, self.event_publisher
        )
        self.ack_use_case = AcknowledgeMessageUseCase(self.uow)
        self.sync_use_case = SyncClientStateUseCase(self.uow)

        # Room management use cases
        self.create_room_use_case = CreateRoomUseCase(
            self.uow, self.event_publisher, self.metrics
        )
        self.join_room_use_case = JoinRoomUseCase(
            self.uow, self.event_publisher, self.metrics
        )
        self.leave_room_use_case = LeaveRoomUseCase(
            self.uow, self.event_publisher, self.metrics
        )
        self.get_room_state_use_case = GetRoomStateUseCase(self.uow)
        self.add_bot_use_case = AddBotUseCase(
            self.uow, self.event_publisher, self.bot_service, self.metrics
        )
        self.remove_player_use_case = RemovePlayerUseCase(
            self.uow, self.event_publisher, self.metrics
        )

        # Lobby use cases
        self.get_room_list_use_case = GetRoomListUseCase(self.uow)
        self.get_room_details_use_case = GetRoomDetailsUseCase(self.uow)

        # Game use cases - Initialize with None for game services
        # These will be properly initialized when game services are available
        try:
            # Try to get game services if available
            from engine.game_service import GameService
            from infrastructure.game_state_store import InMemoryGameStateStore

            self.game_service = GameService()
            self.game_state_store = InMemoryGameStateStore()
        except ImportError:
            logger.warning(
                "Game services not available, game use cases will be limited"
            )
            self.game_service = None
            self.game_state_store = None

        # Initialize game use cases with available services
        if self.game_service and self.game_state_store:
            self.start_game_use_case = StartGameUseCase(
                self.uow, self.event_publisher, self.game_service, self.metrics
            )
            self.declare_use_case = DeclareUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
            self.play_use_case = PlayUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
            self.request_redeal_use_case = RequestRedealUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
            self.accept_redeal_use_case = AcceptRedealUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
            self.decline_redeal_use_case = DeclineRedealUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
            self.redeal_decision_use_case = HandleRedealDecisionUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
            self.player_ready_use_case = MarkPlayerReadyUseCase(
                self.uow, self.event_publisher, self.metrics
            )
            self.leave_game_use_case = LeaveGameUseCase(
                self.uow, self.event_publisher, self.game_state_store, self.metrics
            )
        else:
            # Set to None if game services not available
            self.start_game_use_case = None
            self.declare_use_case = None
            self.play_use_case = None
            self.request_redeal_use_case = None
            self.accept_redeal_use_case = None
            self.decline_redeal_use_case = None
            self.redeal_decision_use_case = None
            self.player_ready_use_case = None
            self.leave_game_use_case = None

    async def dispatch(
        self, event: str, data: Dict[str, Any], context: DispatchContext
    ) -> Optional[Dict[str, Any]]:
        """
        Dispatch an event to the appropriate use case.

        Args:
            event: The event name
            data: The event data
            context: The dispatch context with WebSocket and room info

        Returns:
            Response dict or None if event not handled
        """
        logger.info(
            f"[DISPATCH_DEBUG] Dispatching event '{event}' from player '{context.player_name}' in room '{context.room_id}'"
        )
        handler = self.event_handlers.get(event)
        if not handler:
            logger.warning(f"No handler found for event: {event}")
            return None

        try:
            result = await handler(data, context)
            logger.info(f"[DISPATCH_DEBUG] Event '{event}' handled successfully")
            return result
        except Exception as e:
            logger.error(f"Error handling event {event}: {e}", exc_info=True)
            return {
                "event": "error",
                "data": {
                    "message": f"Failed to handle {event}",
                    "type": "use_case_error",
                    "details": str(e),
                },
            }

    # Connection event handlers

    async def _handle_ping(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle ping event"""
        request = HandlePingRequest(
            player_id=context.player_id or "anonymous",
            room_id=context.room_id,
            sequence_number=data.get("sequence", 0),
        )

        response = await self.ping_use_case.execute(request)

        return {
            "event": "pong",
            "data": {
                "server_time": (
                    response.server_time.isoformat()
                    if hasattr(response, "server_time")
                    else time.time()
                ),
                "sequence": (
                    response.sequence_number
                    if hasattr(response, "sequence_number")
                    else request.sequence_number
                ),
            },
        }

    async def _handle_client_ready(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle client_ready event"""
        # For room connections, we need to get the player info from the data
        player_id = context.player_id or data.get("player_id")
        player_name = context.player_name or data.get("player_name")

        logger.info(
            f"_handle_client_ready: room_id={context.room_id}, player_name={player_name}, player_id={player_id}"
        )
        logger.info(f"Room state available: {context.room_state is not None}")

        # If we still don't have player_id but have player_name and room_id, find it
        if not player_id and player_name and context.room_id != "lobby":
            # Try to find the player in the room state by matching name
            if context.room_state and context.room_state.get("players"):
                logger.info(
                    f"Looking for player {player_name} in room state with {len(context.room_state['players'])} players"
                )
                for player in context.room_state["players"]:
                    logger.info(
                        f"  Slot {player.get('seat_position')}: name={player.get('name')}, player_id={player.get('player_id')}"
                    )
                    if player.get("name") == player_name:
                        player_id = player.get("player_id")
                        logger.info(f"Found matching player_id: {player_id}")
                        break

            # If still no player_id, try to generate it based on the expected format
            if not player_id and context.room_state:
                # Look for the player by name in the room state to get their slot
                for player in context.room_state.get("players", []):
                    if player.get("name") == player_name:
                        seat_position = player.get("seat_position")
                        if seat_position is not None:
                            player_id = f"{context.room_id}_p{seat_position}"
                            logger.info(
                                f"Generated player_id based on seat position: {player_id}"
                            )
                            break

        # Default to anonymous for lobby connections without player info
        if not player_id and context.room_id == "lobby":
            player_id = "anonymous"
        elif not player_id:
            # For room connections, we need a valid player_id
            logger.error(
                f"Could not determine player_id for {player_name} in room {context.room_id}"
            )
            return {
                "event": "error",
                "data": {
                    "message": "Could not determine player identity",
                    "type": "validation_error",
                },
            }

        request = MarkClientReadyRequest(
            player_id=player_id,
            room_id=context.room_id,
            client_version=data.get("version", "unknown"),
        )

        response = await self.client_ready_use_case.execute(request)

        # Log what we're sending back
        response_data = {
            "event": "client_ready_ack",
            "data": {
                "success": response.success,
                "ready": response.is_ready if hasattr(response, "is_ready") else True,
                "room_state": context.room_state,  # Include room state in response
            },
        }

        logger.info(
            f"Sending client_ready_ack response: success={response.success}, has_room_state={context.room_state is not None}"
        )
        if context.room_state:
            logger.info(
                f"Room state players: {[p.get('name') for p in context.room_state.get('players', [])]}"
            )

        return response_data

    async def _handle_ack(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle ack event"""
        request = AcknowledgeMessageRequest(
            player_id=context.player_id or "anonymous",
            message_id=data.get("message_id", ""),
            message_type=data.get("message_type", "unknown"),
            room_id=context.room_id,
        )

        response = await self.ack_use_case.execute(request)

        return {
            "event": "ack_received",
            "data": {
                "message_id": response.message_id,
                "acknowledged": response.acknowledged,
            },
        }

    async def _handle_sync_request(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle sync_request event"""
        request = SyncClientStateRequest(
            player_id=context.player_id or "anonymous",
            room_id=context.room_id,
            last_known_sequence=data.get("last_sequence", 0),
        )

        response = await self.sync_use_case.execute(request)

        return {
            "event": "sync_response",
            "data": {
                "room_state": response.room_state,
                "game_state": response.game_state,
                "events_missed": (
                    response.events_missed if hasattr(response, "events_missed") else 0
                ),
                "current_sequence": response.current_sequence,
            },
        }

    # Room management event handlers

    async def _handle_create_room(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle create_room event"""
        player_name = data.get("player_name")
        if not player_name:
            return {
                "event": "error",
                "data": {
                    "message": "Player name is required",
                    "type": "validation_error",
                },
            }

        # Generate player ID if not provided
        player_id = data.get("player_id", f"player_{uuid.uuid4().hex[:8]}")

        request = CreateRoomRequest(
            host_player_id=player_id,
            host_player_name=player_name,
            room_name=data.get("room_name"),
            max_players=data.get("max_players", 4),
            win_condition_type=data.get("win_condition_type", "score"),
            win_condition_value=data.get("win_condition_value", 50),
            allow_bots=data.get("allow_bots", True),
            is_private=data.get("is_private", False),
        )

        response = await self.create_room_use_case.execute(request)

        # Ensure legacy visibility if needed
        if response.success:
            await self._ensure_legacy_visibility(response.room_info.room_id)

        return {
            "event": "room_created",
            "data": {
                "room_id": response.room_info.room_id,
                "room_code": response.join_code,
                "host_name": player_name,
                "success": response.success,
                "room_info": self._format_room_info(response.room_info),
            },
        }

    async def _handle_join_room(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle join_room event"""
        player_name = data.get("player_name")
        room_id = data.get("room_id") or context.room_id

        if not player_name:
            return {
                "event": "error",
                "data": {
                    "message": "Player name is required",
                    "type": "validation_error",
                },
            }

        # Generate player ID if not provided
        player_id = data.get("player_id", f"{room_id}_p{uuid.uuid4().hex[:4]}")

        request = JoinRoomRequest(
            room_id=room_id,
            player_id=player_id,
            player_name=player_name,
            room_code=data.get("join_code") or data.get("room_code"),
            seat_preference=data.get("seat_preference"),
        )

        response = await self.join_room_use_case.execute(request)

        if response.success:
            return {
                "event": "room_joined",
                "data": {
                    "success": True,
                    "room_id": room_id,
                    "player_id": player_id,
                    "seat_position": response.seat_position,
                    "is_host": response.is_host,
                    "room_info": self._format_room_info(response.room_info),
                },
            }
        else:
            return {
                "event": "join_failed",
                "data": {
                    "success": False,
                    "error": getattr(response, "error", "Failed to join room"),
                },
            }

    async def _handle_leave_room(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle leave_room event"""
        player_id = data.get("player_id") or context.player_id
        room_id = data.get("room_id") or context.room_id

        if not player_id:
            return {
                "event": "error",
                "data": {
                    "message": "Player ID is required",
                    "type": "validation_error",
                },
            }

        request = LeaveRoomRequest(room_id=room_id, player_id=player_id)

        response = await self.leave_room_use_case.execute(request)

        return {
            "event": "left_room",
            "data": {
                "success": response.success,
                "room_id": room_id,
                "player_id": player_id,
                "new_host_id": response.new_host_id,
            },
        }

    async def _handle_get_room_state(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle get_room_state event"""
        room_id = data.get("room_id") or context.room_id

        request = GetRoomStateRequest(
            room_id=room_id, requesting_player_id=context.player_id
        )

        response = await self.get_room_state_use_case.execute(request)

        if response.room_info:
            formatted_room = self._format_room_info(response.room_info)
            logger.info(
                f"Sending room_state for {room_id}: {len(formatted_room.get('players', []))} players"
            )
            logger.info(
                f"Players: {[p['name'] for p in formatted_room.get('players', [])]}"
            )

            # Frontend expects room_update event with room data directly
            return {
                "event": "room_update",
                "data": formatted_room,  # Send room data directly, not nested
            }
        else:
            return {
                "event": "error",
                "data": {"message": "Room not found", "type": "room_not_found"},
            }

    async def _handle_add_bot(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle add_bot event"""
        room_id = data.get("room_id") or context.room_id

        # Handle both slot_id (frontend uses 1-4) and seat_position (backend uses 0-3)
        seat_position = data.get("seat_position")
        if seat_position is None and "slot_id" in data:
            # Convert frontend slot_id (1-4) to backend seat_position (0-3)
            slot_id = data.get("slot_id")
            if isinstance(slot_id, int) and 1 <= slot_id <= 4:
                seat_position = slot_id - 1
                logger.info(
                    f"[BOT_SLOT_FIX] Converted slot_id {slot_id} to seat_position {seat_position}"
                )
            else:
                logger.warning(f"[BOT_SLOT_FIX] Invalid slot_id received: {slot_id}")

        request = AddBotRequest(
            room_id=room_id,
            requesting_player_id=context.player_id
            or data.get("requester_id")
            or "anonymous",
            bot_difficulty=data.get("difficulty", "medium"),
            bot_name=data.get("bot_name"),
            seat_position=seat_position,
        )

        response = await self.add_bot_use_case.execute(request)

        # Add manual broadcast for room update
        formatted_room = self._format_room_info(response.room_info)
        from infrastructure.websocket.connection_singleton import broadcast

        await broadcast(room_id, "room_update", formatted_room)

        return {
            "event": "bot_added",
            "data": {
                "success": True,
                "bot_id": response.bot_info.player_id,
                "bot_name": response.bot_info.player_name,
                "room_info": formatted_room,
            },
        }

    async def _handle_remove_player(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle remove_player event"""
        room_id = data.get("room_id") or context.room_id
        player_to_remove = data.get("player_id")

        logger.info(
            f"[REMOVE_PLAYER_DEBUG] Room: {room_id}, Player to remove: {player_to_remove}"
        )
        logger.info(f"[REMOVE_PLAYER_DEBUG] Request data: {data}")

        if not player_to_remove:
            return {
                "event": "error",
                "data": {
                    "message": "Player ID to remove is required",
                    "type": "validation_error",
                },
            }

        # Get the player name before removal for the kick message
        removed_player_name = "Unknown"
        try:
            async with self.uow:
                room = await self.uow.rooms.get_by_id(room_id)
                if room and player_to_remove.startswith(f"{room_id}_p"):
                    try:
                        slot_index = int(player_to_remove.split("_p")[1])
                        if 0 <= slot_index < len(room.slots) and room.slots[slot_index]:
                            removed_player_name = room.slots[slot_index].name
                    except (ValueError, IndexError):
                        pass
        except Exception as e:
            logger.warning(f"Failed to get removed player name: {e}")

        request = RemovePlayerRequest(
            room_id=room_id,
            target_player_id=player_to_remove,
            requesting_player_id=context.player_id
            or data.get("requester_id")
            or "anonymous",
            reason=data.get("reason"),
        )

        response = await self.remove_player_use_case.execute(request)

        # If we get here, the operation was successful
        formatted_room = self._format_room_info(response.room_info)

        # Send redirect message to the removed player BEFORE broadcasting room update
        from infrastructure.websocket.connection_singleton import (
            broadcast,
            send_to_player,
        )

        if not response.was_bot:
            # Broadcast player_kicked message to the entire room - the frontend will check if it's for them
            kick_message_data = {
                "reason": "You have been removed from the room",
                "redirect_to": "/lobby",
                "removed_by": context.player_name or "Host",
                "removed_player_name": removed_player_name,
            }
            try:
                await broadcast(room_id, "player_kicked", kick_message_data)
                logger.info(f"Broadcasted kick notification for removed player")
            except Exception as e:
                logger.warning(f"Failed to broadcast kick notification: {e}")

        # Broadcast the updated room state to remaining clients
        await broadcast(room_id, "room_update", formatted_room)

        return {
            "event": "player_removed",
            "data": {
                "success": True,
                "removed_player_id": response.removed_player_id,
                "was_bot": response.was_bot,
                "room_info": formatted_room,
            },
        }

    # Lobby event handlers

    async def _handle_request_room_list(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle request_room_list event"""
        request = GetRoomListRequest(
            player_id=context.player_id,
            include_private=data.get("include_private", False),
            include_full=data.get(
                "include_full", True
            ),  # Show full rooms by default so newly created rooms are visible
            include_in_game=data.get("include_in_game", False),
        )

        response = await self.get_room_list_use_case.execute(request)

        # Need to fetch full room details to get players
        rooms_with_players = []
        async with self.uow:
            for room_summary in response.rooms:
                # Get full room details
                room = await self.uow.rooms.get_by_id(room_summary.room_id)
                if room:
                    rooms_with_players.append(
                        {
                            "room_id": room.room_id,
                            "room_code": room_summary.room_code,
                            "room_name": room_summary.room_name,
                            "host_name": room.host_name,
                            "player_count": room_summary.player_count,
                            "max_players": room_summary.max_players,
                            "game_in_progress": room_summary.game_in_progress,
                            "is_private": room_summary.is_private,
                            "players": [
                                (
                                    {"name": slot.name, "is_bot": slot.is_bot}
                                    if slot
                                    else None
                                )
                                for slot in room.slots
                            ],
                        }
                    )

        return {
            "event": "room_list_update",
            "data": {"rooms": rooms_with_players, "total_count": response.total_items},
        }

    async def _handle_get_rooms(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle get_rooms event (alias for request_room_list)"""
        logger.info(
            f"[GET_ROOMS_DEBUG] Received get_rooms request from {context.player_name} in room {context.room_id}"
        )
        result = await self._handle_request_room_list(data, context)
        logger.info(f"[GET_ROOMS_DEBUG] Returning {len(result['data']['rooms'])} rooms")
        return result

    # Game event handlers

    async def _handle_start_game(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle start_game event"""
        if not self.start_game_use_case:
            return {
                "event": "error",
                "data": {
                    "message": "Game service not available",
                    "type": "service_unavailable",
                },
            }

        room_id = data.get("room_id") or context.room_id

        request = StartGameRequest(
            room_id=room_id,
            requesting_player_id=context.player_id
            or data.get("requester_id")
            or "anonymous",
        )

        response = await self.start_game_use_case.execute(request)

        if response.success:
            return {
                "event": "game_started",
                "data": {
                    "success": True,
                    "game_id": response.game_id,
                    "initial_state": response.initial_state,
                },
            }
        else:
            return {
                "event": "error",
                "data": {
                    "message": response.error_message or "Failed to start game",
                    "type": "start_game_failed",
                },
            }

    async def _handle_declare(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle declare event"""
        room_id = data.get("room_id") or context.room_id

        request = DeclareRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            pile_count=data.get("pile_count", 0),
        )

        response = await self.declare_use_case.execute(request)

        if response.success:
            return {
                "event": "declaration_made",
                "data": {
                    "success": True,
                    "player_id": request.player_id,
                    "pile_count": request.pile_count,
                    "all_declared": response.all_players_declared,
                    "game_state": response.game_state,
                },
            }
        else:
            return {
                "event": "error",
                "data": {
                    "message": response.error_message or "Failed to make declaration",
                    "type": "declare_failed",
                },
            }

    async def _handle_play(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle play/play_pieces event"""
        room_id = data.get("room_id") or context.room_id

        request = PlayRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            pieces=data.get("pieces", []),
        )

        response = await self.play_use_case.execute(request)

        if response.success:
            return {
                "event": "play_made",
                "data": {
                    "success": True,
                    "player_id": request.player_id,
                    "pieces_played": response.pieces_played,
                    "turn_winner": response.turn_winner,
                    "round_complete": response.round_complete,
                    "game_complete": response.game_complete,
                    "game_state": response.game_state,
                },
            }
        else:
            return {
                "event": "error",
                "data": {
                    "message": response.error_message or "Invalid play",
                    "type": "play_failed",
                },
            }

    async def _handle_request_redeal(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle request_redeal event"""
        room_id = data.get("room_id") or context.room_id

        request = RequestRedealRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            hand_strength_score=data.get("hand_strength_score"),
        )

        response = await self.request_redeal_use_case.execute(request)

        if response.success:
            return {
                "event": "redeal_requested",
                "data": {
                    "success": True,
                    "requester_id": request.player_id,
                    "reason": request.reason,
                    "votes_needed": response.votes_needed,
                    "current_votes": response.current_votes,
                },
            }
        else:
            return {
                "event": "error",
                "data": {
                    "message": response.error_message or "Cannot request redeal",
                    "type": "redeal_request_failed",
                },
            }

    async def _handle_accept_redeal(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle accept_redeal event"""
        room_id = data.get("room_id") or context.room_id

        request = AcceptRedealRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            redeal_id=data.get("redeal_id", ""),
        )

        response = await self.accept_redeal_use_case.execute(request)

        return {
            "event": "redeal_vote_cast",
            "data": {
                "success": response.success,
                "voter_id": request.player_id,
                "vote": "accept",
                "redeal_approved": response.redeal_approved,
                "votes_for": response.votes_for,
                "votes_needed": response.votes_needed,
            },
        }

    async def _handle_decline_redeal(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle decline_redeal event"""
        room_id = data.get("room_id") or context.room_id

        request = DeclineRedealRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            redeal_id=data.get("redeal_id", ""),
        )

        response = await self.decline_redeal_use_case.execute(request)

        return {
            "event": "redeal_vote_cast",
            "data": {
                "success": response.success,
                "voter_id": request.player_id,
                "vote": "decline",
                "redeal_rejected": response.redeal_rejected,
                "votes_against": response.votes_against,
            },
        }

    async def _handle_redeal_decision(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle redeal_decision event"""
        room_id = data.get("room_id") or context.room_id
        decision = data.get("decision", "").lower()

        if decision == "accept":
            return await self._handle_accept_redeal(data, context)
        elif decision == "decline":
            return await self._handle_decline_redeal(data, context)
        else:
            return {
                "event": "error",
                "data": {
                    "message": "Invalid redeal decision. Must be 'accept' or 'decline'",
                    "type": "validation_error",
                },
            }

    async def _handle_player_ready(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle player_ready event"""
        room_id = data.get("room_id") or context.room_id

        request = MarkPlayerReadyRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            ready_for_phase=data.get("phase", "next"),
        )

        response = await self.player_ready_use_case.execute(request)

        return {
            "event": "player_ready_updated",
            "data": {
                "success": response.success,
                "player_id": request.player_id,
                "ready": request.ready_state,
                "all_players_ready": response.all_players_ready,
            },
        }

    async def _handle_leave_game(
        self, data: Dict[str, Any], context: DispatchContext
    ) -> Dict[str, Any]:
        """Handle leave_game event"""
        room_id = data.get("room_id") or context.room_id

        request = LeaveGameRequest(
            game_id=data.get("game_id") or room_id,  # Use room_id as fallback
            player_id=context.player_id or data.get("player_id"),
            reason=data.get("reason"),
        )

        response = await self.leave_game_use_case.execute(request)

        return {
            "event": "player_left_game",
            "data": {
                "success": response.success,
                "player_id": request.player_id,
                "game_ended": response.game_ended,
                "reason": response.reason,
            },
        }

    # Helper methods

    def _format_room_info(self, room_info) -> Dict[str, Any]:
        """Format room info DTO for WebSocket response"""
        # Handle different status types
        status = room_info.status
        if hasattr(status, "value"):
            status = status.value
        elif not isinstance(status, str):
            status = str(status)

        # Find host name from players
        host_name = "Unknown Host"
        for player in room_info.players:
            if player.is_host:
                host_name = player.player_name
                break

        return {
            "room_id": room_info.room_id,
            "room_code": room_info.room_code,
            "room_name": room_info.room_name,
            "host_id": room_info.host_id,
            "host_name": host_name,  # Add missing host_name field
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.player_name,  # Frontend expects "name"
                    "is_bot": p.is_bot,
                    "is_host": p.is_host,
                    "seat_position": p.seat_position,
                    "avatar_color": getattr(p, "avatar_color", None),
                }
                for p in room_info.players
            ],
            "max_players": room_info.max_players,
            "game_in_progress": room_info.game_in_progress,
            "started": room_info.game_in_progress,  # Add missing started field
            "status": status,
        }

    async def _ensure_legacy_visibility(self, room_id: str) -> None:
        """Ensure room is visible to legacy system if needed"""
        try:
            # Import inside function to avoid circular imports
            from infrastructure.adapters.legacy_repository_bridge import (
                ensure_room_visible_to_legacy,
            )

            await ensure_room_visible_to_legacy(room_id)
            logger.debug(f"Room {room_id} synced to legacy system")
        except ImportError:
            logger.debug(
                f"Legacy bridge not available, skipping sync for room {room_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to sync room {room_id} to legacy system: {e}")
