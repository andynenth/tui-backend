#!/usr/bin/env python3
"""Test WebSocket connection after Phase 1 fixes"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket():
    """Test basic WebSocket connection to lobby"""
    uri = "ws://localhost:5050/ws/lobby"
    
    try:
        logger.info(f"Connecting to {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully!")
            
            # Send a get_rooms message
            message = {
                "event": "get_rooms",
                "data": {}
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
                if data["event"] == "error":
                    logger.error(f"Error: {data.get('data', {}).get('message', 'Unknown error')}")
                else:
                    logger.info("WebSocket connection working properly!")
            
            return True
            
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    if success:
        print("\n✅ WebSocket connection test PASSED!")
    else:
        print("\n❌ WebSocket connection test FAILED!")