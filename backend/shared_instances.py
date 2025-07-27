# backend/shared_instances.py

from engine.bot_manager import BotManager
from engine.async_room_manager import AsyncRoomManager  # Import the AsyncRoomManager class.

# IMPORTANT: Architecture Status Note
# ====================================
# These legacy managers are initialized at startup but are NOT used for
# business logic when clean architecture is enabled (ADAPTER_ENABLED=true).
# 
# With adapter-only mode active:
# - All room operations go through clean architecture repositories
# - All bot operations go through clean architecture services
# - These instances exist but are bypassed by the adapter system
# 
# The warnings "Room not found in AsyncRoomManager" are expected and harmless.
# Phase 7 will remove these legacy components entirely.

# Create a single instance of AsyncRoomManager.
# This instance will be shared across the entire application,
# ensuring that all parts of the backend (API routes, WebSocket handlers)
# interact with the same collection of game rooms.
shared_room_manager = AsyncRoomManager()
shared_bot_manager = BotManager()
