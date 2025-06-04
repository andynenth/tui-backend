# backend/api/routes/ws.py

from fastapi import WebSocket, WebSocketDisconnect, APIRouter # Import WebSocket and WebSocketDisconnect for handling WebSocket connections, and APIRouter for routing.
from backend.socket_manager import register, unregister, broadcast
from backend.shared_instances import shared_room_manager # Import the globally shared RoomManager instance.
import asyncio # Standard library for asynchronous programming.

import backend.socket_manager
print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

router = APIRouter() # Create a new FastAPI APIRouter instance for WebSocket routes.
# room_manager = RoomManager() # (Commented out) Direct instantiation of RoomManager.
room_manager = shared_room_manager # Use the globally shared RoomManager instance to access room data.

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time communication within a specific room.
    Handles connection, message reception, and disconnection.
    Args:
        websocket (WebSocket): The WebSocket connection object.
        room_id (str): The ID of the room the client is connecting to.
    """
    # ✅ Register the WebSocket connection with the socket manager.
    # This function returns the registered WebSocket object, which might be a wrapper.
    registered_ws = await register(room_id, websocket) 

    try:
        while True:
            message = await websocket.receive_json()
            event_name = message.get("event")
            event_data = message.get("data", {})

            print(f"DEBUG_LOBBY_WS: Received event '{event_name}' with data: {event_data}")

            if event_name == "request_room_list":
                # ✅ Get available rooms and send to client
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
                # ✅ Send initial room list when client connects
                available_rooms = room_manager.list_rooms()
                
                await registered_ws.send_json({
                    "event": "room_list_update",
                    "data": {
                        "rooms": available_rooms,
                        "timestamp": asyncio.get_event_loop().time(),
                        "initial": True
                    }
                })
                print(f"DEBUG_LOBBY_WS: Sent initial room list to new client")

    except WebSocketDisconnect:
        unregister("lobby", websocket)
        print(f"DEBUG_LOBBY_WS: Client disconnected from lobby")
    except Exception as e:
        print(f"DEBUG_LOBBY_WS: Error in lobby WebSocket: {e}")
        unregister("lobby", websocket)

@router.websocket("/ws/lobby")
async def notify_lobby_room_updated(room_data):
    """
    ✅ Notify lobby clients about room updates (occupancy changes)
    """
    await broadcast("lobby", "room_updated", {
        "room_id": room_data["room_id"],
        "occupied_slots": room_data["occupied_slots"],
        "total_slots": room_data["total_slots"],
        "timestamp": asyncio.get_event_loop().time()
    })