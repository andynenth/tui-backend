#!/usr/bin/env python3
"""
Test the data flow through the optimization pipeline
"""

import asyncio
import os
import sys
import logging

# Configure logging to see our debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_dataflow():
    """Test the data flow through MigrationAdapter"""
    
    # Import after setting up logging
    from backend.shared_event_store import event_store
    
    print(f"\n✅ Event store type: {type(event_store).__name__}")
    print(f"✅ Migration mode: {os.getenv('MIGRATION_MODE', 'not set')}")
    
    # Test storing an event
    test_room = "TEST123"
    test_event = "test_event"
    test_payload = {"test": "data", "value": 42}
    
    print(f"\n📤 Storing test event...")
    await event_store.store_event(test_room, test_event, test_payload)
    print(f"✅ Event stored successfully")
    
    # Try to retrieve events (if supported)
    try:
        print(f"\n📥 Retrieving events...")
        events = await event_store.get_events(test_room)
        print(f"✅ Retrieved {len(events)} events")
        if events:
            print(f"   Latest event: {events[-1]['event_type']}")
    except Exception as e:
        print(f"⚠️  Could not retrieve events: {e}")

if __name__ == "__main__":
    asyncio.run(test_dataflow())