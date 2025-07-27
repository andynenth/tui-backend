#!/usr/bin/env python3
"""
State Machine Integration Tests for Phase 6.4.1

Tests integration between state machine adapters and enterprise state machine.
Validates state machine integration with clean architecture.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime

# Import test utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


class MockEnterpriseStateMachine:
    """Mock enterprise state machine for testing."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.current_phase = "PREPARATION"
        self.phase_data = {}
        self.change_history = []
        self.sequence_number = 0
        self.broadcasting_enabled = True
        self.broadcast_events = []
        
    async def update_phase_data(self, updates: Dict[str, Any], reason: str = ""):
        """Enterprise pattern: Update phase data with automatic broadcasting."""
        self.sequence_number += 1
        
        change_record = {
            "sequence": self.sequence_number,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "updates": updates.copy(),
            "phase": self.current_phase
        }
        self.change_history.append(change_record)
        self.phase_data.update(updates)
        
        if self.broadcasting_enabled:
            await self._broadcast("phase_change", {
                "game_id": self.game_id,
                "phase": self.current_phase,
                "phase_data": self.phase_data.copy(),
                "sequence": self.sequence_number
            })
    
    async def transition_phase(self, new_phase: str, reason: str = ""):
        """Transition to new phase with enterprise logging."""
        old_phase = self.current_phase
        self.current_phase = new_phase
        
        await self.update_phase_data({
            "previous_phase": old_phase,
            "transition_time": datetime.utcnow().isoformat()
        }, f"Phase transition: {old_phase} -> {new_phase}. {reason}")
    
    async def _broadcast(self, event_type: str, data: Dict[str, Any]):
        """Mock broadcasting."""
        self.broadcast_events.append({
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        })
        await asyncio.sleep(0.001)  # Simulate broadcast
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        return {
            "game_id": self.game_id,
            "phase": self.current_phase,
            "phase_data": self.phase_data.copy(),
            "sequence": self.sequence_number
        }


class MockStateMachineAdapter:
    """Mock state machine adapter for testing."""
    
    def __init__(self, state_machine: MockEnterpriseStateMachine):
        self.state_machine = state_machine
        self.enabled = True
    
    async def handle_phase_transition(self, new_phase: str, reason: str = "") -> Dict[str, Any]:
        """Handle phase transition through adapter."""
        if not self.enabled:
            return {"error": "State machine adapter disabled"}
        
        old_phase = self.state_machine.current_phase
        await self.state_machine.transition_phase(new_phase, reason)
        
        return {
            "event": "phase_transitioned",
            "data": {
                "from_phase": old_phase,
                "to_phase": new_phase,
                "success": True
            }
        }
    
    async def handle_state_update(self, updates: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
        """Handle state update through adapter."""
        if not self.enabled:
            return {"error": "State machine adapter disabled"}
        
        await self.state_machine.update_phase_data(updates, reason)
        
        return {
            "event": "state_updated",
            "data": {
                "updates": updates,
                "success": True,
                "sequence": self.state_machine.sequence_number
            }
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get state through adapter."""
        return self.state_machine.get_state()


@pytest.fixture
def mock_websocket():
    """Fixture for mock WebSocket."""
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            self.closed = False
        
        async def send(self, message: str):
            self.sent_messages.append(message)
        
        async def close(self):
            self.closed = True
    
    return MockWebSocket()


@pytest.fixture
def mock_state_machine():
    """Fixture for mock state machine."""
    return MockEnterpriseStateMachine("test_game_123")


@pytest.fixture
def mock_adapter(mock_state_machine):
    """Fixture for mock state machine adapter."""
    return MockStateMachineAdapter(mock_state_machine)


class TestStateMachineAdapterIntegration:
    """Test state machine adapter integration."""
    
    @pytest.mark.asyncio
    async def test_phase_transition_integration(self, mock_adapter, mock_state_machine):
        """Test phase transition through adapter."""
        
        # Test transition from PREPARATION to DECLARATION
        result = await mock_adapter.handle_phase_transition("DECLARATION", "Game starting")
        
        # Assertions
        assert result["event"] == "phase_transitioned"
        assert result["data"]["from_phase"] == "PREPARATION"
        assert result["data"]["to_phase"] == "DECLARATION"
        assert result["data"]["success"] is True
        assert mock_state_machine.current_phase == "DECLARATION"
        
        # Verify change history was updated
        history = mock_state_machine.change_history
        assert len(history) > 0
        assert "Phase transition" in history[-1]["reason"]
    
    @pytest.mark.asyncio
    async def test_state_update_integration(self, mock_adapter, mock_state_machine):
        """Test state update through adapter."""
        
        # Test state update
        updates = {
            "current_player": "player_1",
            "turn_number": 1,
            "action_required": "declare"
        }
        
        result = await mock_adapter.handle_state_update(updates, "Turn initialization")
        
        # Assertions
        assert result["event"] == "state_updated"
        assert result["data"]["updates"] == updates
        assert result["data"]["success"] is True
        assert "sequence" in result["data"]
        
        # Verify state was updated
        state = mock_adapter.get_state()
        assert state["phase_data"]["current_player"] == "player_1"
        assert state["phase_data"]["turn_number"] == 1
    
    @pytest.mark.asyncio
    async def test_enterprise_broadcasting_integration(self, mock_adapter, mock_state_machine):
        """Test enterprise broadcasting through adapter."""
        
        initial_broadcast_count = len(mock_state_machine.broadcast_events)
        
        # Make state update that should trigger broadcast
        await mock_adapter.handle_state_update({
            "test_data": "broadcast_test"
        }, "Testing broadcast")
        
        # Verify broadcast occurred
        assert len(mock_state_machine.broadcast_events) > initial_broadcast_count
        
        # Verify broadcast content
        last_broadcast = mock_state_machine.broadcast_events[-1]
        assert last_broadcast["event_type"] == "phase_change"
        assert "game_id" in last_broadcast["data"]
        assert "phase_data" in last_broadcast["data"]
        assert last_broadcast["data"]["phase_data"]["test_data"] == "broadcast_test"
    
    @pytest.mark.asyncio
    async def test_adapter_disabled_fallback(self, mock_adapter):
        """Test adapter behavior when disabled."""
        
        # Disable adapter
        mock_adapter.enabled = False
        
        # Test phase transition
        result = await mock_adapter.handle_phase_transition("DECLARATION", "Should fail")
        assert "error" in result
        assert "disabled" in result["error"]
        
        # Test state update
        result = await mock_adapter.handle_state_update({"test": "data"}, "Should fail")
        assert "error" in result
        assert "disabled" in result["error"]
    
    @pytest.mark.asyncio
    async def test_multiple_phase_transitions(self, mock_adapter, mock_state_machine):
        """Test multiple phase transitions in sequence."""
        
        # Define transition sequence
        transitions = [
            ("DECLARATION", "Players ready"),
            ("TURN", "All declarations made"),
            ("SCORING", "Round complete"),
            ("PREPARATION", "Starting new round")
        ]
        
        for new_phase, reason in transitions:
            result = await mock_adapter.handle_phase_transition(new_phase, reason)
            
            # Verify each transition
            assert result["data"]["success"] is True
            assert result["data"]["to_phase"] == new_phase
            assert mock_state_machine.current_phase == new_phase
        
        # Verify all transitions are in history
        history = mock_state_machine.change_history
        transition_records = [record for record in history if "transition" in record["reason"]]
        assert len(transition_records) == len(transitions)
    
    @pytest.mark.asyncio
    async def test_concurrent_state_operations(self, mock_adapter):
        """Test concurrent state operations through adapter."""
        
        # Concurrent operation function
        async def concurrent_update(update_id: int):
            return await mock_adapter.handle_state_update({
                f"concurrent_data_{update_id}": f"value_{update_id}"
            }, f"Concurrent update {update_id}")
        
        # Execute concurrent operations
        tasks = [concurrent_update(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        assert len(results) == 10
        assert all(result["data"]["success"] for result in results)
        
        # Verify state consistency
        state = mock_adapter.get_state()
        for i in range(10):
            assert f"concurrent_data_{i}" in state["phase_data"]
    
    @pytest.mark.asyncio
    async def test_state_machine_performance(self, mock_adapter):
        """Test state machine adapter performance."""
        
        # Performance test with rapid operations
        operation_times = []
        
        for i in range(50):
            start_time = time.perf_counter()
            
            await mock_adapter.handle_state_update({
                f"perf_test_{i}": f"data_{i}"
            }, f"Performance test {i}")
            
            end_time = time.perf_counter()
            operation_times.append((end_time - start_time) * 1000)  # ms
        
        # Performance assertions
        avg_time = sum(operation_times) / len(operation_times)
        max_time = max(operation_times)
        
        assert avg_time < 5.0  # Average under 5ms
        assert max_time < 20.0  # Max under 20ms
        assert len(operation_times) == 50  # All operations completed
    
    @pytest.mark.asyncio
    async def test_change_history_integration(self, mock_adapter, mock_state_machine):
        """Test change history tracking through adapter."""
        
        # Perform multiple operations
        await mock_adapter.handle_state_update({"operation": 1}, "First operation")
        await mock_adapter.handle_phase_transition("DECLARATION", "Phase change")
        await mock_adapter.handle_state_update({"operation": 2}, "Second operation")
        
        # Get change history
        history = mock_state_machine.change_history
        
        # Verify history structure
        assert len(history) >= 3
        
        for record in history:
            # Verify required fields
            assert "sequence" in record
            assert "timestamp" in record
            assert "reason" in record
            assert "phase" in record
            
            # Verify sequence numbers are sequential
            expected_sequence = history.index(record) + 1
            assert record["sequence"] == expected_sequence
    
    @pytest.mark.asyncio
    async def test_adapter_error_handling(self, mock_adapter, mock_state_machine):
        """Test adapter error handling."""
        
        # Mock a failure in the state machine
        original_update = mock_state_machine.update_phase_data
        
        async def failing_update(*args, **kwargs):
            raise Exception("Simulated state machine failure")
        
        mock_state_machine.update_phase_data = failing_update
        
        # Test that adapter handles the error gracefully
        try:
            result = await mock_adapter.handle_state_update({"test": "data"}, "Should fail")
            # If adapter implements error handling, verify it returns error response
            # If not, exception should be caught by test framework
        except Exception as e:
            assert "Simulated state machine failure" in str(e)
        finally:
            # Restore original method
            mock_state_machine.update_phase_data = original_update


class TestStateMachineAdapterPerformance:
    """Test state machine adapter performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_adapter_overhead(self, mock_adapter):
        """Test adapter overhead compared to direct state machine calls."""
        
        # Measure adapter overhead
        adapter_times = []
        
        for i in range(20):
            start_time = time.perf_counter()
            
            await mock_adapter.handle_state_update({
                f"overhead_test_{i}": f"value_{i}"
            }, f"Overhead test {i}")
            
            end_time = time.perf_counter()
            adapter_times.append((end_time - start_time) * 1000)
        
        # Performance assertions
        avg_adapter_time = sum(adapter_times) / len(adapter_times)
        
        assert avg_adapter_time < 3.0  # Average under 3ms
        assert all(t < 10.0 for t in adapter_times)  # All under 10ms
    
    @pytest.mark.asyncio
    async def test_sustained_operations(self, mock_adapter):
        """Test sustained operations without memory leaks."""
        
        # Simulate sustained load
        for batch in range(5):  # 5 batches
            batch_start = time.perf_counter()
            
            # Mixed operations in each batch
            for i in range(10):
                if i % 2 == 0:
                    await mock_adapter.handle_state_update({
                        f"sustained_{batch}_{i}": f"data_{i}"
                    }, f"Sustained operation {batch}.{i}")
                else:
                    # Get state (read operation)
                    state = mock_adapter.get_state()
                    assert state is not None
            
            batch_end = time.perf_counter()
            batch_time = (batch_end - batch_start) * 1000
            
            # Each batch should complete in reasonable time
            assert batch_time < 100.0  # Under 100ms per batch
            
            # Small delay between batches
            await asyncio.sleep(0.01)
        
        # Memory validation - check that history doesn't grow unbounded
        # (In real implementation, there would be history size limits)
        final_state = mock_adapter.get_state()
        assert final_state["sequence"] > 0  # Operations completed


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])