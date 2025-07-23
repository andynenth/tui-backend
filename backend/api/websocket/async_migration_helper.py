# backend/api/websocket/async_migration_helper.py
"""
Helper module for migrating WebSocket handlers to use async room operations.
Provides wrapper functions and patterns for gradual migration.
"""

import logging
from typing import Optional, Union, Dict, Any

from backend.engine.room import Room
from backend.engine.room_manager import RoomManager
from backend.engine.async_room import AsyncRoom
from backend.engine.async_room_manager import AsyncRoomManager
from backend.engine.async_compat import AsyncCompatRoom, AsyncCompatRoomManager

logger = logging.getLogger(__name__)


class WebSocketMigrationHelper:
    """
    Helper class for migrating WebSocket handlers to async.
    Provides unified interface that works with both sync and async room managers.
    """
    
    def __init__(
        self,
        room_manager: Union[RoomManager, AsyncRoomManager, AsyncCompatRoomManager]
    ):
        """
        Initialize with either sync or async room manager.
        
        Args:
            room_manager: Can be sync RoomManager, AsyncRoomManager, or AsyncCompatRoomManager
        """
        self.room_manager = room_manager
        self.is_async = isinstance(room_manager, (AsyncRoomManager, AsyncCompatRoomManager))
        
        logger.info(f"WebSocketMigrationHelper initialized with {'async' if self.is_async else 'sync'} manager")
    
    async def create_room(self, host_name: str) -> str:
        """Create a room using appropriate method based on manager type."""
        if self.is_async:
            return await self.room_manager.create_room(host_name)
        else:
            # Run sync method without blocking event loop
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.room_manager.create_room, host_name)
    
    async def get_room(self, room_id: str) -> Optional[Union[Room, AsyncRoom, AsyncCompatRoom]]:
        """Get a room using appropriate method based on manager type."""
        if self.is_async:
            return await self.room_manager.get_room(room_id)
        else:
            # Run sync method without blocking event loop
            import asyncio
            loop = asyncio.get_event_loop()
            room = await loop.run_in_executor(None, self.room_manager.get_room, room_id)
            # Wrap sync room in async compat if needed
            if room and not isinstance(room, (AsyncRoom, AsyncCompatRoom)):
                from backend.engine.async_compat import AsyncCompatRoom
                return AsyncCompatRoom(room)
            return room
    
    async def delete_room(self, room_id: str) -> bool:
        """Delete a room using appropriate method based on manager type."""
        if self.is_async:
            return await self.room_manager.delete_room(room_id)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.room_manager.delete_room, room_id)
            return True
    
    async def list_rooms(self) -> list:
        """List rooms using appropriate method based on manager type."""
        if self.is_async:
            return await self.room_manager.list_rooms()
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.room_manager.list_rooms)


# WebSocket handler patterns for migration

async def handle_create_room_async(
    helper: WebSocketMigrationHelper,
    player_name: str
) -> Dict[str, Any]:
    """
    Pattern for handling room creation in WebSocket.
    Works with both sync and async room managers.
    """
    try:
        room_id = await helper.create_room(player_name)
        room = await helper.get_room(room_id)
        
        if not room:
            return {
                "type": "error",
                "message": "Failed to create room"
            }
        
        # Get room summary
        if hasattr(room, 'summary') and asyncio.iscoroutinefunction(room.summary):
            summary = await room.summary()
        else:
            summary = room.summary()
        
        return {
            "type": "room_created",
            "room_id": room_id,
            "room": summary
        }
        
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        return {
            "type": "error",
            "message": str(e)
        }


async def handle_join_room_async(
    helper: WebSocketMigrationHelper,
    room_id: str,
    player_name: str
) -> Dict[str, Any]:
    """
    Pattern for handling room join in WebSocket.
    Works with both sync and async rooms.
    """
    try:
        room = await helper.get_room(room_id)
        
        if not room:
            return {
                "type": "error",
                "message": f"Room {room_id} not found"
            }
        
        # Join room using appropriate method
        if hasattr(room, 'join_room') and asyncio.iscoroutinefunction(room.join_room):
            slot = await room.join_room(player_name)
        else:
            # Run sync method without blocking
            import asyncio
            loop = asyncio.get_event_loop()
            slot = await loop.run_in_executor(None, room.join_room, player_name)
        
        # Get updated room summary
        if hasattr(room, 'summary') and asyncio.iscoroutinefunction(room.summary):
            summary = await room.summary()
        else:
            summary = room.summary()
        
        return {
            "type": "joined_room",
            "slot": slot,
            "room": summary
        }
        
    except ValueError as e:
        return {
            "type": "error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        return {
            "type": "error",
            "message": "Failed to join room"
        }


async def handle_exit_room_async(
    helper: WebSocketMigrationHelper,
    room_id: str,
    player_name: str
) -> Dict[str, Any]:
    """
    Pattern for handling room exit in WebSocket.
    Works with both sync and async rooms.
    """
    try:
        room = await helper.get_room(room_id)
        
        if not room:
            return {
                "type": "error",
                "message": f"Room {room_id} not found"
            }
        
        # Exit room using appropriate method
        if hasattr(room, 'exit_room') and asyncio.iscoroutinefunction(room.exit_room):
            is_host = await room.exit_room(player_name)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            is_host = await loop.run_in_executor(None, room.exit_room, player_name)
        
        # Delete room if host exited
        if is_host:
            await helper.delete_room(room_id)
            return {
                "type": "room_deleted",
                "reason": "host_left"
            }
        
        # Get updated room summary
        if hasattr(room, 'summary') and asyncio.iscoroutinefunction(room.summary):
            summary = await room.summary()
        else:
            summary = room.summary()
        
        return {
            "type": "player_left",
            "player_name": player_name,
            "room": summary
        }
        
    except Exception as e:
        logger.error(f"Error exiting room: {e}")
        return {
            "type": "error",
            "message": "Failed to exit room"
        }


async def handle_start_game_async(
    helper: WebSocketMigrationHelper,
    room_id: str,
    broadcast_callback
) -> Dict[str, Any]:
    """
    Pattern for handling game start in WebSocket.
    Works with both sync and async rooms.
    """
    try:
        room = await helper.get_room(room_id)
        
        if not room:
            return {
                "type": "error",
                "message": f"Room {room_id} not found"
            }
        
        # Check if already started
        if room.started:
            return {
                "type": "error",
                "message": "Game already started"
            }
        
        # Start game using appropriate method
        if hasattr(room, 'start_game') and asyncio.iscoroutinefunction(room.start_game):
            result = await room.start_game(broadcast_callback)
        elif hasattr(room, 'start_game_safe'):
            # Use start_game_safe for sync rooms
            result = await room.start_game_safe(broadcast_callback)
        else:
            return {
                "type": "error",
                "message": "Room does not support game start"
            }
        
        if result.get("success"):
            return {
                "type": "game_started",
                "room_id": room_id,
                **result
            }
        else:
            return {
                "type": "error",
                "message": result.get("error", "Failed to start game")
            }
            
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        return {
            "type": "error",
            "message": str(e)
        }


# Example migration patterns

def example_websocket_handler_before():
    """Example: Current WebSocket handler (sync)"""
    # Note: This example shows legacy sync code that needs migration
    # shared_room_manager is now AsyncRoomManager, so these calls would fail
    
    # OLD SYNC CODE (DO NOT USE):
    # room = shared_room_manager.get_room(room_id)  # Would fail - needs await
    # if room:
    #     slot = room.join_room(player_name)  # Would fail - needs await
    pass


async def example_websocket_handler_after():
    """Example: Migrated WebSocket handler (async)"""
    from backend.shared_instances import shared_room_manager
    
    # Create helper
    helper = WebSocketMigrationHelper(shared_room_manager)
    
    # Async calls
    room = await helper.get_room(room_id)
    if room:
        slot = await room.join_room(player_name)  # Proper async call


# Utility to check if room supports async
def is_async_room(room: Any) -> bool:
    """Check if a room object supports async operations."""
    return isinstance(room, (AsyncRoom, AsyncCompatRoom)) or (
        hasattr(room, 'join_room') and 
        asyncio.iscoroutinefunction(room.join_room)
    )


import asyncio