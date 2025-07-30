#!/usr/bin/env python3
"""Test script to create a room via WebSocket."""

import asyncio
import json
import websockets
import uuid

async def test_create_room():
    uri = "ws://localhost:5050/ws/lobby"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send create_room message
        create_room_msg = {
            "action": "create_room",
            "data": {
                "player_name": f"TestPlayer{uuid.uuid4().hex[:8]}"
            }
        }
        
        print(f"Sending: {json.dumps(create_room_msg, indent=2)}")
        await websocket.send(json.dumps(create_room_msg))
        
        # Wait for response
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"Received: {json.dumps(response_data, indent=2)}")
        
        # Keep connection open for a bit to see any other messages
        try:
            while True:
                msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"Additional message: {json.loads(msg)}")
        except asyncio.TimeoutError:
            print("No more messages after 2 seconds")

if __name__ == "__main__":
    asyncio.run(test_create_room())