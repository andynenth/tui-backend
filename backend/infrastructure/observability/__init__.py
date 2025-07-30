"""
Observability infrastructure for monitoring, logging, and tracing.

This module provides:
- Structured logging with context
- Metrics collection and export
- Distributed tracing support
- Health check framework
- Performance monitoring
- Correlation ID tracking
"""

from .logging import (
    # Interfaces
    ILogger,
    ILoggerFactory,
    # Enums
    LogLevel,
    LogFormat,
    # Configuration
    LogConfig,
    LogContext,
    # Implementations
    StructuredLogger,
    ConsoleLogger,
    FileLogger,
    JsonLogger,
    AsyncLogger,
    # Utilities
    get_logger,
    configure_logging,
    log_context,
    log_performance,
)

from .metrics import (
    # Interfaces
    IMetricsCollector,
    IMetricsExporter,
    # Enums
    MetricType,
    MetricUnit,
    # Configuration
    MetricConfig,
    MetricValue,
    MetricTag,
    # Collectors
    InMemoryMetricsCollector,
    PrometheusMetricsCollector,
    # Utilities
    Counter,
    Gauge,
    Histogram,
    Timer,
    get_metrics_collector,
    # Decorators
    track_metrics,
    measure_time,
)

from .tracing import (
    # Interfaces
    ITracer,
    ISpan,
    ISpanContext,
    # Configuration
    TraceConfig,
    SpanKind,
    SpanStatus,
    # Implementations
    InMemoryTracer,
    OpenTelemetryTracer,
    # Utilities
    create_span,
    inject_context,
    extract_context,
    trace,
    get_tracer,
)

from .health import (
    # Interfaces
    IHealthCheck,
    IHealthCheckRegistry,
    # Enums
    HealthStatus,
    ComponentType,
    # Configuration
    HealthCheckConfig,
    HealthCheckResult,
    # Implementations
    HealthCheckRegistry,
    CompositeHealthCheck,
    # Checks
    DatabaseHealthCheck,
    RedisHealthCheck,
    DiskSpaceHealthCheck,
    MemoryHealthCheck,
    # Utilities
    register_health_check,
    run_health_checks,
)

from .correlation import (
    # Context
    CorrelationContext,
    CorrelationMiddleware,
    # Utilities
    get_correlation_id,
    set_correlation_id,
    with_correlation_id,
)

from .monitoring import (
    # Performance
    PerformanceMonitor,
    PerformanceMetrics,
    # Alerts
    AlertManager,
    AlertRule,
    AlertSeverity,
    # Dashboards
    MetricsDashboard,
    DashboardWidget,
)

__all__ = [
    # Logging
    "ILogger",
    "ILoggerFactory",
    "LogLevel",
    "LogFormat",
    "LogConfig",
    "LogContext",
    "StructuredLogger",
    "ConsoleLogger",
    "FileLogger",
    "JsonLogger",
    "AsyncLogger",
    "get_logger",
    "configure_logging",
    "log_context",
    "log_performance",
    # Metrics
    "IMetricsCollector",
    "IMetricsExporter",
    "MetricType",
    "MetricUnit",
    "MetricConfig",
    "MetricValue",
    "MetricTag",
    "InMemoryMetricsCollector",
    "PrometheusMetricsCollector",
    "Counter",
    "Gauge",
    "Histogram",
    "Timer",
    "get_metrics_collector",
    "track_metrics",
    "measure_time",
    # Tracing
    "ITracer",
    "ISpan",
    "ISpanContext",
    "TraceConfig",
    "SpanKind",
    "SpanStatus",
    "InMemoryTracer",
    "OpenTelemetryTracer",
    "create_span",
    "inject_context",
    "extract_context",
    "trace",
    "get_tracer",
    # Health
    "IHealthCheck",
    "IHealthCheckRegistry",
    "HealthStatus",
    "ComponentType",
    "HealthCheckConfig",
    "HealthCheckResult",
    "HealthCheckRegistry",
    "CompositeHealthCheck",
    "DatabaseHealthCheck",
    "RedisHealthCheck",
    "DiskSpaceHealthCheck",
    "MemoryHealthCheck",
    "register_health_check",
    "run_health_checks",
    # Correlation
    "CorrelationContext",
    "CorrelationMiddleware",
    "get_correlation_id",
    "set_correlation_id",
    "with_correlation_id",
    # Monitoring
    "PerformanceMonitor",
    "PerformanceMetrics",
    "AlertManager",
    "AlertRule",
    "AlertSeverity",
    "MetricsDashboard",
    "DashboardWidget",
]


# Convenience functions for quick setup


def setup_basic_observability(
    app_name: str = "liap-tui",
    log_level: LogLevel = LogLevel.INFO,
    enable_metrics: bool = True,
    enable_tracing: bool = True,
) -> None:
    """
    Set up basic observability with sensible defaults.

    Args:
        app_name: Application name for context
        log_level: Minimum log level
        enable_metrics: Whether to enable metrics collection
        enable_tracing: Whether to enable distributed tracing
    """
    # Configure logging
    configure_logging(
        LogConfig(level=log_level, format=LogFormat.JSON, app_name=app_name)
    )

    # Set up metrics if enabled
    if enable_metrics:
        from .metrics import configure_metrics

        configure_metrics(app_name=app_name)

    # Set up tracing if enabled
    if enable_tracing:
        from .tracing import configure_tracing

        configure_tracing(app_name=app_name)


def get_default_logger(name: str) -> ILogger:
    """Get a logger with default configuration."""
    return get_logger(name)


def get_default_metrics() -> IMetricsCollector:
    """Get the default metrics collector."""
    from .metrics import get_metrics_collector

    return get_metrics_collector()


def get_default_tracer() -> ITracer:
    """Get the default tracer."""
    from .tracing import get_tracer

    return get_tracer()
