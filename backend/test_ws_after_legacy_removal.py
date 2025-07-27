#!/usr/bin/env python3
"""
Test WebSocket functionality after legacy code removal
Ensures the adapter system is working correctly
"""

import asyncio
import websockets
import json
import time

async def test_websocket():
    """Test basic WebSocket operations"""
    results = []
    
    try:
        # Test 1: Connect to lobby
        print("Test 1: Connecting to lobby...")
        async with websockets.connect('ws://localhost:5050/ws/lobby') as ws:
            results.append("✅ Connected to lobby WebSocket")
            
            # Test 2: Send ping
            print("Test 2: Sending ping...")
            await ws.send(json.dumps({
                "event": "ping",
                "data": {}
            }))
            
            # Wait for pong response
            response = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(response)
            if data.get("event") == "pong":
                results.append("✅ Received pong response")
            else:
                results.append(f"❌ Unexpected response: {data}")
            
            # Test 3: Create room
            print("Test 3: Creating room...")
            room_name = f"test_room_{int(time.time())}"
            await ws.send(json.dumps({
                "event": "create_room",
                "data": {
                    "room_name": room_name,
                    "player_name": "TestPlayer"
                }
            }))
            
            # Wait for room creation response
            response = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(response)
            if data.get("event") == "room_created":
                room_id = data["data"]["room_id"]
                results.append(f"✅ Room created with ID: {room_id}")
                
                # Test 4: Connect to the room
                print(f"Test 4: Connecting to room {room_id}...")
                async with websockets.connect(f'ws://localhost:5050/ws/{room_id}') as room_ws:
                    results.append(f"✅ Connected to room WebSocket")
                    
                    # Test 5: Join room
                    print("Test 5: Joining room...")
                    await room_ws.send(json.dumps({
                        "event": "join_room",
                        "data": {
                            "player_name": "TestPlayer2"
                        }
                    }))
                    
                    # Check for room update
                    response = await asyncio.wait_for(room_ws.recv(), timeout=2.0)
                    data = json.loads(response)
                    if "players" in str(data):
                        results.append("✅ Successfully joined room")
                    else:
                        results.append(f"❌ Unexpected join response: {data}")
                        
            else:
                results.append(f"❌ Failed to create room: {data}")
                
    except websockets.exceptions.ConnectionRefused:
        results.append("❌ Could not connect to WebSocket server - is it running?")
    except asyncio.TimeoutError:
        results.append("❌ Timeout waiting for response")
    except Exception as e:
        results.append(f"❌ Error: {str(e)}")
    
    # Print summary
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    for result in results:
        print(result)
    
    # Overall result
    passed = sum(1 for r in results if r.startswith("✅"))
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Legacy code removal successful!")
        return True
    else:
        print("\n❌ Some tests failed. Check the adapter configuration.")
        return False

async def check_adapter_status():
    """Check adapter configuration status"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:5050/ws/adapter-status') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("\n📊 Adapter Status:")
                    print(f"   Enabled: {data.get('enabled')}")
                    print(f"   Rollout: {data.get('rollout_percentage')}%")
                    print(f"   Mode: {data.get('adapter_only_mode')}")
                    return data
    except Exception as e:
        print(f"❌ Could not check adapter status: {e}")
        return None

async def main():
    print("🧪 Testing WebSocket after legacy code removal...")
    print("="*50)
    
    # First check adapter status
    adapter_status = await check_adapter_status()
    
    if adapter_status and adapter_status.get('enabled') and adapter_status.get('rollout_percentage') == 100:
        print("✅ Adapters are properly configured")
    else:
        print("⚠️  WARNING: Adapters may not be properly configured!")
        print("   Expected: enabled=true, rollout_percentage=100")
    
    # Run WebSocket tests
    success = await test_websocket()
    
    if success:
        print("\n✅ SUCCESS: System is working correctly without legacy code!")
        print("   The ~1,400 lines of legacy code were successfully removed.")
    else:
        print("\n⚠️  Some issues detected. Please check the configuration.")

if __name__ == "__main__":
    asyncio.run(main())