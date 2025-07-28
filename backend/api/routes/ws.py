# backend/api/routes/ws.py

import asyncio
import logging
import uuid
from typing import Optional

from shared_instances import shared_room_manager
from infrastructure.websocket.broadcast_adapter import broadcast, register, unregister
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.validation import validate_websocket_message
from api.middleware.websocket_rate_limit import (
    check_websocket_rate_limit,
    send_rate_limit_error,
)
from api.websocket.connection_manager import connection_manager
from api.websocket.message_queue import message_queue_manager
from api.routes.ws_adapter_wrapper import adapter_wrapper

# Import clean architecture dependencies
from infrastructure.dependencies import get_unit_of_work

# Set up logging
logger = logging.getLogger(__name__)


router = APIRouter()
room_manager = shared_room_manager


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
            room = await room_manager.get_room(room_id)
            if room and room.started and room.game:
                # This is a workaround - we should improve the tracking mechanism
                logger.warning(
                    f"Using fallback disconnect detection for room {room_id}"
                )

        if connection and room_id != "lobby":
            room = await room_manager.get_room(room_id)
            if room and room.started:  # Only treat as in-game if game started!
                # This is an in-game disconnect
                logger.info(
                    f"🎮 [ROOM_DEBUG] In-game disconnect detected for player '{connection.player_name}' in room '{room_id}'"
                )
                if room.game:
                    # Find the player in the game
                    player = next(
                        (
                            p
                            for p in room.game.players
                            if p.name == connection.player_name
                        ),
                        None,
                    )

                if player and not player.is_bot:

                    # Store original bot state
                    player.original_is_bot = player.is_bot
                    player.is_connected = False
                    player.disconnect_time = connection.disconnect_time

                    # Convert to bot
                    player.is_bot = True

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
                        new_host = await room.migrate_host()
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

                    # Check if all remaining players are bots and mark for cleanup
                    if not room.has_any_human_players():
                        room.mark_for_cleanup()
                        logger.info(
                            f"All players in room {room_id} are now bots. Cleanup scheduled in {room.CLEANUP_TIMEOUT_SECONDS}s"
                        )
                        logger.info(
                            f"🤖 [ROOM_DEBUG] Room '{room_id}' has no human players, marked for cleanup"
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
        unregister(room_id, websocket)
        logger.info(f"🔌 [ROOM_DEBUG] WebSocket unregistered from room '{room_id}'")


async def process_leave_room(room_id: str, player_name: str):
    """Shared logic for handling player leaving room (pre-game)
    This is extracted from the existing leave_room event handler"""
    room = await room_manager.get_room(room_id)
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
        await room_manager.delete_room(room_id)
        logger.info(f"🗑️ [ROOM_DEBUG] Room '{room_id}' deleted because host left")

        # Update lobby with room list
        available_rooms = await room_manager.list_rooms()
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
        await room.exit_room(player_name)
        updated_summary = await room.summary()
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
                "started": updated_summary.get("started", False),
            },
        )

        # Update lobby with updated room info
        available_rooms = await room_manager.list_rooms()
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

    registered_ws = await register(room_id, websocket)

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
                    await registered_ws.send_json(
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
        except Exception as e:
            logger.error(f"[ROOM_LOOKUP_DEBUG] Error checking room existence: {e}", exc_info=True)
            # Don't fail the connection, just log the error

    try:
        while True:
            message = await websocket.receive_json()

            # Validate the message structure and content
            is_valid, error_msg, sanitized_data = validate_websocket_message(message)
            if not is_valid:
                await registered_ws.send_json(
                    {
                        "event": "error",
                        "data": {
                            "message": f"Invalid message: {error_msg}",
                            "type": "validation_error",
                        },
                    }
                )
                continue

            # ===== ADAPTER INTEGRATION START =====
            # IMPORTANT: This is where clean architecture handles ALL requests
            # When ADAPTER_ENABLED=true and ADAPTER_ROLLOUT_PERCENTAGE=100:
            # - ALL messages are handled by clean architecture adapters
            # - The legacy code below (line 328+) is NEVER executed
            # - This is NOT legacy code - it's the integration point
            adapter_response = await adapter_wrapper.try_handle_with_adapter(
                registered_ws, message, room_id
            )
            
            if adapter_response is not None:
                # Adapter handled it, send response if not empty
                if adapter_response:  # Some responses like 'ack' return empty
                    await registered_ws.send_json(adapter_response)
                continue  # Skip legacy handling - THIS LINE PREVENTS LEGACY EXECUTION
            # ===== ADAPTER INTEGRATION END =====


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


@router.get("/ws/adapter-status")
async def get_adapter_status():
    """Get current adapter integration status"""
    return adapter_wrapper.get_status()


async def room_cleanup_task():
    """Background task to clean up abandoned rooms"""
    iteration_count = 0
    logger.info("🧹 [ROOM_DEBUG] Room cleanup task started")

    while True:
        try:
            iteration_count += 1
            rooms_to_cleanup = []

            # Check all rooms (including started ones)
            # Note: list_rooms() only returns non-started rooms, so we need to check all rooms directly
            all_room_ids = list(room_manager.rooms.keys())
            
            # Also check clean architecture rooms
            try:
                from infrastructure.dependencies import get_unit_of_work
                uow = get_unit_of_work()
                async with uow:
                    clean_rooms = await uow.rooms.list()
                    clean_room_ids = [room.room_id for room in clean_rooms]
                    # Add any clean rooms not in legacy
                    for room_id in clean_room_ids:
                        if room_id not in all_room_ids:
                            all_room_ids.append(room_id)
                            logger.debug(f"🧹 [ROOM_DEBUG] Found clean architecture room not in legacy: {room_id}")
            except Exception as e:
                logger.debug(f"🧹 [ROOM_DEBUG] Could not check clean architecture rooms: {e}")

            if all_room_ids:
                logger.info(
                    f"🧹 [ROOM_DEBUG] Cleanup iteration {iteration_count}: Checking {len(all_room_ids)} rooms: {all_room_ids}"
                )

            for room_id in all_room_ids:
                room = await room_manager.get_room(room_id)
                if room:
                    should_cleanup = room.should_cleanup()
                    game_ended = getattr(room, 'game_ended', False)
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
                room = await room_manager.get_room(room_id)
                if room and room.should_cleanup():  # Double-check
                    logger.info(
                        f"🧹 [ROOM_DEBUG] Cleaning up abandoned room {room_id} (no human players)"
                    )

                    # Unregister from bot manager
                    from engine.bot_manager import BotManager

                    bot_manager = BotManager()
                    bot_manager.unregister_game(room_id)

                    # Broadcast room closed
                    await broadcast(
                        room_id,
                        "room_closed",
                        {
                            "reason": "All players disconnected",
                            "timeout_seconds": room.CLEANUP_TIMEOUT_SECONDS,
                        },
                    )

                    # Delete room
                    await room_manager.delete_room(room_id)

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
