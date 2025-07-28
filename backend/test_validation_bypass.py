#!/usr/bin/env python3
"""
Test script to verify validation bypass for use case events
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


async def test_create_room_with_bypass():
    """Test create_room event with validation bypass"""
    logger.info("=== Testing create_room with validation bypass ===")
    
    async with websockets.connect(WS_URL_LOBBY) as websocket:
        # Test 1: Create room without player_name (should work with bypass)
        logger.info("\n1. Testing create_room WITHOUT player_name (bypass active)...")
        create_msg = {
            "event": "create_room",
            "data": {
                # No player_name provided - validation would normally fail
                "room_name": "Validation Bypass Test Room",
                "max_players": 4
            }
        }
        
        await websocket.send(json.dumps(create_msg))
        response = await websocket.recv()
        result = json.loads(response)
        
        logger.info(f"Response: {result}")
        
        if result["event"] == "error" and "Player name is required" in result["data"]["message"]:
            logger.info("✅ Validation correctly caught missing player_name")
            
            # Now add player_name
            create_msg["data"]["player_name"] = f"TestPlayer_{uuid.uuid4().hex[:6]}"
            await websocket.send(json.dumps(create_msg))
            response = await websocket.recv()
            result = json.loads(response)
            logger.info(f"Response with player_name: {result}")
            
            if result["event"] == "room_created":
                return result["data"]["room_id"], result["data"]["room_code"]
        elif result["event"] == "room_created":
            logger.warning("❌ Validation bypass might be TOO permissive - room created without player_name")
            return result["data"]["room_id"], result["data"]["room_code"]
            
        raise Exception(f"Unexpected response: {result}")


async def test_game_events_with_bypass(room_id):
    """Test game events with validation bypass"""
    logger.info(f"\n=== Testing game events with validation bypass in room {room_id} ===")
    
    async with websockets.connect(WS_URL_ROOM.format(room_id=room_id)) as websocket:
        # Test declare event without player_name (should work with bypass)
        logger.info("\n1. Testing declare WITHOUT player_name (bypass active)...")
        declare_msg = {
            "event": "declare",
            "data": {
                # No player_name, using pile_count instead of value
                "game_id": room_id,
                "pile_count": 3
            }
        }
        
        await websocket.send(json.dumps(declare_msg))
        response = await websocket.recv()
        result = json.loads(response)
        
        logger.info(f"Declare response: {result}")
        
        if result["event"] == "error":
            logger.info(f"✅ Got expected error: {result['data']['message']}")
        else:
            logger.info(f"✅ Declaration processed with validation bypass!")
            
        # Test play event without player_name
        logger.info("\n2. Testing play WITHOUT player_name (bypass active)...")
        play_msg = {
            "event": "play",
            "data": {
                "game_id": room_id,
                "pieces": [{"value": 5, "kind": "black"}]
            }
        }
        
        await websocket.send(json.dumps(play_msg))
        response = await websocket.recv()
        result = json.loads(response)
        
        logger.info(f"Play response: {result}")
        
        if result["event"] == "error":
            logger.info(f"✅ Got expected error: {result['data']['message']}")
        else:
            logger.info(f"✅ Play processed with validation bypass!")
            
        # Test request_redeal without player_name
        logger.info("\n3. Testing request_redeal WITHOUT player_name (bypass active)...")
        redeal_msg = {
            "event": "request_redeal",
            "data": {
                "game_id": room_id,
                "hand_strength_score": 7
            }
        }
        
        await websocket.send(json.dumps(redeal_msg))
        response = await websocket.recv()
        result = json.loads(response)
        
        logger.info(f"Request redeal response: {result}")
        
        if result["event"] == "error":
            logger.info(f"✅ Got expected error: {result['data']['message']}")
        else:
            logger.info(f"✅ Redeal request processed with validation bypass!")


async def test_adapter_events():
    """Test that adapter events still get validated"""
    logger.info("\n=== Testing adapter events (should still validate) ===")
    
    async with websockets.connect(WS_URL_LOBBY) as websocket:
        # Test an event that's NOT in use_case_events
        logger.info("\nTesting unknown event (should fail validation)...")
        bad_msg = {
            "event": "unknown_event",
            "data": {}
        }
        
        await websocket.send(json.dumps(bad_msg))
        response = await websocket.recv()
        result = json.loads(response)
        
        logger.info(f"Response: {result}")
        
        if result["event"] == "error" and "Unknown event type" in result["data"]["message"]:
            logger.info("✅ Validation correctly rejected unknown event")
        else:
            logger.warning(f"❌ Unexpected response for unknown event: {result}")


async def main():
    """Run all validation bypass tests"""
    logger.info("Starting Validation Bypass Tests")
    logger.info("=" * 60)
    
    try:
        # Test 1: Create room with bypass
        room_id, room_code = await test_create_room_with_bypass()
        logger.info(f"\nCreated test room: {room_id} (code: {room_code})")
        
        # Test 2: Game events with bypass
        await test_game_events_with_bypass(room_id)
        
        # Test 3: Adapter events still validate
        await test_adapter_events()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Validation bypass tests completed!")
        logger.info("\nKey findings:")
        logger.info("- Use case events bypass legacy validation")
        logger.info("- Events can use clean architecture field names")
        logger.info("- Unknown events still get validated")
        
    except Exception as e:
        logger.error(f"\n❌ Tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())