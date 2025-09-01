#!/usr/bin/env python3
"""
Test to reproduce declaration phase hang issue
"""

import asyncio
import json
import time
import websockets

BASE_URL = "ws://localhost:5050"

async def test_declaration_hang():
    """Reproduce the declaration hang issue"""
    print("=== Testing Declaration Phase Hang ===\n")
    
    # 1. Create room
    async with websockets.connect(f"{BASE_URL}/ws/lobby") as ws:
        # Create room
        await ws.send(json.dumps({
            "event": "create_room",
            "data": {
                "player_name": "TestPlayer",
                "max_players": 4
            }
        }))
        
        response = await ws.recv()
        data = json.loads(response)
        room_id = data["data"]["room_id"]
        print(f"Created room: {room_id}")
    
    # 2. Connect to room and start game
    async with websockets.connect(f"{BASE_URL}/ws/{room_id}") as ws:
        # Join room
        await ws.send(json.dumps({
            "event": "join_room",
            "data": {
                "room_id": room_id,
                "player_name": "TestPlayer"
            }
        }))
        
        await ws.recv()  # join response
        
        # Start game
        await ws.send(json.dumps({
            "event": "start_game",
            "data": {"room_id": room_id}
        }))
        
        # Wait for game to start and reach declaration phase
        declaration_phase = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                data = json.loads(msg)
                
                if data.get("event") == "phase_change":
                    phase = data["data"].get("phase")
                    print(f"Phase changed to: {phase}")
                    
                    if phase == "declaration":
                        declaration_phase = True
                        current_declarer = data["data"].get("current_declarer")
                        print(f"Current declarer: {current_declarer}")
                        
                        # If it's our turn, make a declaration
                        if current_declarer == "TestPlayer":
                            print("Making declaration...")
                            await ws.send(json.dumps({
                                "event": "declare",
                                "data": {
                                    "player_name": "TestPlayer",
                                    "value": 5
                                }
                            }))
                            
            except asyncio.TimeoutError:
                if declaration_phase:
                    # Check if bots are making declarations
                    print(".", end="", flush=True)
        
        print(f"\n\nTest completed after {time.time() - start_time:.1f} seconds")
        print(f"Declaration phase reached: {declaration_phase}")

if __name__ == "__main__":
    asyncio.run(test_declaration_hang())