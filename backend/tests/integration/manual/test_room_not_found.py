#!/usr/bin/env python3
"""
Test script for non-existent room handling
"""

import asyncio
import json
import websockets
import sys

async def test_non_existent_room():
    """Test connecting to a non-existent room"""
    room_id = "FAKE999"
    uri = f"ws://localhost:5050/ws/{room_id}"
    
    print(f"🔗 Connecting to non-existent room: {room_id}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Wait for room_not_found event
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            if data.get("event") == "room_not_found":
                print("✅ Received room_not_found event")
                print(f"   Message: {data['data']['message']}")
                print(f"   Suggestion: {data['data']['suggestion']}")
                print("✅ Test PASSED - Non-existent room handled correctly")
                return True
            else:
                print(f"❌ Unexpected event: {data.get('event')}")
                return False
                
    except asyncio.TimeoutError:
        print("❌ Timeout - No room_not_found event received")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_valid_room():
    """Test that lobby connection still works"""
    uri = "ws://localhost:5050/ws/lobby"
    
    print("\n🔗 Testing valid room connection (lobby)")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected to lobby")
            
            # Send a test message
            await websocket.send(json.dumps({
                "event": "ping",
                "data": {"timestamp": 123}
            }))
            
            # Wait for response (but not room_not_found)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                
                if data.get("event") == "room_not_found":
                    print("❌ Received room_not_found for valid room!")
                    return False
                else:
                    print(f"✅ Received expected event: {data.get('event')}")
                    print("✅ Test PASSED - Valid rooms work correctly")
                    return True
            except asyncio.TimeoutError:
                # No room_not_found is good for lobby
                print("✅ No room_not_found event (expected)")
                print("✅ Test PASSED - Valid rooms work correctly")
                return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing Non-Existent Room Handling\n")
    
    # Test 1: Non-existent room
    test1_passed = await test_non_existent_room()
    
    # Test 2: Valid room (lobby)
    test2_passed = await test_valid_room()
    
    print("\n📊 Test Results:")
    print(f"   Non-existent room test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Valid room test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())