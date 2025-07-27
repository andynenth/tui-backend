#!/usr/bin/env python3
"""
Test the legacy repository bridge functionality.

This script verifies that rooms created in clean architecture
are visible to legacy code after bridging.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append('.')


async def test_bridge():
    """Test the legacy bridge functionality."""
    try:
        # Import required components
        from infrastructure.dependencies import get_unit_of_work
        from infrastructure.adapters.legacy_repository_bridge import (
            legacy_bridge,
            ensure_room_visible_to_legacy
        )
        from shared_instances import shared_room_manager
        from domain.entities.room import Room, RoomStatus
        from domain.entities.player import Player
        
        logger.info("Starting legacy bridge test...")
        
        # Create a room in clean architecture
        room_id = "test_room_123"
        room_code = "TEST123"
        
        logger.info(f"Creating room {room_id} in clean architecture...")
        
        # Create room entity
        room = Room(
            room_id=room_id,
            room_code=room_code,
            room_name="Test Room",
            host_player_id="player_1",
            host_player_name="Test Host",
            max_players=4,
            created_at=datetime.utcnow()
        )
        
        # Add a player
        player = Player(
            player_id="player_1",
            name="Test Host",
            is_bot=False,
            seat_position=0
        )
        room.add_player(player)
        
        # Save to clean architecture
        uow = get_unit_of_work()
        async with uow:
            await uow.rooms.save(room)
            await uow.commit()
        
        logger.info("Room saved to clean architecture repository")
        
        # Check if room exists in legacy manager (should not)
        legacy_room_before = await shared_room_manager.get_room(room_id)
        if legacy_room_before:
            logger.warning("Room already exists in legacy manager!")
        else:
            logger.info("✓ Room not in legacy manager (as expected)")
        
        # Bridge the room
        logger.info("Bridging room to legacy manager...")
        await ensure_room_visible_to_legacy(room_id)
        
        # Check if room now exists in legacy manager
        legacy_room_after = await shared_room_manager.get_room(room_id)
        if legacy_room_after:
            logger.info("✓ Room successfully bridged to legacy manager!")
            logger.info(f"  - Room ID: {legacy_room_after.room_id}")
            logger.info(f"  - Host: {legacy_room_after.host_name}")
            logger.info(f"  - Players: {[p.name for p in legacy_room_after.players if p]}")
            logger.info(f"  - Started: {legacy_room_after.started}")
        else:
            logger.error("✗ Room not found in legacy manager after bridging!")
            return False
        
        # Test updating the room
        logger.info("\nTesting room update sync...")
        
        # Add another player in clean architecture
        player2 = Player(
            player_id="player_2",
            name="Player 2",
            is_bot=False,
            seat_position=1
        )
        
        async with uow:
            room = await uow.rooms.get_by_id(room_id)
            room.add_player(player2)
            await uow.rooms.save(room)
            await uow.commit()
        
        # Re-sync
        await legacy_bridge.sync_room_to_legacy(room_id)
        
        # Check updated room
        legacy_room_updated = await shared_room_manager.get_room(room_id)
        if legacy_room_updated:
            players = [p.name for p in legacy_room_updated.players if p]
            if "Player 2" in players:
                logger.info("✓ Room update successfully synced!")
                logger.info(f"  - Players: {players}")
            else:
                logger.error("✗ Room update not reflected in legacy manager")
        
        logger.info("\nBridge test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Bridge test failed: {e}", exc_info=True)
        return False


async def main():
    """Main test runner."""
    success = await test_bridge()
    
    if success:
        logger.info("\n✅ All bridge tests passed!")
        return 0
    else:
        logger.error("\n❌ Bridge tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)