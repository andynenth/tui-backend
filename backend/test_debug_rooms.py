#!/usr/bin/env python3
"""Debug room listing issue."""

import asyncio
from infrastructure.repositories.in_memory_room_repository import InMemoryRoomRepository
from domain.entities.room import Room

async def test_room_listing():
    repo = InMemoryRoomRepository()
    
    # Create a room
    room = Room(
        room_id="TEST123",
        host_name="Alice",
        max_slots=4
    )
    
    print(f"Room created with status: {room.status.value}")
    print(f"Room slots: {[p.name if p else 'empty' for p in room.slots]}")
    
    # Save room
    await repo.save(room)
    
    # List all rooms
    all_rooms = list(repo._rooms.values())
    print(f"\nTotal rooms in repository: {len(all_rooms)}")
    for r in all_rooms:
        player_count = len([s for s in r.slots if s])
        print(f"  - Room {r.room_id}: status={r.status.value}, players={player_count}")
    
    # List active rooms
    active_rooms = await repo.list_active()
    print(f"\nActive rooms: {len(active_rooms)}")
    for r in active_rooms:
        print(f"  - Room {r.room_id}: status={r.status.value}")

if __name__ == "__main__":
    asyncio.run(test_room_listing())