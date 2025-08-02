"""
Comprehensive test suite for rate limiting functionality.

Tests both REST API and WebSocket rate limiting to ensure:
- Rate limits are enforced correctly
- WebSocket connections aren't broken by rate limiting
- Burst traffic is handled appropriately
- Client blocking works as expected
- Thread safety and cleanup tasks function properly
"""

import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import pytest
from fastapi import Request, WebSocket
from starlette.datastructures import Headers

from api.middleware.rate_limit import (
    RateLimiter,
    RateLimitRule,
    RateLimitStats,
    get_rate_limiter,
    RateLimitMiddleware,
)
from api.middleware.websocket_rate_limit import (
    WebSocketRateLimiter,
    get_websocket_rate_limiter,
    check_websocket_rate_limit,
    send_rate_limit_error,
    WEBSOCKET_RATE_LIMITS,
)


class TestRateLimiter:
    """Test the core RateLimiter class functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a fresh rate limiter instance for each test."""
        return RateLimiter()

    @pytest.fixture
    def basic_rule(self):
        """Create a basic rate limit rule for testing."""
        return RateLimitRule(
            requests=10,
            window_seconds=60,
            burst_multiplier=1.5,
            block_duration_seconds=300,
        )

    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self, rate_limiter, basic_rule):
        """Test that basic rate limiting works correctly."""
        identifier = "test_client_1"

        # First 10 requests should be allowed
        for i in range(10):
            allowed, info = await rate_limiter.check_rate_limit(identifier, basic_rule)
            assert allowed, f"Request {i+1} should be allowed"
            assert info["remaining"] == 9 - i

        # 11th request should be blocked (no burst yet)
        allowed, info = await rate_limiter.check_rate_limit(identifier, basic_rule)
        assert allowed, "Request 11 should be allowed due to burst multiplier"

        # Continue until we hit the burst limit (15 requests)
        for i in range(4):
            allowed, info = await rate_limiter.check_rate_limit(identifier, basic_rule)
            assert allowed, f"Burst request {i+1} should be allowed"

        # 16th request should be blocked
        allowed, info = await rate_limiter.check_rate_limit(identifier, basic_rule)
        assert not allowed, "Request 16 should be blocked"
        assert "retry_after" in info
        assert info["limit"] == 10
        assert info["window"] == 60

    @pytest.mark.asyncio
    async def test_window_expiration(self, rate_limiter, basic_rule):
        """Test that rate limits reset after the time window expires."""
        identifier = "test_client_2"

        # Use up the rate limit
        for _ in range(15):  # Include burst
            await rate_limiter.check_rate_limit(identifier, basic_rule)

        # Should be blocked now
        allowed, _ = await rate_limiter.check_rate_limit(identifier, basic_rule)
        assert not allowed

        # Mock time to simulate window expiration
        with patch("time.time", return_value=time.time() + 61):
            allowed, info = await rate_limiter.check_rate_limit(identifier, basic_rule)
            assert allowed, "Should be allowed after window expires"
            assert info["remaining"] == 9

    @pytest.mark.asyncio
    async def test_client_blocking(self, rate_limiter):
        """Test that repeat offenders get temporarily blocked."""
        identifier = "test_client_3"
        # Create a rule with low limits to trigger blocking
        rule = RateLimitRule(
            requests=5,
            window_seconds=60,
            burst_multiplier=1.2,
            block_duration_seconds=120,
        )

        # Exceed the limit multiple times to trigger blocking
        for _ in range(15):
            await rate_limiter.check_rate_limit(identifier, rule)

        # Check that client is blocked
        allowed, info = await rate_limiter.check_rate_limit(identifier, rule)
        assert not allowed
        assert info.get("blocked") is True
        assert "Temporarily blocked" in info.get("reason", "")

    @pytest.mark.asyncio
    async def test_cleanup_task(self, rate_limiter):
        """Test that the cleanup task removes old data."""
        identifier = "test_client_4"
        rule = RateLimitRule(requests=10, window_seconds=60)

        # Add some requests
        for _ in range(5):
            await rate_limiter.check_rate_limit(identifier, rule)

        # Verify requests are tracked
        assert identifier in rate_limiter.requests
        assert len(rate_limiter.requests[identifier]) == 5

        # Mock time to make requests old
        with patch("time.time", return_value=time.time() + 3700):  # 1 hour + 100s
            await rate_limiter._cleanup_old_data()

        # Old requests should be removed
        assert identifier not in rate_limiter.requests

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter, basic_rule):
        """Test thread safety with concurrent requests."""
        identifier = "test_client_5"

        async def make_request():
            return await rate_limiter.check_rate_limit(identifier, basic_rule)

        # Make 20 concurrent requests
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # Count allowed vs blocked
        allowed_count = sum(1 for allowed, _ in results if allowed)
        blocked_count = sum(1 for allowed, _ in results if not allowed)

        # With burst of 1.5x, we should allow 15 and block 5
        assert allowed_count == 15
        assert blocked_count == 5

    def test_client_identifier_extraction(self, rate_limiter):
        """Test client identifier extraction from various sources."""
        # Test with IP
        identifier = rate_limiter._get_client_identifier(client_ip="192.168.1.1")
        assert identifier == "ip:192.168.1.1"

        # Test with user ID
        identifier = rate_limiter._get_client_identifier(user_id="user123")
        assert identifier == "user:user123"

        # Test with request object
        mock_request = Mock(spec=Request)
        mock_request.client = Mock(host="10.0.0.1")
        mock_request.headers = Headers({})
        identifier = rate_limiter._get_client_identifier(request=mock_request)
        assert identifier == "ip:10.0.0.1"

        # Test with X-Forwarded-For header
        mock_request.headers = Headers({"X-Forwarded-For": "172.16.0.1, 10.0.0.1"})
        identifier = rate_limiter._get_client_identifier(request=mock_request)
        assert identifier == "ip:172.16.0.1"

    @pytest.mark.asyncio
    async def test_stats_tracking(self, rate_limiter, basic_rule):
        """Test that statistics are tracked correctly."""
        # Make requests from different clients
        for i in range(3):
            for j in range(5):
                await rate_limiter.check_rate_limit(
                    f"client_{i}", basic_rule, "test_route"
                )

        stats = rate_limiter.get_stats("test_route")
        assert stats["total_requests"] == 15
        assert stats["unique_clients"] == 3
        assert stats["blocked_requests"] == 0

        # Make requests that will be blocked
        for i in range(3):
            for j in range(20):  # Exceed limit
                await rate_limiter.check_rate_limit(
                    f"client_{i}", basic_rule, "test_route"
                )

        stats = rate_limiter.get_stats("test_route")
        assert stats["total_requests"] == 75  # 15 + 60
        assert stats["blocked_requests"] > 0
        assert stats["block_rate"] > 0


class TestWebSocketRateLimiter:
    """Test WebSocket-specific rate limiting functionality."""

    @pytest.fixture
    def ws_rate_limiter(self):
        """Create a fresh WebSocket rate limiter instance."""
        return WebSocketRateLimiter()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = Mock(spec=WebSocket)
        ws.client = Mock(host="192.168.1.100")
        return ws

    @pytest.mark.asyncio
    async def test_websocket_event_rate_limiting(self, ws_rate_limiter, mock_websocket):
        """Test rate limiting for different WebSocket event types."""
        room_id = "test_room"

        # Test ping events (high limit)
        for i in range(100):
            allowed, info = await ws_rate_limiter.check_websocket_message_rate_limit(
                mock_websocket, room_id, "ping"
            )
            assert allowed, f"Ping {i+1} should be allowed"

        # Test declare events (low limit)
        for i in range(5):
            allowed, info = await ws_rate_limiter.check_websocket_message_rate_limit(
                mock_websocket, room_id, "declare"
            )
            assert allowed, f"Declaration {i+1} should be allowed"

        # 6th declaration should be blocked
        allowed, info = await ws_rate_limiter.check_websocket_message_rate_limit(
            mock_websocket, room_id, "declare"
        )
        assert not allowed, "6th declaration should be blocked"

    @pytest.mark.asyncio
    async def test_room_flood_protection(self, ws_rate_limiter, mock_websocket):
        """Test room-level flood protection."""
        room_id = "flood_test_room"

        # Simulate many messages to trigger flood protection
        for i in range(100):
            # Use different mock websockets to simulate different clients
            mock_ws = Mock(spec=WebSocket)
            mock_ws.client = Mock(host=f"192.168.1.{i % 10}")

            await ws_rate_limiter.check_websocket_message_rate_limit(
                mock_ws, room_id, "play"
            )

        # Check if room is considered flooded
        is_flooded = await ws_rate_limiter.check_room_flood(room_id, threshold=50)
        assert is_flooded, "Room should be detected as flooded"

    @pytest.mark.asyncio
    async def test_connection_stats(self, ws_rate_limiter, mock_websocket):
        """Test connection statistics tracking."""
        room_id = "stats_room"

        # Generate some activity
        for event in ["ping", "play", "declare"]:
            for _ in range(3):
                await ws_rate_limiter.check_websocket_message_rate_limit(
                    mock_websocket, room_id, event
                )

        # Get client ID for stats lookup
        client_id = ws_rate_limiter._get_client_id(mock_websocket, room_id)
        stats = ws_rate_limiter.get_connection_stats(client_id)

        assert stats["ping"] == 3
        assert stats["play"] == 3
        assert stats["declare"] == 3

        # Test global stats
        global_stats = ws_rate_limiter.get_connection_stats()
        assert global_stats["total_connections"] >= 1
        assert global_stats["total_messages"] >= 9

    @pytest.mark.asyncio
    async def test_cleanup_connection(self, ws_rate_limiter, mock_websocket):
        """Test that connection cleanup works properly."""
        room_id = "cleanup_room"

        # Add some stats
        await ws_rate_limiter.check_websocket_message_rate_limit(
            mock_websocket, room_id, "ping"
        )

        client_id = ws_rate_limiter._get_client_id(mock_websocket, room_id)
        assert client_id in ws_rate_limiter.connection_stats

        # Test cleanup (with mocked sleep to avoid waiting)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await ws_rate_limiter.cleanup_connection(mock_websocket, room_id)

        # Stats should be removed
        assert client_id not in ws_rate_limiter.connection_stats

    @pytest.mark.asyncio
    async def test_send_rate_limit_error(self, mock_websocket):
        """Test rate limit error message sending."""
        mock_websocket.send_json = AsyncMock()

        rate_info = {
            "retry_after": 30,
            "limit": 10,
            "window": 60,
            "blocked": False,
            "reason": "Rate limit exceeded",
        }

        await send_rate_limit_error(mock_websocket, rate_info)

        # Verify error was sent
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]

        assert call_args["event"] == "error"
        assert "rate_limit_error" in str(call_args["data"])
        assert call_args["data"]["retry_after"] == 30


class TestRateLimitMiddleware:
    """Test the FastAPI rate limit middleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance with test rules."""
        test_rules = {
            "/api/test": RateLimitRule(requests=5, window_seconds=60),
            "/api/unlimited": RateLimitRule(requests=9999, window_seconds=60),
            "global": RateLimitRule(requests=10, window_seconds=60),
        }

        async def dummy_app(scope, receive, send):
            pass

        return RateLimitMiddleware(dummy_app, test_rules)

    @pytest.mark.asyncio
    async def test_middleware_rate_limiting(self, middleware):
        """Test that middleware enforces rate limits."""
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.url = Mock(path="/api/test")
        mock_request.client = Mock(host="10.0.0.1")
        mock_request.headers = Headers({})

        # Mock call_next to return a successful response
        async def mock_call_next(request):
            mock_response = Mock()
            mock_response.headers = {}
            return mock_response

        # Make 5 requests (should all succeed)
        for i in range(5):
            response = await middleware.dispatch(mock_request, mock_call_next)
            assert response.headers.get("X-RateLimit-Remaining") == str(4 - i)

        # 6th request should be rate limited
        response = await middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_websocket_bypass(self, middleware):
        """Test that WebSocket paths bypass the middleware."""
        mock_request = Mock(spec=Request)
        mock_request.url = Mock(path="/ws/test_room")

        called = False

        async def mock_call_next(request):
            nonlocal called
            called = True
            return Mock()

        await middleware.dispatch(mock_request, mock_call_next)
        assert called, "WebSocket requests should bypass rate limiting"

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, middleware):
        """Test that rate limit headers are added to responses."""
        mock_request = Mock(spec=Request)
        mock_request.url = Mock(path="/api/unlimited")
        mock_request.client = Mock(host="10.0.0.1")
        mock_request.headers = Headers({})

        async def mock_call_next(request):
            mock_response = Mock()
            mock_response.headers = {}
            return mock_response

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert "X-RateLimit-Window" in response.headers


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_game_flow_with_rate_limits(self):
        """Test a complete game flow doesn't trigger rate limits."""
        ws_limiter = get_websocket_rate_limiter()
        mock_ws = Mock(spec=WebSocket)
        mock_ws.client = Mock(host="192.168.1.1")

        room_id = "game_room"
        player_events = [
            "join_room",
            "player_ready",
            "ping",  # Heartbeat
            "declare",  # Declaration phase
            "play_pieces",  # Turn 1
            "ping",  # Heartbeat
            "play_pieces",  # Turn 2
            "play_pieces",  # Turn 3
            "ping",  # Heartbeat
            "leave_game",
        ]

        # All normal game events should be allowed
        for event in player_events:
            allowed, _ = await check_websocket_rate_limit(mock_ws, room_id, event)
            assert allowed, f"Normal game event '{event}' should not be rate limited"

    @pytest.mark.asyncio
    async def test_abuse_scenario_protection(self):
        """Test that abusive behavior is properly rate limited."""
        ws_limiter = get_websocket_rate_limiter()
        mock_ws = Mock(spec=WebSocket)
        mock_ws.client = Mock(host="192.168.1.100")

        # Scenario 1: Rapid room creation
        blocked_at = None
        for i in range(10):
            allowed, _ = await check_websocket_rate_limit(
                mock_ws, "lobby", "create_room"
            )
            if not allowed and blocked_at is None:
                blocked_at = i + 1

        assert (
            blocked_at is not None and blocked_at <= 6
        ), "Rapid room creation should be blocked"

        # Scenario 2: Declaration spam
        blocked_at = None
        for i in range(10):
            allowed, _ = await check_websocket_rate_limit(mock_ws, "room_1", "declare")
            if not allowed and blocked_at is None:
                blocked_at = i + 1

        assert (
            blocked_at is not None and blocked_at <= 6
        ), "Declaration spam should be blocked"

    @pytest.mark.asyncio
    async def test_multiple_clients_fair_usage(self):
        """Test that rate limits are per-client, not global."""
        ws_limiter = get_websocket_rate_limiter()
        room_id = "fair_room"

        # Create 4 different clients (players)
        clients = []
        for i in range(4):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.client = Mock(host=f"192.168.1.{i+1}")
            clients.append(mock_ws)

        # Each client should be able to make their own declarations
        for client in clients:
            for _ in range(3):
                allowed, _ = await check_websocket_rate_limit(
                    client, room_id, "declare"
                )
                assert allowed, "Each client should have their own rate limit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
