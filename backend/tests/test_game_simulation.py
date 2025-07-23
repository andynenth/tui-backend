# backend/tests/test_game_simulation.py

"""
Integration test that simulates a complete game and demonstrates replay functionality.
Run this to verify the event store is working correctly with the game engine.
"""

import asyncio
import json
import logging
from datetime import datetime

from backend.api.services.event_store import event_store
from backend.shared_instances import shared_room_manager, shared_bot_manager
from backend.engine.state_machine.core import GamePhase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simulate_game_with_replay():
    """Simulate a complete game and demonstrate replay capability"""
    
    # Create a test room
    room_id = shared_room_manager.create_room("Alice")
    room = shared_room_manager.get_room(room_id)
    
    logger.info(f"Created room {room_id} with host Alice")
    
    # Add more players
    room.join_room("Bob")
    room.join_room("Charlie")  
    room.join_room("David")
    
    logger.info("Added all players to room")
    
    # Create broadcast callback that logs events
    events_broadcast = []
    
    async def test_broadcast(event_type: str, data: dict):
        events_broadcast.append({
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Broadcast: {event_type}")
    
    # Start the game
    try:
        result = await room.start_game_safe(test_broadcast)
        if not result["success"]:
            logger.error("Failed to start game")
            return
        
        logger.info("Game started successfully")
        
        # Let the game run for a bit to generate events
        await asyncio.sleep(2)
        
        # Get the state machine
        state_machine = room.game_state_machine
        
        # Log current phase
        current_phase = state_machine.get_current_phase()
        logger.info(f"Current phase: {current_phase.value if current_phase else 'Unknown'}")
        
        # Wait a bit more for some game progression
        await asyncio.sleep(3)
        
        # Now let's examine what was stored in the event store
        logger.info("\n" + "="*60)
        logger.info("EXAMINING STORED EVENTS")
        logger.info("="*60)
        
        # Get all events for the room
        all_events = await event_store.get_room_events(room_id)
        logger.info(f"Total events stored: {len(all_events)}")
        
        # Count events by type
        event_types = {}
        for event in all_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        logger.info("\nEvent type breakdown:")
        for event_type, count in sorted(event_types.items()):
            logger.info(f"  {event_type}: {count}")
        
        # Get event timeline
        logger.info("\nEvent timeline:")
        for i, event in enumerate(all_events[:10]):  # Show first 10 events
            logger.info(f"  {i+1}. [{event.sequence}] {event.event_type} - {event.player_id or 'System'}")
        
        if len(all_events) > 10:
            logger.info(f"  ... and {len(all_events) - 10} more events")
        
        # Replay the game state
        logger.info("\n" + "="*60)
        logger.info("REPLAYING GAME STATE")
        logger.info("="*60)
        
        replayed_state = await event_store.replay_room_state(room_id)
        
        logger.info(f"Replayed state from {replayed_state['events_processed']} events")
        logger.info(f"Current phase: {replayed_state.get('phase', 'Unknown')}")
        logger.info(f"Round number: {replayed_state.get('round_number', 0)}")
        
        # Show player information
        if "players" in replayed_state:
            logger.info("\nPlayers in game:")
            for player_name, player_data in replayed_state["players"].items():
                logger.info(f"  {player_name}: {player_data}")
        
        # Show phase-specific data
        if "phase_data" in replayed_state:
            logger.info("\nPhase data:")
            for phase, data in replayed_state["phase_data"].items():
                logger.info(f"  {phase}: {json.dumps(data, indent=2)}")
        
        # Validate event sequence
        logger.info("\n" + "="*60)
        logger.info("VALIDATING EVENT SEQUENCE")
        logger.info("="*60)
        
        validation = await event_store.validate_event_sequence(room_id)
        logger.info(f"Sequence valid: {validation['valid']}")
        logger.info(f"Total events: {validation['total_events']}")
        if validation["gaps"]:
            logger.warning(f"Found {len(validation['gaps'])} gaps in sequence")
        
        # Export complete history
        logger.info("\n" + "="*60)
        logger.info("EXPORTING GAME HISTORY")
        logger.info("="*60)
        
        history = await event_store.export_room_history(room_id)
        
        logger.info(f"Room ID: {history['room_id']}")
        logger.info(f"Total events: {history['total_events']}")
        logger.info(f"Event types: {', '.join(history['event_types'])}")
        
        # Show timeline sample
        logger.info("\nTimeline (last 5 events):")
        for event in history["timeline"][-5:]:
            logger.info(f"  Seq {event['sequence']}: {event['type']} by {event['player'] or 'System'}")
        
        # Test incremental updates
        logger.info("\n" + "="*60)
        logger.info("TESTING INCREMENTAL UPDATES")
        logger.info("="*60)
        
        if all_events:
            mid_sequence = all_events[len(all_events)//2].sequence
            recent_events = await event_store.get_events_since(room_id, mid_sequence)
            logger.info(f"Events since sequence {mid_sequence}: {len(recent_events)}")
        
        # Clean up - delete the room
        shared_room_manager.delete_room(room_id)
        logger.info(f"\nCleaned up - deleted room {room_id}")
        
        # Show final statistics
        stats = await event_store.get_event_stats()
        logger.info("\n" + "="*60)
        logger.info("EVENT STORE STATISTICS")
        logger.info("="*60)
        logger.info(f"Total events in store: {stats['total_events']}")
        logger.info(f"Current sequence counter: {stats['current_sequence']}")
        logger.info(f"Events in last 24h: {stats['events_last_24h']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during game simulation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_debug_endpoints():
    """Test the debug REST endpoints"""
    logger.info("\n" + "="*60)
    logger.info("DEBUG ENDPOINTS TEST")
    logger.info("="*60)
    
    # Note: This would normally use an HTTP client like aiohttp
    # For now, we'll just show what endpoints are available
    
    endpoints = [
        "GET /api/debug/events/{room_id}",
        "GET /api/debug/replay/{room_id}", 
        "GET /api/debug/events/{room_id}/sequence/{seq}",
        "GET /api/debug/export/{room_id}",
        "GET /api/debug/stats",
        "POST /api/debug/cleanup",
        "GET /api/debug/validate/{room_id}"
    ]
    
    logger.info("Available debug endpoints:")
    for endpoint in endpoints:
        logger.info(f"  {endpoint}")
    
    logger.info("\nTo test these endpoints, run the server and use:")
    logger.info("  curl http://localhost:8000/api/debug/stats")
    logger.info("  curl http://localhost:8000/api/debug/events/ROOM_ID")


async def main():
    """Run all tests"""
    logger.info("Starting State Sync/Replay Integration Test")
    logger.info("=" * 60)
    
    # Run game simulation
    success = await simulate_game_with_replay()
    
    if success:
        logger.info("\n✅ Game simulation and replay test completed successfully!")
    else:
        logger.error("\n❌ Game simulation test failed!")
    
    # Show debug endpoint info
    await test_debug_endpoints()
    
    logger.info("\n" + "="*60)
    logger.info("Test completed")


if __name__ == "__main__":
    asyncio.run(main())