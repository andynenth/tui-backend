#!/usr/bin/env python3
"""
🎯 **Phase 4 Event System Test** - Validation and Performance Testing

Tests the integrated event bus system with the game state machine to ensure
proper functionality, performance, and integration.
"""

import asyncio
import logging
import time
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.engine.events import (
    EventBus, EventType, EventPriority, PhaseChangeEvent, ActionEvent,
    get_global_event_bus, reset_global_event_bus, integrate_event_bus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('event_system_test.log')
    ]
)

logger = logging.getLogger(__name__)


class MockStateMachine:
    """Mock state machine for testing event integration."""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.current_phase = None
        self.phase_manager = self
        self.action_processor = self
        self.event_broadcaster = self
        self.game = None
        self.events_received = []
        
    async def trigger_immediate_transition(self, event: str, target_state, reason: str) -> bool:
        logger.info(f"Mock transition: {event} -> {target_state} ({reason})")
        self.events_received.append(('transition', event, target_state, reason))
        return True
        
    async def validate_action(self, action):
        logger.info(f"Mock validate action: {action}")
        self.events_received.append(('validate', action))
        return {'valid': True}
        
    async def broadcast_event(self, event_type: str, event_data: dict):
        logger.info(f"Mock broadcast: {event_type} - {event_data}")
        self.events_received.append(('broadcast', event_type, event_data))
        
    async def store_game_event(self, event_type: str, payload: dict, player_id: str = None):
        logger.info(f"Mock store event: {event_type} - {payload}")
        self.events_received.append(('store', event_type, payload, player_id))


async def test_event_bus_basic():
    """Test basic event bus functionality."""
    logger.info("🧪 Testing basic event bus functionality...")
    
    # Reset any existing global state
    await reset_global_event_bus("test_room_basic")
    
    # Create event bus
    event_bus = get_global_event_bus("test_room_basic")
    await event_bus.start()
    
    try:
        # Create and publish test event
        event = PhaseChangeEvent(
            room_id="test_room_basic",
            new_phase="PREPARATION",
            reason="Test event",
            priority=EventPriority.HIGH
        )
        
        # Publish event
        await event_bus.publish(event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check metrics
        metrics = event_bus.get_metrics()
        logger.info(f"📊 Basic test metrics: {metrics}")
        
        assert metrics.events_published >= 1, "Should have published at least 1 event"
        
        logger.info("✅ Basic event bus test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic test failed: {str(e)}")
        return False
        
    finally:
        await event_bus.stop()


async def test_event_integration():
    """Test event bus integration with state machine."""
    logger.info("🧪 Testing event bus integration...")
    
    # Reset any existing global state
    await reset_global_event_bus("test_room_integration")
    
    # Create mock state machine
    mock_sm = MockStateMachine("test_room_integration")
    
    try:
        # Integrate event bus
        integration = await integrate_event_bus(mock_sm, "test_room_integration")
        
        # Test integration status
        status = integration.get_integration_status()
        logger.info(f"📊 Integration status: {status}")
        
        assert status['is_integrated'], "Integration should be successful"
        assert status['handlers_registered'] > 0, "Should have registered handlers"
        assert status['middleware_count'] > 0, "Should have middleware"
        
        # Test publishing events through integration
        await integration.publish_phase_change("PREPARATION", "DECLARATION", "Test transition")
        await integration.publish_action_event("PLAY", "TestPlayer", {"pieces": [1, 2, 3]})
        await integration.publish_broadcast_event("phase_change", {"phase": "DECLARATION"})
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check if events were processed
        events_received = mock_sm.events_received
        logger.info(f"📨 Events received by mock SM: {len(events_received)}")
        
        # Get final metrics
        final_status = integration.get_integration_status()
        logger.info(f"📊 Final integration metrics: {final_status}")
        
        logger.info("✅ Integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if 'integration' in locals():
            await integration.shutdown()


async def test_performance():
    """Test event system performance."""
    logger.info("🧪 Testing event system performance...")
    
    # Reset any existing global state
    await reset_global_event_bus("test_room_performance")
    
    # Create event bus
    event_bus = get_global_event_bus("test_room_performance")
    await event_bus.start()
    
    try:
        # Performance test parameters
        num_events = 1000
        event_types = [EventType.ACTION_RECEIVED, EventType.PHASE_CHANGE_COMPLETED, EventType.BROADCAST_SENT]
        
        logger.info(f"🚀 Publishing {num_events} events for performance test...")
        
        start_time = time.time()
        
        # Publish events rapidly
        for i in range(num_events):
            event_type = event_types[i % len(event_types)]
            
            if event_type == EventType.PHASE_CHANGE_COMPLETED:
                event = PhaseChangeEvent(
                    room_id="test_room_performance",
                    new_phase=f"PHASE_{i}",
                    reason=f"Performance test {i}",
                    priority=EventPriority.NORMAL
                )
            elif event_type == EventType.ACTION_RECEIVED:
                event = ActionEvent(
                    room_id="test_room_performance",
                    action_type="PLAY",
                    player_name=f"Player{i % 4}",
                    action_payload={"test_data": i},
                    priority=EventPriority.NORMAL
                )
            else:
                # Create generic broadcast event
                from backend.engine.events.event_types import BroadcastEvent
                event = BroadcastEvent(
                    room_id="test_room_performance",
                    broadcast_type="performance_test",
                    message_data={"test_data": i},
                    priority=EventPriority.NORMAL
                )
                event.event_type = event_type
            
            await event_bus.publish(event)
            
            # Small delay to prevent overwhelming
            if i % 100 == 0:
                await asyncio.sleep(0.001)
        
        publish_time = time.time() - start_time
        
        # Wait for all events to be processed
        logger.info("⏳ Waiting for event processing to complete...")
        await asyncio.sleep(2.0)
        
        total_time = time.time() - start_time
        
        # Get final metrics
        metrics = event_bus.get_metrics()
        
        # Calculate performance stats
        events_per_second_publish = num_events / publish_time
        events_per_second_total = metrics.events_processed / total_time
        
        logger.info(f"📊 Performance Results:")
        logger.info(f"   Events Published: {metrics.events_published}")
        logger.info(f"   Events Processed: {metrics.events_processed}")
        logger.info(f"   Events Failed: {metrics.events_failed}")
        logger.info(f"   Publish Rate: {events_per_second_publish:.1f} events/sec")
        logger.info(f"   Processing Rate: {events_per_second_total:.1f} events/sec")
        logger.info(f"   Average Processing Time: {metrics.average_processing_time:.4f}s")
        logger.info(f"   Total Time: {total_time:.3f}s")
        
        # Performance assertions
        assert events_per_second_publish > 100, f"Publish rate too slow: {events_per_second_publish}"
        assert metrics.average_processing_time < 0.1, f"Processing too slow: {metrics.average_processing_time}"
        
        logger.info("✅ Performance test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance test failed: {str(e)}")
        return False
        
    finally:
        await event_bus.stop()


async def test_error_handling():
    """Test event system error handling."""
    logger.info("🧪 Testing event system error handling...")
    
    # Reset any existing global state
    await reset_global_event_bus("test_room_errors")
    
    # Create event bus
    event_bus = get_global_event_bus("test_room_errors")
    await event_bus.start()
    
    try:
        # Test with invalid event data
        event = PhaseChangeEvent(
            room_id="test_room_errors",
            new_phase="INVALID_PHASE",
            reason="Error test",
            priority=EventPriority.HIGH
        )
        
        # Publish potentially problematic event
        await event_bus.publish(event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check that system is still functioning
        metrics = event_bus.get_metrics()
        logger.info(f"📊 Error handling metrics: {metrics}")
        
        # System should still be operational
        assert metrics.events_published >= 1, "Should have published events"
        
        logger.info("✅ Error handling test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {str(e)}")
        return False
        
    finally:
        await event_bus.stop()


async def main():
    """Run all event system tests."""
    logger.info("🚀 Starting Phase 4 Event System Tests")
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Basic Event Bus", test_event_bus_basic),
        ("Event Integration", test_event_integration),
        ("Performance", test_performance),
        ("Error Handling", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Running {test_name} test...")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            test_results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name} test CRASHED: {str(e)}")
            test_results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("📊 TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Phase 4 Event System is ready for production.")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed. Phase 4 Event System needs fixes.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)