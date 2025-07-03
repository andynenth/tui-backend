#!/usr/bin/env python3
"""
Phase 1 Post-Migration Validation Tests

Run these tests after completing the migration to ensure everything works correctly.
"""

import asyncio
import json
import time
from typing import Dict, Any

# Test framework
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}


def test(name: str):
    """Decorator for test functions"""
    def decorator(func):
        async def wrapper():
            print(f"\n🧪 Testing: {name}")
            try:
                result = await func() if asyncio.iscoroutinefunction(func) else func()
                if result:
                    print(f"  ✅ PASSED")
                    test_results["passed"] += 1
                    test_results["tests"].append({"name": name, "passed": True})
                else:
                    print(f"  ❌ FAILED")
                    test_results["failed"] += 1
                    test_results["tests"].append({"name": name, "passed": False})
                return result
            except Exception as e:
                print(f"  ❌ FAILED with error: {e}")
                test_results["failed"] += 1
                test_results["tests"].append({"name": name, "passed": False, "error": str(e)})
                return False
        return wrapper
    return decorator


@test("StateManager Creation")
async def test_state_manager_creation():
    """Test that StateManager can be created and initialized"""
    from backend.engine.state import StateManager
    
    manager = StateManager(game_id="test_game", room_id="test_room")
    assert manager.current_version == 0
    assert manager.current_snapshot is None
    return True


@test("State Snapshot Creation")
async def test_snapshot_creation():
    """Test creating state snapshots with version incrementing"""
    from backend.engine.state import StateManager
    
    manager = StateManager(game_id="test_game", room_id="test_room")
    
    # Create first snapshot
    snapshot1 = await manager.create_snapshot(
        phase="PREPARATION",
        phase_data={"test": "data"},
        players={"player1": {"score": 0}},
        round_number=1,
        turn_number=0,
        reason="Test snapshot 1"
    )
    
    assert snapshot1.version == 1
    assert snapshot1.phase == "PREPARATION"
    assert manager.current_version == 1
    
    # Create second snapshot
    snapshot2 = await manager.create_snapshot(
        phase="DECLARATION",
        phase_data={"test": "data2"},
        players={"player1": {"score": 10}},
        round_number=1,
        turn_number=1,
        reason="Test snapshot 2"
    )
    
    assert snapshot2.version == 2
    assert manager.current_version == 2
    
    return True


@test("Checksum Calculation")
async def test_checksum():
    """Test that checksums are calculated and validated correctly"""
    from backend.engine.state import StateSnapshot
    
    snapshot = StateSnapshot(
        version=1,
        timestamp=time.time(),
        game_id="test",
        room_id="test",
        phase="TURN",
        phase_data={"current_player": "player1"},
        players={"player1": {"score": 5}},
        round_number=1,
        turn_number=3,
        reason="Test"
    )
    
    # Verify checksum was calculated
    assert snapshot.checksum is not None
    assert len(snapshot.checksum) == 16  # We use first 16 chars
    
    # Verify validation works
    assert snapshot.validate_checksum() == True
    
    # Modify data and verify checksum fails
    snapshot.phase = "MODIFIED"
    assert snapshot.validate_checksum() == False
    
    return True


@test("State History Tracking")
async def test_history():
    """Test that state history is maintained correctly"""
    from backend.engine.state import StateManager
    
    manager = StateManager(game_id="test", room_id="test", max_history=3)
    
    # Create 4 snapshots (more than max_history)
    for i in range(4):
        await manager.create_snapshot(
            phase=f"PHASE_{i}",
            phase_data={"index": i},
            players={},
            round_number=1,
            turn_number=i,
            reason=f"Snapshot {i}"
        )
    
    # Should only have 3 in history (max_history)
    assert len(manager.snapshot_history) == 3
    
    # Should be able to get version history
    history = manager.get_version_history(limit=10)
    assert len(history) == 3
    assert history[-1]["version"] == 4  # Latest
    assert history[0]["version"] == 2   # Oldest kept
    
    return True


@test("WebSocket Integration")
async def test_websocket_integration():
    """Test that state updates include version and checksum"""
    from backend.engine.state import StateManager
    
    # Mock broadcast function
    broadcast_calls = []
    
    async def mock_broadcast(room_id: str, event: str, data: dict):
        broadcast_calls.append({
            "room_id": room_id,
            "event": event,
            "data": data
        })
    
    # Temporarily replace broadcast
    import backend.socket_manager
    original_broadcast = getattr(backend.socket_manager, 'broadcast', None)
    backend.socket_manager.broadcast = mock_broadcast
    
    try:
        manager = StateManager(game_id="test", room_id="test_room")
        
        # Create snapshot
        await manager.create_snapshot(
            phase="TURN",
            phase_data={"current_player": "player1"},
            players={"player1": {"score": 0}},
            round_number=1,
            turn_number=1,
            reason="Test broadcast"
        )
        
        # Verify broadcast was called
        assert len(broadcast_calls) == 1
        call = broadcast_calls[0]
        
        assert call["room_id"] == "test_room"
        assert call["event"] == "phase_change"
        assert "version" in call["data"]
        assert "checksum" in call["data"]
        assert call["data"]["version"] == 1
        
    finally:
        # Restore original broadcast
        if original_broadcast:
            backend.socket_manager.broadcast = original_broadcast
    
    return True


@test("Version Mismatch Detection")
async def test_version_mismatch():
    """Test detection of client version mismatches"""
    from backend.engine.state import StateManager
    
    manager = StateManager(game_id="test", room_id="test")
    
    # Create a snapshot
    await manager.create_snapshot(
        phase="TURN",
        phase_data={},
        players={},
        round_number=1,
        turn_number=1,
        reason="Test"
    )
    
    # Test version validation
    assert manager.validate_client_version(1) == True   # Current version
    assert manager.validate_client_version(0) == False  # Old version
    assert manager.validate_client_version(2) == False  # Future version
    
    return True


@test("State Diff Retrieval")
async def test_state_diff():
    """Test getting state differences for catch-up"""
    from backend.engine.state import StateManager
    
    manager = StateManager(game_id="test", room_id="test")
    
    # Create multiple snapshots
    for i in range(5):
        await manager.create_snapshot(
            phase=f"PHASE_{i}",
            phase_data={"index": i},
            players={},
            round_number=1,
            turn_number=i,
            reason=f"Change {i}"
        )
    
    # Get diffs from various versions
    diff_from_0 = manager.get_state_diff(0)
    assert len(diff_from_0) == 5  # All 5 snapshots
    
    diff_from_3 = manager.get_state_diff(3)
    assert len(diff_from_3) == 2  # Versions 4 and 5
    
    diff_from_5 = manager.get_state_diff(5)
    assert len(diff_from_5) == 0  # No new versions
    
    return True


@test("Enterprise Architecture Integration")
async def test_enterprise_integration():
    """Test integration with existing enterprise architecture"""
    from backend.migration.phase1.state_manager_hook import StateManagerHook, setup_state_manager_integration
    from backend.engine.state import StateManager
    
    # Create a mock state machine
    class MockStateMachine:
        def __init__(self):
            self.room_id = "test_room"
            self.game = type('obj', (object,), {
                'players': [],
                'round_number': 1,
                'turn_number': 0
            })
            self.current_state = None
            
        async def transition_to(self, new_phase):
            return True
    
    # Create a mock game state
    class MockGameState:
        def __init__(self):
            self.phase_name = type('obj', (object,), {'value': 'TURN'})
            self.phase_data = {"test": "data"}
            self._auto_broadcast_phase_change_called = False
            
        async def _auto_broadcast_phase_change(self, reason: str):
            self._auto_broadcast_phase_change_called = True
    
    # Test setup
    state_machine = MockStateMachine()
    game_state = MockGameState()
    state_machine.current_state = game_state
    
    # Set up integration
    state_manager = setup_state_manager_integration(state_machine, "test_room")
    
    # Verify state manager was created
    assert state_manager is not None
    assert hasattr(state_machine, '_state_manager')
    
    return True


async def run_all_tests():
    """Run all validation tests"""
    print("🚀 Phase 1 Migration Validation Tests")
    print("=" * 50)
    
    # Run all test functions
    for name, obj in globals().items():
        if name.startswith('test_') and callable(obj):
            await obj()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary:")
    print(f"  ✅ Passed: {test_results['passed']}")
    print(f"  ❌ Failed: {test_results['failed']}")
    print(f"  📝 Total: {test_results['passed'] + test_results['failed']}")
    
    # Save results
    with open('validation_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    if test_results['failed'] == 0:
        print("\n🎉 All tests passed! Migration successful!")
        return True
    else:
        print("\n❌ Some tests failed. Please investigate before proceeding.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)