#!/usr/bin/env python3
"""
Test Adapter Integration with Live Server
Verifies the adapter system is working correctly after integration into ws.py
"""

import asyncio
import json
import os
import websockets
import aiohttp
from datetime import datetime


async def test_adapter_status():
    """Test the adapter status endpoint"""
    print("\n1️⃣ Testing Adapter Status Endpoint")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/api/ws/adapter-status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Status endpoint working")
                    print(f"   Enabled: {data.get('enabled', False)}")
                    print(f"   Rollout: {data.get('rollout_percentage', 0)}%")
                    print(f"   Shadow Mode: {data.get('shadow_mode', {}).get('enabled', False)}")
                    return data
                else:
                    print(f"❌ Status endpoint returned {resp.status}")
        except Exception as e:
            print(f"❌ Error accessing status endpoint: {e}")
            print("   Make sure the server is running on localhost:8000")
    
    return None


async def test_websocket_with_adapters(enabled: bool = False):
    """Test WebSocket functionality with adapters"""
    env_status = "ENABLED" if enabled else "DISABLED"
    print(f"\n2️⃣ Testing WebSocket with Adapters {env_status}")
    print("=" * 50)
    
    try:
        # Connect to lobby
        uri = "ws://localhost:8000/ws/lobby"
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Test 1: Ping message
            ping_msg = {
                "event": "ping",
                "data": {"timestamp": 123456}
            }
            
            await websocket.send(json.dumps(ping_msg))
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            pong_data = json.loads(response)
            
            if pong_data.get("event") == "pong":
                print(f"✅ Ping/Pong working")
                print(f"   Response: {json.dumps(pong_data, indent=2)}")
                
                # Check if this came from adapter or legacy
                if enabled and pong_data.get("data", {}).get("adapter_handled"):
                    print("   ✅ Response from ADAPTER system")
                else:
                    print("   ℹ️  Response from LEGACY system")
            else:
                print(f"❌ Unexpected response: {pong_data}")
            
            # Test 2: Create room
            create_room_msg = {
                "event": "create_room",
                "data": {"player_name": f"TestPlayer_{datetime.now().strftime('%H%M%S')}"}
            }
            
            await websocket.send(json.dumps(create_room_msg))
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            room_data = json.loads(response)
            
            if room_data.get("event") == "room_created":
                print(f"✅ Room creation working")
                print(f"   Room ID: {room_data.get('data', {}).get('room_id')}")
            else:
                print(f"❌ Room creation failed: {room_data}")
                
    except asyncio.TimeoutError:
        print("❌ WebSocket timeout - no response received")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


async def main():
    """Run all integration tests"""
    print("🧪 Adapter Integration Live Test")
    print("=" * 70)
    print("Make sure the server is running with appropriate environment variables:")
    print("  - ADAPTER_ENABLED=false (default)")
    print("  - ADAPTER_ROLLOUT_PERCENTAGE=0 (default)")
    print("")
    
    # Test 1: Check adapter status
    status = await test_adapter_status()
    
    if status:
        adapter_enabled = status.get("enabled", False)
        
        # Test 2: Test with current adapter state
        await test_websocket_with_adapters(adapter_enabled)
        
        print("\n" + "=" * 70)
        print("📊 Test Summary:")
        print(f"   Adapter Status: {'ENABLED' if adapter_enabled else 'DISABLED'}")
        print(f"   Rollout: {status.get('rollout_percentage', 0)}%")
        
        if not adapter_enabled:
            print("\n💡 To test with adapters enabled:")
            print("   1. Set environment variable: ADAPTER_ENABLED=true")
            print("   2. Set rollout percentage: ADAPTER_ROLLOUT_PERCENTAGE=100")
            print("   3. Restart the server")
            print("   4. Run this test again")
    else:
        print("\n❌ Could not connect to server")
        print("   Make sure the server is running on localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())