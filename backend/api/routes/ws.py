# backend/api/routes/ws.py

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from backend.socket_manager import register, unregister, broadcast
from backend.shared_instances import shared_room_manager
import asyncio
from backend.engine.game_flow_controller import handle_websocket_message

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
                
                # Phase-validated game actions
                elif event_name in ["declare", "play_pieces", "pass_turn"]:
                    player_name = event_data.get("player_name")
                    
                    # Get game controller
                    from backend.api.routes.routes import get_game_controller
                    controller = get_game_controller(room_id)
                    
                    if controller:
                        # Route through phase-aware controller
                        result = await handle_websocket_message(
                            room_id,
                            player_name,
                            {"action": event_name, "data": event_data}
                        )
                        
                        if result.get("error"):
                            await registered_ws.send_json({
                                "event": "error",
                                "data": {
                                    "message": result["error"],
                                    "current_phase": result.get("current_phase"),
                                    "allowed_actions": result.get("allowed_actions", [])
                                }
                            })
                    else:
                        # No active game controller
                        await registered_ws.send_json({
                            "event": "error",
                            "data": {"message": "No active game"}
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