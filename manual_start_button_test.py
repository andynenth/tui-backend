#!/usr/bin/env python3
"""
Manual test for start button functionality.
This simulates the exact flow: lobby → create room → start button press
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_start_button_flow():
    """Test the complete start button flow"""
    # First connect to lobby to create room
    lobby_uri = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(lobby_uri) as lobby_websocket:
            logger.info("🔌 Connected to WebSocket")
            
            # Step 1: Create a room (simulates lobby → create room)
            logger.info("📍 Step 1: Creating room...")
            create_room_msg = {
                "event": "create_room",
                "data": {
                    "player_name": "TestPlayer1",
                    "room_name": "Test Room"
                }
            }
            await lobby_websocket.send(json.dumps(create_room_msg))
            
            # Wait for room_created or room_list_update response
            response = await lobby_websocket.recv()
            create_response = json.loads(response)
            logger.info(f"✅ Response received: {create_response}")
            
            # Extract room_id from either room_created or room_list_update
            room_id = None
            if create_response.get("event") == "room_created":
                room_id = create_response["data"]["room_id"]
            elif create_response.get("event") == "room_list_update":
                # Get the first room from the list (our newly created room)
                rooms = create_response["data"]["rooms"]
                if rooms:
                    room_id = rooms[0]["room_id"]
                    logger.info(f"✅ Room created via list update")
            
            if not room_id:
                logger.error(f"❌ Could not extract room_id from: {create_response}")
                return False
            logger.info(f"🏠 Room ID: {room_id}")
            
            # Step 2: Connect to the specific room
            logger.info("📍 Step 2: Connecting to room WebSocket...")
            room_uri = f"ws://localhost:5050/ws/{room_id}"
            
            async with websockets.connect(room_uri) as room_websocket:
                logger.info("✅ Connected to room WebSocket")
                
                # Send client_ready to identify as the player
                client_ready_msg = {
                    "event": "client_ready",
                    "data": {
                        "player_name": "TestPlayer1",
                        "player_id": "TestPlayer1"
                    }
                }
                await room_websocket.send(json.dumps(client_ready_msg))
                logger.info("📡 Sent client_ready message")
                
                # Wait for acknowledgment and room state
                for _ in range(5):  # Wait for messages
                    try:
                        response = await asyncio.wait_for(room_websocket.recv(), timeout=2.0)
                        room_response = json.loads(response)
                        event = room_response.get('event', 'unknown')
                        logger.info(f"📢 Room message: {event}")
                    except asyncio.TimeoutError:
                        break
                
                # Step 3: Press start button (the critical test)
                logger.info("📍 Step 3: Pressing start button...")
                start_game_msg = {
                    "event": "start_game",
                    "data": {}
                }
                await room_websocket.send(json.dumps(start_game_msg))
                logger.info("🖱️ Start game message sent")
                
                # Wait for game_started response
                logger.info("⏳ Waiting for game_started response...")
                try:
                    response = await asyncio.wait_for(room_websocket.recv(), timeout=5.0)
                    start_response = json.loads(response)
                    logger.info(f"📢 Response received: {start_response}")
                    
                    if start_response.get("event") == "game_started":
                        logger.info("🎉 SUCCESS! Start button works - game started!")
                        return True
                    elif start_response.get("event") == "error":
                        logger.error(f"❌ ERROR: {start_response.get('data', {}).get('message', 'Unknown error')}")
                        return False
                    else:
                        logger.warning(f"⚠️ Unexpected response: {start_response}")
                        return False
                        
                except asyncio.TimeoutError:
                    logger.error("❌ TIMEOUT: No response to start_game within 5 seconds")
                    return False
                
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

async def main():
    logger.info("🧪 Starting manual start button test...")
    logger.info("🚨 Make sure server is running with ./start.sh")
    
    success = await test_start_button_flow()
    
    if success:
        logger.info("✅ START BUTTON TEST PASSED!")
        logger.info("🎯 The hive mind debugging was successful!")
    else:
        logger.error("❌ START BUTTON TEST FAILED!")
        logger.error("🔍 Further investigation needed")

if __name__ == "__main__":
    asyncio.run(main())