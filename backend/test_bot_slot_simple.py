#!/usr/bin/env python
"""Simple test to check BOT_SLOT_FIX logging by removing then adding a bot"""

import asyncio
import json
import websockets
import logging
import os

# Enable debug logging
os.environ['LOG_LEVEL'] = 'DEBUG'

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_bot_slot_conversion():
    """Test adding a bot using slot_id and check if conversion is logged"""
    
    ws_url = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info("Connected to lobby WebSocket")
            
            # Create a room (it will auto-fill with bots)
            create_room_msg = {
                "event": "create_room",
                "data": {
                    "player_name": "TestHost",
                    "room_name": "Test Bot Slot Conversion",
                    "max_players": 4
                }
            }
            
            await websocket.send(json.dumps(create_room_msg))
            
            # Wait for room creation
            room_id = None
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if data.get("event") == "room_created":
                    room_id = data["data"]["room_id"]
                    logger.info(f"Room created: {room_id}")
                    break
            
            # Connect to the room
            room_ws_url = f"ws://localhost:5050/ws/{room_id}"
            async with websockets.connect(room_ws_url) as room_ws:
                logger.info(f"Connected to room {room_id}")
                
                # Send client_ready
                await room_ws.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "TestHost", "version": "1.0.0"}
                }))
                
                # Wait for ack
                response = await room_ws.recv()
                data = json.loads(response)
                logger.info(f"Client ready ack: {data.get('event')}")
                
                # Get current room state
                room_state = data.get("data", {}).get("room_state", {})
                players = room_state.get("players", [])
                logger.info(f"Current players: {[p['name'] for p in players]}")
                
                # Find a bot to remove
                bot_to_remove = None
                for player in players:
                    if player.get("is_bot"):
                        bot_to_remove = player["player_id"]
                        logger.info(f"Will remove bot: {player['name']} (ID: {bot_to_remove})")
                        break
                
                if bot_to_remove:
                    # Remove the bot
                    remove_msg = {
                        "event": "remove_player",
                        "data": {"player_id": bot_to_remove}
                    }
                    await room_ws.send(json.dumps(remove_msg))
                    
                    # Wait for removal response
                    while True:
                        response = await room_ws.recv()
                        data = json.loads(response)
                        if data.get("event") == "player_removed":
                            logger.info("Bot removed successfully")
                            break
                        elif data.get("event") == "room_update":
                            # Just log and continue
                            logger.info("Received room update after removal")
                    
                    # Now add a bot using slot_id (frontend format)
                    logger.info("\n=== TESTING BOT ADDITION WITH slot_id ===")
                    logger.info("Sending add_bot with slot_id=2 (frontend 1-based index)")
                    
                    add_bot_msg = {
                        "event": "add_bot",
                        "data": {
                            "slot_id": 2,  # Frontend uses 1-based indexing
                            "difficulty": "medium",
                            "bot_name": "TestBot_SlotID"
                        }
                    }
                    
                    await room_ws.send(json.dumps(add_bot_msg))
                    
                    # Wait for response
                    response = await room_ws.recv()
                    data = json.loads(response)
                    logger.info(f"Bot addition response: {data}")
                    
                    logger.info("\n=== CHECK SERVER LOGS FOR [BOT_SLOT_FIX] MESSAGE ===")
                    logger.info("The server should have logged:")
                    logger.info("[BOT_SLOT_FIX] Converted slot_id 2 to seat_position 1")
                    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting bot slot conversion test...")
    logger.info("Server should be running with LOG_LEVEL=DEBUG")
    asyncio.run(test_bot_slot_conversion())
    logger.info("\nTest complete!")