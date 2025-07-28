"""
LEGACY_CODE: This file is scheduled for removal after Phase 6 migration
REPLACEMENT: backend/infrastructure/dependencies.py (DI container)
REMOVAL_TARGET: Phase 7.3
FEATURE_FLAG: USE_LEGACY_SHARED_INSTANCES
DEPENDENCIES: engine/async_room_manager.py, engine/bot_manager.py
LAST_MODIFIED: 2025-07-05
MIGRATION_STATUS: ready_for_removal
"""

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
