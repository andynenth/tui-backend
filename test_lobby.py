#!/usr/bin/env python3
"""Test lobby functionality"""

import asyncio
import websockets
import json
import uuid

async def test_lobby():
    # Connect to lobby
    uri = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to lobby")
            
            # Wait for client_ready acknowledgment
            await asyncio.sleep(0.5)
            
            # Send get_rooms request
            get_rooms = {
                "event": "get_rooms",
                "data": {}
            }
            await websocket.send(json.dumps(get_rooms))
            print("Sent get_rooms request")
            
            # Listen for room_list_update
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"Received: {data}")
                    
                    if data.get("event") == "room_list_update":
                        print(f"Room list update received: {data.get('data', {}).get('rooms', [])}")
                        break
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for room list")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_lobby())