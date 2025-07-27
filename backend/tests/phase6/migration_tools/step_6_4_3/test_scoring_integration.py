#!/usr/bin/env python3
"""
Scoring Integration Tests for Phase 6.4.3

Tests integration between scoring adapters and scoring engine.
Validates scoring integration with clean architecture.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime

# Import test utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))


class MockPlayer:
    """Mock player for scoring integration tests."""
    
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.score = 0
        self.round_scores = []
        self.declared_piles = 0
        self.actual_piles = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "score": self.score,
            "round_scores": self.round_scores.copy(),
            "declared_piles": self.declared_piles,
            "actual_piles": self.actual_piles
        }


class MockScoringEngine:
    """Mock scoring engine for integration testing."""
    
    def __init__(self):
        self.calculation_history = []
        
    def calculate_round_score(self, declared: int, actual: int, multiplier: int = 1) -> Dict[str, Any]:
        """Calculate round score."""
        # Simple scoring logic for testing
        if declared == actual:
            base_score = 10 + (5 if actual == 0 else 0)  # Bonus for zero piles
        else:
            difference = abs(declared - actual)
            base_score = -5 if difference < 3 else -10  # Penalty for mismatch
        
        final_score = base_score * multiplier
        
        result = {
            "declared": declared,
            "actual": actual,
            "multiplier": multiplier,
            "base_score": base_score,
            "final_score": final_score,
            "match": declared == actual,
            "calculation_time_ms": 0.01
        }
        
        self.calculation_history.append(result)
        return result
    
    def calculate_game_score(self, players: List[MockPlayer]) -> Dict[str, Any]:
        """Calculate total game scores."""
        results = {}
        for player in players:
            total_score = sum(player.round_scores)
            player.score = total_score
            
            results[player.player_id] = {
                "player_name": player.name,
                "total_score": total_score,
                "round_count": len(player.round_scores)
            }
        
        return {"players": results}
    
    def detect_win_condition(self, players: List[MockPlayer], round_number: int) -> Dict[str, Any]:
        """Detect win conditions."""
        scores = [(player.player_id, player.name, player.score) for player in players]
        scores.sort(key=lambda x: x[2], reverse=True)
        
        highest_score = scores[0][2] if scores else 0
        winner_id = scores[0][0] if scores else None
        winner_name = scores[0][1] if scores else None
        
        score_win = highest_score >= 50
        round_win = round_number >= 20
        win_detected = score_win or round_win
        
        return {
            "win_detected": win_detected,
            "win_type": "score_limit" if score_win else "round_limit" if round_win else None,
            "winner_id": winner_id if win_detected else None,
            "winner_name": winner_name if win_detected else None,
            "winning_score": highest_score if win_detected else None,
            "round_number": round_number
        }


class MockScoringAdapter:
    """Mock scoring adapter for testing."""
    
    def __init__(self, scoring_engine: MockScoringEngine):
        self.scoring_engine = scoring_engine
        self.enabled = True
    
    async def handle_scoring_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scoring request through adapter."""
        if not self.enabled:
            return {"error": "Scoring adapter disabled"}
        
        if action == "calculate_round_score":
            declared = data.get("declared")
            actual = data.get("actual")
            multiplier = data.get("multiplier", 1)
            
            if declared is None or actual is None:
                return {"error": "Missing declared or actual pile count"}
            
            result = self.scoring_engine.calculate_round_score(declared, actual, multiplier)
            
            return {
                "event": "round_score_calculated",
                "data": {
                    "scoring_result": result,
                    "success": True
                }
            }
        
        elif action == "calculate_game_scores":
            players_data = data.get("players", [])
            
            if not players_data:
                return {"error": "No players provided"}
            
            # Convert to MockPlayer objects
            players = []
            for player_data in players_data:
                player = MockPlayer(player_data["player_id"], player_data["name"])
                player.round_scores = player_data.get("round_scores", [])
                players.append(player)
            
            result = self.scoring_engine.calculate_game_score(players)
            
            return {
                "event": "game_scores_calculated",
                "data": {
                    "game_scores": result,
                    "success": True
                }
            }
        
        elif action == "check_win_condition":
            players_data = data.get("players", [])
            round_number = data.get("round_number", 1)
            
            if not players_data:
                return {"error": "No players provided"}
            
            # Convert to MockPlayer objects
            players = []
            for player_data in players_data:
                player = MockPlayer(player_data["player_id"], player_data["name"])
                player.score = player_data.get("score", 0)
                players.append(player)
            
            result = self.scoring_engine.detect_win_condition(players, round_number)
            
            return {
                "event": "win_condition_checked",
                "data": {
                    "win_result": result,
                    "success": True
                }
            }
        
        else:
            return {"error": f"Unknown scoring action: {action}"}


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
def mock_scoring_engine():
    """Fixture for mock scoring engine."""
    return MockScoringEngine()


@pytest.fixture
def mock_scoring_adapter(mock_scoring_engine):
    """Fixture for mock scoring adapter."""
    return MockScoringAdapter(mock_scoring_engine)


class TestScoringAdapterIntegration:
    """Test scoring adapter integration."""
    
    @pytest.mark.asyncio
    async def test_round_score_calculation_integration(self, mock_scoring_adapter, mock_scoring_engine):
        """Test round score calculation through adapter."""
        
        # Test perfect match
        scoring_data = {
            "declared": 2,
            "actual": 2,
            "multiplier": 1
        }
        
        result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", scoring_data)
        
        # Assertions
        assert result["event"] == "round_score_calculated"
        assert result["data"]["success"] is True
        assert "scoring_result" in result["data"]
        
        scoring_result = result["data"]["scoring_result"]
        assert scoring_result["declared"] == 2
        assert scoring_result["actual"] == 2
        assert scoring_result["match"] is True
        assert scoring_result["final_score"] > 0  # Should be positive for match
        
        # Test mismatch
        mismatch_data = {
            "declared": 2,
            "actual": 4,
            "multiplier": 1
        }
        
        result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", mismatch_data)
        
        scoring_result = result["data"]["scoring_result"]
        assert scoring_result["match"] is False
        assert scoring_result["final_score"] < 0  # Should be negative for mismatch
    
    @pytest.mark.asyncio
    async def test_game_score_calculation_integration(self, mock_scoring_adapter):
        """Test game score calculation through adapter."""
        
        # Test data with multiple players
        players_data = [
            {
                "player_id": "player_1",
                "name": "Alice",
                "round_scores": [10, 15, -5, 20]
            },
            {
                "player_id": "player_2", 
                "name": "Bob",
                "round_scores": [5, 10, 10, 15]
            }
        ]
        
        game_data = {"players": players_data}
        
        result = await mock_scoring_adapter.handle_scoring_request("calculate_game_scores", game_data)
        
        # Assertions
        assert result["event"] == "game_scores_calculated"
        assert result["data"]["success"] is True
        assert "game_scores" in result["data"]
        
        game_scores = result["data"]["game_scores"]["players"]
        
        # Check Alice's score
        assert "player_1" in game_scores
        alice_score = game_scores["player_1"]
        assert alice_score["player_name"] == "Alice"
        assert alice_score["total_score"] == 40  # 10+15-5+20
        assert alice_score["round_count"] == 4
        
        # Check Bob's score
        assert "player_2" in game_scores
        bob_score = game_scores["player_2"]
        assert bob_score["player_name"] == "Bob"
        assert bob_score["total_score"] == 40  # 5+10+10+15
    
    @pytest.mark.asyncio
    async def test_win_condition_integration(self, mock_scoring_adapter):
        """Test win condition detection through adapter."""
        
        # Test score-based win
        players_data = [
            {"player_id": "player_1", "name": "Alice", "score": 55},
            {"player_id": "player_2", "name": "Bob", "score": 40},
            {"player_id": "player_3", "name": "Charlie", "score": 35}
        ]
        
        win_data = {
            "players": players_data,
            "round_number": 10
        }
        
        result = await mock_scoring_adapter.handle_scoring_request("check_win_condition", win_data)
        
        # Assertions
        assert result["event"] == "win_condition_checked"
        assert result["data"]["success"] is True
        assert "win_result" in result["data"]
        
        win_result = result["data"]["win_result"]
        assert win_result["win_detected"] is True
        assert win_result["win_type"] == "score_limit"
        assert win_result["winner_id"] == "player_1"
        assert win_result["winner_name"] == "Alice"
        assert win_result["winning_score"] == 55
        
        # Test round-based win
        players_data_round_win = [
            {"player_id": "player_1", "name": "Alice", "score": 35},
            {"player_id": "player_2", "name": "Bob", "score": 40},
            {"player_id": "player_3", "name": "Charlie", "score": 30}
        ]
        
        win_data_round = {
            "players": players_data_round_win,
            "round_number": 20
        }
        
        result = await mock_scoring_adapter.handle_scoring_request("check_win_condition", win_data_round)
        
        win_result = result["data"]["win_result"]
        assert win_result["win_detected"] is True
        assert win_result["win_type"] == "round_limit"
        assert win_result["winner_name"] == "Bob"  # Highest score
    
    @pytest.mark.asyncio
    async def test_scoring_adapter_error_handling(self, mock_scoring_adapter):
        """Test scoring adapter error handling."""
        
        # Test missing data
        result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", {})
        assert "error" in result
        assert "Missing declared or actual" in result["error"]
        
        # Test empty players list
        result = await mock_scoring_adapter.handle_scoring_request("calculate_game_scores", {})
        assert "error" in result
        assert "No players provided" in result["error"]
        
        # Test unknown action
        result = await mock_scoring_adapter.handle_scoring_request("unknown_action", {})
        assert "error" in result
        assert "Unknown scoring action" in result["error"]
    
    @pytest.mark.asyncio
    async def test_adapter_disabled_fallback(self, mock_scoring_adapter):
        """Test adapter behavior when disabled."""
        
        # Disable adapter
        mock_scoring_adapter.enabled = False
        
        # Test any request
        result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", {
            "declared": 2,
            "actual": 2
        })
        
        assert "error" in result
        assert "disabled" in result["error"]
    
    @pytest.mark.asyncio
    async def test_multiplier_integration(self, mock_scoring_adapter):
        """Test multiplier application through adapter."""
        
        # Test with multiplier
        scoring_data = {
            "declared": 2,
            "actual": 2,
            "multiplier": 3
        }
        
        result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", scoring_data)
        
        scoring_result = result["data"]["scoring_result"]
        assert scoring_result["multiplier"] == 3
        
        # Calculate expected score (base score should be multiplied)
        base_score = scoring_result["base_score"]
        expected_final = base_score * 3
        assert scoring_result["final_score"] == expected_final
    
    @pytest.mark.asyncio
    async def test_concurrent_scoring_operations(self, mock_scoring_adapter):
        """Test concurrent scoring operations through adapter."""
        
        # Concurrent operation function
        async def concurrent_scoring_operation(operation_id: int):
            """Perform concurrent scoring operation."""
            try:
                scoring_data = {
                    "declared": operation_id % 4,
                    "actual": (operation_id + 1) % 4,
                    "multiplier": 1
                }
                
                result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", scoring_data)
                
                return {
                    "success": True,
                    "operation_id": operation_id,
                    "scoring_success": result.get("data", {}).get("success", False)
                }
                
            except Exception as e:
                return {"success": False, "operation_id": operation_id, "error": str(e)}
        
        # Execute concurrent operations
        tasks = [concurrent_scoring_operation(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Verify results
        successful_operations = [r for r in results if r.get("success")]
        assert len(successful_operations) == 20
        
        # Verify all scoring operations were successful
        successful_scoring = [r for r in successful_operations if r.get("scoring_success")]
        assert len(successful_scoring) == 20
    
    @pytest.mark.asyncio
    async def test_scoring_adapter_performance(self, mock_scoring_adapter):
        """Test scoring adapter performance."""
        
        # Performance test with rapid operations
        operation_times = []
        
        for i in range(50):
            start_time = time.perf_counter()
            
            scoring_data = {
                "declared": i % 5,
                "actual": (i + 1) % 5,
                "multiplier": 1
            }
            
            result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", scoring_data)
            
            end_time = time.perf_counter()
            operation_times.append((end_time - start_time) * 1000)  # ms
            
            # Verify operation succeeded
            assert result.get("data", {}).get("success") is True
        
        # Performance assertions
        avg_time = sum(operation_times) / len(operation_times)
        max_time = max(operation_times)
        
        assert avg_time < 5.0  # Average under 5ms
        assert max_time < 20.0  # Max under 20ms
        assert len(operation_times) == 50  # All operations completed
    
    @pytest.mark.asyncio
    async def test_edge_case_values_integration(self, mock_scoring_adapter):
        """Test edge case values through adapter."""
        
        # Test boundary values
        edge_cases = [
            (0, 0),   # Minimum values
            (8, 8),   # Maximum values
            (0, 8),   # Min to max
            (8, 0),   # Max to min
        ]
        
        for declared, actual in edge_cases:
            scoring_data = {
                "declared": declared,
                "actual": actual,
                "multiplier": 1
            }
            
            result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", scoring_data)
            
            # Should handle all edge cases successfully
            assert result.get("data", {}).get("success") is True
            
            scoring_result = result["data"]["scoring_result"]
            assert scoring_result["declared"] == declared
            assert scoring_result["actual"] == actual
            assert isinstance(scoring_result["final_score"], (int, float))


class TestScoringAdapterCompliance:
    """Test scoring adapter compliance with requirements."""
    
    @pytest.mark.asyncio
    async def test_mathematical_accuracy_compliance(self, mock_scoring_adapter):
        """Test mathematical accuracy through adapter."""
        
        # Test known calculation cases
        test_cases = [
            {"declared": 2, "actual": 2, "expected_positive": True},  # Match should be positive
            {"declared": 2, "actual": 4, "expected_positive": False}, # Mismatch should be negative
            {"declared": 0, "actual": 0, "expected_bonus": True},     # Zero match should have bonus
        ]
        
        for test_case in test_cases:
            scoring_data = {
                "declared": test_case["declared"],
                "actual": test_case["actual"],
                "multiplier": 1
            }
            
            result = await mock_scoring_adapter.handle_scoring_request("calculate_round_score", scoring_data)
            
            assert result.get("data", {}).get("success") is True
            
            scoring_result = result["data"]["scoring_result"]
            
            if test_case.get("expected_positive"):
                assert scoring_result["final_score"] > 0
            elif test_case.get("expected_positive") is False:
                assert scoring_result["final_score"] < 0
            
            if test_case.get("expected_bonus") and test_case["declared"] == 0:
                # Zero pile bonus should result in higher score than normal match
                assert scoring_result["final_score"] > 10  # Base match score
    
    @pytest.mark.asyncio
    async def test_win_condition_accuracy_compliance(self, mock_scoring_adapter):
        """Test win condition accuracy through adapter."""
        
        # Test various win scenarios
        win_scenarios = [
            {
                "players": [{"player_id": "p1", "name": "Player1", "score": 50}],
                "round_number": 5,
                "should_win": True,
                "win_type": "score_limit"
            },
            {
                "players": [{"player_id": "p1", "name": "Player1", "score": 30}],
                "round_number": 20,
                "should_win": True,
                "win_type": "round_limit"
            },
            {
                "players": [{"player_id": "p1", "name": "Player1", "score": 30}],
                "round_number": 15,
                "should_win": False,
                "win_type": None
            }
        ]
        
        for scenario in win_scenarios:
            win_data = {
                "players": scenario["players"],
                "round_number": scenario["round_number"]
            }
            
            result = await mock_scoring_adapter.handle_scoring_request("check_win_condition", win_data)
            
            assert result.get("data", {}).get("success") is True
            
            win_result = result["data"]["win_result"]
            
            if scenario["should_win"]:
                assert win_result["win_detected"] is True
                assert win_result["win_type"] == scenario["win_type"]
                assert win_result["winner_id"] is not None
            else:
                assert win_result["win_detected"] is False


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])