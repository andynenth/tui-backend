"""
Chaos engineering tests for resilience patterns.

Tests system behavior under adverse conditions.
"""

import asyncio
import pytest
import time
import random
from datetime import timedelta
from unittest.mock import Mock, AsyncMock

from backend.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState
)
from backend.infrastructure.resilience.retry import (
    Retry, RetryConfig, RetryStrategy, RetryExhaustedError
)
from backend.infrastructure.resilience.bulkhead import (
    SemaphoreBulkhead, BulkheadConfig, BulkheadFullError
)
from backend.infrastructure.resilience.timeout import (
    TimeoutHandler, TimeoutConfig, TimeoutError
)
from backend.infrastructure.resilience.connection_pool import (
    ConnectionPool, ConnectionFactory, ConnectionPoolConfig
)
from backend.infrastructure.resilience.load_shedding import (
    AdaptiveLoadShedder, SheddingConfig, RequestContext, LoadMetrics
)


class TestCircuitBreaker:
    """Chaos tests for circuit breaker."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_cascade_failure(self):
        """Test circuit breaker under cascading failures."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=timedelta(seconds=1),
            half_open_max_calls=2
        )
        cb = CircuitBreaker("test", config)
        
        # Simulate cascading failures
        failure_count = 0
        async def failing_service():
            nonlocal failure_count
            failure_count += 1
            if failure_count < 10:  # First 10 calls fail
                raise Exception("Service unavailable")
            return "Success"
        
        # Should trip after 3 failures
        for i in range(3):
            with pytest.raises(Exception):
                await cb.call_async(failing_service)
        
        assert cb.state == CircuitState.OPEN
        
        # Should fail fast when open
        with pytest.raises(Exception) as exc_info:
            await cb.call_async(failing_service)
        assert "Circuit breaker is OPEN" in str(exc_info.value)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should transition to half-open and eventually close
        result = await cb.call_async(failing_service)
        assert result == "Success"
        assert cb.state == CircuitState.HALF_OPEN
        
        # One more success should close it
        result = await cb.call_async(failing_service)
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_concurrent_requests(self):
        """Test circuit breaker under high concurrency."""
        config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=timedelta(seconds=0.5)
        )
        cb = CircuitBreaker("concurrent", config)
        
        call_count = 0
        async def flaky_service():
            nonlocal call_count
            call_count += 1
            # 30% failure rate
            if random.random() < 0.3:
                raise Exception("Random failure")
            await asyncio.sleep(0.01)  # Simulate work
            return call_count
        
        # Run many concurrent requests
        tasks = []
        for _ in range(100):
            tasks.append(cb.call_async(flaky_service))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have some successes and failures
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        assert len(successes) > 0
        assert len(failures) > 0
        
        # Circuit might be open at the end
        stats = cb.get_stats()
        assert stats['total_calls'] == 100


class TestRetryMechanism:
    """Chaos tests for retry mechanism."""
    
    @pytest.mark.asyncio
    async def test_retry_intermittent_failures(self):
        """Test retry with intermittent failures."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=timedelta(milliseconds=10),
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=True
        )
        retry = Retry(config)
        
        attempt_count = 0
        async def intermittent_service():
            nonlocal attempt_count
            attempt_count += 1
            # Fail first 3 attempts
            if attempt_count <= 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return f"Success on attempt {attempt_count}"
        
        result = await retry.execute_async(intermittent_service)
        assert result == "Success on attempt 4"
        assert attempt_count == 4
        
        # Check retry stats
        stats = retry.get_stats()
        assert stats['successful_calls'] == 1
        assert stats['average_attempts'] == 4.0
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test retry exhaustion handling."""
        config = RetryConfig(
            max_attempts=3,
            initial_delay=timedelta(milliseconds=1)
        )
        retry = Retry(config)
        
        async def always_failing():
            raise Exception("Always fails")
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry.execute_async(always_failing)
        
        assert exc_info.value.attempts == 3
        assert "Always fails" in str(exc_info.value)
    
    def test_retry_backoff_strategies(self):
        """Test different backoff strategies under load."""
        strategies = [
            RetryStrategy.FIXED,
            RetryStrategy.LINEAR,
            RetryStrategy.EXPONENTIAL,
            RetryStrategy.FIBONACCI
        ]
        
        for strategy in strategies:
            config = RetryConfig(
                max_attempts=5,
                initial_delay=timedelta(milliseconds=10),
                strategy=strategy,
                jitter=False
            )
            
            delays = []
            for attempt in range(1, 6):
                delay = config.calculate_delay(attempt)
                delays.append(delay)
            
            # Verify delays are calculated correctly
            if strategy == RetryStrategy.FIXED:
                assert all(d == delays[0] for d in delays)
            elif strategy == RetryStrategy.LINEAR:
                assert delays == [0.01 * i for i in range(1, 6)]
            elif strategy == RetryStrategy.EXPONENTIAL:
                assert delays[1] > delays[0]  # Increasing
            elif strategy == RetryStrategy.FIBONACCI:
                # Fibonacci sequence
                assert delays[2] == delays[0] + delays[1]


class TestBulkhead:
    """Chaos tests for bulkhead pattern."""
    
    @pytest.mark.asyncio
    async def test_bulkhead_resource_isolation(self):
        """Test bulkhead prevents resource exhaustion."""
        config = BulkheadConfig(
            max_concurrent=3,
            max_queue_size=2,
            timeout=timedelta(seconds=1)
        )
        bulkhead = SemaphoreBulkhead(config)
        
        # Track concurrent executions
        max_concurrent = 0
        current_concurrent = 0
        
        async def slow_operation():
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            
            await asyncio.sleep(0.1)  # Simulate work
            
            current_concurrent -= 1
            return "Done"
        
        # Start many concurrent operations
        tasks = []
        for i in range(10):
            async def wrapper():
                try:
                    await bulkhead.acquire_async()
                    try:
                        return await slow_operation()
                    finally:
                        await bulkhead.release_async()
                except BulkheadFullError:
                    return "Rejected"
            
            tasks.append(wrapper())
        
        results = await asyncio.gather(*tasks)
        
        # Should have limited concurrent executions
        assert max_concurrent <= config.max_concurrent
        
        # Some requests should be rejected
        rejected = [r for r in results if r == "Rejected"]
        assert len(rejected) > 0
        
        # Check stats
        stats = bulkhead.get_stats()
        assert stats['rejected_calls'] > 0
    
    def test_bulkhead_thread_safety(self):
        """Test bulkhead under multi-threaded load."""
        import threading
        
        config = BulkheadConfig(
            max_concurrent=5,
            max_queue_size=10
        )
        bulkhead = SemaphoreBulkhead(config)
        
        results = []
        errors = []
        
        def worker(worker_id):
            for i in range(20):
                try:
                    bulkhead.acquire(timeout=0.5)
                    try:
                        time.sleep(0.01)  # Simulate work
                        results.append(f"Worker {worker_id} - Task {i}")
                    finally:
                        bulkhead.release()
                except Exception as e:
                    errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Verify resource limits were respected
        assert bulkhead.get_active_count() == 0
        assert len(results) + len(errors) == 200  # All tasks accounted for


class TestConnectionPool:
    """Chaos tests for connection pooling."""
    
    class MockConnectionFactory(ConnectionFactory):
        """Mock connection factory for testing."""
        
        def __init__(self, failure_rate=0.0):
            self.failure_rate = failure_rate
            self.created = 0
            self.destroyed = 0
        
        def create(self):
            if random.random() < self.failure_rate:
                raise Exception("Connection failed")
            self.created += 1
            return f"Connection-{self.created}"
        
        def validate(self, connection):
            # Randomly invalidate old connections
            conn_num = int(connection.split('-')[1])
            return conn_num > self.created - 10  # Last 10 are valid
        
        def destroy(self, connection):
            self.destroyed += 1
        
        async def create_async(self):
            return self.create()
        
        async def validate_async(self, connection):
            return self.validate(connection)
        
        async def destroy_async(self, connection):
            self.destroy(connection)
    
    def test_connection_pool_stress(self):
        """Test connection pool under stress."""
        factory = self.MockConnectionFactory(failure_rate=0.1)
        config = ConnectionPoolConfig(
            min_size=2,
            max_size=10,
            max_overflow=5,
            timeout=timedelta(seconds=1)
        )
        pool = ConnectionPool(factory, config)
        
        # Simulate many concurrent users
        def user_simulation():
            for _ in range(50):
                try:
                    conn = pool.acquire(timeout=0.5)
                    time.sleep(random.uniform(0.001, 0.01))  # Use connection
                    pool.release(conn)
                except Exception:
                    pass  # Some failures expected
        
        import threading
        threads = []
        for _ in range(20):
            t = threading.Thread(target=user_simulation)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check pool stats
        stats = pool.get_stats()
        assert stats['current']['size'] <= config.max_size + config.max_overflow
        assert stats['totals']['created'] >= config.min_size
        assert stats['totals']['timeouts'] > 0  # Some timeouts expected
    
    def test_connection_pool_recovery(self):
        """Test pool recovery from failures."""
        factory = self.MockConnectionFactory()
        config = ConnectionPoolConfig(
            min_size=5,
            max_size=10,
            max_lifetime=timedelta(seconds=1)
        )
        pool = ConnectionPool(factory, config)
        
        # Use connections normally
        connections = []
        for _ in range(5):
            connections.append(pool.acquire())
        
        # Return them
        for conn in connections:
            pool.release(conn)
        
        # Wait for connections to expire
        time.sleep(1.1)
        
        # Pool should create new connections
        new_conn = pool.acquire()
        assert new_conn.startswith("Connection-")
        assert int(new_conn.split('-')[1]) > 5  # New connection
        
        pool.release(new_conn)
        
        # Verify old connections were destroyed
        stats = pool.get_stats()
        assert stats['totals']['destroyed'] >= 5


class TestLoadShedding:
    """Chaos tests for load shedding."""
    
    @pytest.mark.asyncio
    async def test_load_shedding_overload(self):
        """Test load shedding under system overload."""
        config = SheddingConfig(
            high_threshold=70.0,
            critical_threshold=85.0,
            overload_threshold=95.0
        )
        shedder = AdaptiveLoadShedder(config)
        
        # Simulate increasing load
        load_levels = [30, 50, 75, 90, 98]  # Increasing CPU usage
        
        for cpu_load in load_levels:
            # Update metrics
            metrics = LoadMetrics(
                cpu_percent=cpu_load,
                memory_percent=60.0,
                request_rate=100.0,
                response_time_p99=0.5,
                error_rate=0.02
            )
            shedder.update_metrics(metrics)
            
            # Simulate requests
            accepted = 0
            rejected = 0
            
            for i in range(100):
                context = RequestContext(
                    request_id=f"req-{i}",
                    priority=random.randint(1, 3),
                    client_id=f"client-{i % 10}"
                )
                
                if shedder.should_accept(context):
                    accepted += 1
                else:
                    rejected += 1
            
            print(f"CPU {cpu_load}%: Accepted={accepted}, Rejected={rejected}")
            
            # Higher load should reject more requests
            if cpu_load >= 90:
                assert rejected > 30  # Should shed significant load
            elif cpu_load >= 75:
                assert rejected > 5   # Should shed some load
    
    def test_load_shedding_fairness(self):
        """Test fair load shedding across clients."""
        config = SheddingConfig(
            strategy=SheddingStrategy.FAIR_QUEUING
        )
        shedder = AdaptiveLoadShedder(config)
        
        # Set high load
        metrics = LoadMetrics(
            cpu_percent=85.0,
            memory_percent=70.0
        )
        shedder.update_metrics(metrics)
        
        # Simulate requests from different clients
        client_stats = {}
        
        # One client sends many more requests
        for i in range(1000):
            if i < 900:
                client_id = "heavy-client"
            else:
                client_id = f"normal-client-{i % 10}"
            
            if client_id not in client_stats:
                client_stats[client_id] = {'requests': 0, 'accepted': 0}
            
            context = RequestContext(
                request_id=f"req-{i}",
                client_id=client_id
            )
            
            client_stats[client_id]['requests'] += 1
            if shedder.should_accept(context):
                client_stats[client_id]['accepted'] += 1
        
        # Check fairness
        heavy_client_rate = (client_stats['heavy-client']['accepted'] / 
                           client_stats['heavy-client']['requests'])
        
        # Heavy client should be throttled more
        assert heavy_client_rate < 0.7  # Should be limited
        
        # Get shedding stats
        stats = shedder.get_stats()
        assert stats['totals']['shed'] > 100  # Should shed requests


class TestChaosScenarios:
    """Integration tests for chaos scenarios."""
    
    @pytest.mark.asyncio
    async def test_cascading_failure_recovery(self):
        """Test system recovery from cascading failures."""
        # Setup resilience components
        circuit_breaker = CircuitBreaker("service", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=timedelta(seconds=0.5)
        ))
        
        retry = Retry(RetryConfig(
            max_attempts=3,
            initial_delay=timedelta(milliseconds=100)
        ))
        
        bulkhead = SemaphoreBulkhead(BulkheadConfig(
            max_concurrent=5
        ))
        
        # Simulate a service that recovers after some failures
        call_count = 0
        async def unreliable_service():
            nonlocal call_count
            call_count += 1
            
            # Fail first 10 calls, then recover
            if call_count <= 10:
                raise Exception("Service down")
            
            return f"Success after {call_count} calls"
        
        # Protected service call
        async def protected_call():
            await bulkhead.acquire_async()
            try:
                return await circuit_breaker.call_async(
                    lambda: retry.execute_async(unreliable_service)
                )
            finally:
                await bulkhead.release_async()
        
        # Run many concurrent calls
        results = []
        for i in range(20):
            try:
                result = await protected_call()
                results.append(result)
            except Exception as e:
                results.append(f"Failed: {str(e)}")
            
            # Small delay between calls
            await asyncio.sleep(0.1)
        
        # System should eventually recover
        successes = [r for r in results if r.startswith("Success")]
        assert len(successes) > 0
        
        # Circuit breaker should have opened and closed
        cb_stats = circuit_breaker.get_stats()
        assert cb_stats['state_changes'] > 0
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_protection(self):
        """Test protection against resource exhaustion."""
        # Memory manager mock
        from backend.infrastructure.optimization.memory_manager import MemoryManager
        
        memory_manager = MemoryManager(
            soft_limit_mb=100,
            hard_limit_mb=200
        )
        
        # Connection pool
        factory = self.MockConnectionFactory()
        conn_pool = ConnectionPool(factory, ConnectionPoolConfig(
            max_size=10,
            max_overflow=5
        ))
        
        # Load shedder
        load_shedder = AdaptiveLoadShedder()
        
        # Simulate memory pressure
        async def memory_intensive_operation():
            # Check memory before proceeding
            memory_manager.check_limits()
            
            # Get connection from pool
            conn = conn_pool.acquire(timeout=1.0)
            try:
                # Simulate work
                await asyncio.sleep(0.05)
                return "Completed"
            finally:
                conn_pool.release(conn)
        
        # Run operations with load shedding
        async def protected_operation(request_id: str):
            context = RequestContext(
                request_id=request_id,
                priority=2
            )
            
            if not load_shedder.should_accept(context):
                raise Exception("Request shed due to load")
            
            return await memory_intensive_operation()
        
        # Simulate high load
        load_shedder.update_metrics(LoadMetrics(
            cpu_percent=80.0,
            memory_percent=75.0,
            active_connections=100
        ))
        
        # Run many operations
        results = await asyncio.gather(
            *[protected_operation(f"req-{i}") for i in range(50)],
            return_exceptions=True
        )
        
        # Should have some successes and some shedding
        successes = [r for r in results if r == "Completed"]
        shed = [r for r in results if isinstance(r, Exception) and "shed" in str(r)]
        
        assert len(successes) > 0
        assert len(shed) > 0
        
        # Pool should not be exhausted
        pool_stats = conn_pool.get_stats()
        assert pool_stats['current']['size'] <= 15  # max_size + max_overflow