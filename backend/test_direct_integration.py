#!/usr/bin/env python3
"""
Test script for direct use case integration
Tests connection and lobby events through the new routing
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
WS_URL = "ws://localhost:8000/ws/lobby"


async def test_connection_events():
    """Test connection events (ping, client_ready, ack, sync_request)"""
    logger.info("=== Testing Connection Events ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info("Connected to WebSocket")
            
            # Test 1: Ping
            logger.info("Testing ping event...")
            ping_msg = {
                "event": "ping",
                "data": {
                    "timestamp": datetime.now().timestamp(),
                    "sequence": 1
                }
            }
            await websocket.send(json.dumps(ping_msg))
            response = await websocket.recv()
            pong = json.loads(response)
            logger.info(f"Ping response: {pong}")
            assert pong["event"] == "pong", f"Expected 'pong', got {pong['event']}"
            
            # Test 2: Client Ready
            logger.info("Testing client_ready event...")
            ready_msg = {
                "event": "client_ready",
                "data": {
                    "version": "1.0.0",
                    "player_id": f"test_player_{uuid.uuid4().hex[:8]}"
                }
            }
            await websocket.send(json.dumps(ready_msg))
            response = await websocket.recv()
            ready_ack = json.loads(response)
            logger.info(f"Client ready response: {ready_ack}")
            assert ready_ack["event"] == "client_ready_ack", f"Expected 'client_ready_ack', got {ready_ack['event']}"
            
            # Test 3: Ack
            logger.info("Testing ack event...")
            ack_msg = {
                "event": "ack",
                "data": {
                    "message_id": "test_msg_123"
                }
            }
            await websocket.send(json.dumps(ack_msg))
            response = await websocket.recv()
            ack_response = json.loads(response)
            logger.info(f"Ack response: {ack_response}")
            assert ack_response["event"] == "ack_received", f"Expected 'ack_received', got {ack_response['event']}"
            
            # Test 4: Sync Request
            logger.info("Testing sync_request event...")
            sync_msg = {
                "event": "sync_request",
                "data": {
                    "last_sequence": 0
                }
            }
            await websocket.send(json.dumps(sync_msg))
            response = await websocket.recv()
            sync_response = json.loads(response)
            logger.info(f"Sync response: {sync_response}")
            assert sync_response["event"] == "sync_response", f"Expected 'sync_response', got {sync_response['event']}"
            
            logger.info("✅ All connection events passed!")
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise


async def test_lobby_events():
    """Test lobby events (request_room_list, get_rooms)"""
    logger.info("\n=== Testing Lobby Events ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info("Connected to WebSocket")
            
            # Test 1: Request Room List
            logger.info("Testing request_room_list event...")
            room_list_msg = {
                "event": "request_room_list",
                "data": {
                    "include_private": False,
                    "include_full": False,
                    "include_in_progress": True
                }
            }
            await websocket.send(json.dumps(room_list_msg))
            response = await websocket.recv()
            room_list = json.loads(response)
            logger.info(f"Room list response: {room_list}")
            assert room_list["event"] == "room_list", f"Expected 'room_list', got {room_list['event']}"
            assert "rooms" in room_list["data"], "Response should contain rooms"
            assert "total_count" in room_list["data"], "Response should contain total_count"
            
            # Test 2: Get Rooms (alias)
            logger.info("Testing get_rooms event (alias)...")
            get_rooms_msg = {
                "event": "get_rooms",
                "data": {}
            }
            await websocket.send(json.dumps(get_rooms_msg))
            response = await websocket.recv()
            rooms_response = json.loads(response)
            logger.info(f"Get rooms response: {rooms_response}")
            assert rooms_response["event"] == "room_list", f"Expected 'room_list', got {rooms_response['event']}"
            
            logger.info("✅ All lobby events passed!")
            
    except Exception as e:
        logger.error(f"Lobby test failed: {e}")
        raise


async def test_error_handling():
    """Test error handling for invalid events"""
    logger.info("\n=== Testing Error Handling ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            logger.info("Connected to WebSocket")
            
            # Test 1: Missing event
            logger.info("Testing missing event...")
            no_event_msg = {
                "data": {"test": "data"}
            }
            await websocket.send(json.dumps(no_event_msg))
            response = await websocket.recv()
            error_response = json.loads(response)
            logger.info(f"Error response: {error_response}")
            assert error_response["event"] == "error", f"Expected 'error', got {error_response['event']}"
            assert error_response["data"]["type"] == "routing_error", "Should be routing error"
            
            # Test 2: Unsupported event
            logger.info("Testing unsupported event...")
            unsupported_msg = {
                "event": "unsupported_event_xyz",
                "data": {}
            }
            await websocket.send(json.dumps(unsupported_msg))
            response = await websocket.recv()
            error_response = json.loads(response)
            logger.info(f"Error response: {error_response}")
            assert error_response["event"] == "error", f"Expected 'error', got {error_response['event']}"
            assert error_response["data"]["type"] == "unsupported_event", "Should be unsupported event"
            
            logger.info("✅ Error handling tests passed!")
            
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        raise


async def main():
    """Run all tests"""
    logger.info("Starting Direct Integration Tests")
    logger.info("=" * 50)
    
    try:
        # Test connection events
        await test_connection_events()
        
        # Test lobby events
        await test_lobby_events()
        
        # Test error handling
        await test_error_handling()
        
        logger.info("\n" + "=" * 50)
        logger.info("🎉 All tests passed successfully!")
        logger.info("Connection and lobby events are working with direct use case integration")
        
    except Exception as e:
        logger.error(f"\n❌ Tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())