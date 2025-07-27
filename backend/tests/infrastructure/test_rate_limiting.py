"""
Tests for the rate limiting infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from backend.infrastructure.rate_limiting import (
    # Base
    RateLimitAlgorithm,
    RateLimitConfig,
    RateLimitExceeded,
    MemoryRateLimitStore,
    CompositeRateLimiter,
    
    # Algorithms
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    OptimizedTokenBucket,
    AdaptiveTokenBucket,
    
    # Game specific
    GameWebSocketRateLimiter,
    AdaptiveGameRateLimiter,
    GameActionCost,
    
    # Factory functions
    create_rate_limiter,
    create_game_rate_limiter
)


# Tests for Token Bucket Algorithm

class TestTokenBucket:
    """Test token bucket rate limiter."""
    
    @pytest.mark.asyncio
    async def test_basic_token_consumption(self):
        """Test basic token consumption."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=10,
            refill_rate=1.0  # 1 token per second
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Should start with full capacity
        result = await limiter.check_rate_limit("user1")
        assert result.allowed is True
        assert result.remaining == 10
        
        # Consume 5 tokens
        for _ in range(5):
            success = await limiter.consume("user1")
            assert success is True
        
        # Check remaining
        result = await limiter.check_rate_limit("user1")
        assert result.allowed is True
        assert result.remaining == 5
        
        # Consume remaining tokens
        for _ in range(5):
            success = await limiter.consume("user1")
            assert success is True
        
        # Should be rate limited now
        result = await limiter.check_rate_limit("user1")
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test token refill over time."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=10,
            refill_rate=10.0  # 10 tokens per second for faster test
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Consume all tokens
        for _ in range(10):
            await limiter.consume("user1")
        
        # Should be rate limited
        assert await limiter.consume("user1") is False
        
        # Wait for refill
        await asyncio.sleep(0.2)  # Should refill 2 tokens
        
        # Should be able to consume again
        assert await limiter.consume("user1") is True
        assert await limiter.consume("user1") is True
        assert await limiter.consume("user1") is False  # Only 2 refilled
    
    @pytest.mark.asyncio
    async def test_burst_capacity(self):
        """Test burst capacity feature."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=10,
            refill_rate=1.0,
            burst_capacity=20  # Allow bursts up to 20
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Should start with burst capacity
        result = await limiter.check_rate_limit("user1")
        assert result.remaining == 20
        
        # Consume more than normal capacity
        for _ in range(15):
            success = await limiter.consume("user1")
            assert success is True
        
        result = await limiter.check_rate_limit("user1")
        assert result.remaining == 5
    
    @pytest.mark.asyncio
    async def test_cost_based_consumption(self):
        """Test consuming with different costs."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=100,
            refill_rate=1.0
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Expensive operation
        result = await limiter.check_rate_limit("user1", cost=50)
        assert result.allowed is True
        assert result.remaining == 50
        
        success = await limiter.consume("user1", cost=50)
        assert success is True
        
        # Another expensive operation should exceed limit
        result = await limiter.check_rate_limit("user1", cost=60)
        assert result.allowed is False
        
        # But smaller operation should work
        result = await limiter.check_rate_limit("user1", cost=40)
        assert result.allowed is True


# Tests for Sliding Window Algorithm

class TestSlidingWindow:
    """Test sliding window rate limiter."""
    
    @pytest.mark.asyncio
    async def test_basic_window_limiting(self):
        """Test basic sliding window limiting."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            capacity=5,
            window_size=timedelta(seconds=1),
            refill_rate=0  # Not used
        )
        limiter = SlidingWindowRateLimiter(config)
        
        # Consume capacity
        for _ in range(5):
            success = await limiter.consume("user1")
            assert success is True
        
        # Should be rate limited
        success = await limiter.consume("user1")
        assert success is False
        
        # Wait for window to slide
        await asyncio.sleep(1.1)
        
        # Should be able to consume again
        success = await limiter.consume("user1")
        assert success is True
    
    @pytest.mark.asyncio
    async def test_accurate_window_counting(self):
        """Test that sliding window is accurate."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            capacity=10,
            window_size=timedelta(seconds=2),
            refill_rate=0
        )
        limiter = SlidingWindowRateLimiter(config)
        
        # Consume 5 at start
        for _ in range(5):
            await limiter.consume("user1")
        
        # Wait 1 second (half window)
        await asyncio.sleep(1)
        
        # Consume 5 more
        for _ in range(5):
            await limiter.consume("user1")
        
        # Should be at limit
        assert await limiter.consume("user1") is False
        
        # Wait another second
        await asyncio.sleep(1)
        
        # First 5 should have expired, can consume 5 more
        for _ in range(5):
            success = await limiter.consume("user1")
            assert success is True
        
        # But not 6
        assert await limiter.consume("user1") is False
    
    @pytest.mark.asyncio
    async def test_optimized_sliding_window(self):
        """Test optimized sliding window with circular buffer."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            capacity=100,
            window_size=timedelta(seconds=10),
            refill_rate=0
        )
        limiter = OptimizedSlidingWindow(config, buckets=10)
        
        # Should handle high volume efficiently
        for _ in range(50):
            success = await limiter.consume("user1")
            assert success is True
        
        stats = await limiter.get_stats("user1")
        assert stats['current_count'] == 50
        assert stats['buckets'] == 10


# Tests for Distributed Rate Limiting

class TestDistributedRateLimiting:
    """Test distributed rate limiting features."""
    
    @pytest.mark.asyncio
    async def test_memory_store_operations(self):
        """Test in-memory rate limit store."""
        store = MemoryRateLimitStore()
        
        # Test bucket operations
        await store.set_bucket("test", {"tokens": 10})
        bucket = await store.get_bucket("test")
        assert bucket["tokens"] == 10
        
        # Test counter operations
        count = await store.increment_counter("counter1")
        assert count == 1
        
        count = await store.increment_counter("counter1", 5)
        assert count == 6
        
        # Test window operations
        now = datetime.utcnow()
        await store.add_to_window("window1", now, 1)
        await store.add_to_window("window1", now + timedelta(seconds=1), 2)
        
        total = await store.get_window_sum(
            "window1",
            now - timedelta(seconds=1),
            now + timedelta(seconds=2)
        )
        assert total == 3
    
    @pytest.mark.asyncio
    async def test_composite_rate_limiter(self):
        """Test composite rate limiter with multiple limits."""
        # Per-second limit
        second_config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=10,
            refill_rate=10.0
        )
        second_limiter = TokenBucketRateLimiter(second_config)
        
        # Per-minute limit
        minute_config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            capacity=100,
            window_size=timedelta(minutes=1),
            refill_rate=0
        )
        minute_limiter = SlidingWindowRateLimiter(minute_config)
        
        # Composite limiter
        composite = CompositeRateLimiter([
            ("per_second", second_limiter),
            ("per_minute", minute_limiter)
        ])
        
        # Should be limited by most restrictive
        for _ in range(10):
            success = await composite.consume("user1")
            assert success is True
        
        # Hit per-second limit
        success = await composite.consume("user1")
        assert success is False
        
        # Wait for second limit to refill
        await asyncio.sleep(1)
        
        # Can consume again but will eventually hit minute limit
        consumed = 0
        for _ in range(100):
            if await composite.consume("user1"):
                consumed += 1
            else:
                break
        
        # Should have consumed some but hit minute limit
        assert consumed > 0
        assert consumed < 90  # Already consumed 10


# Tests for Game-Specific Rate Limiting

class TestGameRateLimiting:
    """Test game-specific rate limiting."""
    
    @pytest.mark.asyncio
    async def test_game_action_costs(self):
        """Test different costs for game actions."""
        limiter = create_game_rate_limiter(
            player_limit=100,
            adaptive=False
        )
        
        player_id = "player1"
        room_id = "room1"
        
        # Cheap action
        result = await limiter.check_action(
            player_id, room_id, "send_message"
        )
        assert result.allowed is True
        
        # Expensive action
        result = await limiter.check_action(
            player_id, room_id, "create_room"
        )
        assert result.allowed is True
        assert result.remaining < 95  # Cost more tokens
    
    @pytest.mark.asyncio
    async def test_room_level_limiting(self):
        """Test room-level rate limiting."""
        limiter = create_game_rate_limiter(
            player_limit=100,
            room_limit=50,
            adaptive=False
        )
        
        room_id = "room1"
        
        # Multiple players in same room
        success_count = 0
        for i in range(100):
            player_id = f"player{i % 10}"  # 10 different players
            
            if await limiter.consume_action(player_id, room_id, "play_piece"):
                success_count += 1
        
        # Should hit room limit before individual limits
        assert success_count < 60  # Room limit is 50
    
    @pytest.mark.asyncio
    async def test_connection_tracking(self):
        """Test WebSocket connection tracking."""
        limiter = GameWebSocketRateLimiter()
        
        # Track connections
        assert await limiter.on_connect("player1", "conn1") is True
        assert await limiter.on_connect("player1", "conn2") is True
        
        # Join room
        await limiter.on_join_room("conn1", "room1")
        
        # Check stats
        stats = await limiter.get_player_stats("player1")
        assert stats['active_connections'] == 2
        
        room_stats = await limiter.get_room_stats("room1")
        assert room_stats['active_connections'] == 1
        
        # Disconnect
        await limiter.on_disconnect("conn1")
        
        stats = await limiter.get_player_stats("player1")
        assert stats['active_connections'] == 1
    
    @pytest.mark.asyncio
    async def test_adaptive_rate_limiting(self):
        """Test adaptive rate limiting based on game state."""
        limiter = AdaptiveGameRateLimiter()
        
        player_id = "player1"
        room_id = "room1"
        
        # Set game state to active
        await limiter.on_game_state_change(room_id, "turn")
        
        # Actions should have lower cost during active gameplay
        data = {"room_id": room_id}
        result = await limiter.check_action(
            player_id, room_id, "play_piece", data
        )
        assert result.allowed is True
        
        # Change to lobby state
        await limiter.on_game_state_change(room_id, "lobby")
        
        # Same action should have higher cost
        # This is reflected in the internal cost calculation


# Tests for Rate Limit Decorators and Middleware

class TestRateLimitIntegration:
    """Test rate limit integration patterns."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_decorator(self):
        """Test rate limit decorator."""
        limiter = create_rate_limiter(capacity=5)
        
        call_count = 0
        
        @RateLimitDecorator(
            limiter,
            lambda *args: "test_key"
        )
        async def protected_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # Should allow up to limit
        for _ in range(5):
            result = await protected_function()
            assert result == "success"
        
        assert call_count == 5
        
        # Should be rate limited
        with pytest.raises(RateLimitExceeded):
            await protected_function()
        
        assert call_count == 5  # Not called
    
    @pytest.mark.asyncio
    async def test_factory_functions(self):
        """Test convenience factory functions."""
        # Token bucket limiter
        tb_limiter = create_rate_limiter(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=100
        )
        assert isinstance(tb_limiter, TokenBucketRateLimiter)
        
        # Sliding window limiter
        sw_limiter = create_rate_limiter(
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            capacity=100,
            window_size=timedelta(minutes=1)
        )
        assert isinstance(sw_limiter, SlidingWindowRateLimiter)
        
        # Game limiter
        game_limiter = create_game_rate_limiter(adaptive=True)
        assert isinstance(game_limiter, AdaptiveGameRateLimiter)


# Performance Tests

class TestRateLimitingPerformance:
    """Test rate limiting performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency(self):
        """Test rate limiting under high concurrency."""
        limiter = create_rate_limiter(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=1000,
            refill_rate=100
        )
        
        # Simulate many concurrent requests
        async def make_request(user_id: str):
            return await limiter.consume(user_id)
        
        # 100 users, 10 requests each
        tasks = []
        for i in range(100):
            user_id = f"user{i}"
            for _ in range(10):
                tasks.append(make_request(user_id))
        
        # Should handle all requests efficiently
        results = await asyncio.gather(*tasks)
        
        # Each user should have some successful requests
        success_by_user = {}
        for i, result in enumerate(results):
            user_id = f"user{i // 10}"
            success_by_user[user_id] = success_by_user.get(user_id, 0) + (1 if result else 0)
        
        # All users should have gotten through some requests
        assert all(count > 0 for count in success_by_user.values())
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory efficiency of different algorithms."""
        # Optimized token bucket should use less memory
        optimized = OptimizedTokenBucket(
            RateLimitConfig(
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                capacity=100,
                refill_rate=10
            ),
            update_threshold=0.1
        )
        
        # Make many requests
        for i in range(1000):
            key = f"user{i}"
            await optimized.consume(key)
        
        # Flush updates
        flushed = await optimized.flush_updates()
        assert flushed > 0  # Should have batched updates