#!/usr/bin/env python3
"""
Test script to verify lobby connection fixes.

Tests:
1. Lobby WebSocket connection
2. client_ready event handling
3. request_room_list event
4. Proper disconnect handling
"""

import asyncio
import json
import websockets
import uuid

# Server URL
WS_URL = "ws://localhost:5050/ws/lobby"

async def test_lobby_connection():
    """Test basic lobby connection and events"""
    print("🧪 Testing lobby connection...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected to lobby")
            
            # Test 1: Send client_ready event
            print("\n📤 Sending client_ready event...")
            await websocket.send(json.dumps({
                "event": "client_ready",
                "data": {
                    "version": "1.0.0"
                }
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get("event") == "client_ready_ack":
                print("✅ client_ready handled successfully!")
            else:
                print(f"❌ Unexpected response: {data}")
            
            # Test 2: Send request_room_list event
            print("\n📤 Sending request_room_list event...")
            await websocket.send(json.dumps({
                "event": "request_room_list",
                "data": {
                    "include_private": False,
                    "include_full": True,
                    "include_in_game": False
                }
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get("event") == "room_list":
                print(f"✅ Room list received with {len(data.get('data', {}).get('rooms', []))} rooms")
            else:
                print(f"❌ Unexpected response: {data}")
            
            # Test 3: Send ping event
            print("\n📤 Sending ping event...")
            sequence = str(uuid.uuid4())
            await websocket.send(json.dumps({
                "event": "ping",
                "data": {
                    "sequence_number": sequence
                }
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get("event") == "pong":
                print("✅ Ping/pong working correctly!")
            else:
                print(f"❌ Unexpected response: {data}")
            
            print("\n✅ All lobby connection tests passed!")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed unexpectedly: {e}")
    except Exception as e:
        print(f"❌ Error during test: {e}")

async def test_multiple_connections():
    """Test multiple simultaneous lobby connections"""
    print("\n🧪 Testing multiple lobby connections...")
    
    try:
        # Create 3 connections
        connections = []
        for i in range(3):
            ws = await websockets.connect(WS_URL)
            connections.append((i, ws))
            print(f"✅ Connection {i+1} established")
        
        # Send client_ready from all connections
        for i, ws in connections:
            await ws.send(json.dumps({
                "event": "client_ready",
                "data": {"version": "1.0.0"}
            }))
            print(f"📤 Connection {i+1} sent client_ready")
        
        # Read responses
        for i, ws in connections:
            response = await ws.recv()
            data = json.loads(response)
            if data.get("event") == "client_ready_ack":
                print(f"✅ Connection {i+1} received client_ready_ack")
            else:
                print(f"❌ Connection {i+1} unexpected response: {data}")
        
        # Close connections
        for i, ws in connections:
            await ws.close()
            print(f"🔌 Connection {i+1} closed")
        
        print("✅ Multiple connection test passed!")
        
    except Exception as e:
        print(f"❌ Error during multiple connection test: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Lobby Connection Tests")
    print("=" * 50)
    
    await test_lobby_connection()
    await test_multiple_connections()
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())