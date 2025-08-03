# backend/async_migration_example.py
"""
Example showing how WebSocket handlers will transition from sync to async room operations.
This file demonstrates the migration pattern for Phase 1.
"""

from backend.engine.room_manager import RoomManager
from backend.engine.async_compat import AsyncCompatRoomManager, AsyncCompatRoom

# Initialize the compatibility layer
sync_room_manager = RoomManager()
async_room_manager = AsyncCompatRoomManager(sync_room_manager)


# Example: Current WebSocket Handler Pattern (simplified)
async def websocket_handler_before(room_id: str, player_name: str):
    """Current pattern - sync calls in async context."""
    # ❌ Sync call in async context (not ideal)
    room = sync_room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    # ❌ Another sync call
    try:
        slot = room.join_room(player_name)
        return {"success": True, "slot": slot}
    except ValueError as e:
        return {"error": str(e)}


# Example: Transitional Pattern (Phase 1)
async def websocket_handler_transitional(room_id: str, player_name: str):
    """Transitional pattern - using async compatibility layer."""
    # ✅ Async call with compatibility wrapper
    room = await async_room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    # ✅ Async operations on wrapped room
    try:
        slot = await room.join_room(player_name)
        return {"success": True, "slot": slot}
    except ValueError as e:
        return {"error": str(e)}


# Example: Final Pattern (After full migration)
async def websocket_handler_final(room_id: str, player_name: str):
    """Final pattern - native async all the way."""
    # ✅ Native async room manager (future)
    room = await async_room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    # ✅ Native async room operations (future)
    try:
        slot = await room.join_room(player_name)
        # Could also do database operations here
        # await db.record_player_joined(room_id, player_name, slot)
        return {"success": True, "slot": slot}
    except ValueError as e:
        return {"error": str(e)}


# Example: How existing code continues to work
def legacy_code_example():
    """Legacy sync code continues to work during migration."""
    # Old sync code still works with the underlying sync objects
    room_id = sync_room_manager.create_room("LegacyHost")
    room = sync_room_manager.get_room(room_id)

    # Sync operations still work
    slot = room.join_room("LegacyPlayer")
    print(f"Legacy code: Player joined slot {slot}")

    return room_id


# Example: Mixed usage during migration
async def mixed_usage_example():
    """Shows how sync and async can coexist during migration."""
    # Create room with sync code
    room_id = legacy_code_example()

    # Access same room with async code
    async_room = await async_room_manager.get_room(room_id)

    # Both can modify the same underlying room
    await async_room.join_room("AsyncPlayer")

    # Verify both players are in the room
    sync_room = sync_room_manager.get_room(room_id)
    players = [p.name for p in sync_room.players if p]
    print(f"Players in room: {players}")
    # Output: ['LegacyHost', 'LegacyPlayer', 'AsyncPlayer']


# Example: Safe concurrent operations
async def concurrent_operations_example(room_id: str):
    """Shows how locks ensure thread safety."""
    room = await async_room_manager.get_room(room_id)
    if not room:
        raise ValueError("Room not found")

    # These operations are safe to run concurrently
    # The AsyncCompatRoom locks prevent race conditions
    import asyncio

    async def try_join(player_num):
        try:
            slot = await room.join_room(f"Player{player_num}")
            return f"Player{player_num} got slot {slot}"
        except ValueError as e:
            return f"Player{player_num} failed: {e}"

    # Run 10 join attempts concurrently
    results = await asyncio.gather(*[try_join(i) for i in range(10)])

    for result in results:
        print(result)


if __name__ == "__main__":
    # Demonstration of the migration pattern
    import asyncio

    async def main():
        print("=== Liap Tui Async Migration Demo ===\n")

        # Show mixed usage
        print("1. Mixed sync/async usage:")
        await mixed_usage_example()

        print("\n2. WebSocket handler patterns:")

        # Create a test room
        room_id = await async_room_manager.create_room("DemoHost")

        # Show transitional pattern
        result = await websocket_handler_transitional(room_id, "DemoPlayer")
        print(f"Transitional pattern result: {result}")

        print("\n3. Concurrent operations:")
        await concurrent_operations_example(room_id)

        print("\n=== Demo Complete ===")

    asyncio.run(main())
