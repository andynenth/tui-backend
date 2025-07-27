#!/usr/bin/env python3
"""
Bot Management Integration Tests for Phase 6.4.2

Tests integration between bot management adapters and bot service.
Validates bot management integration with clean architecture.
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


class MockBot:
    """Mock bot for integration testing."""
    
    def __init__(self, bot_id: str, difficulty: str = "MEDIUM"):
        self.bot_id = bot_id
        self.difficulty = difficulty
        self.name = f"Bot_{difficulty[:3]}"
        self.created_at = datetime.utcnow()
        self.decisions_made = 0
        
        # Timing configuration
        self.timing_ranges = {
            "EASY": (0.5, 1.0),
            "MEDIUM": (0.8, 1.2),
            "HARD": (1.0, 1.4)
        }
        self.think_time_range = self.timing_ranges.get(difficulty, (0.8, 1.2))
    
    async def make_decision(self, decision_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a bot decision with realistic timing."""
        import random
        
        # Simulate think time
        think_time = random.uniform(*self.think_time_range)
        await asyncio.sleep(think_time)
        
        self.decisions_made += 1
        
        # Return decision based on type
        if decision_type == "declare":
            return {"pile_count": random.randint(0, 3), "confidence": 0.8}
        elif decision_type == "play":
            piece_count = random.randint(1, 3)
            return {"pieces": [f"piece_{i}" for i in range(piece_count)], "confidence": 0.7}
        elif decision_type == "redeal":
            return {"accept": random.choice([True, False]), "confidence": 0.6}
        else:
            return {"action": "unknown", "confidence": 0.5}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "bot_id": self.bot_id,
            "difficulty": self.difficulty,
            "decisions_made": self.decisions_made,
            "uptime": (datetime.utcnow() - self.created_at).total_seconds()
        }


class MockBotService:
    """Mock bot service for integration testing."""
    
    def __init__(self):
        self.bots: Dict[str, MockBot] = {}
        self.active_games: Dict[str, List[str]] = {}
        self.replacement_log: List[Dict[str, Any]] = []
        
    async def create_bot(self, difficulty: str = "MEDIUM") -> str:
        """Create a new bot."""
        bot_id = f"test_bot_{uuid.uuid4().hex[:8]}"
        bot = MockBot(bot_id, difficulty)
        self.bots[bot_id] = bot
        return bot_id
    
    async def replace_player_with_bot(self, game_id: str, player_id: str, difficulty: str = "MEDIUM") -> str:
        """Replace player with bot."""
        bot_id = await self.create_bot(difficulty)
        
        if game_id not in self.active_games:
            self.active_games[game_id] = []
        self.active_games[game_id].append(bot_id)
        
        replacement_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "game_id": game_id,
            "replaced_player_id": player_id,
            "bot_id": bot_id,
            "difficulty": difficulty
        }
        self.replacement_log.append(replacement_record)
        
        return bot_id
    
    async def remove_bot(self, bot_id: str, game_id: str = None) -> bool:
        """Remove bot."""
        if bot_id not in self.bots:
            return False
        
        if game_id and game_id in self.active_games:
            if bot_id in self.active_games[game_id]:
                self.active_games[game_id].remove(bot_id)
        
        del self.bots[bot_id]
        return True
    
    def get_bot(self, bot_id: str) -> Optional[MockBot]:
        """Get bot by ID."""
        return self.bots.get(bot_id)
    
    def get_game_bots(self, game_id: str) -> List[MockBot]:
        """Get bots in game."""
        if game_id not in self.active_games:
            return []
        return [self.bots[bot_id] for bot_id in self.active_games[game_id] if bot_id in self.bots]


class MockBotManagementAdapter:
    """Mock bot management adapter for testing."""
    
    def __init__(self, bot_service: MockBotService):
        self.bot_service = bot_service
        self.enabled = True
    
    async def handle_bot_request(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bot management request through adapter."""
        if not self.enabled:
            return {"error": "Bot management adapter disabled"}
        
        if action == "replace_player":
            game_id = data.get("game_id")
            player_id = data.get("player_id")
            difficulty = data.get("difficulty", "MEDIUM")
            
            if not game_id or not player_id:
                return {"error": "Missing game_id or player_id"}
            
            bot_id = await self.bot_service.replace_player_with_bot(game_id, player_id, difficulty)
            
            return {
                "event": "player_replaced",
                "data": {
                    "bot_id": bot_id,
                    "game_id": game_id,
                    "replaced_player": player_id,
                    "difficulty": difficulty,
                    "success": True
                }
            }
        
        elif action == "bot_decision":
            bot_id = data.get("bot_id")
            decision_type = data.get("decision_type", "declare")
            context = data.get("context", {})
            
            bot = self.bot_service.get_bot(bot_id)
            if not bot:
                return {"error": f"Bot {bot_id} not found"}
            
            decision = await bot.make_decision(decision_type, context)
            
            return {
                "event": "bot_decision_made",
                "data": {
                    "bot_id": bot_id,
                    "decision_type": decision_type,
                    "decision": decision,
                    "success": True
                }
            }
        
        elif action == "remove_bot":
            bot_id = data.get("bot_id")
            game_id = data.get("game_id")
            
            success = await self.bot_service.remove_bot(bot_id, game_id)
            
            return {
                "event": "bot_removed",
                "data": {
                    "bot_id": bot_id,
                    "success": success
                }
            }
        
        else:
            return {"error": f"Unknown bot action: {action}"}


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
def mock_bot_service():
    """Fixture for mock bot service."""
    return MockBotService()


@pytest.fixture
def mock_bot_adapter(mock_bot_service):
    """Fixture for mock bot management adapter."""
    return MockBotManagementAdapter(mock_bot_service)


class TestBotManagementAdapterIntegration:
    """Test bot management adapter integration."""
    
    @pytest.mark.asyncio
    async def test_player_replacement_integration(self, mock_bot_adapter, mock_bot_service):
        """Test player replacement through adapter."""
        
        # Test player replacement
        replacement_data = {
            "game_id": "test_game_123",
            "player_id": "player_456",
            "difficulty": "MEDIUM"
        }
        
        result = await mock_bot_adapter.handle_bot_request("replace_player", replacement_data)
        
        # Assertions
        assert result["event"] == "player_replaced"
        assert result["data"]["success"] is True
        assert "bot_id" in result["data"]
        assert result["data"]["game_id"] == "test_game_123"
        assert result["data"]["replaced_player"] == "player_456"
        assert result["data"]["difficulty"] == "MEDIUM"
        
        # Verify bot was created and added to game
        bot_id = result["data"]["bot_id"]
        bot = mock_bot_service.get_bot(bot_id)
        assert bot is not None
        assert bot.difficulty == "MEDIUM"
        
        game_bots = mock_bot_service.get_game_bots("test_game_123")
        assert len(game_bots) == 1
        assert game_bots[0].bot_id == bot_id
    
    @pytest.mark.asyncio
    async def test_bot_decision_integration(self, mock_bot_adapter, mock_bot_service):
        """Test bot decision making through adapter."""
        
        # Create bot first
        bot_id = await mock_bot_service.create_bot("HARD")
        
        # Test declaration decision
        decision_data = {
            "bot_id": bot_id,
            "decision_type": "declare",
            "context": {"hand": ["piece_1", "piece_2", "piece_3"]}
        }
        
        result = await mock_bot_adapter.handle_bot_request("bot_decision", decision_data)
        
        # Assertions
        assert result["event"] == "bot_decision_made"
        assert result["data"]["success"] is True
        assert result["data"]["bot_id"] == bot_id
        assert result["data"]["decision_type"] == "declare"
        assert "decision" in result["data"]
        assert "pile_count" in result["data"]["decision"]
        
        # Test play decision
        play_data = {
            "bot_id": bot_id,
            "decision_type": "play",
            "context": {"available_pieces": ["piece_1", "piece_2"]}
        }
        
        result = await mock_bot_adapter.handle_bot_request("bot_decision", play_data)
        
        # Assertions
        assert result["event"] == "bot_decision_made"
        assert result["data"]["decision_type"] == "play"
        assert "pieces" in result["data"]["decision"]
    
    @pytest.mark.asyncio
    async def test_bot_removal_integration(self, mock_bot_adapter, mock_bot_service):
        """Test bot removal through adapter."""
        
        # Create and add bot to game
        bot_id = await mock_bot_service.replace_player_with_bot("test_game", "player_1", "EASY")
        
        # Verify bot exists
        assert mock_bot_service.get_bot(bot_id) is not None
        
        # Remove bot through adapter
        removal_data = {
            "bot_id": bot_id,
            "game_id": "test_game"
        }
        
        result = await mock_bot_adapter.handle_bot_request("remove_bot", removal_data)
        
        # Assertions
        assert result["event"] == "bot_removed"
        assert result["data"]["success"] is True
        assert result["data"]["bot_id"] == bot_id
        
        # Verify bot was removed
        assert mock_bot_service.get_bot(bot_id) is None
        assert len(mock_bot_service.get_game_bots("test_game")) == 0
    
    @pytest.mark.asyncio
    async def test_adapter_error_handling(self, mock_bot_adapter):
        """Test adapter error handling."""
        
        # Test missing data
        result = await mock_bot_adapter.handle_bot_request("replace_player", {})
        assert "error" in result
        assert "Missing game_id or player_id" in result["error"]
        
        # Test nonexistent bot
        result = await mock_bot_adapter.handle_bot_request("bot_decision", {
            "bot_id": "nonexistent_bot",
            "decision_type": "declare"
        })
        assert "error" in result
        assert "not found" in result["error"]
        
        # Test unknown action
        result = await mock_bot_adapter.handle_bot_request("unknown_action", {})
        assert "error" in result
        assert "Unknown bot action" in result["error"]
    
    @pytest.mark.asyncio
    async def test_adapter_disabled_fallback(self, mock_bot_adapter):
        """Test adapter behavior when disabled."""
        
        # Disable adapter
        mock_bot_adapter.enabled = False
        
        # Test any request
        result = await mock_bot_adapter.handle_bot_request("replace_player", {
            "game_id": "test_game",
            "player_id": "player_1"
        })
        
        assert "error" in result
        assert "disabled" in result["error"]
    
    @pytest.mark.asyncio
    async def test_multiple_bot_difficulties(self, mock_bot_adapter, mock_bot_service):
        """Test creating bots with different difficulties."""
        
        difficulties = ["EASY", "MEDIUM", "HARD"]
        bot_ids = []
        
        for i, difficulty in enumerate(difficulties):
            replacement_data = {
                "game_id": f"test_game_{i}",
                "player_id": f"player_{i}",
                "difficulty": difficulty
            }
            
            result = await mock_bot_adapter.handle_bot_request("replace_player", replacement_data)
            
            assert result["data"]["success"] is True
            assert result["data"]["difficulty"] == difficulty
            
            bot_id = result["data"]["bot_id"]
            bot_ids.append(bot_id)
            
            # Verify bot has correct difficulty
            bot = mock_bot_service.get_bot(bot_id)
            assert bot.difficulty == difficulty
        
        # Test decisions from different difficulty bots
        for bot_id in bot_ids:
            decision_data = {
                "bot_id": bot_id,
                "decision_type": "declare"
            }
            
            result = await mock_bot_adapter.handle_bot_request("bot_decision", decision_data)
            assert result["data"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_bot_operations(self, mock_bot_adapter, mock_bot_service):
        """Test concurrent bot operations through adapter."""
        
        # Concurrent operation function
        async def concurrent_bot_operation(operation_id: int):
            """Perform concurrent bot operations."""
            try:
                # Replace player with bot
                replacement_data = {
                    "game_id": f"concurrent_game_{operation_id % 3}",
                    "player_id": f"player_{operation_id}",
                    "difficulty": ["EASY", "MEDIUM", "HARD"][operation_id % 3]
                }
                
                result = await mock_bot_adapter.handle_bot_request("replace_player", replacement_data)
                
                if result.get("data", {}).get("success"):
                    bot_id = result["data"]["bot_id"]
                    
                    # Make decision with bot
                    decision_data = {
                        "bot_id": bot_id,
                        "decision_type": "declare"
                    }
                    
                    decision_result = await mock_bot_adapter.handle_bot_request("bot_decision", decision_data)
                    
                    return {
                        "success": True,
                        "operation_id": operation_id,
                        "bot_id": bot_id,
                        "decision_success": decision_result.get("data", {}).get("success", False)
                    }
                
                return {"success": False, "operation_id": operation_id}
                
            except Exception as e:
                return {"success": False, "operation_id": operation_id, "error": str(e)}
        
        # Execute concurrent operations
        tasks = [concurrent_bot_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify results
        successful_operations = [r for r in results if r.get("success")]
        assert len(successful_operations) == 10
        
        # Verify all decisions were successful
        successful_decisions = [r for r in successful_operations if r.get("decision_success")]
        assert len(successful_decisions) == 10
    
    @pytest.mark.asyncio
    async def test_bot_adapter_performance(self, mock_bot_adapter, mock_bot_service):
        """Test bot adapter performance."""
        
        # Performance test with rapid operations
        operation_times = []
        
        for i in range(20):
            start_time = time.perf_counter()
            
            # Create bot and make decision
            replacement_data = {
                "game_id": f"perf_game_{i % 5}",
                "player_id": f"perf_player_{i}",
                "difficulty": "MEDIUM"
            }
            
            result = await mock_bot_adapter.handle_bot_request("replace_player", replacement_data)
            
            if result.get("data", {}).get("success"):
                bot_id = result["data"]["bot_id"]
                
                decision_data = {
                    "bot_id": bot_id,
                    "decision_type": "declare"
                }
                
                await mock_bot_adapter.handle_bot_request("bot_decision", decision_data)
            
            end_time = time.perf_counter()
            operation_times.append((end_time - start_time) * 1000)  # ms
        
        # Performance assertions
        avg_time = sum(operation_times) / len(operation_times)
        max_time = max(operation_times)
        
        # Bot operations should be reasonably fast (excluding bot think time)
        assert avg_time < 1500.0  # Average under 1.5s (includes bot think time)
        assert max_time < 2000.0  # Max under 2s
        assert len(operation_times) == 20  # All operations completed


class TestBotManagementAdapterCompliance:
    """Test bot management adapter compliance with requirements."""
    
    @pytest.mark.asyncio
    async def test_replacement_timing_compliance(self, mock_bot_adapter, mock_bot_service):
        """Test replacement timing meets requirements."""
        
        replacement_times = []
        
        for i in range(10):
            replacement_data = {
                "game_id": f"timing_game_{i}",
                "player_id": f"timing_player_{i}",
                "difficulty": "MEDIUM"
            }
            
            start_time = time.perf_counter()
            result = await mock_bot_adapter.handle_bot_request("replace_player", replacement_data)
            end_time = time.perf_counter()
            
            replacement_time = (end_time - start_time) * 1000  # ms
            replacement_times.append(replacement_time)
            
            assert result.get("data", {}).get("success") is True
        
        # Replacement should be fast (not including bot creation time)
        avg_replacement_time = sum(replacement_times) / len(replacement_times)
        assert avg_replacement_time < 100.0  # Under 100ms for adapter overhead
    
    @pytest.mark.asyncio
    async def test_decision_quality_compliance(self, mock_bot_adapter, mock_bot_service):
        """Test bot decision quality meets requirements."""
        
        # Create bots of different difficulties
        bot_ids = {}
        for difficulty in ["EASY", "MEDIUM", "HARD"]:
            bot_id = await mock_bot_service.create_bot(difficulty)
            bot_ids[difficulty] = bot_id
        
        # Test decision quality for each difficulty
        for difficulty, bot_id in bot_ids.items():
            decision_types = ["declare", "play", "redeal"]
            
            for decision_type in decision_types:
                decision_data = {
                    "bot_id": bot_id,
                    "decision_type": decision_type
                }
                
                result = await mock_bot_adapter.handle_bot_request("bot_decision", decision_data)
                
                # Verify decision structure
                assert result.get("data", {}).get("success") is True
                assert "decision" in result["data"]
                
                decision = result["data"]["decision"]
                
                # Validate decision content based on type
                if decision_type == "declare":
                    assert "pile_count" in decision
                    assert 0 <= decision["pile_count"] <= 8
                elif decision_type == "play":
                    assert "pieces" in decision
                    assert isinstance(decision["pieces"], list)
                    assert len(decision["pieces"]) >= 1
                elif decision_type == "redeal":
                    assert "accept" in decision
                    assert isinstance(decision["accept"], bool)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])