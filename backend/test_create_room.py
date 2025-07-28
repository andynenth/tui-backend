#!/usr/bin/env python3
"""Test room creation via WebSocket"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_create_room():
    """Test creating a room via WebSocket"""
    uri = "ws://localhost:5050/ws/lobby"
    
    try:
        logger.info(f"Connecting to {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully!")
            
            # Send a create_room message
            message = {
                "event": "create_room",
                "data": {
                    "player_name": "TestPlayer",
                    "room_config": {
                        "max_players": 4,
                        "bot_count": 2
                    }
                }
            }
            logger.info(f"Sending: {message}")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Parse response
            data = json.loads(response)
            if "event" in data:
                logger.info(f"Event type: {data['event']}")
                if data["event"] == "room_created":
                    logger.info(f"Room created successfully: {data.get('data', {})}")
                    return True
                elif data["event"] == "error":
                    logger.error(f"Error: {data.get('data', {}).get('message', 'Unknown error')}")
                    logger.error(f"Error details: {data.get('data', {})}")
            
            return False
            
    except Exception as e:
        logger.error(f"Room creation test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_create_room())
    if success:
        print("\n✅ Room creation test PASSED!")
    else:
        print("\n❌ Room creation test FAILED!")