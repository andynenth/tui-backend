#!/usr/bin/env python3
"""
Test script to verify EventStore integration
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5050"


def test_eventstore_integration():
    """Test that events are being stored and can be retrieved"""
    
    print("🧪 Testing EventStore Integration...")
    print("-" * 50)
    # Step 1: Create a room
    print("\n1️⃣ Creating a test room...")
    # Note: Room creation is WebSocket-only, so we'll need to check existing rooms
    # or use a known room_id from manual testing
    
    # For now, let's check if the debug endpoint is accessible
    print("\n2️⃣ Checking if debug routes are mounted...")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/events/TEST123")
        print(f"Debug endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Debug routes are successfully mounted!")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error accessing debug endpoint: {e}")
        
    # Step 3: Check EventStore stats
    print("\n3️⃣ Checking EventStore statistics...")
    try:
        response = requests.get(f"{BASE_URL}/api/event-store/stats")
        if response.status_code == 200:
            print("✅ EventStore stats endpoint accessible!")
            stats = response.json()
            print(f"Total events: {stats.get('statistics', {}).get('total_events', 0)}")
            print(f"Current sequence: {stats.get('statistics', {}).get('current_sequence', 0)}")
        else:
            print(f"EventStore stats status: {response.status_code}")
    except Exception as e:
        print(f"EventStore stats error: {e}")
        
    # Step 4: Test replay endpoint
    print("\n4️⃣ Testing replay endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/replay/TEST123")
        if response.status_code == 200:
            print("✅ Replay endpoint accessible!")
            replay_data = response.json()
            print(f"Replay response: {json.dumps(replay_data, indent=2)[:200]}...")
        else:
            print(f"Replay endpoint status: {response.status_code}")
    except Exception as e:
        print(f"Replay endpoint error: {e}")


def main():
    """Run the test"""
    print(f"🚀 Starting EventStore Integration Test at {datetime.now()}")
    test_eventstore_integration()
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()