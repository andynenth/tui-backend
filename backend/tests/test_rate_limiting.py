# backend/tests/test_rate_limiting.py

"""
Tests for rate limiting functionality.
"""

import asyncio
import time

import pytest
from api.middleware.rate_limiter import (
    RateLimiter,
    check_websocket_rate_limit,
    cleanup_websocket_limiter,
)
from fastapi import WebSocket
from fastapi.testclient import TestClient


class TestRateLimiter:
    """Test token bucket rate limiter implementation."""
    
    def test_initial_bucket_full(self):
        """Test that new clients start with full token bucket."""
        limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
        
        allowed, tokens = limiter.is_allowed("client1")
        assert allowed is True
        assert tokens == 9  # Started with 10, consumed 1
        
    def test_consume_multiple_tokens(self):
        """Test consuming multiple tokens at once."""
        limiter = RateLimiter(max_tokens=10, refill_rate=1.0)
        
        allowed, tokens = limiter.is_allowed("client1", tokens_required=5)
        assert allowed is True
        assert tokens == 5  # Started with 10, consumed 5
        
    def test_bucket_exhaustion(self):
        """Test that bucket can be exhausted."""
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        
        # Consume all tokens
        for i in range(5):
            allowed, tokens = limiter.is_allowed("client1")
            assert allowed is True
            
        # Next request should be denied
        allowed, tokens = limiter.is_allowed("client1")
        assert allowed is False
        assert tokens == 0
        
    def test_token_refill(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(max_tokens=5, refill_rate=10.0)  # 10 tokens per second
        
        # Consume all tokens
        for i in range(5):
            limiter.is_allowed("client1")
            
        # Wait for refill
        time.sleep(0.3)  # Should refill ~3 tokens
        
        allowed, tokens = limiter.is_allowed("client1")
        assert allowed is True
        assert tokens >= 2  # Should have at least 2 tokens (3 refilled - 1 consumed)
        
    def test_max_tokens_cap(self):
        """Test that tokens don't exceed maximum."""
        limiter = RateLimiter(max_tokens=5, refill_rate=100.0)  # Very fast refill
        
        # Wait for potential overfill
        time.sleep(1.0)
        
        allowed, tokens = limiter.is_allowed("client1")
        assert allowed is True
        assert tokens == 4  # Should be capped at max_tokens - 1
        
    def test_multiple_clients(self):
        """Test that different clients have separate buckets."""
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        
        # Exhaust client1's tokens
        for i in range(5):
            limiter.is_allowed("client1")
            
        # Client2 should still have tokens
        allowed, tokens = limiter.is_allowed("client2")
        assert allowed is True
        assert tokens == 4
        
        # Client1 should be rate limited
        allowed, tokens = limiter.is_allowed("client1")
        assert allowed is False
        
    def test_cleanup_old_buckets(self):
        """Test cleanup of old unused buckets."""
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        
        # Create some buckets
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        
        # Manually set old timestamp for client1
        tokens, _ = limiter.buckets["client1"]
        limiter.buckets["client1"] = (tokens, time.time() - 7200)  # 2 hours ago
        
        # Clean up old buckets
        limiter.cleanup_old_buckets(max_age=3600)  # 1 hour
        
        assert "client1" not in limiter.buckets
        assert "client2" in limiter.buckets


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self, client_host="127.0.0.1", client_port=12345):
        self.client = type('Client', (), {
            'host': client_host,
            'port': client_port
        })()
        self.closed = False
        self.close_code = None
        self.close_reason = None
        
    async def close(self, code=1000, reason=""):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


class TestWebSocketRateLimiting:
    """Test WebSocket-specific rate limiting."""
    
    @pytest.mark.asyncio
    async def test_connection_rate_limit(self):
        """Test connection rate limiting."""
        # Create multiple connections from same IP
        websockets = []
        
        for i in range(6):  # Default limit is 5 connections per minute
            ws = MockWebSocket()
            websockets.append(ws)
            allowed, error = await check_websocket_rate_limit(ws, "ws_connect")
            
            if i < 5:
                assert allowed is True
                assert error is None
            else:
                assert allowed is False
                assert "Too many connections" in error
                
    @pytest.mark.asyncio
    async def test_message_rate_limit(self):
        """Test message rate limiting."""
        ws = MockWebSocket()
        
        # Default limit is 120 messages per minute (2 per second)
        # Send burst of messages
        allowed_count = 0
        for i in range(130):
            allowed, error = await check_websocket_rate_limit(ws, "ws_message")
            if allowed:
                allowed_count += 1
                
        # Should allow around 120 messages
        assert 115 <= allowed_count <= 125  # Some tolerance for timing
        
    @pytest.mark.asyncio
    async def test_event_specific_limits(self):
        """Test different limits for different events."""
        ws = MockWebSocket()
        
        # Declare events have lower limit (10 per minute)
        declare_allowed = 0
        for i in range(15):
            allowed, error = await check_websocket_rate_limit(ws, "ws_declare")
            if allowed:
                declare_allowed += 1
                
        assert declare_allowed == 10
        
        # Play events have medium limit (30 per minute)
        ws2 = MockWebSocket(client_port=12346)  # Different connection
        play_allowed = 0
        for i in range(35):
            allowed, error = await check_websocket_rate_limit(ws2, "ws_play")
            if allowed:
                play_allowed += 1
                
        assert play_allowed == 30
        
    @pytest.mark.asyncio
    async def test_cleanup_on_disconnect(self):
        """Test that rate limiters are cleaned up on disconnect."""
        from api.middleware.rate_limiter import ws_message_limiters
        
        ws = MockWebSocket()
        connection_id = f"{ws.client.host}:{ws.client.port}"
        
        # Create rate limiter by checking rate limit
        await check_websocket_rate_limit(ws, "ws_message")
        assert connection_id in ws_message_limiters
        
        # Clean up
        cleanup_websocket_limiter(ws)
        assert connection_id not in ws_message_limiters


@pytest.mark.asyncio
async def test_rest_api_rate_limiting(client: TestClient):
    """Test REST API rate limiting integration."""
    # This would require a test client with the middleware installed
    # Placeholder for integration test
    pass