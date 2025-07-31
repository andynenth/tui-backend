#!/usr/bin/env python3
"""
Simple WebSocket client to test what events the backend actually sends.
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_events():
    """Connect to backend and listen for events."""
    
    # Create a test room first via REST API
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Create room
        room_data = {
            "room_name": "Test Room",
            "max_players": 4,
            "host_name": "TestHost"
        }
        
        async with session.post('http://localhost:5050/api/rooms', json=room_data) as resp:
            if resp.status != 200:
                logger.error(f"Failed to create room: {resp.status}")
                return
            
            result = await resp.json()
            room_id = result['room_id']
            logger.info(f"Created room: {room_id}")
        
        # Add bots to fill the room
        for i in range(3):
            bot_data = {"bot_name": f"Bot{i+1}"}
            async with session.post(f'http://localhost:5050/api/rooms/{room_id}/bots', json=bot_data) as resp:
                if resp.status == 200:
                    logger.info(f"Added Bot{i+1}")
    
    # Connect via WebSocket
    uri = f"ws://localhost:5050/ws/{room_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to WebSocket: {uri}")
            
            # Send initial ready message
            ready_msg = {
                "event": "client_ready",
                "data": {
                    "room_id": room_id,
                    "player_name": "TestHost",
                    "is_reconnection": False
                }
            }
            await websocket.send(json.dumps(ready_msg))
            logger.info("Sent client_ready")
            
            # Start the game
            start_msg = {
                "event": "start_game", 
                "data": {"player_name": "TestHost"}
            }
            await websocket.send(json.dumps(start_msg))
            logger.info("Sent start_game")
            
            # Listen for events
            event_count = 0
            while event_count < 10:  # Limit to avoid infinite loop
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    event_count += 1
                    
                    logger.info(f"Event {event_count}: {data['event']}")
                    
                    if data['event'] == 'game_started':
                        logger.info("🎮 GAME_STARTED EVENT:")
                        logger.info(json.dumps(data, indent=2))
                    
                    elif data['event'] == 'phase_change':
                        logger.info("🔄 PHASE_CHANGE EVENT:")
                        logger.info(json.dumps(data, indent=2))
                        
                        # Check if phase_data is present
                        if 'phase_data' in data.get('data', {}):
                            logger.info("✅ phase_data is present")
                        else:
                            logger.warning("❌ phase_data is missing!")
                    
                except asyncio.TimeoutError:
                    logger.info("No more events received, stopping")
                    break
                    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_events())