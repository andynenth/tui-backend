import asyncio
import json
import websockets
import time

async def test_heartbeat():
    uri = "ws://localhost:5050/ws/D651CB"
    async with websockets.connect(uri) as websocket:
        # First receive the initial message
        initial = await websocket.recv()
        print(f"Initial: {initial}")
        
        # Send join_room event
        await websocket.send(json.dumps({
            "event": "join_room",
            "data": {
                "room_id": "D651CB",
                "player_name": "TestBot"
            }
        }))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Join response: {response}")
        
        # Send multiple heartbeats
        for i in range(3):
            heartbeat_data = {
                "event": "heartbeat",
                "data": {
                    "timestamp": time.time(),
                    "game_context": {
                        "phase": "TURN",
                        "is_my_turn": False,
                        "waiting_for": "other_player"
                    },
                    "performance": {
                        "memory_mb": 125.5 + i
                    }
                }
            }
            
            await websocket.send(json.dumps(heartbeat_data))
            print(f"Sent heartbeat {i+1}")
            
            # Wait for pong response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received (timeout)")
            
            await asyncio.sleep(2)
        
        # Keep connection open to be tracked
        print("Keeping connection open for 10 seconds...")
        await asyncio.sleep(10)

asyncio.run(test_heartbeat())