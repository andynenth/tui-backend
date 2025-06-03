# backend/shared_instances.py

from engine.room_manager import RoomManager # Import the RoomManager class.

# Create a single instance of RoomManager.
# This instance will be shared across the entire application,
# ensuring that all parts of the backend (API routes, WebSocket handlers)
# interact with the same collection of game rooms.
shared_room_manager = RoomManager()
