#!/usr/bin/env python3
"""
Test script for game events through direct use case integration
Tests: start_game, declare, play, request_redeal, accept_redeal, decline_redeal, player_ready
"""

import asyncio
import json
import logging
import websockets
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket server URL
WS_URL_LOBBY = "ws://localhost:5050/ws/lobby"
WS_URL_ROOM = "ws://localhost:5050/ws/{room_id}"


async def create_test_room():
    """Create a room for testing"""
    async with websockets.connect(WS_URL_LOBBY) as websocket:
        create_msg = {
            "event": "create_room",
            "data": {
                "player_name": f"TestHost_{uuid.uuid4().hex[:6]}",
                "room_name": "Game Test Room",
                "max_players": 4,
                "allow_bots": True
            }
        }
        
        await websocket.send(json.dumps(create_msg))
        response = await websocket.recv()
        result = json.loads(response)
        
        if result["event"] == "room_created":
            return result["data"]["room_id"], result["data"]["room_code"]
        else:
            raise Exception(f"Failed to create room: {result}")


async def test_game_events(room_id):
    """Test game events"""
    logger.info(f"=== Testing Game Events in room {room_id} ===")
    
    try:
        async with websockets.connect(WS_URL_ROOM.format(room_id=room_id)) as websocket:
            logger.info(f"Connected to room {room_id} WebSocket")
            
            # Test 1: Start Game
            logger.info("\n1. Testing start_game...")
            start_msg = {
                "event": "start_game",
                "data": {
                    "room_id": room_id
                }
            }
            
            await websocket.send(json.dumps(start_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Start game response: {result}")
            
            if result["event"] == "error":
                logger.error(f"Start game error: {result['data']['message']}")
                # Try with requester_id
                start_msg["data"]["requester_id"] = "test_player"
                await websocket.send(json.dumps(start_msg))
                response = await websocket.recv()
                result = json.loads(response)
                logger.info(f"Start game retry response: {result}")
            
            if result["event"] == "game_started":
                logger.info("✅ Game started successfully")
                game_id = result["data"].get("game_id", room_id)
            else:
                logger.warning("Could not start game, continuing with other tests...")
                game_id = room_id
            
            # Test 2: Declare
            logger.info("\n2. Testing declare...")
            declare_msg = {
                "event": "declare",
                "data": {
                    "game_id": game_id,
                    "room_id": room_id,
                    "pile_count": 3,
                    "player_id": "test_player"
                }
            }
            
            await websocket.send(json.dumps(declare_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Declare response: {result}")
            if result["event"] == "declaration_made":
                logger.info("✅ Declaration made successfully")
            elif result["event"] == "error":
                logger.warning(f"Declaration failed: {result['data']['message']}")
            
            # Test 3: Play pieces
            logger.info("\n3. Testing play...")
            play_msg = {
                "event": "play",
                "data": {
                    "game_id": game_id,
                    "room_id": room_id,
                    "pieces": [{"value": 5, "kind": "black"}],
                    "player_id": "test_player"
                }
            }
            
            await websocket.send(json.dumps(play_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Play response: {result}")
            if result["event"] == "play_made":
                logger.info("✅ Play made successfully")
            elif result["event"] == "error":
                logger.warning(f"Play failed: {result['data']['message']}")
            
            # Test 4: Request redeal
            logger.info("\n4. Testing request_redeal...")
            redeal_msg = {
                "event": "request_redeal",
                "data": {
                    "game_id": game_id,
                    "room_id": room_id,
                    "player_id": "test_player",
                    "hand_strength_score": 7
                }
            }
            
            await websocket.send(json.dumps(redeal_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Request redeal response: {result}")
            if result["event"] == "redeal_requested":
                logger.info("✅ Redeal requested successfully")
                redeal_id = result["data"].get("redeal_id", "test_redeal")
            elif result["event"] == "error":
                logger.warning(f"Redeal request failed: {result['data']['message']}")
                redeal_id = "test_redeal"
            
            # Test 5: Accept redeal
            logger.info("\n5. Testing accept_redeal...")
            accept_msg = {
                "event": "accept_redeal",
                "data": {
                    "game_id": game_id,
                    "room_id": room_id,
                    "player_id": "test_player_2",
                    "redeal_id": redeal_id
                }
            }
            
            await websocket.send(json.dumps(accept_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Accept redeal response: {result}")
            if result["event"] == "redeal_vote_cast":
                logger.info("✅ Redeal vote cast successfully")
            elif result["event"] == "error":
                logger.warning(f"Accept redeal failed: {result['data']['message']}")
            
            # Test 6: Decline redeal
            logger.info("\n6. Testing decline_redeal...")
            decline_msg = {
                "event": "decline_redeal",
                "data": {
                    "game_id": game_id,
                    "room_id": room_id,
                    "player_id": "test_player_3",
                    "redeal_id": redeal_id
                }
            }
            
            await websocket.send(json.dumps(decline_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Decline redeal response: {result}")
            if result["event"] == "redeal_vote_cast":
                logger.info("✅ Redeal decline cast successfully")
            elif result["event"] == "error":
                logger.warning(f"Decline redeal failed: {result['data']['message']}")
            
            # Test 7: Player ready
            logger.info("\n7. Testing player_ready...")
            ready_msg = {
                "event": "player_ready",
                "data": {
                    "game_id": game_id,
                    "room_id": room_id,
                    "player_id": "test_player",
                    "phase": "next",
                    "ready": True
                }
            }
            
            await websocket.send(json.dumps(ready_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Player ready response: {result}")
            if result["event"] == "player_ready_updated":
                logger.info("✅ Player ready updated successfully")
            elif result["event"] == "error":
                logger.warning(f"Player ready failed: {result['data']['message']}")
            
            logger.info("\n✅ Game event tests completed!")
            
    except Exception as e:
        logger.error(f"Game events test failed: {e}")
        raise


async def test_error_handling():
    """Test error handling for game events"""
    logger.info("\n=== Testing Game Event Error Handling ===")
    
    try:
        async with websockets.connect(WS_URL_LOBBY) as websocket:
            # Test 1: Start game without room_id
            logger.info("Testing start_game without room_id...")
            bad_start_msg = {
                "event": "start_game",
                "data": {}
            }
            
            await websocket.send(json.dumps(bad_start_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Error response: {result}")
            assert result["event"] == "error", "Should return error"
            logger.info("✅ Error handling correct")
            
            # Test 2: Declare without game_id
            logger.info("\nTesting declare without game_id...")
            bad_declare_msg = {
                "event": "declare",
                "data": {
                    "pile_count": 3
                }
            }
            
            await websocket.send(json.dumps(bad_declare_msg))
            response = await websocket.recv()
            result = json.loads(response)
            
            logger.info(f"Error response: {result}")
            assert result["event"] == "error", "Should return error"
            logger.info("✅ Error handling correct")
            
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        raise


async def main():
    """Run all game event tests"""
    logger.info("Starting Game Events Integration Tests")
    logger.info("=" * 60)
    
    try:
        # Create a test room
        room_id, room_code = await create_test_room()
        logger.info(f"Created test room: {room_id} (code: {room_code})")
        
        # Test game events
        await test_game_events(room_id)
        
        # Test error handling
        await test_error_handling()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 All game event tests completed!")
        logger.info("Note: Some tests may fail due to game state requirements")
        
    except Exception as e:
        logger.error(f"\n❌ Tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())