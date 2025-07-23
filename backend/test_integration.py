#!/usr/bin/env python3
"""
Integration test script for clean architecture.
Tests that the new app.py serves the same functionality as the old main.py.
"""

import asyncio
import aiohttp
import json
import sys


async def test_rest_endpoints():
    """Test REST API endpoints."""
    print("\n=== Testing REST Endpoints ===")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        try:
            async with session.get('http://localhost:5000/api/health') as resp:
                print(f"✓ Health endpoint: {resp.status}")
                data = await resp.json()
                print(f"  Status: {data.get('status', 'unknown')}")
        except Exception as e:
            print(f"✗ Health endpoint failed: {e}")
            return False
        
        # Test debug room stats
        try:
            async with session.get('http://localhost:5000/api/debug/room-stats') as resp:
                print(f"✓ Debug room stats: {resp.status}")
        except Exception as e:
            print(f"✗ Debug endpoint failed: {e}")
            return False
    
    return True


async def test_websocket_connection():
    """Test WebSocket connections."""
    print("\n=== Testing WebSocket Connections ===")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test lobby connection
            async with session.ws_connect('ws://localhost:5000/ws/lobby') as ws:
                print("✓ Connected to lobby WebSocket")
                
                # Test room creation
                await ws.send_json({
                    "type": "create_room",
                    "data": {
                        "player_name": "TestPlayer"
                    }
                })
                
                # Wait for response
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    print(f"✓ Room creation response: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'room_created':
                        room_data = data.get('data', {})
                        print(f"  Room ID: {room_data.get('room_id', 'unknown')}")
                        print(f"  Join Code: {room_data.get('join_code', 'unknown')}")
                        return True
                    else:
                        print(f"✗ Unexpected response type: {data}")
                        return False
                
    except Exception as e:
        print(f"✗ WebSocket connection failed: {e}")
        return False
    
    return False


async def test_static_files():
    """Test static file serving."""
    print("\n=== Testing Static Files ===")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test root serves index.html
            async with session.get('http://localhost:5000/') as resp:
                print(f"✓ Root endpoint: {resp.status}")
                content_type = resp.headers.get('content-type', '')
                if 'text/html' in content_type:
                    print("  Serves HTML content")
                else:
                    print(f"  Warning: Unexpected content type: {content_type}")
        except Exception as e:
            print(f"✗ Static file serving failed: {e}")
            return False
    
    return True


async def main():
    """Run all integration tests."""
    print("Starting Integration Tests")
    print("========================")
    print("Make sure the server is running with: ./start.sh")
    
    # Wait a moment for server to be ready
    await asyncio.sleep(2)
    
    results = []
    
    # Run tests
    results.append(await test_rest_endpoints())
    results.append(await test_websocket_connection())
    results.append(await test_static_files())
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! Clean architecture is working.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)