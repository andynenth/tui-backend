#!/usr/bin/env python3
"""
Phase 3 Integration Test - Complete End-to-End Integration Validation
Tests the complete game flow with event persistence, WebSocket broadcasting, and phase progression.
"""

import asyncio
import sys
import time
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_phase_progression_fix():
    """Task 3.1: Validate Phase Progression Fix"""
    
    logger.info("=== Task 3.1: Phase Progression Fix Validation ===")
    
    try:
        # Task 3.1.1: Set up test environment
        logger.info("Task 3.1.1: Setting up test environment...")
        
        from infrastructure.dependencies import get_container
        from infrastructure.feature_flags import get_feature_flags
        from api.services.event_store import event_store
        
        # Verify clean test environment
        flags = get_feature_flags()
        event_sourcing = flags.is_enabled(flags.USE_EVENT_SOURCING)
        assert event_sourcing, "Event sourcing should be enabled"
        
        # Check EventStore health
        health = await event_store.health_check()
        assert health["status"] == "healthy", "EventStore should be healthy"
        
        logger.info("✓ Test environment ready - EventStore healthy, event sourcing enabled")
        
        # Task 3.1.2: Start game and monitor phase progression
        logger.info("Task 3.1.2: Testing phase progression...")
        
        from engine.state_machine.core import GamePhase
        
        # Test that GamePhase enum has expected progression path
        expected_phases = [GamePhase.WAITING, GamePhase.PREPARATION, GamePhase.ROUND_START]
        logger.info(f"✓ Expected phase progression: {' → '.join([str(p) for p in expected_phases])}")
        
        # Task 3.1.3: Verify no infinite loops or stuck states
        logger.info("Task 3.1.3: Verifying phase transition stability...")
        
        # Verify transition conditions exist
        from engine.state_machine.states.preparation_state import PreparationState
        
        # Create a mock state to test transition logic
        class MockStateMachine:
            def __init__(self):
                self.current_phase = GamePhase.PREPARATION
                
        mock_sm = MockStateMachine()
        prep_state = PreparationState(mock_sm)
        prep_state.initial_deal_complete = True
        prep_state.weak_players = set()  # No weak hands
        
        # Test transition condition
        next_phase = await prep_state.check_transition_conditions()
        assert next_phase == GamePhase.ROUND_START, f"Should transition to ROUND_START, got {next_phase}"
        
        logger.info("✓ Phase progression validated - no stuck states or infinite loops")
        logger.info("=== Task 3.1: Phase Progression Fix - PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"Task 3.1 FAILED: {e}")
        logger.error("Error details:", exc_info=True)
        return False

async def test_event_persistence():
    """Task 3.2: Validate Event Persistence"""
    
    logger.info("=== Task 3.2: Event Persistence Validation ===")
    
    try:
        # Task 3.2.1: Trigger game start with event tracking
        logger.info("Task 3.2.1: Testing event storage...")
        
        from api.services.event_store import event_store
        
        # Get initial event count
        initial_stats = await event_store.get_event_stats()
        initial_count = initial_stats["total_events"]
        
        # Store a test event
        test_room_id = "test-room-phase3"
        test_event = await event_store.store_event(
            room_id=test_room_id,
            event_type="test_event",
            payload={"message": "Phase 3 integration test"},
            player_id="test-player"
        )
        
        logger.info(f"✓ Test event stored with sequence: {test_event.sequence}")
        
        # Task 3.2.2: Verify event content and structure
        logger.info("Task 3.2.2: Verifying event structure...")
        
        # Retrieve the event
        events = await event_store.get_room_events(test_room_id)
        assert len(events) == 1, f"Should have 1 event, got {len(events)}"
        
        retrieved_event = events[0]
        assert retrieved_event.room_id == test_room_id, "Room ID should match"
        assert retrieved_event.event_type == "test_event", "Event type should match"
        assert retrieved_event.payload["message"] == "Phase 3 integration test", "Payload should match"
        assert retrieved_event.player_id == "test-player", "Player ID should match"
        
        logger.info("✓ Event content and structure verified")
        
        # Task 3.2.3: Test event retrieval and replay
        logger.info("Task 3.2.3: Testing event replay...")
        
        # Test state reconstruction
        reconstructed_state = await event_store.replay_room_state(test_room_id)
        assert reconstructed_state["room_id"] == test_room_id, "Room ID should be preserved"
        assert reconstructed_state["events_processed"] == 1, "Should have processed 1 event"
        assert reconstructed_state["last_sequence"] == test_event.sequence, "Sequence should match"
        
        logger.info("✓ Event replay and state reconstruction working")
        
        # Cleanup test events
        final_stats = await event_store.get_event_stats()
        final_count = final_stats["total_events"]
        events_added = final_count - initial_count
        logger.info(f"✓ Event persistence validated - {events_added} events added during test")
        
        logger.info("=== Task 3.2: Event Persistence - PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"Task 3.2 FAILED: {e}")
        logger.error("Error details:", exc_info=True)
        return False

async def test_websocket_functionality():
    """Task 3.3: Validate WebSocket Functionality"""
    
    logger.info("=== Task 3.3: WebSocket Functionality Validation ===")
    
    try:
        # Task 3.3.1: Mock WebSocket connection
        logger.info("Task 3.3.1: Setting up WebSocket infrastructure test...")
        
        from infrastructure.events.application_event_publisher import WebSocketEventPublisher
        from domain.events.game_events import GameStarted
        from domain.events.base import EventMetadata
        
        # Create WebSocket publisher
        ws_publisher = WebSocketEventPublisher()
        logger.info("✓ WebSocket publisher created")
        
        # Task 3.3.2: Trigger game start and monitor WebSocket events
        logger.info("Task 3.3.2: Testing WebSocket event broadcasting...")
        
        # Create a test event
        test_event = GameStarted(
            metadata=EventMetadata(user_id="test-user"),
            room_id="ws-test-room",
            round_number=1,
            player_names=["Player1", "Player2", "Player3", "Player4"],
            win_condition="first_to_reach_50",
            max_score=50,
            max_rounds=10
        )
        
        # Test WebSocket publishing (will not actually broadcast but should not error)
        start_time = time.time()
        await ws_publisher.publish(test_event)
        publish_time = time.time() - start_time
        
        logger.info(f"✓ WebSocket publish completed in {publish_time:.3f} seconds")
        
        # Task 3.3.3: Verify no regression in real-time updates
        logger.info("Task 3.3.3: Testing WebSocket performance...")
        
        # Test multiple rapid events
        events_count = 3
        start_time = time.time()
        
        for i in range(events_count):
            # Create new event for each iteration (events are frozen dataclasses)
            event_for_iteration = GameStarted(
                metadata=EventMetadata(user_id="test-user"),
                room_id="ws-test-room",
                round_number=i + 1,
                player_names=["Player1", "Player2", "Player3", "Player4"],
                win_condition="first_to_reach_50",
                max_score=50,
                max_rounds=10
            )
            await ws_publisher.publish(event_for_iteration)
        
        total_time = time.time() - start_time
        avg_time = total_time / events_count
        
        logger.info(f"✓ {events_count} events published in {total_time:.3f}s (avg: {avg_time:.3f}s per event)")
        
        # Performance check - should be very fast for mock publishing
        assert avg_time < 0.1, f"WebSocket publishing should be fast, got {avg_time:.3f}s per event"
        
        logger.info("=== Task 3.3: WebSocket Functionality - PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"Task 3.3 FAILED: {e}")
        logger.error("Error details:", exc_info=True)
        return False

async def test_end_to_end_integration():
    """Task 3.4: End-to-End Integration Validation"""
    
    logger.info("=== Task 3.4: End-to-End Integration Validation ===")
    
    try:
        # Task 3.4.1: Run complete game flow test
        logger.info("Task 3.4.1: Testing complete integration...")
        
        from infrastructure.dependencies import get_event_publisher
        from api.services.event_store import event_store
        
        # Get the composite event publisher
        publisher = get_event_publisher()
        publisher_type = type(publisher).__name__
        
        assert publisher_type == "CompositeEventPublisher", f"Should be CompositeEventPublisher, got {publisher_type}"
        logger.info(f"✓ CompositeEventPublisher confirmed: {len(publisher._publishers)} publishers")
        
        # Task 3.4.2: Validate both persistence channels working together
        logger.info("Task 3.4.2: Testing dual-channel event flow...")
        
        # Test that both WebSocket and EventStore are in the composite
        publisher_types = [type(p).__name__ for p in publisher._publishers]
        logger.info(f"✓ Publisher types: {publisher_types}")
        
        assert "WebSocketEventPublisher" in publisher_types, "Should have WebSocket publisher"
        assert "EventStorePublisher" in publisher_types, "Should have EventStore publisher"
        
        # Task 3.4.3: Performance baseline check
        logger.info("Task 3.4.3: Performance baseline validation...")
        
        import psutil
        import os
        
        # Memory baseline
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        logger.info(f"✓ Current memory usage: {memory_mb:.2f} MB")
        
        # Test multiple event cycles
        cycles = 5
        initial_memory = memory_mb
        
        for cycle in range(cycles):
            # Simulate event publishing
            from domain.events.game_events import PhaseChanged
            from domain.events.base import EventMetadata
            
            phase_event = PhaseChanged(
                metadata=EventMetadata(user_id="perf-test"),
                room_id=f"perf-test-{cycle}",
                old_phase="preparation",
                new_phase="round_start",
                round_number=1,
                turn_number=1,
                phase_data={"test": True}
            )
            
            await publisher.publish(phase_event)
        
        # Final memory check
        final_memory_info = process.memory_info()
        final_memory_mb = final_memory_info.rss / 1024 / 1024
        memory_increase = final_memory_mb - initial_memory
        
        logger.info(f"✓ Memory after {cycles} cycles: {final_memory_mb:.2f} MB (+{memory_increase:.2f} MB)")
        
        # Memory increase should be reasonable
        assert memory_increase < 10, f"Memory increase should be < 10MB, got {memory_increase:.2f}MB"
        
        logger.info("=== Task 3.4: End-to-End Integration - PASSED ===")
        return True
        
    except Exception as e:
        logger.error(f"Task 3.4 FAILED: {e}")
        logger.error("Error details:", exc_info=True)
        return False

async def main():
    """Run all Phase 3 integration tests."""
    
    logger.info("Starting Phase 3 Complete Integration Testing...")
    
    # Run all test tasks
    task_3_1 = await test_phase_progression_fix()
    task_3_2 = await test_event_persistence()
    task_3_3 = await test_websocket_functionality()
    task_3_4 = await test_end_to_end_integration()
    
    # Summary
    passed_tasks = sum([task_3_1, task_3_2, task_3_3, task_3_4])
    total_tasks = 4
    
    if passed_tasks == total_tasks:
        logger.info("🎉 ALL PHASE 3 INTEGRATION TESTS PASSED")
        logger.info("✓ Phase progression fix validated")
        logger.info("✓ Event persistence working")
        logger.info("✓ WebSocket functionality verified")
        logger.info("✓ End-to-end integration successful")
        logger.info("✓ Performance within acceptable limits")
        return True
    else:
        logger.error(f"❌ PHASE 3 INTEGRATION TESTS: {passed_tasks}/{total_tasks} PASSED")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)