#!/usr/bin/env python
"""Test script to check BOT_SLOT_FIX logging"""

import asyncio
import json
import websockets
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_bot_slot_conversion():
    """Test adding a bot using slot_id and check if conversion is logged"""
    
    # Connect to WebSocket
    ws_url = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info("Connected to WebSocket")
            
            # Create a room first
            create_room_msg = {
                "event": "create_room",
                "data": {
                    "player_name": "TestHost",
                    "room_name": "Test Room for Bot Logging",
                    "max_players": 4,
                    "allow_bots": False  # Don't auto-fill with bots
                }
            }
            
            logger.info("Creating room...")
            await websocket.send(json.dumps(create_room_msg))
            
            # Wait for room creation response (might get room_list_update first)
            room_id = None
            while True:
                response = await websocket.recv()
                response_data = json.loads(response)
                logger.info(f"Received event: {response_data.get('event')}")
                
                if response_data.get("event") == "room_created":
                    room_id = response_data["data"]["room_id"]
                    break
                elif response_data.get("event") == "room_list_update":
                    # Skip room list updates
                    continue
            
            if room_id:
                logger.info(f"Room created with ID: {room_id}")
                
                # Connect to the room
                room_ws_url = f"ws://localhost:5050/ws/{room_id}"
                async with websockets.connect(room_ws_url) as room_websocket:
                    logger.info(f"Connected to room {room_id}")
                    
                    # Send client_ready
                    client_ready_msg = {
                        "event": "client_ready",
                        "data": {
                            "player_name": "TestHost",
                            "version": "1.0.0"
                        }
                    }
                    await room_websocket.send(json.dumps(client_ready_msg))
                    await room_websocket.recv()  # Consume response
                    
                    # Now test adding a bot with slot_id (frontend format)
                    logger.info("Testing bot addition with slot_id=2 (should convert to seat_position=1)")
                    add_bot_msg = {
                        "event": "add_bot",
                        "data": {
                            "slot_id": 2,  # Frontend uses 1-based indexing
                            "difficulty": "medium",
                            "bot_name": "Test Bot"
                        }
                    }
                    
                    await room_websocket.send(json.dumps(add_bot_msg))
                    
                    # Wait for response
                    bot_response = await room_websocket.recv()
                    bot_data = json.loads(bot_response)
                    logger.info(f"Bot addition response: {bot_data}")
                    
                    # Test with invalid slot_id
                    logger.info("Testing bot addition with invalid slot_id=5")
                    invalid_bot_msg = {
                        "event": "add_bot", 
                        "data": {
                            "slot_id": 5,  # Invalid - should trigger warning
                            "difficulty": "medium"
                        }
                    }
                    
                    await room_websocket.send(json.dumps(invalid_bot_msg))
                    invalid_response = await room_websocket.recv()
                    invalid_data = json.loads(invalid_response)
                    logger.info(f"Invalid bot response: {invalid_data}")
                    
                    # Test with seat_position directly (backend format)
                    logger.info("Testing bot addition with seat_position=2 directly")
                    seat_bot_msg = {
                        "event": "add_bot",
                        "data": {
                            "seat_position": 2,  # Backend uses 0-based indexing
                            "difficulty": "hard"
                        }
                    }
                    
                    await room_websocket.send(json.dumps(seat_bot_msg))
                    seat_response = await room_websocket.recv()
                    seat_data = json.loads(seat_response)
                    logger.info(f"Seat position bot response: {seat_data}")
                    
    except Exception as e:
        logger.error(f"Error during test: {e}")

if __name__ == "__main__":
    logger.info("Starting bot slot conversion test...")
    asyncio.run(test_bot_slot_conversion())
    logger.info("\nTest complete! Check server logs for [BOT_SLOT_FIX] messages")