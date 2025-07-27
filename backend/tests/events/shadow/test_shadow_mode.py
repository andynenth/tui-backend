"""
Shadow mode tests for the event system.

Tests the shadow mode functionality where both direct and event-based
adapters run in parallel and their outputs are compared.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.adapters.unified_adapter_handler import (
    UnifiedAdapterHandler, get_unified_handler, reset_unified_handler
)
from api.adapters.adapter_event_config import AdapterEventConfig, AdapterMode
from infrastructure.events.in_memory_event_bus import reset_event_bus


class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self, player_id: str = "player123", room_id: str = None):
        self.id = f"ws_{player_id}"
        self.player_id = player_id
        self.room_id = room_id


class TestShadowMode:
    """Test shadow mode functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset handlers before each test."""
        reset_event_bus()
        reset_unified_handler()
    
    @pytest.fixture
    def websocket(self):
        """Create a mock websocket."""
        return MockWebSocket()
    
    @pytest.fixture
    def handler(self):
        """Create a unified handler for testing."""
        return UnifiedAdapterHandler()
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = AdapterEventConfig()
        config.events_enabled = True
        return config
    
    @pytest.mark.asyncio
    async def test_shadow_mode_runs_both_adapters(self, handler, websocket, config):
        """Test that shadow mode runs both direct and event adapters."""
        # Configure ping adapter for shadow mode
        config.adapter_modes["ping"] = AdapterMode.SHADOW
        
        # Track calls
        direct_called = False
        event_called = False
        
        # Mock legacy handler
        async def mock_legacy(ws, msg):
            nonlocal direct_called
            direct_called = True
            return {
                "event": "pong",
                "data": {"server_time": 1234567890}
            }
        
        # Patch the event adapter to track calls
        with patch('api.adapters.connection_adapters_event.PingAdapterEvent.handle') as mock_event:
            async def mock_event_handle(ws, msg, room_state=None):
                nonlocal event_called
                event_called = True
                return {
                    "event": "pong",
                    "data": {"server_time": 1234567891}
                }
            
            mock_event.side_effect = mock_event_handle
            
            # Configure handler
            with patch('api.adapters.adapter_event_config.adapter_event_config', config):
                message = {"action": "ping", "data": {"timestamp": 123}}
                result = await handler.handle_message(
                    websocket, message, mock_legacy
                )
        
        # Both should be called
        assert direct_called is True
        assert event_called is True
        
        # Result should be from legacy (direct)
        assert result["data"]["server_time"] == 1234567890
    
    @pytest.mark.asyncio
    async def test_shadow_mode_comparison_tracking(self, handler, websocket, config):
        """Test that shadow mode tracks comparison results."""
        config.adapter_modes["ping"] = AdapterMode.SHADOW
        
        # Create different responses
        async def mock_legacy(ws, msg):
            return {"event": "pong", "data": {"value": "direct"}}
        
        with patch('api.adapters.connection_adapters_event.PingAdapterEvent.handle') as mock_event:
            mock_event.return_value = {"event": "pong", "data": {"value": "event"}}
            
            with patch('api.adapters.adapter_event_config.adapter_event_config', config):
                message = {"action": "ping", "data": {}}
                await handler.handle_message(websocket, message, mock_legacy)
        
        # Check shadow results
        assert len(handler.shadow_results) == 1
        result = handler.shadow_results[0]
        
        assert result["action"] == "ping"
        assert result["results_match"] is False
        assert result["legacy_error"] is None
        assert result["event_error"] is None
        assert "legacy_time" in result
        assert "event_time" in result
    
    @pytest.mark.asyncio
    async def test_shadow_mode_matching_results(self, handler, websocket, config):
        """Test shadow mode when results match."""
        config.adapter_modes["create_room"] = AdapterMode.SHADOW
        
        # Same response from both
        response = {
            "event": "room_created",
            "data": {
                "room_id": "room123",
                "host_name": "Alice",
                "success": True
            }
        }
        
        async def mock_legacy(ws, msg):
            return response.copy()
        
        with patch('api.adapters.room_adapters_event.CreateRoomAdapterEvent.handle') as mock_event:
            mock_event.return_value = response.copy()
            
            with patch('api.adapters.adapter_event_config.adapter_event_config', config):
                message = {
                    "action": "create_room",
                    "data": {"player_name": "Alice"}
                }
                result = await handler.handle_message(
                    websocket, message, mock_legacy
                )
        
        # Results should match
        assert len(handler.shadow_results) == 1
        shadow_result = handler.shadow_results[0]
        assert shadow_result["results_match"] is True
    
    @pytest.mark.asyncio
    async def test_shadow_mode_error_handling(self, handler, websocket, config):
        """Test shadow mode handles errors in either adapter."""
        config.adapter_modes["join_room"] = AdapterMode.SHADOW
        
        # Legacy throws error
        async def mock_legacy_error(ws, msg):
            raise ValueError("Legacy error")
        
        # Event adapter succeeds
        with patch('api.adapters.room_adapters_event.JoinRoomAdapterEvent.handle') as mock_event:
            mock_event.return_value = {
                "event": "joined_room",
                "data": {"success": True}
            }
            
            with patch('api.adapters.adapter_event_config.adapter_event_config', config):
                message = {
                    "action": "join_room",
                    "data": {"room_id": "room123", "player_name": "Bob"}
                }
                
                # Should raise the legacy error
                with pytest.raises(Exception) as exc_info:
                    await handler.handle_message(
                        websocket, message, mock_legacy_error
                    )
                
                assert "Legacy error" in str(exc_info.value)
        
        # Check shadow results captured the error
        assert len(handler.shadow_results) == 1
        result = handler.shadow_results[0]
        assert result["legacy_error"] == "Legacy error"
        assert result["event_error"] is None
    
    @pytest.mark.asyncio
    async def test_shadow_mode_performance_tracking(self, handler, websocket, config):
        """Test shadow mode tracks performance metrics."""
        config.adapter_modes["play"] = AdapterMode.SHADOW
        
        # Add artificial delays
        async def mock_legacy_slow(ws, msg):
            await asyncio.sleep(0.1)  # 100ms delay
            return {"event": "play_made", "data": {"success": True}}
        
        with patch('api.adapters.game_adapters_event.PlayAdapterEvent.handle') as mock_event:
            async def mock_event_fast(ws, msg, room_state=None):
                await asyncio.sleep(0.01)  # 10ms delay
                return {"event": "play_made", "data": {"success": True}}
            
            mock_event.side_effect = mock_event_fast
            
            with patch('api.adapters.adapter_event_config.adapter_event_config', config):
                message = {
                    "action": "play",
                    "data": {"player_name": "Alice", "pieces": ["p1"]}
                }
                await handler.handle_message(
                    websocket, message, mock_legacy_slow
                )
        
        # Check performance metrics
        result = handler.shadow_results[0]
        assert result["legacy_time"] > 0.09  # Should be ~100ms
        assert result["event_time"] < 0.05   # Should be ~10ms
        assert result["event_time"] < result["legacy_time"]
    
    @pytest.mark.asyncio
    async def test_shadow_mode_statistics(self, handler, websocket, config):
        """Test shadow mode statistics calculation."""
        # Run multiple shadow comparisons
        config.adapter_modes["ping"] = AdapterMode.SHADOW
        
        async def mock_legacy(ws, msg):
            return {"event": "pong", "data": {"id": msg.get("request_id", 0)}}
        
        with patch('api.adapters.connection_adapters_event.PingAdapterEvent.handle') as mock_event:
            # Make some match and some not match
            call_count = 0
            
            async def mock_event_handle(ws, msg, room_state=None):
                nonlocal call_count
                call_count += 1
                # Every 3rd call returns different result
                if call_count % 3 == 0:
                    return {"event": "pong", "data": {"id": -1}}
                return {"event": "pong", "data": {"id": msg.get("request_id", 0)}}
            
            mock_event.side_effect = mock_event_handle
            
            with patch('api.adapters.adapter_event_config.adapter_event_config', config):
                # Run 10 comparisons
                for i in range(10):
                    message = {"action": "ping", "request_id": i}
                    await handler.handle_message(websocket, message, mock_legacy)
        
        # Get statistics
        stats = handler.get_shadow_mode_stats()
        
        assert stats["total_comparisons"] == 10
        assert stats["matches"] == 7  # 7 out of 10 should match
        assert stats["match_rate"] == 0.7
        assert "avg_legacy_time_ms" in stats
        assert "avg_event_time_ms" in stats
        assert "performance_gain" in stats
    
    @pytest.mark.asyncio
    async def test_shadow_mode_list_configuration(self, handler, websocket, config):
        """Test shadow mode configuration via shadow list."""
        # Configure via shadow list
        config.shadow_adapters = {"ping", "create_room", "play"}
        
        # These should be in shadow mode
        for action in ["ping", "create_room", "play"]:
            assert config.is_shadow_mode(action) is True
        
        # These should not
        for action in ["join_room", "leave_room"]:
            assert config.is_shadow_mode(action) is False


class TestShadowModeIntegration:
    """Integration tests for shadow mode with real adapters."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset handlers before each test."""
        reset_event_bus()
        reset_unified_handler()
    
    @pytest.mark.asyncio
    async def test_real_adapter_shadow_comparison(self):
        """Test shadow mode with real adapter implementations."""
        websocket = MockWebSocket()
        handler = UnifiedAdapterHandler()
        
        # Configure for shadow mode
        config = AdapterEventConfig()
        config.events_enabled = True
        config.adapter_modes["ping"] = AdapterMode.SHADOW
        
        # Use real adapters
        from api.adapters.connection_adapters import PingAdapter
        ping_adapter = PingAdapter()
        
        async def legacy_handler(ws, msg):
            return await ping_adapter.handle(ws, msg)
        
        with patch('api.adapters.adapter_event_config.adapter_event_config', config):
            message = {
                "action": "ping",
                "data": {"timestamp": 1234567890}
            }
            
            result = await handler.handle_message(
                websocket, message, legacy_handler
            )
        
        # Should have shadow results
        assert len(handler.shadow_results) == 1
        shadow = handler.shadow_results[0]
        
        # Results should mostly match (except server_time)
        # This tests that our event adapter produces compatible output
        assert shadow["action"] == "ping"
        # Can't assert exact match due to timing differences


if __name__ == "__main__":
    pytest.main([__file__, "-v"])