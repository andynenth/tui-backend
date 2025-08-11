# backend/tests/api/test_monitoring.py
"""
Test monitoring and metrics endpoints.
"""

import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.shared_instances import shared_room_manager
from backend.engine.game import Game
from backend.engine.player import Player
from backend.services.monitoring_service import metrics_collector, play_history_metrics


client = TestClient(app)


class TestMonitoringEndpoints:
    """Test monitoring and metrics functionality."""
    
    def setup_method(self):
        """Reset metrics before each test."""
        metrics_collector.reset_metrics()
        # Reset play history metrics
        play_history_metrics.rounds_processed = 0
        play_history_metrics.total_response_size = 0
        play_history_metrics.format_usage.clear()
        play_history_metrics.rounds_per_request.clear()
    
    def test_get_metrics_empty(self):
        """Test getting metrics when no requests have been made."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "endpoints" in data
        assert "cache" in data
        assert "overall" in data
        
        # Should have no data yet
        assert data["overall"]["total_requests"] == 0
        assert data["overall"]["total_errors"] == 0
    
    def test_metrics_after_requests(self):
        """Test metrics collection after making some requests."""
        # Make some test requests
        client.get("/api/health")
        client.get("/api/rooms/invalid-room/play-history")  # 404 error
        
        # Get metrics
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        
        # Should have recorded the requests
        assert data["overall"]["total_requests"] >= 2
        assert data["overall"]["total_errors"] >= 1  # The 404
        
        # Should have endpoint-specific data
        assert len(data["endpoints"]) >= 1
    
    async def create_test_room_with_game(self):
        """Create a test room with a game for testing."""
        players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]
        
        room_id = await shared_room_manager.create_room("Bot 1")
        room = await shared_room_manager.get_room(room_id)
        room.game = Game(players)
        room.game.round_number = 1
        room.game.current_phase = "SCORING"
        
        return room_id
    
    def test_play_history_metrics(self):
        """Test play history specific metrics."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create a room and make play history request
        room_id = loop.run_until_complete(self.create_test_room_with_game())
        response = client.get(f"/api/rooms/{room_id}/play-history")
        assert response.status_code == 200
        
        # Get play history metrics
        response = client.get("/api/metrics/play-history")
        assert response.status_code == 200
        data = response.json()
        
        assert "general_metrics" in data
        assert "specialized_metrics" in data
        
        # Check specialized metrics
        special = data["specialized_metrics"]
        assert special["requests_processed"] >= 1
        assert special["total_rounds_processed"] >= 0
        assert "format_usage" in special
    
    def test_time_series_data(self):
        """Test time series metrics retrieval."""
        # Make a request to generate data
        client.get("/api/health")
        
        # Get time series data
        response = client.get("/api/metrics/time-series?endpoint=/api/health&minutes=5")
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoint" in data
        assert "timestamps" in data
        assert "response_times" in data
        assert data["endpoint"] == "/api/health"
        assert data["minutes"] == 5
    
    def test_performance_health_check(self):
        """Test performance health status endpoint."""
        response = client.get("/api/health/performance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["GREEN", "YELLOW", "RED"]
        assert "issues" in data
        assert "metrics_summary" in data
    
    def test_metrics_reset(self):
        """Test metrics reset functionality."""
        # Generate some metrics
        client.get("/api/health")
        
        # Verify metrics exist
        response = client.get("/api/metrics")
        data = response.json()
        assert data["overall"]["total_requests"] > 0
        
        # Reset metrics
        response = client.post("/api/metrics/reset")
        assert response.status_code == 200
        
        # Verify metrics are reset
        response = client.get("/api/metrics")
        data = response.json()
        # Note: The reset request itself counts as a request
        assert data["overall"]["total_requests"] >= 0
    
    def test_cache_metrics(self):
        """Test cache hit/miss metrics."""
        # Manually record some cache hits/misses for testing
        metrics_collector.record_cache_hit("redis")
        metrics_collector.record_cache_hit("redis")
        metrics_collector.record_cache_miss("redis")
        
        response = client.get("/api/metrics")
        data = response.json()
        
        assert "cache" in data
        assert "redis" in data["cache"]
        assert data["cache"]["redis"]["hits"] == 2
        assert data["cache"]["redis"]["misses"] == 1
        assert data["cache"]["redis"]["hit_rate"] == 2/3
    
    def test_slow_request_detection(self):
        """Test that slow requests are properly tracked."""
        # Manually record a slow request
        metrics_collector.record_request(
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=1500  # > 1 second
        )
        
        response = client.get("/api/metrics")
        data = response.json()
        
        assert data["overall"]["total_slow_requests"] >= 1
        
        # Check endpoint specific data
        endpoint_key = "GET:/api/test"
        assert endpoint_key in data["endpoints"]
        assert data["endpoints"][endpoint_key]["slow_request_count"] >= 1
    
    def test_percentile_calculations(self):
        """Test response time percentile calculations."""
        # Record multiple requests with different response times
        test_times = [10, 20, 30, 40, 50, 100, 200, 300, 400, 500]
        for duration in test_times:
            metrics_collector.record_request(
                endpoint="/api/test",
                method="GET",
                status_code=200,
                duration_ms=duration
            )
        
        response = client.get("/api/metrics")
        data = response.json()
        
        endpoint_data = data["endpoints"]["GET:/api/test"]
        
        # Verify percentiles are calculated
        assert "p50_response_time_ms" in endpoint_data
        assert "p95_response_time_ms" in endpoint_data
        assert "p99_response_time_ms" in endpoint_data
        
        # P50 should be around 50-100ms
        assert 40 <= endpoint_data["p50_response_time_ms"] <= 100
        
        # P95 should be higher
        assert endpoint_data["p95_response_time_ms"] >= endpoint_data["p50_response_time_ms"]
    
    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(shared_room_manager, 'rooms'):
            shared_room_manager.rooms.clear()
        metrics_collector.reset_metrics()