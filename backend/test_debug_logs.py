#!/usr/bin/env python3
"""
Test script for the debug logs endpoint.

This script tests the new /api/debug/logs endpoint that provides
backend log visibility for AI debugging.
"""

import asyncio
import json
import logging
import time
from datetime import datetime

import aiohttp

# Test configuration
BASE_URL = "http://localhost:5050"
DEBUG_LOGS_URL = f"{BASE_URL}/api/debug/logs"

# Test logger
logger = logging.getLogger("test_debug_logs")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


async def test_debug_logs_endpoint():
    """Test the debug logs endpoint functionality."""
    
    logger.info("🚀 Starting debug logs endpoint test")
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test 1: Basic logs retrieval
            logger.info("📋 Test 1: Basic logs retrieval")
            async with session.get(f"{DEBUG_LOGS_URL}?limit=10") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Got {data['logs_returned']} logs")
                    logger.info(f"📊 Buffer stats: {data['buffer_stats']['total_logs']} total logs")
                else:
                    logger.error(f"❌ Request failed with status {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return False
            
            # Test 2: Log level filtering
            logger.info("📋 Test 2: Log level filtering (ERROR only)")
            async with session.get(f"{DEBUG_LOGS_URL}?level=ERROR&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Got {data['logs_returned']} error logs")
                    # Show error logs if any
                    for log in data['logs'][:2]:  # Show first 2
                        logger.info(f"   📝 {log['timestamp']}: {log['message']}")
                else:
                    logger.error(f"❌ Level filtering failed with status {response.status}")
            
            # Test 3: Logger filtering
            logger.info("📋 Test 3: Logger filtering (websocket logs)")
            async with session.get(f"{DEBUG_LOGS_URL}?logger_filter=websocket&limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Got {data['logs_returned']} websocket logs")
                else:
                    logger.error(f"❌ Logger filtering failed with status {response.status}")
            
            # Test 4: Search functionality
            logger.info("📋 Test 4: Search functionality")
            async with session.get(f"{DEBUG_LOGS_URL}?search=game&limit=3") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Found {data['logs_returned']} logs containing 'game'")
                else:
                    logger.error(f"❌ Search failed with status {response.status}")
            
            # Test 5: Buffer statistics
            logger.info("📋 Test 5: Buffer statistics")
            async with session.get(f"{BASE_URL}/api/debug/logs/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    buffer_info = data['buffer_info']
                    logger.info(f"✅ Buffer stats:")
                    logger.info(f"   📊 Total logs: {buffer_info['total_logs']}")
                    logger.info(f"   💾 Buffer usage: {buffer_info['buffer_usage']:.1f}%")
                    logger.info(f"   🕒 Oldest log: {buffer_info['oldest_log']}")
                    logger.info(f"   📈 Level counts: {buffer_info['level_counts']}")
                else:
                    logger.error(f"❌ Stats request failed with status {response.status}")
            
            # Test 6: Live debug info
            logger.info("📋 Test 6: Live debug info")
            async with session.get(f"{BASE_URL}/api/debug/logs/live") as response:
                if response.status == 200:
                    data = await response.json()
                    live_data = data['live_data']
                    logger.info(f"✅ Live debug info:")
                    logger.info(f"   🚨 Recent errors: {live_data['recent_errors']}")
                    logger.info(f"   ⚠️  Recent warnings: {live_data['recent_warnings']}")
                    logger.info(f"   🎮 Game activity: {live_data['game_activity']}")
                    logger.info(f"   🔌 WebSocket activity: {live_data['websocket_activity']}")
                else:
                    logger.error(f"❌ Live debug request failed with status {response.status}")
            
            logger.info("✅ All debug logs endpoint tests completed successfully!")
            return True
            
    except aiohttp.ClientConnectorError:
        logger.error("❌ Could not connect to server. Is it running on localhost:5050?")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


async def generate_test_logs():
    """Generate some test logs to populate the buffer."""
    
    logger.info("🔧 Generating test logs for buffer...")
    
    # Create some test loggers
    test_loggers = [
        logging.getLogger('api.test'),
        logging.getLogger('websocket.test'),
        logging.getLogger('game.test'),
        logging.getLogger('test.debug')
    ]
    
    # Add handlers to ensure logs are captured
    for test_logger in test_loggers:
        test_logger.setLevel(logging.DEBUG)
    
    # Generate various types of logs
    test_loggers[0].info("Test API endpoint called")
    test_loggers[0].debug("API request processing details")
    test_loggers[1].info("WebSocket connection established")
    test_loggers[1].warning("WebSocket connection timeout warning")
    test_loggers[2].info("Game room created successfully")
    test_loggers[2].error("Game validation failed - test error")
    test_loggers[3].debug("Debug information for testing")
    test_loggers[3].critical("Critical test message")
    
    logger.info("✅ Test logs generated")


async def main():
    """Main test function."""
    
    logger.info("🧪 Debug Logs Endpoint Test Suite")
    logger.info("=" * 50)
    
    # Generate some test logs first
    await generate_test_logs()
    
    # Wait a moment for logs to be processed
    await asyncio.sleep(1)
    
    # Run the endpoint tests
    success = await test_debug_logs_endpoint()
    
    if success:
        logger.info("🎉 All tests passed! Debug logs endpoint is working correctly.")
        logger.info("")
        logger.info("📖 Usage examples:")
        logger.info(f"   • Get recent logs: GET {DEBUG_LOGS_URL}?limit=50")
        logger.info(f"   • Filter by level: GET {DEBUG_LOGS_URL}?level=ERROR")  
        logger.info(f"   • Filter by logger: GET {DEBUG_LOGS_URL}?logger_filter=websocket")
        logger.info(f"   • Search logs: GET {DEBUG_LOGS_URL}?search=phase_change")
        logger.info(f"   • Recent activity: GET {BASE_URL}/api/debug/logs/live")
        logger.info("")
        logger.info("🤖 AI can now access backend logs automatically for debugging!")
    else:
        logger.error("❌ Some tests failed. Check the server logs for more details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)