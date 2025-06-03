# backend/api/routes/ws.py

from fastapi import WebSocket, WebSocketDisconnect, APIRouter # Import WebSocket and WebSocketDisconnect for handling WebSocket connections, and APIRouter for routing.
from backend.socket_manager import register, unregister, broadcast # Import functions from the custom socket_manager for managing WebSocket connections and broadcasting messages.
# from backend.engine.room_manager import RoomManager # (Commented out) Original RoomManager import.
from backend.shared_instances import shared_room_manager # Import the globally shared RoomManager instance.
import asyncio # Standard library for asynchronous programming.

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
        # Keep the connection open to receive messages from the client.
        while True:
            message = await websocket.receive_json() # Receive a JSON message from the client.
            event_name = message.get("event") # Extract the event name from the message.
            event_data = message.get("data", {}) # Extract the event data (default to empty dict if not present).

            print(f"DEBUG_WS_RECEIVE: Received event '{event_name}' from client in room {room_id} with data: {event_data}")

            # Handle specific events received from the client.
            if event_name == "client_ready":
                # No need for await asyncio.sleep(0) here anymore,
                # as cleanup in socket_manager.py and await register() should be sufficient.

                room = room_manager.get_room(room_id) # Get the room object.
                if room:
                    updated_summary = room.summary() # Get the current summary of the room.
                    # ✅ Send the initial room state directly back to the newly registered WebSocket.
                    await registered_ws.send_json({
                        "event": "room_state_update",
                        "data": {"slots": updated_summary["slots"], "host_name": updated_summary["host_name"]}
                    })
                    await asyncio.sleep(0) # Yield control to the event loop after sending.
                    print(f"DEBUG_WS_RECEIVE: Sent initial room state to client in room {room_id} after client_ready.")
                else:
                    print(f"DEBUG_WS_RECEIVE: Room {room_id} not found for client_ready event.")
                    # If the room is not found, inform the client that the room is closed.
                    await registered_ws.send_json({"event": "room_closed", "data": {"message": "Room not found."}})
                    await asyncio.sleep(0) # Yield control.
            # ... (Other event handling logic would go here, e.g., for game actions)
    except WebSocketDisconnect:
        # This exception is raised when a WebSocket client disconnects.
        unregister(room_id, websocket) # Unregister the disconnected WebSocket.
        print(f"DEBUG_WS_DISCONNECT: WebSocket client disconnected from room {room_id}.")
    except Exception as e:
        # Catch any other unexpected exceptions during WebSocket communication.
        print(f"DEBUG_WS_ERROR: WebSocket error in room {room_id}: {e}")
        unregister(room_id, websocket) # Ensure the WebSocket is unregistered even on error.
