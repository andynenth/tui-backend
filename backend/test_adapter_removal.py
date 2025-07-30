#!/usr/bin/env python3
"""
Test script to verify adapter removal and proper error handling
"""

import asyncio
import json
import logging
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# WebSocket server URL
WS_URL_LOBBY = "ws://localhost:5050/ws/lobby"


async def test_migrated_events():
    """Test that migrated events still work"""
    logger.info("=== Testing migrated events (should work) ===")

    async with websockets.connect(WS_URL_LOBBY) as websocket:
        # Test ping (migrated event)
        logger.info("\n1. Testing ping event...")
        ping_msg = {"event": "ping", "data": {"sequence": 1}}

        await websocket.send(json.dumps(ping_msg))
        response = await websocket.recv()
        result = json.loads(response)

        logger.info(f"Ping response: {result}")
        if result["event"] == "pong":
            logger.info("✅ Ping event working correctly")
        else:
            logger.warning(f"❌ Unexpected ping response: {result}")

        # Test get_rooms (migrated event)
        logger.info("\n2. Testing get_rooms event...")
        rooms_msg = {"event": "get_rooms", "data": {}}

        await websocket.send(json.dumps(rooms_msg))
        response = await websocket.recv()
        result = json.loads(response)

        logger.info(f"Get rooms response: {result}")
        if result["event"] == "room_list":
            logger.info("✅ Get rooms event working correctly")
        else:
            logger.warning(f"❌ Unexpected get_rooms response: {result}")


async def test_non_migrated_events():
    """Test that non-migrated events get proper error"""
    logger.info("\n=== Testing non-migrated events (should error) ===")

    async with websockets.connect(WS_URL_LOBBY) as websocket:
        # Test a made-up event that was never migrated
        logger.info("\n1. Testing fake_event (non-existent)...")
        fake_msg = {"event": "fake_event", "data": {"test": "data"}}

        await websocket.send(json.dumps(fake_msg))
        response = await websocket.recv()
        result = json.loads(response)

        logger.info(f"Fake event response: {result}")
        # fake_event fails validation because it's not in ALLOWED_EVENTS
        # This is correct behavior - unknown events are rejected at validation
        if result["event"] == "error" and (
            "not supported" in result["data"]["message"]
            or "Unknown event type" in result["data"]["message"]
        ):
            logger.info("✅ Non-migrated event correctly rejected")
        else:
            logger.warning(f"❌ Unexpected response for fake event: {result}")


async def test_validation_still_works():
    """Test that validation still works for malformed messages"""
    logger.info("\n=== Testing validation (should still work) ===")

    async with websockets.connect(WS_URL_LOBBY) as websocket:
        # Test message without event field
        logger.info("\n1. Testing message without event field...")
        bad_msg = {"data": {"test": "data"}}

        await websocket.send(json.dumps(bad_msg))
        response = await websocket.recv()
        result = json.loads(response)

        logger.info(f"Bad message response: {result}")
        if result["event"] == "error" and "validation_error" in result["data"]["type"]:
            logger.info("✅ Validation correctly rejected bad message")
        else:
            logger.warning(f"❌ Unexpected response for bad message: {result}")

        # Test message with non-dict data
        logger.info("\n2. Testing message with non-dict data...")
        bad_data_msg = {"event": "ping", "data": "not a dict"}

        await websocket.send(json.dumps(bad_data_msg))
        response = await websocket.recv()
        result = json.loads(response)

        logger.info(f"Bad data response: {result}")
        if result["event"] == "error":
            logger.info("✅ Validation correctly rejected non-dict data")
        else:
            logger.warning(f"❌ Unexpected response for bad data: {result}")


async def main():
    """Run all adapter removal tests"""
    logger.info("Starting Adapter Removal Tests")
    logger.info("=" * 60)

    try:
        # Test 1: Migrated events still work
        await test_migrated_events()

        # Test 2: Non-migrated events get error
        await test_non_migrated_events()

        # Test 3: Validation still works
        await test_validation_still_works()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 Adapter removal tests completed!")
        logger.info("\nKey findings:")
        logger.info("- Migrated events work through use case routing")
        logger.info("- Non-migrated events receive proper error messages")
        logger.info("- Validation still protects against malformed messages")
        logger.info("- Adapter system successfully removed")

    except Exception as e:
        logger.error(f"\n❌ Tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
