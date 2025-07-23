# backend/api/websocket/migration_example.py
"""
Example showing how to migrate WebSocket handlers from sync to async room operations.
This demonstrates the patterns for Phase 2 migration.
"""

from fastapi import WebSocket
import logging

# Import migration helper
from .async_migration_helper import (
    WebSocketMigrationHelper,
    handle_create_room_async,
    handle_join_room_async,
    handle_exit_room_async,
    handle_start_game_async
)

logger = logging.getLogger(__name__)


# BEFORE: Current WebSocket handler pattern (simplified)
async def websocket_handler_before(websocket: WebSocket):
    """Current pattern - sync room operations in async context."""
    from backend.shared_instances import shared_room_manager
    
    # Accept connection
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "create_room":
                # ❌ Sync call in async context
                room_id = shared_room_manager.create_room(data["player_name"])
                room = shared_room_manager.get_room(room_id)
                
                await websocket.send_json({
                    "type": "room_created",
                    "room_id": room_id,
                    "room": room.summary()
                })
            
            elif data["type"] == "join_room":
                # ❌ More sync calls
                room = shared_room_manager.get_room(data["room_id"])
                if room:
                    try:
                        slot = room.join_room(data["player_name"])
                        await websocket.send_json({
                            "type": "joined",
                            "slot": slot
                        })
                    except ValueError as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e)
                        })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# AFTER: Migrated WebSocket handler pattern
async def websocket_handler_after(websocket: WebSocket):
    """Migrated pattern - proper async room operations."""
    from backend.shared_instances import shared_room_manager
    
    # Create migration helper
    helper = WebSocketMigrationHelper(shared_room_manager)
    
    # Accept connection
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "create_room":
                # ✅ Proper async call through helper
                result = await handle_create_room_async(
                    helper,
                    data["player_name"]
                )
                await websocket.send_json(result)
            
            elif data["type"] == "join_room":
                # ✅ Async join operation
                result = await handle_join_room_async(
                    helper,
                    data["room_id"],
                    data["player_name"]
                )
                await websocket.send_json(result)
            
            elif data["type"] == "exit_room":
                # ✅ Async exit operation
                result = await handle_exit_room_async(
                    helper,
                    data["room_id"],
                    data["player_name"]
                )
                await websocket.send_json(result)
            
            elif data["type"] == "start_game":
                # ✅ Async game start
                result = await handle_start_game_async(
                    helper,
                    data["room_id"],
                    lambda event_type, data: websocket.send_json({
                        "type": "game_event",
                        "event": event_type,
                        "data": data
                    })
                )
                await websocket.send_json(result)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# PATTERN: Gradual migration of individual handlers
class WebSocketHandlerMigration:
    """Shows how to migrate handlers one at a time."""
    
    def __init__(self, room_manager):
        self.helper = WebSocketMigrationHelper(room_manager)
    
    async def handle_create_room(self, player_name: str):
        """Migrated handler for room creation."""
        return await handle_create_room_async(self.helper, player_name)
    
    async def handle_join_room(self, room_id: str, player_name: str):
        """Migrated handler for joining room."""
        return await handle_join_room_async(self.helper, room_id, player_name)
    
    # Can migrate other handlers gradually...


# PATTERN: Using with existing connection manager
async def integrate_with_connection_manager():
    """Shows integration with existing ConnectionManager."""
    from backend.api.websocket.connection_manager import ConnectionManager
    from backend.shared_instances import shared_room_manager
    
    # Create helper
    helper = WebSocketMigrationHelper(shared_room_manager)
    connection_manager = ConnectionManager()
    
    async def handle_player_action(room_id: str, player_name: str, action: dict):
        """Handle player action with async room operations."""
        
        # Get room asynchronously
        room = await helper.get_room(room_id)
        if not room:
            await connection_manager.send_to_player(
                room_id,
                player_name,
                {"type": "error", "message": "Room not found"}
            )
            return
        
        # Process action based on type
        if action["type"] == "join":
            result = await handle_join_room_async(helper, room_id, player_name)
            
            # Broadcast to all players in room
            if result["type"] != "error":
                await connection_manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "player_joined",
                        "player": player_name,
                        "room": result["room"]
                    }
                )
        
        # Add more action handlers...


# PATTERN: Compatibility during migration
async def mixed_usage_pattern():
    """Shows how sync and async can work together during migration."""
    from backend.shared_instances import shared_room_manager
    from backend.engine.async_room_manager import AsyncRoomManager
    
    # Option 1: Use compatibility helper with sync manager
    helper1 = WebSocketMigrationHelper(shared_room_manager)
    room_id = await helper1.create_room("Player1")
    
    # Option 2: Use new async manager directly
    async_manager = AsyncRoomManager()
    helper2 = WebSocketMigrationHelper(async_manager)
    room_id2 = await helper2.create_room("Player2")
    
    # Both work seamlessly!


# PATTERN: Error handling
async def robust_error_handling(websocket: WebSocket, helper: WebSocketMigrationHelper):
    """Shows proper error handling in async context."""
    
    try:
        # Room operations
        room = await helper.get_room(room_id)
        if not room:
            await websocket.send_json({
                "type": "error",
                "code": "ROOM_NOT_FOUND",
                "message": f"Room {room_id} does not exist"
            })
            return
        
        # Join with timeout
        try:
            import asyncio
            slot = await asyncio.wait_for(
                room.join_room(player_name),
                timeout=5.0
            )
            
            await websocket.send_json({
                "type": "joined",
                "slot": slot
            })
            
        except asyncio.TimeoutError:
            await websocket.send_json({
                "type": "error",
                "code": "TIMEOUT",
                "message": "Join operation timed out"
            })
        
        except ValueError as e:
            # Room full or other game logic error
            await websocket.send_json({
                "type": "error",
                "code": "GAME_ERROR",
                "message": str(e)
            })
            
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in WebSocket handler: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred"
        })


# Example: Full migration of a WebSocket endpoint
from fastapi import APIRouter

router = APIRouter()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """Fully migrated WebSocket endpoint using async operations."""
    from backend.shared_instances import shared_room_manager
    from backend.api.websocket.connection_manager import ConnectionManager
    
    # Initialize
    helper = WebSocketMigrationHelper(shared_room_manager)
    connection_manager = ConnectionManager()
    
    # Accept connection
    await websocket.accept()
    
    # Get room
    room = await helper.get_room(room_id)
    if not room:
        await websocket.close(code=4004, reason="Room not found")
        return
    
    player_name = None
    
    try:
        # Connection loop
        while True:
            data = await websocket.receive_json()
            
            # Authenticate player
            if data["type"] == "authenticate":
                player_name = data["player_name"]
                
                # Add to connection manager
                await connection_manager.add_connection(
                    room_id,
                    player_name,
                    websocket
                )
                
                # Send room state
                room_summary = await room.summary() if hasattr(room, 'summary') else room.summary()
                await websocket.send_json({
                    "type": "authenticated",
                    "room": room_summary
                })
            
            # Handle game actions
            elif data["type"] == "game_action" and player_name:
                # Process game action asynchronously
                # This is where you'd integrate with the game state machine
                pass
                
    except Exception as e:
        logger.error(f"WebSocket error for {player_name} in room {room_id}: {e}")
        
    finally:
        # Clean up
        if player_name:
            await connection_manager.remove_connection(room_id, player_name)
            
            # Handle player disconnect
            is_host = await room.exit_room(player_name)
            if is_host:
                await helper.delete_room(room_id)
                await connection_manager.broadcast_to_room(
                    room_id,
                    {"type": "room_closed", "reason": "host_disconnected"}
                )