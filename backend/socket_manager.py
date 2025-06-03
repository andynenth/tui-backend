# backend/socket_manager.py

from fastapi.websockets import WebSocket # Import WebSocket for handling WebSocket connections.
from typing import Dict, List, Optional # Import type hints for better code readability and maintainability.
import asyncio # Import asyncio for asynchronous operations, especially for queues and tasks.
import weakref # Import weakref to create weak references to WebSocket objects, preventing memory leaks.

# Dictionary to store WebSocket connections for each room.
# Keys are room IDs (str), and values are lists of weak references to WebSocket objects.
room_connections: Dict[str, List[weakref.ReferenceType[WebSocket]]] = {}

# ✅ Add a Queue for Broadcast Messages (to solve Race Condition issues).
# This dictionary maps room IDs to asyncio.Queue instances.
broadcast_queues: Dict[str, asyncio.Queue] = {}

# ✅ Add a Task for managing the Broadcast Queue for each room.
# This dictionary maps room IDs to asyncio.Task instances, which run background processing.
broadcast_tasks: Dict[str, asyncio.Task] = {}


async def _process_broadcast_queue(room_id: str):
    """
    Background task to process messages from the broadcast queue for a specific room.
    This ensures that messages are sent sequentially and handles disconnections gracefully.
    """
    queue = broadcast_queues[room_id] # Get the asyncio.Queue for the specified room.
    print(f"DEBUG_WS: Starting broadcast queue processor for room {room_id}.")
    while True:
        message = await queue.get() # Wait for and retrieve a message from the queue.
        event = message["event"] # Extract the event name from the message.
        data = message["data"] # Extract the data associated with the event.

        # Filter for active connections (where the weak reference still points to an object)
        # and are in an OPEN state (client_state.value == 1).
        active_and_open_websockets: List[WebSocket] = []
        # Clean up room_connections before attempting to send messages.
        if room_id in room_connections:
            room_connections[room_id] = [
                ref for ref in room_connections[room_id]
                if ref() is not None and ref().client_state.value == 1 # 1 = State.OPEN
            ]
            for ws_ref in room_connections[room_id]:
                ws = ws_ref()
                if ws is not None: # Should be rarely None after the filtering above.
                    active_and_open_websockets.append(ws)

        if not active_and_open_websockets:
            print(f"DEBUG_WS: No active (open) connections found for room {room_id} during queue processing. Skipping message.")
            # If no active connections remain, clean up the queue and its associated task.
            if room_id in broadcast_queues:
                del broadcast_queues[room_id]
            if room_id in broadcast_tasks:
                broadcast_tasks[room_id].cancel() # Cancel the background task.
                del broadcast_tasks[room_id]
            continue # Skip to wait for the next message in the queue (or exit if queue is deleted).

        print(f"DEBUG_WS: Queue processor broadcasting event '{event}' to {len(active_and_open_websockets)} clients in room {room_id}.")

        for ws in active_and_open_websockets:
            try:
                # Send the message as JSON to the WebSocket client.
                await ws.send_json({"event": event, "data": data})
                await asyncio.sleep(0) # Yield control to the event loop, allowing other tasks to run.
                print(f"DEBUG_WS: Successfully sent to a client in room {room_id} (WS state: {ws.client_state.name}).")
            except Exception as e:
                print(f"DEBUG_WS: Error sending to client in room {room_id}: {e}. Unregistering connection.")
                unregister(room_id, ws) # Let unregister handle the removal of the problematic connection.

        # After the broadcast loop, clean up the list again (for connections that might have failed during the loop).
        if room_id in room_connections:
            room_connections[room_id] = [
                ref for ref in room_connections[room_id]
                if ref() is not None and ref().client_state.value == 1
            ]
            if not room_connections[room_id]:
                del room_connections[room_id]


async def register(room_id: str, websocket: WebSocket) -> WebSocket:
    """
    Registers a new WebSocket connection for a given room.
    Accepts the WebSocket connection and initializes a broadcast queue/task if it doesn't exist for the room.
    Args:
        room_id (str): The ID of the room.
        websocket (WebSocket): The WebSocket object to register.
    Returns:
        WebSocket: The accepted WebSocket object.
    """
    await websocket.accept() # Accept the WebSocket connection.
    
    # Check if a broadcast queue already exists for this room.
    if room_id not in broadcast_queues:
        broadcast_queues[room_id] = asyncio.Queue() # Create a new queue if not present.
        # Start a new background task to process messages from this room's broadcast queue.
        broadcast_tasks[room_id] = asyncio.create_task(_process_broadcast_queue(room_id))
        print(f"DEBUG_WS: Created new broadcast queue and task for room {room_id}.")

    # ✅ Clean up stale connections before adding the new one and counting.
    # This filters out any dead or closed connections from the list.
    room_connections[room_id] = [
        ref for ref in room_connections.get(room_id, [])
        if ref() is not None and ref().client_state.value == 1 # Filter for open connections.
    ]
    
    ws_ref = weakref.ref(websocket) # Create a weak reference to the WebSocket object.
    if ws_ref not in room_connections[room_id]:
        room_connections[room_id].append(ws_ref) # Add the weak reference to the list.
        print(f"DEBUG_WS: Registered new connection for room {room_id}. Total active connections: {len(room_connections[room_id])}")
    else:
        print(f"DEBUG_WS: WebSocket already registered for room {room_id}. Skipping.")
    
    return websocket # Return the accepted WebSocket object.

def unregister(room_id: str, websocket: WebSocket):
    """
    Unregisters a WebSocket connection from a room.
    Removes the connection and cleans up the broadcast queue/task if no connections remain for the room.
    Args:
        room_id (str): The ID of the room.
        websocket (WebSocket): The WebSocket object to unregister.
    """
    if room_id in room_connections:
        # Filter out the specific WebSocket connection to unregister.
        room_connections[room_id] = [
            ref for ref in room_connections[room_id]
            if ref() is not None and ref() is not websocket # Check if object is not None and not the one to unregister.
        ]
        
        print(f"DEBUG_WS: Unregistered connection for room {room_id}. Remaining active connections: {len(room_connections[room_id])}")
        
        if not room_connections[room_id]: # If no connections remain for this room.
            del room_connections[room_id] # Delete the room's connection list.
            # If no connections are left, cancel the broadcast queue and task for this room.
            if room_id in broadcast_queues:
                broadcast_tasks[room_id].cancel() # Cancel the background task.
                del broadcast_tasks[room_id] # Delete the task reference.
                del broadcast_queues[room_id] # Delete the queue reference.
                print(f"DEBUG_WS: Cleaned up broadcast queue and task for room {room_id} (no active connections).")
    else:
        print(f"DEBUG_WS: Attempted to unregister from non-existent room {room_id}")

# ✅ The broadcast function now puts messages into the queue instead of sending directly.
async def broadcast(room_id: str, event: str, data: dict):
    """
    Adds a message to the broadcast queue for a specific room.
    The message will be processed and sent by the background queue processor.
    Args:
        room_id (str): The ID of the room to broadcast to.
        event (str): The name of the event to broadcast.
        data (dict): The data associated with the event.
    """
    if room_id not in broadcast_queues:
        print(f"DEBUG_WS: Broadcast queue not found for room {room_id}. Cannot broadcast.")
        return # Or raise an error if broadcasting must always have a queue.
    
    await broadcast_queues[room_id].put({"event": event, "data": data}) # Add the message to the queue.
    print(f"DEBUG_WS: Message for event '{event}' added to queue for room {room_id}.")
