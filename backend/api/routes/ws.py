# backend/api/routes/ws.py

import asyncio
import logging
import uuid

import backend.socket_manager
from backend.shared_instances import shared_room_manager
from backend.socket_manager import broadcast, register, unregister
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.validation import validate_websocket_message
from api.middleware.websocket_rate_limit import check_websocket_rate_limit, send_rate_limit_error
from api.websocket.connection_manager import connection_manager
from api.websocket.message_queue import message_queue_manager

# Set up logging
logger = logging.getLogger(__name__)

print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

router = APIRouter()
room_manager = shared_room_manager


async def broadcast_with_queue(room_id: str, event: str, data: dict):
    """Broadcast to room and queue messages for disconnected players"""
    # Get list of disconnected players in the room
    room = room_manager.get_room(room_id)
    if room and room.game:
        disconnected_players = []
        for player in room.game.players:
            if player and hasattr(player, 'is_connected') and not player.is_connected:
                disconnected_players.append(player.name)
        
        # Queue messages for disconnected players
        for player_name in disconnected_players:
            await message_queue_manager.queue_message(room_id, player_name, event, data)
    
    # Broadcast to connected players
    await broadcast(room_id, event, data)


async def handle_disconnect(room_id: str, websocket: WebSocket):
    """Handle player disconnection with bot activation"""
    try:
        # Generate a unique websocket ID for tracking
        websocket_id = getattr(websocket, '_ws_id', None)
        
        logger.info(f"Handling disconnect for room {room_id}, websocket_id: {websocket_id}")
        
        # Try to find player by checking all players in the room if websocket_id fails
        connection = None
        if websocket_id:
            # Get connection info
            connection = await connection_manager.handle_disconnect(websocket_id)
        
        if not connection and room_id != "lobby":
            # Fallback: Check if any player in the room is missing their websocket
            room = room_manager.get_room(room_id)
            if room and room.started and room.game:
                # This is a workaround - we should improve the tracking mechanism
                logger.warning(f"Using fallback disconnect detection for room {room_id}")
        
        if connection and room_id != "lobby":
                # This is an in-game disconnect
                room = room_manager.get_room(room_id)
                if room and room.started and room.game:
                    # Find the player in the game
                    player = next(
                        (p for p in room.game.players if p.name == connection.player_name),
                        None
                    )
                    
                    if player and not player.is_bot:
                        # Store original bot state
                        player.original_is_bot = player.is_bot
                        player.is_connected = False
                        player.disconnect_time = connection.disconnect_time
                        
                        # Convert to bot
                        player.is_bot = True
                        
                        # Create message queue for the disconnected player
                        await message_queue_manager.create_queue(room_id, connection.player_name)
                        
                        logger.info(f"Player {connection.player_name} disconnected from game in room {room_id}. Bot activated.")
                        
                        # Check if disconnecting player was the host
                        new_host = None
                        if room.is_host(connection.player_name):
                            new_host = room.migrate_host()
                            if new_host:
                                logger.info(f"Host migrated to {new_host} in room {room_id}")
                        
                        # Broadcast disconnect event
                        await broadcast(
                            room_id,
                            "player_disconnected",
                            {
                                "player_name": connection.player_name,
                                "ai_activated": True,
                                "can_reconnect": True,
                                "is_bot": True
                            }
                        )
                        
                        # Broadcast host change if migration occurred
                        if new_host:
                            await broadcast(
                                room_id,
                                "host_changed",
                                {
                                    "old_host": connection.player_name,
                                    "new_host": new_host,
                                    "message": f"{new_host} is now the host"
                                }
                            )
                else:
                    logger.warning(f"No connection found for websocket_id {websocket_id} in room {room_id}")
        else:
            logger.warning(f"No websocket_id found on websocket object for room {room_id}")
    except Exception as e:
        logger.error(f"Error handling disconnect: {e}")
    finally:
        # Always unregister the websocket
        unregister(room_id, websocket)


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time communication within a specific room.
    Also handles special 'lobby' room for lobby updates.
    """
    # Generate unique ID for this websocket
    websocket._ws_id = str(uuid.uuid4())
    
    registered_ws = await register(room_id, websocket)

    try:
        while True:
            message = await websocket.receive_json()
            
            # Validate the message structure and content
            is_valid, error_msg, sanitized_data = validate_websocket_message(message)
            if not is_valid:
                await registered_ws.send_json({
                    "event": "error",
                    "data": {
                        "message": f"Invalid message: {error_msg}",
                        "type": "validation_error"
                    }
                })
                continue
            
            event_name = message.get("event")
            # Use sanitized data instead of raw event data
            event_data = sanitized_data or message.get("data", {})
            
            # Check rate limit for this event with proper error handling
            try:
                rate_limit_allowed, rate_limit_info = await check_websocket_rate_limit(
                    websocket, room_id, event_name
                )
                
                if not rate_limit_allowed:
                    # Send rate limit error and continue
                    try:
                        await send_rate_limit_error(registered_ws, rate_limit_info)
                    except Exception as e:
                        logger.warning(f"Error sending rate limit message: {e}")
                    continue
                elif rate_limit_info and "warning" in rate_limit_info:
                    # Send rate limit warning but allow the event to proceed
                    try:
                        await registered_ws.send_json({
                            "event": "rate_limit_warning",
                            "data": rate_limit_info["warning"]
                        })
                    except Exception as e:
                        logger.debug(f"Could not send rate limit warning: {e}")
            except Exception as e:
                # Log the error but don't close the connection
                logger.error(f"Rate limit check error for {event_name}: {e}", exc_info=True)
                # Allow the event to proceed to prevent connection disruption
                rate_limit_allowed = True

            # Handle reliable message delivery events
            if event_name == "ack":
                # Handle message acknowledgment
                sequence = event_data.get("sequence")
                client_id = event_data.get("client_id", "unknown")

                if sequence is not None:
                    from backend.socket_manager import socket_manager

                    await socket_manager.handle_ack(room_id, sequence, client_id)
                continue

            elif event_name == "sync_request":
                # Handle client synchronization request
                client_id = event_data.get("client_id", "unknown")

                from backend.socket_manager import socket_manager

                await socket_manager.request_client_sync(
                    room_id, registered_ws, client_id
                )
                continue

            # ✅ Handle lobby-specific events
            if room_id == "lobby":
                if event_name == "request_room_list" or event_name == "get_rooms":
                    # Get available rooms and send to client
                    available_rooms = room_manager.list_rooms()

                    await registered_ws.send_json(
                        {
                            "event": "room_list_update",
                            "data": {
                                "rooms": available_rooms,
                                "timestamp": asyncio.get_event_loop().time(),
                                "requested_by": event_data.get(
                                    "player_name", "unknown"
                                ),
                            },
                        }
                    )

                elif event_name == "ping":
                    # Respond to heartbeat ping with pong
                    await registered_ws.send_json(
                        {
                            "event": "pong",
                            "data": {
                                "timestamp": event_data.get("timestamp", asyncio.get_event_loop().time()),
                                "server_time": asyncio.get_event_loop().time(),
                            },
                        }
                    )

                elif event_name == "client_ready":
                    # Send initial room list when client connects to lobby
                    available_rooms = room_manager.list_rooms()

                    await registered_ws.send_json(
                        {
                            "event": "room_list_update",
                            "data": {
                                "rooms": available_rooms,
                                "timestamp": asyncio.get_event_loop().time(),
                                "initial": True,
                            },
                        }
                    )
                    
                    # Track player connection if player_name provided
                    player_name = event_data.get("player_name")
                    if player_name and hasattr(registered_ws, '_ws_id'):
                        await connection_manager.register_player("lobby", player_name, registered_ws._ws_id)

                elif event_name == "create_room":
                    # Create new room (using validated/sanitized data)
                    player_name = event_data.get("player_name")

                    try:
                        # Create the room
                        room_id = room_manager.create_room(player_name)

                        # Send success response to the client
                        await registered_ws.send_json(
                            {
                                "event": "room_created",
                                "data": {
                                    "room_id": room_id,
                                    "host_name": player_name,
                                    "success": True,
                                },
                            }
                        )

                        # Notify all lobby clients about the new room
                        from .routes import notify_lobby_room_created

                        await notify_lobby_room_created(
                            {"room_id": room_id, "host_name": player_name}
                        )

                    except Exception as e:
                        # Send error response
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {
                                    "message": f"Failed to create room: {str(e)}",
                                    "type": "room_creation_error",
                                },
                            }
                        )

                elif event_name == "get_rooms":
                    # Send current room list
                    available_rooms = room_manager.list_rooms()

                    await registered_ws.send_json(
                        {
                            "event": "room_list",
                            "data": {
                                "rooms": available_rooms,
                                "timestamp": asyncio.get_event_loop().time(),
                            },
                        }
                    )

                elif event_name == "join_room":
                    # Handle room joining from lobby (using validated data)
                    room_id_to_join = event_data.get("room_id")
                    player_name = event_data.get("player_name")

                    try:
                        # Get the room
                        room = room_manager.get_room(room_id_to_join)
                        if not room:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": "Room not found",
                                        "type": "join_room_error",
                                    },
                                }
                            )
                            continue

                        # Check if room is full
                        if room.is_full():
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": "Room is full",
                                        "type": "join_room_error",
                                    },
                                }
                            )
                            continue

                        # Check if room has started
                        if room.started:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": "Room has already started",
                                        "type": "join_room_error",
                                    },
                                }
                            )
                            continue

                        # Try to join the room
                        result = await room.join_room_safe(player_name)

                        if result["success"]:
                            # Send success response to the client
                            await registered_ws.send_json(
                                {
                                    "event": "room_joined",
                                    "data": {
                                        "room_id": room_id_to_join,
                                        "player_name": player_name,
                                        "assigned_slot": result["assigned_slot"],
                                        "success": True,
                                    },
                                }
                            )

                            # Broadcast room update to all clients in the room
                            room_summary = result["room_state"]
                            await broadcast(
                                room_id_to_join,
                                "room_update",
                                {
                                    "players": room_summary["players"],
                                    "host_name": room_summary["host_name"],
                                    "operation_id": result["operation_id"],
                                    "room_id": room_id_to_join,
                                    "started": room_summary.get("started", False),
                                },
                            )

                            # Notify all lobby clients about room update
                            from .routes import notify_lobby_room_updated

                            await notify_lobby_room_updated(result["room_state"])

                        else:
                            # Send error response
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get(
                                            "reason", "Failed to join room"
                                        ),
                                        "type": "join_room_error",
                                    },
                                }
                            )

                    except Exception as e:
                        # Send error response
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {
                                    "message": f"Failed to join room: {str(e)}",
                                    "type": "join_room_error",
                                },
                            }
                        )

            # ✅ Handle room-specific events
            else:
                if event_name == "ping":
                    # Respond to heartbeat ping with pong
                    await registered_ws.send_json(
                        {
                            "event": "pong",
                            "data": {
                                "timestamp": event_data.get("timestamp", asyncio.get_event_loop().time()),
                                "server_time": asyncio.get_event_loop().time(),
                                "room_id": room_id,
                            },
                        }
                    )

                elif event_name == "client_ready":
                    room = room_manager.get_room(room_id)
                    if room:
                        updated_summary = room.summary()
                        await registered_ws.send_json(
                            {
                                "event": "room_state_update",
                                "data": {
                                    "slots": updated_summary["slots"],
                                    "host_name": updated_summary["host_name"],
                                },
                            }
                        )
                        
                        # Track player connection if player_name provided
                        player_name = event_data.get("player_name")
                        if player_name and hasattr(registered_ws, '_ws_id'):
                            await connection_manager.register_player(room_id, player_name, registered_ws._ws_id)
                            
                            # Check if reconnecting to an active game
                            if room.game_started and room.game:
                                player = next(
                                    (p for p in room.game.players if p.name == player_name),
                                    None
                                )
                                if player and player.is_bot and not player.original_is_bot:
                                    # This is a human player reconnecting
                                    player.is_bot = False
                                    player.is_connected = True
                                    player.disconnect_time = None
                                    
                                    logger.info(f"Player {player_name} reconnected to game in room {room_id}")
                                    
                                    # Get queued messages for the reconnecting player
                                    queued_messages = await message_queue_manager.get_queued_messages(room_id, player_name)
                                    
                                    # Send queued messages to the reconnecting player
                                    if queued_messages:
                                        await registered_ws.send_json({
                                            "event": "queued_messages",
                                            "data": {
                                                "messages": queued_messages,
                                                "count": len(queued_messages)
                                            }
                                        })
                                        logger.info(f"Sent {len(queued_messages)} queued messages to {player_name}")
                                    
                                    # Clear the message queue
                                    await message_queue_manager.clear_queue(room_id, player_name)
                                    
                                    # Broadcast reconnection
                                    await broadcast(
                                        room_id,
                                        "player_reconnected",
                                        {
                                            "player_name": player_name,
                                            "resumed_control": True,
                                            "is_bot": False
                                        }
                                    )

                        # Send current game phase if game is running
                        if room.started and room.game_state_machine:
                            current_phase = room.game_state_machine.get_current_phase()
                            if current_phase:
                                phase_data = room.game_state_machine.get_phase_data()
                                allowed_actions = [
                                    action.value
                                    for action in room.game_state_machine.get_allowed_actions()
                                ]

                                # Add player hands data
                                players_data = {}
                                if room.game and hasattr(room.game, "players"):
                                    for player in room.game.players:
                                        player_name = getattr(
                                            player, "name", str(player)
                                        )
                                        player_hand = []

                                        # Get player's hand
                                        if hasattr(player, "hand") and player.hand:
                                            player_hand = [
                                                str(piece) for piece in player.hand
                                            ]

                                        players_data[player_name] = {
                                            "hand": player_hand,
                                            "hand_size": len(player_hand),
                                            "zero_declares_in_a_row": getattr(
                                                player, "zero_declares_in_a_row", 0
                                            ),
                                            "declared": getattr(player, "declared", 0),
                                            "score": getattr(player, "score", 0),
                                        }

                                # Get current round number
                                current_round = 1
                                if room.game:
                                    current_round = getattr(
                                        room.game, "round_number", 1
                                    )

                                await registered_ws.send_json(
                                    {
                                        "event": "phase_change",
                                        "data": {
                                            "phase": current_phase.value,
                                            "allowed_actions": allowed_actions,
                                            "phase_data": phase_data,
                                            "players": players_data,
                                            "round": current_round,
                                        },
                                    }
                                )

                        await asyncio.sleep(0)
                    else:
                        await registered_ws.send_json(
                            {
                                "event": "room_closed",
                                "data": {"message": "Room not found."},
                            }
                        )
                        await asyncio.sleep(0)

                elif event_name == "get_room_state":
                    room = room_manager.get_room(room_id)
                    if room:
                        updated_summary = room.summary()
                        await registered_ws.send_json(
                            {
                                "event": "room_update",
                                "data": {
                                    "players": updated_summary["players"],
                                    "host_name": updated_summary["host_name"],
                                    "room_id": room_id,
                                    "started": updated_summary.get("started", False),
                                },
                            }
                        )
                    else:
                        await registered_ws.send_json(
                            {
                                "event": "room_closed",
                                "data": {"message": "Room not found."},
                            }
                        )

                elif event_name == "remove_player":
                    # Already validated - slot_id is guaranteed to be present and valid
                    slot_id = event_data.get("slot_id")

                    room = room_manager.get_room(room_id)
                    if room:
                        try:
                            # Convert to 0-indexed (frontend sends 1-4, backend uses 0-3)
                            slot_index = int(slot_id) - 1

                            # Use assign_slot_safe to clear the slot
                            result = await room.assign_slot_safe(slot_index, None)

                            if result["success"]:
                                # Broadcast room update to all clients in the room
                                updated_summary = room.summary()
                                await broadcast(
                                    room_id,
                                    "room_update",
                                    {
                                        "players": updated_summary["players"],
                                        "host_name": updated_summary["host_name"],
                                        "room_id": room_id,
                                        "started": updated_summary.get(
                                            "started", False
                                        ),
                                    },
                                )

                                # Update lobby with room list (room may now be available)
                                available_rooms = room_manager.list_rooms()
                                await broadcast(
                                    "lobby",
                                    "room_list_update",
                                    {
                                        "rooms": available_rooms,
                                        "timestamp": asyncio.get_event_loop().time(),
                                    },
                                )

                            else:
                                await registered_ws.send_json(
                                    {
                                        "event": "error",
                                        "data": {
                                            "message": "Failed to remove player from slot"
                                        },
                                    }
                                )

                        except (ValueError, IndexError) as e:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": f"Invalid slot ID: {slot_id}"},
                                }
                            )
                    else:
                        await registered_ws.send_json(
                            {
                                "event": "room_closed",
                                "data": {"message": "Room not found."},
                            }
                        )

                elif event_name == "add_bot":
                    # Already validated - slot_id is guaranteed to be present and valid
                    slot_id = event_data.get("slot_id")

                    room = room_manager.get_room(room_id)
                    if room:
                        try:
                            # Convert to 0-indexed (frontend sends 1-4, backend uses 0-3)
                            slot_index = int(slot_id) - 1

                            # Generate bot name
                            bot_name = f"Bot {slot_id}"

                            # Use assign_slot_safe to add the bot
                            result = await room.assign_slot_safe(slot_index, bot_name)

                            if result["success"]:
                                # Broadcast room update to all clients in the room
                                updated_summary = room.summary()
                                await broadcast(
                                    room_id,
                                    "room_update",
                                    {
                                        "players": updated_summary["players"],
                                        "host_name": updated_summary["host_name"],
                                        "room_id": room_id,
                                        "started": updated_summary.get(
                                            "started", False
                                        ),
                                    },
                                )

                                # Update lobby with room list (room may now be full)
                                available_rooms = room_manager.list_rooms()
                                await broadcast(
                                    "lobby",
                                    "room_list_update",
                                    {
                                        "rooms": available_rooms,
                                        "timestamp": asyncio.get_event_loop().time(),
                                    },
                                )

                            else:
                                await registered_ws.send_json(
                                    {
                                        "event": "error",
                                        "data": {
                                            "message": "Failed to add bot to slot"
                                        },
                                    }
                                )

                        except (ValueError, IndexError) as e:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": f"Invalid slot ID: {slot_id}"},
                                }
                            )
                    else:
                        await registered_ws.send_json(
                            {
                                "event": "room_closed",
                                "data": {"message": "Room not found."},
                            }
                        )

                elif event_name == "leave_room":
                    room = room_manager.get_room(room_id)
                    if room:
                        try:
                            # Find which player is leaving by checking the websocket
                            # For now, we'll need the player name from the event data
                            player_name = event_data.get("player_name")
                            if not player_name:
                                # If no player name provided, we can't identify who's leaving
                                await registered_ws.send_json(
                                    {
                                        "event": "error",
                                        "data": {
                                            "message": "Player name required for leave_room"
                                        },
                                    }
                                )
                                continue

                            # Check if this player is the host
                            is_host_leaving = player_name == room.host_name

                            if is_host_leaving:
                                # Host is leaving - close the entire room
                                # Broadcast room closure to all clients
                                await broadcast(
                                    room_id,
                                    "room_closed",
                                    {
                                        "message": f"Room closed by host {player_name}",
                                        "reason": "host_left",
                                    },
                                )

                                # Remove the room from the manager
                                room_manager.delete_room(room_id)

                                # Send confirmation to the leaving host
                                await registered_ws.send_json(
                                    {
                                        "event": "player_left",
                                        "data": {
                                            "player_name": player_name,
                                            "success": True,
                                            "room_closed": True,
                                        },
                                    }
                                )

                                # Update lobby with room list
                                available_rooms = room_manager.list_rooms()
                                await broadcast(
                                    "lobby",
                                    "room_list_update",
                                    {
                                        "rooms": available_rooms,
                                        "timestamp": asyncio.get_event_loop().time(),
                                    },
                                )

                            else:
                                # Regular player leaving - just remove them from the room
                                room.exit_room(player_name)

                                # Broadcast room update to remaining clients
                                updated_summary = room.summary()
                                await broadcast(
                                    room_id,
                                    "room_update",
                                    {
                                        "players": updated_summary["players"],
                                        "host_name": updated_summary["host_name"],
                                        "room_id": room_id,
                                        "started": updated_summary.get(
                                            "started", False
                                        ),
                                    },
                                )

                                # Notify the leaving player
                                await registered_ws.send_json(
                                    {
                                        "event": "player_left",
                                        "data": {
                                            "player_name": player_name,
                                            "success": True,
                                        },
                                    }
                                )

                        except Exception as e:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Failed to leave room"},
                                }
                            )
                    else:
                        await registered_ws.send_json(
                            {
                                "event": "room_closed",
                                "data": {"message": "Room not found."},
                            }
                        )

                # 🔧 FIX: Add missing redeal decision handler
                elif event_name == "redeal_decision":
                    # Already validated
                    player_name = event_data.get("player_name")
                    choice = event_data.get("choice")

                    try:
                        # Import inside function to avoid circular imports
                        from .routes import get_redeal_controller

                        controller = get_redeal_controller(room_id)

                        # Handle the player's redeal decision
                        await controller.handle_player_decision(player_name, choice)
                        print(
                            f"✅ Processed redeal decision: {player_name} -> {choice}"
                        )

                    except Exception as e:
                        print(f"❌ Error processing redeal decision: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {
                                    "message": "Failed to process redeal decision"
                                },
                            }
                        )

                # ✅ ADD: Missing game WebSocket handlers
                elif event_name == "declare":
                    # Handle player declaration (already validated)
                    player_name = event_data.get("player_name")
                    value = event_data.get("value")

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for declaration (same as REST endpoint)
                        from engine.state_machine.core import ActionType, GameAction

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.DECLARE,
                            payload={"value": value},
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if result.get("success"):
                            # Don't send declare_success - let state machine broadcast 'declare' event like bots
                            print(f"✅ Declaration queued: {player_name} -> {value}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get(
                                            "error", "Declaration failed"
                                        )
                                    },
                                }
                            )

                    except Exception as e:
                        print(f"❌ Declaration error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to process declaration"},
                            }
                        )

                elif event_name == "play":
                    # Handle piece playing (already validated)
                    player_name = event_data.get("player_name")
                    indices = event_data.get("indices", [])

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for piece playing (convert indices to pieces)
                        from engine.state_machine.core import ActionType, GameAction

                        # Convert indices to actual pieces
                        pieces = []
                        if hasattr(room.game, "players"):
                            # Find the player and get pieces from their hand by indices
                            player = next(
                                (
                                    p
                                    for p in room.game.players
                                    if getattr(p, "name", str(p)) == player_name
                                ),
                                None,
                            )
                            if player and hasattr(player, "hand"):
                                for idx in indices:
                                    if 0 <= idx < len(player.hand):
                                        pieces.append(player.hand[idx])

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.PLAY_PIECES,
                            payload={
                                "pieces": pieces
                            },  # Send actual pieces, not indices
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if not result:
                            # Handle None result (shouldn't happen with new base_state)
                            await registered_ws.send_json(
                                {
                                    "event": "play_rejected",
                                    "data": {"message": "Invalid play - try again"},
                                }
                            )
                        elif result.get("success") == False:
                            # Handle validation failure
                            await registered_ws.send_json(
                                {
                                    "event": "play_rejected",
                                    "data": {
                                        "message": result.get("error", "Invalid play"),
                                        "details": result.get(
                                            "details", "Please try different pieces"
                                        ),
                                    },
                                }
                            )
                        else:
                            print(f"✅ Play accepted: {player_name}")

                    except Exception as e:
                        print(f"❌ Play error: {e}")
                        import traceback

                        traceback.print_exc()
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to process piece play"},
                            }
                        )

                elif event_name == "play_pieces":
                    # Handle piece playing (legacy handler - already validated)
                    player_name = event_data.get("player_name")
                    indices = event_data.get("indices", [])

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for piece playing (convert indices to pieces)
                        from engine.state_machine.core import ActionType, GameAction

                        # Convert indices to actual pieces
                        pieces = []
                        if hasattr(room.game, "players"):
                            # Find the player and get pieces from their hand by indices
                            player = next(
                                (
                                    p
                                    for p in room.game.players
                                    if getattr(p, "name", str(p)) == player_name
                                ),
                                None,
                            )
                            if player and hasattr(player, "hand"):
                                for idx in indices:
                                    if 0 <= idx < len(player.hand):
                                        pieces.append(player.hand[idx])

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.PLAY_PIECES,
                            payload={
                                "pieces": pieces
                            },  # Send actual pieces, not indices
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if result.get("success"):
                            await registered_ws.send_json(
                                {
                                    "event": "play_success",
                                    "data": {
                                        "player_name": player_name,
                                        "indices": indices,
                                    },
                                }
                            )
                            print(f"✅ Play queued: {player_name} -> {indices}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get("error", "Play failed")
                                    },
                                }
                            )

                    except Exception as e:
                        print(f"❌ Play pieces error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to process piece play"},
                            }
                        )

                elif event_name == "request_redeal":
                    # Handle redeal request (already validated)
                    player_name = event_data.get("player_name")

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for redeal request (same as REST endpoint)
                        from engine.state_machine.core import ActionType, GameAction

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.REDEAL_REQUEST,
                            payload={"accept": True},
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if result.get("success"):
                            await registered_ws.send_json(
                                {
                                    "event": "redeal_success",
                                    "data": {"player_name": player_name},
                                }
                            )
                            print(f"✅ Redeal request queued: {player_name}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get(
                                            "error", "Redeal request failed"
                                        )
                                    },
                                }
                            )

                    except Exception as e:
                        print(f"❌ Redeal request error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to process redeal request"},
                            }
                        )

                elif event_name == "accept_redeal":
                    # Handle redeal acceptance
                    player_name = event_data.get("player_name")

                    if not player_name:
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Player name required"},
                            }
                        )
                        continue

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for redeal acceptance
                        from engine.state_machine.core import ActionType, GameAction

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.REDEAL_RESPONSE,
                            payload={"accept": True},
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if result.get("success"):
                            await registered_ws.send_json(
                                {
                                    "event": "redeal_response_success",
                                    "data": {
                                        "player_name": player_name,
                                        "choice": "accept",
                                    },
                                }
                            )
                            print(f"✅ Redeal accept queued: {player_name}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get(
                                            "error", "Redeal response failed"
                                        )
                                    },
                                }
                            )

                    except Exception as e:
                        print(f"❌ Accept redeal error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {
                                    "message": "Failed to process redeal acceptance"
                                },
                            }
                        )

                elif event_name == "decline_redeal":
                    # Handle redeal decline
                    player_name = event_data.get("player_name")

                    if not player_name:
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Player name required"},
                            }
                        )
                        continue

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for redeal decline
                        from engine.state_machine.core import ActionType, GameAction

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.REDEAL_RESPONSE,
                            payload={"accept": False},
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if result.get("success"):
                            await registered_ws.send_json(
                                {
                                    "event": "redeal_response_success",
                                    "data": {
                                        "player_name": player_name,
                                        "choice": "decline",
                                    },
                                }
                            )
                            print(f"✅ Redeal decline queued: {player_name}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get(
                                            "error", "Redeal response failed"
                                        )
                                    },
                                }
                            )

                    except Exception as e:
                        print(f"❌ Decline redeal error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to process redeal decline"},
                            }
                        )

                elif event_name == "player_ready":
                    # Handle player ready (used in multiple phases)
                    player_name = event_data.get("player_name")

                    if not player_name:
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Player name required"},
                            }
                        )
                        continue

                    try:
                        room = room_manager.get_room(room_id)
                        if not room or not room.game_state_machine:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Game not found"},
                                }
                            )
                            continue

                        # Create GameAction for player ready
                        from engine.state_machine.core import ActionType, GameAction

                        action = GameAction(
                            player_name=player_name,
                            action_type=ActionType.PLAYER_READY,
                            payload={},
                        )

                        result = await room.game_state_machine.handle_action(action)

                        if result.get("success"):
                            await registered_ws.send_json(
                                {
                                    "event": "ready_success",
                                    "data": {"player_name": player_name},
                                }
                            )
                            print(f"✅ Player ready queued: {player_name}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {
                                        "message": result.get(
                                            "error", "Ready signal failed"
                                        )
                                    },
                                }
                            )

                    except Exception as e:
                        print(f"❌ Player ready error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to process ready signal"},
                            }
                        )

                elif event_name == "leave_game":
                    # Handle leaving game (different from leave_room)
                    player_name = event_data.get("player_name")

                    if not player_name:
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Player name required"},
                            }
                        )
                        continue

                    try:
                        # For now, treat leave_game same as leave_room
                        # Future: might need separate logic for mid-game leaving
                        room = room_manager.get_room(room_id)
                        if room:
                            is_host_leaving = player_name == room.host_name

                            if is_host_leaving:
                                # Host leaving - close entire room/game
                                await broadcast(
                                    room_id,
                                    "game_ended",
                                    {
                                        "reason": "host_left",
                                        "message": f"Game ended - host {player_name} left",
                                    },
                                )
                                room_manager.delete_room(room_id)
                                print(
                                    f"✅ Game ended: host {player_name} left room {room_id}"
                                )
                            else:
                                # Regular player leaving game
                                room.exit_room(player_name)
                                updated_summary = room.summary()
                                await broadcast(
                                    room_id,
                                    "room_update",
                                    {
                                        "players": updated_summary["players"],
                                        "host_name": updated_summary["host_name"],
                                        "room_id": room_id,
                                        "started": updated_summary.get(
                                            "started", False
                                        ),
                                    },
                                )
                                print(
                                    f"✅ Player {player_name} left game in room {room_id}"
                                )

                        await registered_ws.send_json(
                            {
                                "event": "leave_game_success",
                                "data": {"player_name": player_name},
                            }
                        )

                    except Exception as e:
                        print(f"❌ Leave game error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to leave game"},
                            }
                        )

                elif event_name == "start_game":
                    # Handle start game request
                    try:
                        room = room_manager.get_room(room_id)
                        if not room:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Room not found"},
                                }
                            )
                            continue

                        # Create broadcast callback for this room
                        async def room_broadcast(event_type: str, event_data: dict):
                            await broadcast(room_id, event_type, event_data)

                        # Start the game (same logic as REST endpoint)
                        result = await room.start_game_safe(room_broadcast)

                        if result.get("success"):
                            # Broadcast to all players in the room so they all navigate to game
                            await broadcast(
                                room_id,
                                "game_started",
                                {"room_id": room_id, "success": True},
                            )
                            print(f"✅ Game started in room {room_id}")
                        else:
                            await registered_ws.send_json(
                                {
                                    "event": "error",
                                    "data": {"message": "Failed to start game"},
                                }
                            )

                    except Exception as e:
                        print(f"❌ Start game error: {e}")
                        await registered_ws.send_json(
                            {
                                "event": "error",
                                "data": {"message": "Failed to start game"},
                            }
                        )

    except WebSocketDisconnect:
        await handle_disconnect(room_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error in room {room_id}: {e}")
        await handle_disconnect(room_id, websocket)
