# Example Contract Tests for Critical WebSocket Messages
"""
Example tests demonstrating how to use the contract testing framework
to ensure backend compatibility during refactoring.
"""

import pytest
import asyncio
from typing import Dict, Any, Optional

from tests.contracts.websocket_contracts import (
    CREATE_ROOM_CONTRACT,
    JOIN_ROOM_CONTRACT,
    DECLARE_CONTRACT,
    PLAY_CONTRACT,
    get_contract
)
from tests.contracts.golden_master import (
    GoldenMasterCapture,
    GoldenMasterComparator,
    GoldenMasterRecord
)
from tests.contracts.parallel_runner import (
    ParallelContractRunner,
    TestSuite
)


class TestWebSocketContracts:
    """Contract tests for WebSocket message compatibility"""
    
    @pytest.fixture
    def golden_master_capture(self):
        """Golden master capture tool"""
        return GoldenMasterCapture()
    
    @pytest.fixture
    def comparator(self):
        """Behavior comparator"""
        return GoldenMasterComparator(
            ignore_fields=["timestamp", "server_time", "room_id"]
        )
    
    @pytest.fixture
    def parallel_runner(self, current_handler, new_handler, comparator):
        """Parallel test runner"""
        return ParallelContractRunner(
            current_system_handler=current_handler,
            new_system_handler=new_handler,  # None if not refactored yet
            comparator=comparator
        )
    
    @pytest.mark.asyncio
    async def test_create_room_contract(self, parallel_runner):
        """Test create_room message maintains exact behavior"""
        # Test cases for create_room
        test_cases = [
            # Valid room creation
            (
                CREATE_ROOM_CONTRACT,
                {
                    "action": "create_room",
                    "data": {
                        "player_name": "Alice"
                    }
                },
                None  # No initial room state
            ),
            # Room creation with long name
            (
                CREATE_ROOM_CONTRACT,
                {
                    "action": "create_room",
                    "data": {
                        "player_name": "VeryLongPlayerName123"
                    }
                },
                None
            ),
            # Room creation with special characters
            (
                CREATE_ROOM_CONTRACT,
                {
                    "action": "create_room",
                    "data": {
                        "player_name": "Player One"
                    }
                },
                None
            ),
        ]
        
        # Run tests
        suite = await parallel_runner.run_contract_suite(test_cases)
        
        # Generate report
        report = parallel_runner.generate_compatibility_report(suite)
        print(report)
        
        # Assert all tests passed
        assert suite.success_rate == 100.0, f"Contract tests failed: {suite.get_summary()}"
    
    @pytest.mark.asyncio
    async def test_join_room_contract(self, parallel_runner):
        """Test join_room message maintains exact behavior"""
        # Initial room state with one player
        room_state = {
            "room_id": "ABC123",
            "players": [
                {"name": "Alice", "slot": 0, "is_host": True}
            ],
            "started": False
        }
        
        test_cases = [
            # Valid join
            (
                JOIN_ROOM_CONTRACT,
                {
                    "action": "join_room",
                    "data": {
                        "room_id": "ABC123",
                        "player_name": "Bob"
                    }
                },
                room_state
            ),
            # Join full room (should fail)
            (
                JOIN_ROOM_CONTRACT,
                {
                    "action": "join_room",
                    "data": {
                        "room_id": "FULL01",
                        "player_name": "Charlie"
                    }
                },
                {
                    "room_id": "FULL01",
                    "players": [
                        {"name": "P1", "slot": 0},
                        {"name": "P2", "slot": 1},
                        {"name": "P3", "slot": 2},
                        {"name": "P4", "slot": 3}
                    ],
                    "started": False
                }
            ),
        ]
        
        suite = await parallel_runner.run_contract_suite(test_cases)
        assert suite.success_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_game_action_contracts(self, parallel_runner):
        """Test game action messages maintain exact behavior"""
        # Game state during declaration phase
        declaration_state = {
            "room_id": "GAME01",
            "phase": "DECLARATION",
            "players": [
                {"name": "Alice", "declared": False},
                {"name": "Bob", "declared": False},
                {"name": "Charlie", "declared": False},
                {"name": "David", "declared": False}
            ]
        }
        
        # Game state during turn phase
        turn_state = {
            "room_id": "GAME01",
            "phase": "TURN",
            "current_player": "Alice",
            "required_piece_count": 3,
            "players": [
                {"name": "Alice", "hand": ["R10", "R9", "R8", "B7", "B6"]},
                {"name": "Bob", "hand": ["G10", "G9", "G8", "G7", "G6"]}
            ]
        }
        
        test_cases = [
            # Valid declaration
            (
                DECLARE_CONTRACT,
                {
                    "action": "declare",
                    "data": {
                        "player_name": "Alice",
                        "value": 3
                    }
                },
                declaration_state
            ),
            # Valid play
            (
                PLAY_CONTRACT,
                {
                    "action": "play",
                    "data": {
                        "player_name": "Alice",
                        "indices": [0, 1, 2]  # R10, R9, R8
                    }
                },
                turn_state
            ),
            # Invalid play - wrong piece count
            (
                PLAY_CONTRACT,
                {
                    "action": "play",
                    "data": {
                        "player_name": "Alice",
                        "indices": [0, 1]  # Only 2 pieces
                    }
                },
                turn_state
            ),
        ]
        
        suite = await parallel_runner.run_contract_suite(test_cases)
        
        # Check specific test results
        for result in suite.results:
            if "wrong piece count" in result.test_name:
                # This should fail with specific error
                assert not result.success
                assert result.current_behavior.response["event"] == "play_rejected"
            else:
                # Other tests should pass
                assert result.success, f"Test {result.test_name} failed"
    
    @pytest.mark.asyncio
    async def test_capture_golden_masters(self, golden_master_capture, current_handler):
        """Capture golden masters from current system"""
        # Test messages to capture
        test_messages = [
            {
                "action": "create_room",
                "data": {"player_name": "Alice"}
            },
            {
                "action": "ping",
                "data": {"timestamp": 1234567890}
            },
            {
                "action": "declare",
                "data": {"player_name": "Bob", "value": 2}
            }
        ]
        
        # Capture behavior for each message
        for message in test_messages:
            record = await golden_master_capture.capture_message_behavior(
                current_handler,
                message
            )
            
            # Save golden master
            filepath = golden_master_capture.save_golden_master(record)
            print(f"Saved golden master: {filepath}")
            
            # Verify we can load it back
            loaded = golden_master_capture.load_golden_master(
                record.message_name,
                record.test_id
            )
            assert loaded is not None
            assert loaded.input_message == message
    
    @pytest.mark.asyncio
    async def test_timing_comparison(self, parallel_runner):
        """Test that refactored system maintains performance"""
        test_cases = [
            (
                get_contract("ping"),
                {
                    "action": "ping",
                    "data": {"timestamp": 1234567890}
                },
                None
            )
        ]
        
        # Run multiple iterations to get average timing
        iterations = 10
        results = []
        
        for _ in range(iterations):
            suite = await parallel_runner.run_contract_suite(test_cases)
            results.append(suite.results[0])
        
        # Analyze timing
        if results[0].new_behavior:  # Only if new system exists
            avg_current_time = sum(r.current_behavior.timing["duration_ms"] for r in results) / iterations
            avg_new_time = sum(r.new_behavior.timing["duration_ms"] for r in results) / iterations
            
            # New system should not be significantly slower (max 20% overhead)
            performance_ratio = avg_new_time / avg_current_time
            assert performance_ratio < 1.2, f"New system is {performance_ratio:.2f}x slower"
            
            print(f"Performance comparison:")
            print(f"  Current system: {avg_current_time:.2f}ms average")
            print(f"  New system: {avg_new_time:.2f}ms average")
            print(f"  Ratio: {performance_ratio:.2f}x")


# Mock handlers for testing (replace with actual handlers)
async def mock_current_handler(websocket, message, room_state, broadcast):
    """Mock current system handler"""
    action = message.get("action")
    
    if action == "create_room":
        # Simulate current behavior
        await websocket.send_json({
            "event": "room_created",
            "data": {
                "room_id": "ABC123",
                "host_name": message["data"]["player_name"],
                "success": True
            }
        })
        await broadcast("lobby", "room_list_update", {
            "rooms": [],
            "timestamp": 1234567890.123,
            "reason": "new_room_created"
        })
    
    elif action == "ping":
        await websocket.send_json({
            "event": "pong",
            "data": {
                "timestamp": message["data"].get("timestamp"),
                "server_time": 1234567890.123
            }
        })
    
    # Add more action handlers as needed


async def mock_new_handler(websocket, message, room_state, broadcast):
    """Mock new system handler (refactored)"""
    # This would be your refactored handler
    # For now, just mirror current behavior
    return await mock_current_handler(websocket, message, room_state, broadcast)


# Fixtures for pytest
@pytest.fixture
def current_handler():
    return mock_current_handler


@pytest.fixture
def new_handler():
    # Return None if new system not ready yet
    # return None
    return mock_new_handler  # When refactored system is ready