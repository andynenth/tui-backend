import asyncio
import json
import websockets

async def test_heartbeat():
    uri = "ws://localhost:5050/ws/6BD64D"
    async with websockets.connect(uri) as websocket:
        # First receive the room_not_found or initial message
        initial = await websocket.recv()
        print(f"Initial: {initial}")
        
        # Send client_ready first
        await websocket.send(json.dumps({
            "event": "client_ready",
            "data": {
                "room_id": "6BD64D",
                "player_name": "TestPlayer"
            }
        }))
        
        # Send a heartbeat event
        heartbeat_data = {
            "event": "heartbeat",
            "data": {
                "timestamp": 1234567890,
                "game_context": {
                    "phase": "TURN",
                    "is_my_turn": True,
                    "waiting_for": "play"
                },
                "performance": {
                    "memory_mb": 125.5
                }
            }
        }
        
        await websocket.send(json.dumps(heartbeat_data))
        print("Sent heartbeat")
        
        # Wait for pong response
        response = await websocket.recv()
        print(f"Received pong: {response}")
        
        # Keep connection open briefly
        await asyncio.sleep(1)

asyncio.run(test_heartbeat())
