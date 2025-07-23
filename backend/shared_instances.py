# backend/shared_instances.py

from engine.bot_manager import BotManager
from engine.async_room_manager import AsyncRoomManager  # Import the AsyncRoomManager class.

# Create a single instance of AsyncRoomManager.
# This instance will be shared across the entire application,
# ensuring that all parts of the backend (API routes, WebSocket handlers)
# interact with the same collection of game rooms.
shared_room_manager = AsyncRoomManager()
shared_bot_manager = BotManager()
