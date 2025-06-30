#!/usr/bin/env python3
"""
Test script to verify event-driven state machine core conversion

This test validates that:
1. Polling loop has been removed
2. Event processing works immediately 
3. State transitions happen without delays
4. Async task management works correctly
"""

import asyncio
import time
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.state_machine.events.event_types import GameEvent


class MockGame:
    def __init__(self):
        self.players = []
        self.room_id = "test_room"


async def test_no_polling_loop():
    """Test that no background polling task is created"""
    print("🧪 Testing: No polling loop created")
    
    sm = GameStateMachine(MockGame())
    await sm.start()
    
    # Should not have _process_task running
    assert sm._process_task is None or sm._process_task.done(), "Polling task should not be active"
    
    # Event processor should be available
    assert hasattr(sm, 'event_processor'), "EventProcessor should be available"
    assert hasattr(sm, 'transition_lock'), "Transition lock should be available"
    assert hasattr(sm, 'active_tasks'), "Active tasks management should be available"
    
    await sm.stop()
    print("✅ No polling loop test passed")


async def test_immediate_event_processing():
    """Test that events are processed immediately without delays"""
    print("🧪 Testing: Immediate event processing")
    
    sm = GameStateMachine(MockGame())
    await sm.start()
    
    # Create test action
    action = GameAction(
        action_type=ActionType.DEAL_CARDS,
        player_name="test_player",
        payload={}
    )
    
    # Measure processing time
    start_time = time.perf_counter()
    result = await sm.handle_action(action)
    elapsed = time.perf_counter() - start_time
    
    # Should complete very quickly (no polling delays)
    assert elapsed < 0.1, f"Processing took too long: {elapsed:.3f}s"
    assert result["immediate"] == True, "Result should be marked as immediate"
    assert "processing_time" in result, "Processing time should be reported"
    
    print(f"✅ Event processed in {elapsed:.3f}s - immediate processing working")
    
    await sm.stop()


async def test_async_task_management():
    """Test that async task lifecycle management works"""
    print("🧪 Testing: Async task lifecycle management")
    
    sm = GameStateMachine(MockGame())
    await sm.start()
    
    initial_task_count = len(asyncio.all_tasks())
    
    # Create some managed tasks
    task1 = await sm.create_managed_task(asyncio.sleep(0.1), "test_task_1")
    task2 = await sm.create_managed_task(asyncio.sleep(0.1), "test_task_2")
    
    # Tasks should be tracked
    assert len(sm.active_tasks) >= 2, "Tasks should be tracked"
    
    # Cleanup all tasks
    await sm.cleanup_all_tasks()
    
    # Tasks should be cleaned up
    assert len(sm.active_tasks) == 0, "All tasks should be cleaned up"
    
    # Task count should not grow significantly
    final_task_count = len(asyncio.all_tasks())
    assert final_task_count - initial_task_count < 5, "Task count should not grow significantly"
    
    await sm.stop()
    print("✅ Async task management test passed")


async def test_event_driven_transitions():
    """Test that state transitions work without polling"""
    print("🧪 Testing: Event-driven state transitions")
    
    sm = GameStateMachine(MockGame())
    await sm.start(GamePhase.PREPARATION)
    
    # Should start in preparation phase
    assert sm.current_phase == GamePhase.PREPARATION, "Should start in preparation"
    
    # Test immediate transition
    start_time = time.perf_counter()
    await sm._immediate_transition_to(GamePhase.DECLARATION, "Test transition")
    elapsed = time.perf_counter() - start_time
    
    # Should transition immediately
    assert elapsed < 0.05, f"Transition took too long: {elapsed:.3f}s"
    assert sm.current_phase == GamePhase.DECLARATION, "Should be in declaration phase"
    
    await sm.stop()
    print("✅ Event-driven transition test passed")


async def test_display_metadata_broadcast():
    """Test that display metadata is included in broadcasts"""
    print("🧪 Testing: Display metadata broadcast")
    
    broadcast_events = []
    
    async def mock_broadcast(event_type, event_data):
        broadcast_events.append((event_type, event_data))
    
    sm = GameStateMachine(MockGame(), broadcast_callback=mock_broadcast)
    await sm.start()
    
    # Should have broadcast phase change with display metadata
    assert len(broadcast_events) > 0, "Should have broadcast events"
    
    phase_change_event = None
    for event_type, event_data in broadcast_events:
        if event_type == "phase_change":
            phase_change_event = event_data
            break
    
    assert phase_change_event is not None, "Should have phase_change event"
    assert "immediate" in phase_change_event, "Should have immediate flag"
    assert "display" in phase_change_event, "Should have display metadata"
    
    await sm.stop()
    print("✅ Display metadata broadcast test passed")


async def run_all_tests():
    """Run all event-driven core tests"""
    print("🚀 Testing Event-Driven State Machine Core Conversion")
    print("=" * 60)
    
    tests = [
        test_no_polling_loop,
        test_immediate_event_processing,
        test_async_task_management,
        test_event_driven_transitions,
        test_display_metadata_broadcast
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All event-driven core tests passed!")
        print("✅ Phase 3.1 core conversion successful")
    else:
        print("❌ Some tests failed - check implementation")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)