#!/usr/bin/env python3
"""
Test script to trigger adapter initialization by making a WebSocket connection.
"""

import asyncio
import websockets
import json

async def test_websocket_connection():
    """Connect to the WebSocket and send a test message."""
    uri = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a ping to trigger adapter initialization
            message = {
                "event": "ping",
                "data": {}
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Sent ping message")
            
            # Wait for response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Keep connection open briefly to see logs
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔌 Testing WebSocket connection to trigger adapter initialization...")
    asyncio.run(test_websocket_connection())
    print("✅ Test complete - check server logs for adapter initialization messages")