# backend/api/routes/ws.py

import asyncio

import backend.socket_manager
from backend.shared_instances import shared_room_manager
from backend.socket_manager import broadcast, register, unregister
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.validation import validate_websocket_message

print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

router = APIRouter()
room_manager = shared_room_manager


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time communication within a specific room.
    Also handles special 'lobby' room for lobby updates.
    """
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
                if event_name == "client_ready":
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
        unregister(room_id, websocket)
        if room_id == "lobby":
            pass
        else:
            pass
    except Exception as e:
        unregister(room_id, websocket)
