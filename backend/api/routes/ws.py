# backend/api/routes/ws.py

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from backend.socket_manager import register, unregister, broadcast
from backend.shared_instances import shared_room_manager
import asyncio

import backend.socket_manager
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
            event_name = message.get("event")
            event_data = message.get("data", {})

            print(f"DEBUG_WS_RECEIVE: Received event '{event_name}' from client in room {room_id} with data: {event_data}")

            # ✅ Handle lobby-specific events
            if room_id == "lobby":
                if event_name == "request_room_list":
                    # Get available rooms and send to client
                    available_rooms = room_manager.list_rooms()
                    
                    await registered_ws.send_json({
                        "event": "room_list_update",
                        "data": {
                            "rooms": available_rooms,
                            "timestamp": asyncio.get_event_loop().time(),
                            "requested_by": event_data.get("player_name", "unknown")
                        }
                    })
                    print(f"DEBUG_LOBBY_WS: Sent room list with {len(available_rooms)} rooms")

                elif event_name == "client_ready":
                    # Send initial room list when client connects to lobby
                    available_rooms = room_manager.list_rooms()
                    
                    await registered_ws.send_json({
                        "event": "room_list_update",
                        "data": {
                            "rooms": available_rooms,
                            "timestamp": asyncio.get_event_loop().time(),
                            "initial": True
                        }
                    })
                    print(f"DEBUG_LOBBY_WS: Sent initial room list to new lobby client")

                elif event_name == "create_room":
                    # Create new room
                    player_name = event_data.get("player_name", "Unknown Player")
                    
                    try:
                        # Create the room
                        room_id = room_manager.create_room(player_name)
                        
                        # Send success response to the client
                        await registered_ws.send_json({
                            "event": "room_created",
                            "data": {
                                "room_id": room_id,
                                "host_name": player_name,
                                "success": True
                            }
                        })
                        print(f"DEBUG_LOBBY_WS: Created room {room_id} for player {player_name}")
                        
                        # Notify all lobby clients about the new room
                        from .routes import notify_lobby_room_created
                        await notify_lobby_room_created({
                            "room_id": room_id,
                            "host_name": player_name
                        })
                        
                    except Exception as e:
                        # Send error response
                        await registered_ws.send_json({
                            "event": "error",
                            "data": {
                                "message": f"Failed to create room: {str(e)}",
                                "type": "room_creation_error"
                            }
                        })
                        print(f"DEBUG_LOBBY_WS: Failed to create room for {player_name}: {str(e)}")

                elif event_name == "get_rooms":
                    # Send current room list
                    available_rooms = room_manager.list_rooms()
                    
                    await registered_ws.send_json({
                        "event": "room_list",
                        "data": {
                            "rooms": available_rooms,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    })
                    print(f"DEBUG_LOBBY_WS: Sent room list with {len(available_rooms)} rooms")

            # ✅ Handle room-specific events
            else:
                if event_name == "client_ready":
                    room = room_manager.get_room(room_id)
                    if room:
                        updated_summary = room.summary()
                        await registered_ws.send_json({
                            "event": "room_state_update",
                            "data": {"slots": updated_summary["slots"], "host_name": updated_summary["host_name"]}
                        })
                        await asyncio.sleep(0)
                        print(f"DEBUG_WS_RECEIVE: Sent initial room state to client in room {room_id} after client_ready.")
                    else:
                        print(f"DEBUG_WS_RECEIVE: Room {room_id} not found for client_ready event.")
                        await registered_ws.send_json({"event": "room_closed", "data": {"message": "Room not found."}})
                        await asyncio.sleep(0)

                elif event_name == "get_room_state":
                    room = room_manager.get_room(room_id)
                    if room:
                        updated_summary = room.summary()
                        await registered_ws.send_json({
                            "event": "room_update",
                            "data": {
                                "players": updated_summary["slots"],
                                "host_name": updated_summary["host_name"],
                                "room_id": room_id,
                                "started": updated_summary.get("started", False)
                            }
                        })
                        print(f"DEBUG_WS_RECEIVE: Sent room state to client in room {room_id}")
                    else:
                        await registered_ws.send_json({"event": "room_closed", "data": {"message": "Room not found."}})
                        print(f"DEBUG_WS_RECEIVE: Room {room_id} not found for get_room_state")

                elif event_name == "remove_player":
                    slot_id = event_data.get("slot_id")
                    if slot_id is None:
                        print(f"DEBUG_WS_RECEIVE: Invalid remove_player data: {event_data}")
                        continue

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
                                await broadcast(room_id, "room_update", {
                                    "players": updated_summary["slots"],
                                    "host_name": updated_summary["host_name"],
                                    "room_id": room_id,
                                    "started": updated_summary.get("started", False)
                                })
                                print(f"DEBUG_WS_RECEIVE: Successfully removed player from slot {slot_id} in room {room_id}")
                            else:
                                await registered_ws.send_json({
                                    "event": "error",
                                    "data": {"message": "Failed to remove player from slot"}
                                })
                                
                        except (ValueError, IndexError) as e:
                            print(f"DEBUG_WS_RECEIVE: Invalid slot_id {slot_id}: {e}")
                            await registered_ws.send_json({
                                "event": "error", 
                                "data": {"message": f"Invalid slot ID: {slot_id}"}
                            })
                    else:
                        await registered_ws.send_json({
                            "event": "room_closed", 
                            "data": {"message": "Room not found."}
                        })

                elif event_name == "add_bot":
                    slot_id = event_data.get("slot_id")
                    if slot_id is None:
                        print(f"DEBUG_WS_RECEIVE: Invalid add_bot data: {event_data}")
                        continue

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
                                await broadcast(room_id, "room_update", {
                                    "players": updated_summary["slots"],
                                    "host_name": updated_summary["host_name"],
                                    "room_id": room_id,
                                    "started": updated_summary.get("started", False)
                                })
                                print(f"DEBUG_WS_RECEIVE: Successfully added bot to slot {slot_id} in room {room_id}")
                            else:
                                await registered_ws.send_json({
                                    "event": "error",
                                    "data": {"message": "Failed to add bot to slot"}
                                })
                                
                        except (ValueError, IndexError) as e:
                            print(f"DEBUG_WS_RECEIVE: Invalid slot_id {slot_id}: {e}")
                            await registered_ws.send_json({
                                "event": "error", 
                                "data": {"message": f"Invalid slot ID: {slot_id}"}
                            })
                    else:
                        await registered_ws.send_json({
                            "event": "room_closed", 
                            "data": {"message": "Room not found."}
                        })

                elif event_name == "leave_room":
                    room = room_manager.get_room(room_id)
                    if room:
                        try:
                            # Find which player is leaving by checking the websocket
                            # For now, we'll need the player name from the event data
                            player_name = event_data.get("player_name")
                            if not player_name:
                                # If no player name provided, we can't identify who's leaving
                                print(f"DEBUG_WS_RECEIVE: leave_room missing player_name: {event_data}")
                                await registered_ws.send_json({
                                    "event": "error",
                                    "data": {"message": "Player name required for leave_room"}
                                })
                                continue
                            
                            # Check if this player is the host
                            is_host_leaving = (player_name == room.host_name)
                            
                            if is_host_leaving:
                                # Host is leaving - close the entire room
                                # Broadcast room closure to all clients
                                await broadcast(room_id, "room_closed", {
                                    "message": f"Room closed by host {player_name}",
                                    "reason": "host_left"
                                })
                                
                                # Remove the room from the manager
                                room_manager.delete_room(room_id)
                                print(f"DEBUG_WS_RECEIVE: Host {player_name} left, room {room_id} closed")
                                
                                # Send confirmation to the leaving host
                                await registered_ws.send_json({
                                    "event": "player_left",
                                    "data": {"player_name": player_name, "success": True, "room_closed": True}
                                })
                                
                                # Update lobby with room list
                                available_rooms = room_manager.list_rooms()
                                await broadcast("lobby", "room_list_update", {
                                    "rooms": available_rooms,
                                    "timestamp": asyncio.get_event_loop().time()
                                })
                                
                            else:
                                # Regular player leaving - just remove them from the room
                                room.exit_room(player_name)
                                
                                # Broadcast room update to remaining clients
                                updated_summary = room.summary()
                                await broadcast(room_id, "room_update", {
                                    "players": updated_summary["slots"],
                                    "host_name": updated_summary["host_name"],
                                    "room_id": room_id,
                                    "started": updated_summary.get("started", False)
                                })
                                
                                # Notify the leaving player
                                await registered_ws.send_json({
                                    "event": "player_left",
                                    "data": {"player_name": player_name, "success": True}
                                })
                                
                                print(f"DEBUG_WS_RECEIVE: Player {player_name} left room {room_id}")
                                
                        except Exception as e:
                            print(f"DEBUG_WS_RECEIVE: Error processing leave_room: {e}")
                            await registered_ws.send_json({
                                "event": "error",
                                "data": {"message": "Failed to leave room"}
                            })
                    else:
                        await registered_ws.send_json({
                            "event": "room_closed", 
                            "data": {"message": "Room not found."}
                        })
                
                # 🔧 FIX: Add missing redeal decision handler
                elif event_name == "redeal_decision":
                    player_name = event_data.get("player_name")
                    choice = event_data.get("choice")
                    
                    if not player_name or not choice:
                        print(f"❌ Invalid redeal_decision data: {event_data}")
                        continue
                        
                    try:
                        # Import inside function to avoid circular imports
                        from .routes import get_redeal_controller
                        controller = get_redeal_controller(room_id)
                        
                        # Handle the player's redeal decision
                        await controller.handle_player_decision(player_name, choice)
                        print(f"✅ Processed redeal decision: {player_name} -> {choice}")
                        
                    except Exception as e:
                        print(f"❌ Error processing redeal decision: {e}")
                        await registered_ws.send_json({
                            "event": "error",
                            "data": {"message": "Failed to process redeal decision"}
                        })
                        
    except WebSocketDisconnect:
        unregister(room_id, websocket)
        if room_id == "lobby":
            print(f"DEBUG_LOBBY_WS: Client disconnected from lobby")
        else:
            print(f"DEBUG_WS_DISCONNECT: WebSocket client disconnected from room {room_id}.")
    except Exception as e:
        print(f"DEBUG_WS_ERROR: WebSocket error in room {room_id}: {e}")
        unregister(room_id, websocket)