"""
Tests for the observability infrastructure.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import logging

from backend.infrastructure.observability import (
    # Logging
    LogLevel,
    LogFormat,
    LogConfig,
    LogContext,
    StructuredLogger,
    AsyncLogger,
    configure_logging,
    get_logger,
    log_context,
    log_performance,
    
    # Metrics
    MetricType,
    MetricUnit,
    MetricConfig,
    MetricTag,
    InMemoryMetricsCollector,
    Counter,
    Gauge,
    Histogram,
    Timer,
    track_metrics,
    
    # Tracing
    SpanKind,
    SpanStatus,
    TraceConfig,
    InMemoryTracer,
    create_span,
    trace,
    
    # Health
    HealthStatus,
    ComponentType,
    HealthCheckConfig,
    HealthCheckResult,
    HealthCheckRegistry,
    DiskSpaceHealthCheck,
    MemoryHealthCheck,
    
    # Correlation
    CorrelationContext,
    get_correlation_id,
    set_correlation_id,
    
    # Monitoring
    AlertSeverity,
    PerformanceMonitor,
    AlertManager,
    AlertRule,
    GamePerformanceMonitor
)


# Tests for Logging

class TestStructuredLogging:
    """Test structured logging functionality."""
    
    def test_basic_logging(self):
        """Test basic log operations."""
        config = LogConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON
        )
        logger = StructuredLogger("test", config)
        
        # Capture output
        output = []
        logger._output = lambda msg: output.append(msg)
        
        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message", user_id="123")
        logger.error("Error message", error_code=500)
        
        assert len(output) == 3
        
        # Check JSON format
        for msg in output:
            data = json.loads(msg)
            assert 'timestamp' in data
            assert 'level' in data
            assert 'message' in data
    
    def test_log_levels(self):
        """Test log level filtering."""
        config = LogConfig(
            level=LogLevel.WARNING,
            format=LogFormat.TEXT
        )
        logger = StructuredLogger("test", config)
        
        output = []
        logger._output = lambda msg: output.append(msg)
        
        logger.debug("Debug")  # Should be filtered
        logger.info("Info")    # Should be filtered
        logger.warning("Warning")  # Should pass
        logger.error("Error")     # Should pass
        
        assert len(output) == 2
        assert "Warning" in output[0]
        assert "Error" in output[1]
    
    def test_context_logging(self):
        """Test logging with context."""
        config = LogConfig(level=LogLevel.INFO)
        logger = StructuredLogger("test", config)
        
        # Create child logger with context
        child_logger = logger.with_context(
            request_id="req123",
            user_id="user456"
        )
        
        output = []
        child_logger._output = lambda msg: output.append(msg)
        
        child_logger.info("Test message")
        
        data = json.loads(output[0])
        assert data['request_id'] == "req123"
        assert data['user_id'] == "user456"
    
    def test_log_context_manager(self):
        """Test log context manager."""
        logger = get_logger("test")
        
        output = []
        logger._output = lambda msg: output.append(msg)
        
        with log_context(correlation_id="corr123", room_id="room456"):
            logger.info("Inside context")
        
        logger.info("Outside context")
        
        # Check first message has context
        data1 = json.loads(output[0])
        assert data1['correlation_id'] == "corr123"
        assert data1['room_id'] == "room456"
        
        # Check second message doesn't have context
        data2 = json.loads(output[1])
        assert 'correlation_id' not in data2
        assert 'room_id' not in data2
    
    @pytest.mark.asyncio
    async def test_async_logger(self):
        """Test async logger with buffering."""
        config = LogConfig(
            level=LogLevel.INFO,
            async_mode=True,
            buffer_size=10
        )
        logger = AsyncLogger("test", config)
        
        output = []
        logger._output = lambda msg: output.append(msg)
        
        # Log multiple messages quickly
        for i in range(5):
            logger.info(f"Message {i}")
        
        # Wait for async processing
        await asyncio.sleep(0.2)
        
        # Should have all messages
        assert len(output) == 5
        
        # Shutdown logger
        logger.shutdown()
    
    @pytest.mark.asyncio
    async def test_log_performance_decorator(self):
        """Test performance logging decorator."""
        logger = get_logger("test")
        
        output = []
        logger._output = lambda msg: output.append(msg)
        
        @log_performance(logger, "test_operation")
        async def slow_operation():
            await asyncio.sleep(0.1)
            return "done"
        
        result = await slow_operation()
        assert result == "done"
        
        # Check performance log
        assert len(output) == 1
        data = json.loads(output[0])
        assert "test_operation completed" in data['message']
        assert data['duration_seconds'] > 0.09
        assert data['status'] == "success"


# Tests for Metrics

class TestMetricsCollection:
    """Test metrics collection functionality."""
    
    def test_counter_metrics(self):
        """Test counter metric operations."""
        config = MetricConfig(prefix="test")
        collector = InMemoryMetricsCollector(config)
        
        # Increment counter
        collector.increment("requests", 1)
        collector.increment("requests", 2)
        collector.increment("errors", 1)
        
        metrics = collector.get_metrics()
        assert metrics['counters']['test.requests'] == 3
        assert metrics['counters']['test.errors'] == 1
    
    def test_gauge_metrics(self):
        """Test gauge metric operations."""
        config = MetricConfig(prefix="test")
        collector = InMemoryMetricsCollector(config)
        
        # Set gauge values
        collector.gauge("memory_usage", 75.5)
        collector.gauge("cpu_usage", 45.2)
        
        metrics = collector.get_metrics()
        assert metrics['gauges']['test.memory_usage']['value'] == 75.5
        assert metrics['gauges']['test.cpu_usage']['value'] == 45.2
    
    def test_histogram_metrics(self):
        """Test histogram metric operations."""
        config = MetricConfig(prefix="test")
        collector = InMemoryMetricsCollector(config)
        
        # Record histogram values
        for value in [10, 20, 30, 40, 50]:
            collector.histogram("response_time", value)
        
        metrics = collector.get_metrics()
        hist = metrics['histograms']['test.response_time']
        
        assert hist['count'] == 5
        assert hist['sum'] == 150
        assert hist['mean'] == 30
        assert hist['min'] == 10
        assert hist['max'] == 50
    
    def test_timer_metrics(self):
        """Test timer metric operations."""
        config = MetricConfig(prefix="test")
        collector = InMemoryMetricsCollector(config)
        
        # Use timer context manager
        timer = Timer(collector, "operation")
        
        with timer.time():
            time.sleep(0.1)
        
        metrics = collector.get_metrics()
        timer_stats = metrics['timers']['test.operation']
        
        assert timer_stats['count'] == 1
        assert timer_stats['mean'] > 0.09
    
    def test_metric_tags(self):
        """Test metrics with tags."""
        config = MetricConfig(
            prefix="test",
            default_tags=[MetricTag("env", "test")]
        )
        collector = InMemoryMetricsCollector(config)
        
        # Counter with tags
        counter = Counter(collector, "requests")
        tagged_counter = counter.with_tags(endpoint="/api/users", method="GET")
        tagged_counter.increment()
        
        metrics = collector.get_metrics()
        # Tagged metric should have separate entry
        assert any("endpoint=/api/users" in key for key in metrics['counters'])
    
    @pytest.mark.asyncio
    async def test_track_metrics_decorator(self):
        """Test metrics tracking decorator."""
        @track_metrics("database.query")
        async def query_database():
            await asyncio.sleep(0.05)
            return "result"
        
        # Execute function
        result = await query_database()
        assert result == "result"
        
        # Check metrics were recorded
        collector = get_metrics_collector()
        metrics = collector.get_metrics()
        
        # Should have call count and duration
        assert any("database.query.calls" in key for key in metrics['counters'])
        assert any("database.query.duration" in key for key in metrics['timers'])


# Tests for Tracing

class TestDistributedTracing:
    """Test distributed tracing functionality."""
    
    def test_basic_span_creation(self):
        """Test creating and ending spans."""
        config = TraceConfig(service_name="test-service")
        tracer = InMemoryTracer(config)
        
        # Create span
        span = tracer.start_span("test-operation")
        span.set_attribute("user_id", "123")
        span.add_event("Processing started")
        span.end()
        
        # Check span was recorded
        traces = tracer.get_traces()
        assert len(traces) == 1
        
        trace_id = list(traces.keys())[0]
        spans = traces[trace_id]
        assert len(spans) == 1
        assert spans[0]['name'] == "test-operation"
        assert spans[0]['attributes']['user_id'] == "123"
    
    def test_span_context_manager(self):
        """Test span context manager."""
        tracer = InMemoryTracer(TraceConfig())
        
        with tracer.span("parent-operation") as parent:
            parent.set_attribute("level", "parent")
            
            with tracer.span("child-operation") as child:
                child.set_attribute("level", "child")
        
        traces = tracer.get_traces()
        trace_id = list(traces.keys())[0]
        spans = traces[trace_id]
        
        assert len(spans) == 2
        
        # Find parent and child
        parent_span = next(s for s in spans if s['name'] == "parent-operation")
        child_span = next(s for s in spans if s['name'] == "child-operation")
        
        # Check parent-child relationship
        assert child_span['parent_span_id'] == parent_span['span_id']
        assert child_span['trace_id'] == parent_span['trace_id']
    
    def test_span_exception_handling(self):
        """Test span exception recording."""
        tracer = InMemoryTracer(TraceConfig())
        
        try:
            with tracer.span("failing-operation") as span:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        traces = tracer.get_traces()
        trace_id = list(traces.keys())[0]
        span_data = traces[trace_id][0]
        
        assert span_data['status'] == SpanStatus.ERROR.value
        assert any(e['name'] == "exception" for e in span_data['events'])
    
    def test_trace_context_propagation(self):
        """Test trace context injection and extraction."""
        tracer = InMemoryTracer(TraceConfig())
        
        # Create span and inject context
        span = tracer.start_span("operation")
        carrier = {}
        tracer.inject(carrier)
        
        assert 'traceparent' in carrier
        
        # Extract context
        extracted = tracer.extract(carrier)
        assert extracted is not None
        assert extracted.trace_id == span.get_context().trace_id
        
        span.end()
    
    @pytest.mark.asyncio
    async def test_trace_decorator(self):
        """Test trace decorator."""
        @trace("decorated_function")
        async def test_function(value: int) -> int:
            await asyncio.sleep(0.01)
            return value * 2
        
        result = await test_function(5)
        assert result == 10
        
        # Check trace was created
        tracer = get_tracer()
        traces = tracer.get_traces()
        assert len(traces) > 0


# Tests for Health Checks

class TestHealthChecks:
    """Test health check functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_health_check(self):
        """Test basic health check operation."""
        class CustomHealthCheck(BaseHealthCheck):
            async def _perform_check(self) -> HealthCheckResult:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    component_type=self.component_type,
                    message="All good"
                )
        
        check = CustomHealthCheck("test", ComponentType.CUSTOM)
        result = await check.check()
        
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All good"
        assert result.duration_ms is not None
    
    @pytest.mark.asyncio
    async def test_health_check_registry(self):
        """Test health check registry."""
        registry = HealthCheckRegistry()
        
        # Add multiple checks
        check1 = Mock(spec=IHealthCheck)
        check1.get_name.return_value = "check1"
        check1.get_component_type.return_value = ComponentType.DATABASE
        check1.check = AsyncMock(return_value=HealthCheckResult(
            name="check1",
            status=HealthStatus.HEALTHY,
            component_type=ComponentType.DATABASE
        ))
        
        check2 = Mock(spec=IHealthCheck)
        check2.get_name.return_value = "check2"
        check2.get_component_type.return_value = ComponentType.CACHE
        check2.check = AsyncMock(return_value=HealthCheckResult(
            name="check2",
            status=HealthStatus.DEGRADED,
            component_type=ComponentType.CACHE
        ))
        
        registry.register(check1)
        registry.register(check2)
        
        # Run all checks
        results = await registry.check_all()
        assert len(results) == 2
        
        # Check overall status
        overall = registry.get_overall_status()
        assert overall == HealthStatus.DEGRADED  # Worst status
    
    @pytest.mark.asyncio
    async def test_disk_space_health_check(self):
        """Test disk space health check."""
        check = DiskSpaceHealthCheck(
            path="/",
            warning_threshold_gb=1000,  # High threshold for test
            critical_threshold_gb=500
        )
        
        result = await check.check()
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert 'free_gb' in result.details
        assert 'disk_free_bytes' in result.metrics
    
    @pytest.mark.asyncio
    async def test_memory_health_check(self):
        """Test memory health check."""
        check = MemoryHealthCheck(
            warning_threshold_percent=99,  # High threshold for test
            critical_threshold_percent=99.9
        )
        
        result = await check.check()
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert 'percent' in result.details
        assert 'memory_percent' in result.metrics


# Tests for Correlation

class TestCorrelation:
    """Test correlation ID tracking."""
    
    def test_correlation_context(self):
        """Test correlation context management."""
        # Initially no correlation ID
        assert CorrelationContext.get_correlation_id() is None
        
        # Set correlation ID
        corr_id = CorrelationContext.generate_correlation_id()
        CorrelationContext.set_correlation_id(corr_id)
        
        assert CorrelationContext.get_correlation_id() == corr_id
        
        # Use context manager
        with CorrelationContext.with_correlation_id("test-123"):
            assert CorrelationContext.get_correlation_id() == "test-123"
        
        # Should restore previous ID
        assert CorrelationContext.get_correlation_id() == corr_id
    
    @pytest.mark.asyncio
    async def test_correlation_decorator(self):
        """Test correlation decorator."""
        from backend.infrastructure.observability.correlation import with_correlation_id
        
        @with_correlation_id()
        async def process_request():
            return CorrelationContext.get_correlation_id()
        
        corr_id = await process_request()
        assert corr_id is not None
        assert len(corr_id) == 36  # UUID format


# Tests for Performance Monitoring

class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""
    
    def test_performance_monitor(self):
        """Test basic performance monitoring."""
        monitor = PerformanceMonitor(window_size_seconds=60)
        
        # Record some requests
        monitor.record_request("/api/users", 50.0)
        monitor.record_request("/api/users", 100.0)
        monitor.record_request("/api/users", 150.0, is_error=True)
        
        # Get metrics
        metrics = monitor.get_current_metrics()
        
        assert metrics.request_count == 3
        assert metrics.error_count == 1
        assert metrics.error_rate == 1/3
        assert metrics.avg_duration_ms == 100.0
    
    def test_alert_manager(self):
        """Test alert management."""
        manager = AlertManager()
        
        # Add alert rule
        rule = AlertRule(
            name="high_error_rate",
            metric_name="error_rate",
            condition=lambda x: x > 0.1,
            severity=AlertSeverity.WARNING,
            message_template="Error rate is {value:.1%}"
        )
        manager.add_rule(rule)
        
        # Evaluate metric
        alerts = manager.evaluate_metric("error_rate", 0.15)
        
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING
        assert "15.0%" in alerts[0].message
        
        # Check active alerts
        active = manager.get_active_alerts()
        assert len(active) == 1
    
    def test_game_performance_monitor(self):
        """Test game-specific performance monitoring."""
        monitor = GamePerformanceMonitor()
        
        # Record game metrics
        monitor.record_turn("room1", 45.0, 4)
        monitor.record_turn("room1", 55.0, 4)
        monitor.record_bot_response("bot1", 750.0)
        monitor.record_bot_response("bot2", 1200.0)
        
        # Get game metrics
        metrics = monitor.get_game_metrics()
        
        assert metrics['turn_metrics']['count'] == 2
        assert metrics['turn_metrics']['avg_ms'] == 50.0
        assert metrics['bot_metrics']['count'] == 2
        assert metrics['bot_metrics']['within_target'] == 1.0  # Both within 500-1500ms


# Integration Tests

class TestObservabilityIntegration:
    """Test integration between observability components."""
    
    @pytest.mark.asyncio
    async def test_logging_with_correlation(self):
        """Test logging with correlation context."""
        configure_logging(LogConfig(level=LogLevel.INFO))
        logger = get_logger("test")
        
        output = []
        logger._output = lambda msg: output.append(msg)
        
        # Log with correlation context
        with CorrelationContext.with_correlation_id("corr-123"):
            with log_context(user_id="user-456"):
                logger.info("Test message")
        
        data = json.loads(output[0])
        assert data['correlation_id'] == "corr-123"
        assert data['user_id'] == "user-456"
    
    @pytest.mark.asyncio
    async def test_tracing_with_metrics(self):
        """Test tracing with metrics collection."""
        @trace("test_operation")
        @track_metrics("test_operation")
        async def operation():
            await asyncio.sleep(0.01)
            return "done"
        
        result = await operation()
        assert result == "done"
        
        # Check both trace and metrics were recorded
        tracer = get_tracer()
        traces = tracer.get_traces()
        assert len(traces) > 0
        
        collector = get_metrics_collector()
        metrics = collector.get_metrics()
        assert any("test_operation.calls" in key for key in metrics['counters'])