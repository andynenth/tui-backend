#!/usr/bin/env python3
"""Simple test to check WebSocket connection"""

import asyncio
import websockets
import json

async def test_connection():
    """Test basic WebSocket connection"""
    try:
        print("Attempting to connect to ws://localhost:8000/ws/lobby")
        async with websockets.connect("ws://localhost:8000/ws/lobby") as websocket:
            print("Connected successfully!")
            
            # Send a ping
            msg = {"event": "ping", "data": {}}
            await websocket.send(json.dumps(msg))
            print(f"Sent: {msg}")
            
            # Get response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Is the server running on http://localhost:8000 ?")

if __name__ == "__main__":
    asyncio.run(test_connection())