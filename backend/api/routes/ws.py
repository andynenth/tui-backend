# backend/api/routes/ws.py

import asyncio
import logging
import uuid
from typing import Optional

# Legacy shared_instances removed - using clean architecture
from infrastructure.websocket.connection_singleton import broadcast, register, unregister, get_connection_id_for_websocket
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.validation import validate_websocket_message
from api.middleware.websocket_rate_limit import (
    check_websocket_rate_limit,
    send_rate_limit_error,
)
from api.websocket.connection_manager import connection_manager
from api.websocket.message_queue import message_queue_manager
# Adapter system removed in Phase 3 Day 5
# from api.routes.ws_adapter_wrapper import adapter_wrapper

# Import clean architecture dependencies
from infrastructure.dependencies import get_unit_of_work
from application.services.room_application_service import RoomApplicationService
from application.services.lobby_application_service import LobbyApplicationService
from application.dto.lobby import GetRoomListRequest
from infrastructure.dependencies import get_event_publisher, get_bot_service, get_metrics_collector
from application.websocket.websocket_config import websocket_config

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter()


async def get_current_player_name(websocket_id: str) -> Optional[str]:
    """Get the player name associated with a WebSocket ID"""
    if websocket_id in connection_manager.websocket_to_player:
        _, player_name = connection_manager.websocket_to_player[websocket_id]
        return player_name
    return None


async def broadcast_with_queue(room_id: str, event: str, data: dict):
    """Broadcast to room and queue messages for disconnected players"""
    # Get list of disconnected players in the room using clean architecture
    try:
        uow = get_unit_of_work()
        async with uow:
            room = await uow.rooms.get_by_id(room_id)
            if room and room.game:
                disconnected_players = []
                for player in room.game.players:
                    if player and hasattr(player, "is_connected") and not player.is_connected:
                        disconnected_players.append(player.name)

                # Queue messages for disconnected players
                for player_name in disconnected_players:
                    await message_queue_manager.queue_message(room_id, player_name, event, data)
    except Exception as e:
        logger.error(f"Error in broadcast_with_queue: {e}", exc_info=True)

    # Broadcast to connected players
    await broadcast(room_id, event, data)


async def handle_disconnect(room_id: str, websocket: WebSocket):
    """Handle player disconnection with bot activation"""
    try:
        # Generate a unique websocket ID for tracking
        websocket_id = getattr(websocket, "_ws_id", None)

        import time

        disconnect_time = time.time()

        logger.info(
            f"🔌 [ROOM_DEBUG] Handling disconnect for room '{room_id}', websocket_id: {websocket_id} at {disconnect_time}"
        )

        # Try to find player by checking all players in the room if websocket_id fails
        connection = None
        if websocket_id:
            # Get connection info
            connection = await connection_manager.handle_disconnect(websocket_id)

        if not connection and room_id != "lobby":
            # Fallback: Check if any player in the room is missing their websocket
            # Get room using clean architecture
            uow_check = get_unit_of_work()
            async with uow_check:
                room = await uow_check.rooms.get_by_id(room_id)
            if room and room.started and room.game:
                # This is a workaround - we should improve the tracking mechanism
                logger.warning(
                    f"Using fallback disconnect detection for room {room_id}"
                )

        if connection and room_id != "lobby":
            # Get room using clean architecture
            uow_check = get_unit_of_work()
            async with uow_check:
                room = await uow_check.rooms.get_by_id(room_id)
            if room and room.is_game_started():  # Only treat as in-game if game started!
                # This is an in-game disconnect
                logger.info(
                    f"🎮 [ROOM_DEBUG] In-game disconnect detected for player '{connection.player_name}' in room '{room_id}'"
                )
                player = None
                if room.game:
                    # Find the player in the game
                    player = room.get_player(connection.player_name)

                if player and not player.is_bot:
                    # Use the player's disconnect method which handles bot activation
                    player.disconnect(room_id=room_id, activate_bot=True)

                    # Create message queue for the disconnected player
                    await message_queue_manager.create_queue(
                        room_id, connection.player_name
                    )

                    logger.info(
                        f"Player {connection.player_name} disconnected from game in room {room_id}. Bot activated."
                    )

                    # Check if disconnecting player was the host
                    new_host = None
                    if room.is_host(connection.player_name):
                        new_host_player = room.migrate_host()
                        new_host = new_host_player.name if new_host_player else None
                        if new_host:
                            logger.info(
                                f"Host migrated to {new_host} in room {room_id}"
                            )

                    # Broadcast disconnect event
                    await broadcast(
                        room_id,
                        "player_disconnected",
                        {
                            "player_name": connection.player_name,
                            "ai_activated": True,
                            "can_reconnect": True,
                            "is_bot": True,
                        },
                    )

                    # Broadcast host change if migration occurred
                    if new_host:
                        await broadcast(
                            room_id,
                            "host_changed",
                            {
                                "old_host": connection.player_name,
                                "new_host": new_host,
                                "message": f"{new_host} is now the host",
                            },
                        )

                    # Save room changes back to repository
                    await uow_check.rooms.save(room)
                    await uow_check.commit()
                    
                    # Check if all remaining players are bots and update status
                    if room.get_human_count() == 0:
                        # Room will automatically be marked as ABANDONED by _update_room_status()
                        logger.info(
                            f"All players in room {room_id} are now bots. Room status: {room.status.value}"
                        )
                        logger.info(
                            f"🤖 [ROOM_DEBUG] Room '{room_id}' has no human players, status: {room.status.value}"
                        )
                else:
                    logger.warning(f"No game object found for started room {room_id}")
            else:
                # This is a pre-game disconnect - treat as leave_room
                logger.info(
                    f"🚪 [ROOM_DEBUG] Pre-game disconnect detected for player '{connection.player_name}' in room '{room_id}'"
                )
                # Reuse existing leave_room logic
                await process_leave_room(room_id, connection.player_name)
        else:
            logger.warning(
                f"No websocket_id found on websocket object for room {room_id}"
            )
            logger.info(
                f"⚠️ [ROOM_DEBUG] WebSocket disconnect without ID for room '{room_id}'"
            )
    except Exception as e:
        logger.error(f"Error handling disconnect: {e}")
    finally:
        # Always unregister the websocket
        connection_id = getattr(websocket, '_connection_id', None) or get_connection_id_for_websocket(websocket)
        if connection_id:
            await unregister(connection_id)
            logger.info(f"🔌 [ROOM_DEBUG] WebSocket unregistered from room '{room_id}' (connection_id: {connection_id})")
        else:
            logger.warning(f"Could not find connection_id for websocket in room '{room_id}'")


async def process_leave_room(room_id: str, player_name: str):
    """Shared logic for handling player leaving room (pre-game)
    This is extracted from the existing leave_room event handler"""
    # Get room using clean architecture
    uow = get_unit_of_work()
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
    if not room:
        logger.warning(f"[ROOM_DEBUG] Room {room_id} not found in process_leave_room")
        return

    # Check if host is leaving
    is_host_leaving = room.is_host(player_name)
    logger.info(
        f"👤 [ROOM_DEBUG] process_leave_room: Player '{player_name}' leaving room '{room_id}', is_host={is_host_leaving}"
    )

    if is_host_leaving:
        # EXISTING host leave logic from leave_room handler
        logger.info(
            f"👑 [ROOM_DEBUG] Host '{player_name}' leaving room '{room_id}' - deleting room"
        )
        await broadcast(
            room_id,
            "room_closed",
            {
                "message": f"Room closed by host {player_name}",
                "reason": "host_left",  # Keep existing reason for compatibility
            },
        )
        # Delete room using clean architecture
        uow_delete = get_unit_of_work()
        async with uow_delete:
            await uow_delete.rooms.delete(room_id)
            await uow_delete.commit()
        logger.info(f"🗑️ [ROOM_DEBUG] Room '{room_id}' deleted because host left")

        # Update lobby with room list using clean architecture
        lobby_service = LobbyApplicationService(
            unit_of_work=get_unit_of_work(),
            metrics=get_metrics_collector()
        )
        list_request = GetRoomListRequest(
            player_id="",
            include_full=False,
            include_in_game=False
        )
        list_response = await lobby_service._get_room_list_use_case.execute(list_request)
        
        # Convert room summaries to legacy format
        available_rooms = [
            {
                "room_id": room.room_id,
                "room_code": room.room_code,
                "room_name": room.room_name,
                "host_name": room.host_name,
                "player_count": room.player_count,
                "max_players": room.max_players,
                "game_in_progress": room.game_in_progress,
                "is_private": room.is_private
            }
            for room in list_response.rooms
        ]
        
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )
    else:
        # EXISTING player leave logic from leave_room handler
        logger.info(f"👤 [ROOM_DEBUG] Player '{player_name}' leaving room '{room_id}'")
        was_host = room.remove_player(player_name)
        
        # Save room changes
        await uow.rooms.save(room)
        await uow.commit()
        
        # Get updated room state
        updated_summary = {
            "players": [
                {"name": p.name, "is_bot": p.is_bot} if p else None
                for p in room.slots
            ],
            "host_name": room.host_name,
            "room_id": room_id,
            "started": room.is_game_started()
        }
        logger.info(
            f"📊 [ROOM_DEBUG] Room state after player left: players={updated_summary['players']}, host={updated_summary['host_name']}"
        )
        await broadcast(
            room_id,
            "room_update",
            {
                "players": updated_summary["players"],
                "host_name": updated_summary["host_name"],
                "room_id": room_id,
                "started": updated_summary["started"],
            },
        )

        # Update lobby with updated room info using clean architecture
        lobby_service = LobbyApplicationService(
            unit_of_work=get_unit_of_work(),
            metrics=get_metrics_collector()
        )
        list_request = GetRoomListRequest(
            player_id="",
            include_full=False,
            include_in_game=False
        )
        list_response = await lobby_service._get_room_list_use_case.execute(list_request)
        
        # Convert room summaries to legacy format
        available_rooms = [
            {
                "room_id": room.room_id,
                "room_code": room.room_code,
                "room_name": room.room_name,
                "host_name": room.host_name,
                "player_count": room.player_count,
                "max_players": room.max_players,
                "game_in_progress": room.game_in_progress,
                "is_private": room.is_private
            }
            for room in list_response.rooms
        ]
        
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time communication within a specific room.
    Also handles special 'lobby' room for lobby updates.
    """
    # Generate unique ID for this websocket
    websocket._ws_id = str(uuid.uuid4())

    import time

    logger.info(
        f"🔌 [ROOM_DEBUG] New WebSocket connection to room '{room_id}', ws_id: {websocket._ws_id} at {time.time()}"
    )

    # Ensure cleanup task is running (fallback if startup event missed)
    start_cleanup_task()

    connection_id = await register(room_id, websocket)
    # Store connection_id on websocket for later retrieval
    websocket._connection_id = connection_id
    
    # For lobby connections, register with the API connection manager as anonymous
    if room_id == "lobby":
        # Use a unique anonymous identifier for lobby connections
        anonymous_player = f"anonymous_{websocket._ws_id[:8]}"
        await connection_manager.register_player(room_id, anonymous_player, websocket._ws_id)
        logger.info(f"Registered anonymous lobby connection: {anonymous_player}")

    # Check if room exists (excluding lobby)
    if room_id != "lobby":
        logger.debug(f"[ROOM_LOOKUP_DEBUG] Checking if room exists: {room_id}")
        logger.debug(f"[ROOM_LOOKUP_DEBUG] Using clean architecture repository")
        
        # Use clean architecture repository to check room existence
        try:
            uow = get_unit_of_work()
            async with uow:
                room = await uow.rooms.get_by_id(room_id)
                logger.debug(f"[ROOM_LOOKUP_DEBUG] Room lookup result: {room is not None}")
                
                if not room:
                    logger.warning(f"[ROOM_LOOKUP_DEBUG] Room {room_id} not found in clean architecture repository!")
                    
                    # Send room_not_found event
                    await websocket.send_json(
                        {
                            "event": "room_not_found",
                            "data": {
                                "room_id": room_id,
                                "message": "This game room no longer exists",
                                "suggestion": "The server may have restarted. Please create or join a new game.",
                                "timestamp": asyncio.get_event_loop().time(),
                            },
                        }
                    )
                    logger.info(f"Sent room_not_found for non-existent room: {room_id}")
                    # Continue running to allow frontend to handle gracefully
                else:
                    logger.info(f"[ROOM_LOOKUP_DEBUG] Room {room_id} found successfully in clean architecture!")
                    
                    # For room connections, we need to register the player
                    # Try to get player name from the first message or use anonymous
                    temp_player_name = f"player_{websocket._ws_id[:8]}"
                    await connection_manager.register_player(room_id, temp_player_name, websocket._ws_id)
                    logger.info(f"Registered temporary player connection: {temp_player_name} for room {room_id}")
        except Exception as e:
            logger.error(f"[ROOM_LOOKUP_DEBUG] Error checking room existence: {e}", exc_info=True)
            # Don't fail the connection, just log the error

    try:
        while True:
            message = await websocket.receive_json()

            # Check if validation should be bypassed
            event_name = message.get("event", "")
            bypass_validation = websocket_config.should_bypass_validation(event_name)
            
            if bypass_validation:
                # Skip validation for use case events
                logger.debug(f"Bypassing validation for use case event: {event_name}")
                sanitized_data = message.get("data", {})
            else:
                # Validate the message structure and content
                is_valid, error_msg, sanitized_data = validate_websocket_message(message)
                if not is_valid:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "data": {
                                "message": f"Invalid message: {error_msg}",
                                "type": "validation_error",
                            },
                        }
                    )
                    continue

            # ===== MESSAGE ROUTING START =====
            # Check if this event should use direct use case routing
            if websocket_config.should_use_use_case(event_name):
                # Use direct message router for use case events
                from application.websocket.message_router import MessageRouter
                from application.websocket.use_case_dispatcher import DispatchContext
                
                # Create message router if not exists
                if not hasattr(websocket_endpoint, '_message_router'):
                    websocket_endpoint._message_router = MessageRouter()
                
                router = websocket_endpoint._message_router
                
                # Route directly to use case
                try:
                    response = await router.route_message(websocket, message, room_id)
                    if response:
                        await websocket.send_json(response)
                    continue  # Skip adapter/legacy handling
                except Exception as e:
                    logger.error(f"Error in direct use case routing: {e}", exc_info=True)
                    await websocket.send_json({
                        "event": "error",
                        "data": {
                            "message": f"Failed to process {event_name}",
                            "type": "use_case_error",
                            "details": str(e)
                        }
                    })
                    continue
            
            # ===== ADAPTER SYSTEM REMOVED =====
            # Adapter system was removed in Phase 3 Day 5
            # All events now use direct use case routing
            # Non-migrated events fall through to error handling below
            
            # If we reach here, the event was not handled
            logger.warning(f"Unhandled event: {event_name}")
            await websocket.send_json({
                "event": "error",
                "data": {
                    "message": f"Event '{event_name}' is not supported",
                    "type": "unsupported_event"
                }
            })
            continue


            # ===== LEGACY HANDLERS REMOVED =====
            # Date: 2025-07-27
            # Reason: This code is NEVER executed when adapters are enabled
            # The continue statement on line 330 prevents execution from reaching here
            # Original code preserved in ws.py.backup_before_legacy_removal
            #
            # Statistics:
            # - Lines removed: 333-1738 (~1,405 lines of dead code)
            # - All functionality handled by clean architecture adapters
            # - No impact on system operation
            #
            # To restore if needed:
            # cp api/routes/ws.py.backup_before_legacy_removal api/routes/ws.py
            # =====================================

            # Legacy handler code has been removed. See backup file for original.
            pass  # This pass statement maintains the code structure
    except WebSocketDisconnect:
        await handle_disconnect(room_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error in room {room_id}: {e}")
        await handle_disconnect(room_id, websocket)


# Adapter status endpoint removed in Phase 3 Day 5
# @router.get("/ws/adapter-status")
# async def get_adapter_status():
#     """Get current adapter integration status"""
#     return adapter_wrapper.get_status()


async def room_cleanup_task():
    """Background task to clean up abandoned rooms"""
    iteration_count = 0
    logger.info("🧹 [ROOM_DEBUG] Room cleanup task started")

    while True:
        try:
            iteration_count += 1
            rooms_to_cleanup = []

            # Get all rooms using clean architecture
            all_room_ids = []
            try:
                uow = get_unit_of_work()
                async with uow:
                    # Get all rooms (both active and inactive)
                    clean_rooms = await uow.rooms.list_active(limit=1000)
                    all_room_ids = [room.room_id for room in clean_rooms]
                    logger.debug(f"🧹 [ROOM_DEBUG] Found {len(all_room_ids)} rooms in clean architecture")
            except Exception as e:
                logger.error(f"🧹 [ROOM_DEBUG] Error getting rooms from clean architecture: {e}")

            if all_room_ids:
                logger.info(
                    f"🧹 [ROOM_DEBUG] Cleanup iteration {iteration_count}: Checking {len(all_room_ids)} rooms: {all_room_ids}"
                )

            for room_id in all_room_ids:
                # Get room using clean architecture
                uow_check = get_unit_of_work()
                async with uow_check:
                    room = await uow_check.rooms.get_by_id(room_id)
                if room:
                    # Check cleanup conditions using domain logic
                    # For clean architecture rooms, check if room has no human players
                    has_humans = any(slot and not slot.is_bot for slot in room.slots)
                    game_ended = False  # Clean architecture doesn't track game_ended
                    
                    # Check if room should be cleaned up based on status
                    should_cleanup = (
                        room.status.value in ["COMPLETED", "ABANDONED"] or
                        (not has_humans and room.status.value == "IN_GAME")
                    )
                    logger.info(
                        f"🧹 CLEANUP_CHECK: Room {room_id} - game_ended={game_ended}, should_cleanup={should_cleanup}"
                    )
                    if should_cleanup:
                        rooms_to_cleanup.append(room_id)
                        logger.info(
                            f"🧹 [ROOM_DEBUG] Room '{room_id}' marked for cleanup"
                        )

            # Clean up rooms
            if rooms_to_cleanup:
                logger.info(
                    f"🧹 [ROOM_DEBUG] Cleaning up {len(rooms_to_cleanup)} rooms: {rooms_to_cleanup}"
                )

            for room_id in rooms_to_cleanup:
                # Get room and double-check cleanup conditions
                uow_delete = get_unit_of_work()
                async with uow_delete:
                    room = await uow_delete.rooms.get_by_id(room_id)
                    
                    if room:
                        # Re-check cleanup conditions
                        has_humans = any(slot and not slot.is_bot for slot in room.slots)
                        should_still_cleanup = (
                            room.status.value in ["COMPLETED", "ABANDONED"] or
                            (not has_humans and room.status.value == "IN_GAME")
                        )
                    else:
                        should_still_cleanup = False
                    
                if room and should_still_cleanup:
                    logger.info(
                        f"🧹 [ROOM_DEBUG] Cleaning up abandoned room {room_id} (no human players)"
                    )

                    # Bot unregistration handled by clean architecture
                    # Legacy bot_manager.unregister_game(room_id) no longer needed
                    # Clean architecture handles bot lifecycle automatically

                    # Broadcast room closed
                    await broadcast(
                        room_id,
                        "room_closed",
                        {
                            "reason": "All players disconnected",
                            "timeout_seconds": 30,  # Using fixed timeout since clean arch rooms don't have CLEANUP_TIMEOUT_SECONDS
                        },
                    )

                    # Delete room using clean architecture
                    async with uow_delete:
                        await uow_delete.rooms.delete(room_id)
                        await uow_delete.commit()

                    logger.info(
                        f"✅ [ROOM_DEBUG] Room {room_id} cleaned up successfully"
                    )

        except Exception as e:
            logger.error(f"Error in room cleanup task: {e}")

        # Run every 5 seconds
        await asyncio.sleep(5)


# Start the cleanup task when the module is imported
# This will run in the background
cleanup_task_started = False


def start_cleanup_task():
    global cleanup_task_started
    if not cleanup_task_started:
        cleanup_task_started = True
        logger.info("🧹 [ROOM_DEBUG] Starting room cleanup background task")
        asyncio.create_task(room_cleanup_task())
    else:
        logger.info("🧹 [ROOM_DEBUG] Room cleanup task already running")
