"""
Metrics collection and export infrastructure.

Provides flexible metrics collection with support for various metric types
and export formats.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import asyncio
from collections import defaultdict, deque
import threading
from contextlib import contextmanager
from functools import wraps
import json


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Similar to histogram with percentiles
    TIMER = "timer"  # Duration measurements


class MetricUnit(Enum):
    """Units for metric values."""

    NONE = "none"
    BYTES = "bytes"
    KILOBYTES = "kilobytes"
    MEGABYTES = "megabytes"
    GIGABYTES = "gigabytes"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    MICROSECONDS = "microseconds"
    PERCENTAGE = "percentage"
    COUNT = "count"
    REQUESTS = "requests"
    ERRORS = "errors"
    CONNECTIONS = "connections"


@dataclass
class MetricTag:
    """Tag for metric categorization."""

    key: str
    value: str


@dataclass
class MetricValue:
    """A single metric measurement."""

    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: List[MetricTag] = field(default_factory=list)


@dataclass
class MetricConfig:
    """Configuration for metrics collection."""

    prefix: str = "app"
    default_tags: List[MetricTag] = field(default_factory=list)
    histogram_buckets: List[float] = field(
        default_factory=lambda: [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1,
            2.5,
            5,
            10,
        ]
    )
    summary_percentiles: List[float] = field(
        default_factory=lambda: [0.5, 0.9, 0.95, 0.99]
    )
    export_interval: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    retention_period: timedelta = field(default_factory=lambda: timedelta(hours=24))


class IMetricsCollector(ABC):
    """Interface for metrics collection."""

    @abstractmethod
    def increment(
        self, name: str, value: float = 1, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Increment a counter metric."""
        pass

    @abstractmethod
    def gauge(
        self, name: str, value: float, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Set a gauge metric."""
        pass

    @abstractmethod
    def histogram(
        self, name: str, value: float, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Record a histogram value."""
        pass

    @abstractmethod
    def timer(
        self, name: str, duration: float, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Record a timer duration."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        pass


class IMetricsExporter(ABC):
    """Interface for exporting metrics."""

    @abstractmethod
    async def export(self, metrics: Dict[str, Any]) -> None:
        """Export metrics to external system."""
        pass


class InMemoryMetricsCollector(IMetricsCollector):
    """
    In-memory metrics collector with aggregation.

    Features:
    - Thread-safe collection
    - Automatic aggregation
    - Configurable retention
    - Multiple metric types
    """

    def __init__(self, config: MetricConfig):
        """Initialize metrics collector."""
        self.config = config
        self._lock = threading.RLock()

        # Storage for different metric types
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, MetricValue] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)

        # Time series data for retention
        self._time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup()

    def increment(
        self, name: str, value: float = 1, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Increment a counter metric."""
        metric_name = self._build_name(name, tags)

        with self._lock:
            self._counters[metric_name] += value
            self._record_time_series(metric_name, value, MetricType.COUNTER)

    def gauge(
        self, name: str, value: float, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Set a gauge metric."""
        metric_name = self._build_name(name, tags)

        with self._lock:
            self._gauges[metric_name] = MetricValue(
                value=value, tags=self._merge_tags(tags)
            )
            self._record_time_series(metric_name, value, MetricType.GAUGE)

    def histogram(
        self, name: str, value: float, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Record a histogram value."""
        metric_name = self._build_name(name, tags)

        with self._lock:
            self._histograms[metric_name].append(value)
            self._record_time_series(metric_name, value, MetricType.HISTOGRAM)

    def timer(
        self, name: str, duration: float, tags: Optional[List[MetricTag]] = None
    ) -> None:
        """Record a timer duration."""
        metric_name = self._build_name(name, tags)

        with self._lock:
            self._timers[metric_name].append(duration)
            self._record_time_series(metric_name, duration, MetricType.TIMER)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics with aggregations."""
        with self._lock:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "counters": dict(self._counters),
                "gauges": {
                    name: {"value": mv.value, "timestamp": mv.timestamp.isoformat()}
                    for name, mv in self._gauges.items()
                },
                "histograms": {
                    name: self._calculate_histogram_stats(values)
                    for name, values in self._histograms.items()
                },
                "timers": {
                    name: self._calculate_timer_stats(values)
                    for name, values in self._timers.items()
                },
            }

            return metrics

    def _build_name(self, name: str, tags: Optional[List[MetricTag]] = None) -> str:
        """Build full metric name with tags."""
        full_name = f"{self.config.prefix}.{name}"

        if tags:
            tag_str = ",".join(f"{t.key}={t.value}" for t in tags)
            full_name = f"{full_name},{tag_str}"

        return full_name

    def _merge_tags(self, tags: Optional[List[MetricTag]] = None) -> List[MetricTag]:
        """Merge provided tags with default tags."""
        merged = self.config.default_tags.copy()

        if tags:
            # Override defaults with provided tags
            tag_dict = {t.key: t.value for t in merged}
            for tag in tags:
                tag_dict[tag.key] = tag.value

            merged = [MetricTag(k, v) for k, v in tag_dict.items()]

        return merged

    def _record_time_series(
        self, name: str, value: float, metric_type: MetricType
    ) -> None:
        """Record value in time series for retention."""
        entry = {
            "timestamp": datetime.utcnow(),
            "value": value,
            "type": metric_type.value,
        }
        self._time_series[name].append(entry)

    def _calculate_histogram_stats(self, values: List[float]) -> Dict[str, Any]:
        """Calculate histogram statistics."""
        if not values:
            return {"count": 0, "sum": 0, "mean": 0, "min": 0, "max": 0, "buckets": {}}

        sorted_values = sorted(values)

        # Calculate buckets
        buckets = {}
        for bucket in self.config.histogram_buckets:
            count = sum(1 for v in values if v <= bucket)
            buckets[str(bucket)] = count

        # Calculate percentiles
        percentiles = {}
        for p in self.config.summary_percentiles:
            idx = int(len(sorted_values) * p)
            percentiles[f"p{int(p * 100)}"] = sorted_values[
                min(idx, len(sorted_values) - 1)
            ]

        return {
            "count": len(values),
            "sum": sum(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "buckets": buckets,
            "percentiles": percentiles,
        }

    def _calculate_timer_stats(self, durations: List[float]) -> Dict[str, Any]:
        """Calculate timer statistics."""
        stats = self._calculate_histogram_stats(durations)

        # Add rate calculation
        if durations:
            stats["rate"] = len(durations) / (
                (
                    datetime.utcnow()
                    - self._time_series[f"{self.config.prefix}.timer"][0]["timestamp"]
                ).total_seconds()
            )
        else:
            stats["rate"] = 0

        return stats

    def _start_cleanup(self) -> None:
        """Start background cleanup task."""

        def cleanup_loop():
            while True:
                time.sleep(self.config.retention_period.total_seconds() / 10)
                self._cleanup_old_data()

        self._cleanup_task = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_task.start()

    def _cleanup_old_data(self) -> None:
        """Clean up old time series data."""
        cutoff_time = datetime.utcnow() - self.config.retention_period

        with self._lock:
            # Clean up time series
            for name, series in self._time_series.items():
                while series and series[0]["timestamp"] < cutoff_time:
                    series.popleft()

            # Clean up histogram and timer data
            # In production, would implement sliding window


class PrometheusMetricsCollector(InMemoryMetricsCollector):
    """
    Metrics collector with Prometheus format export.

    Formats metrics in Prometheus exposition format.
    """

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        lines = []
        metrics = self.get_metrics()

        # Counters
        for name, value in metrics["counters"].items():
            clean_name = name.replace(".", "_").replace(",", "_")
            lines.append(f"# TYPE {clean_name} counter")
            lines.append(f"{clean_name} {value}")

        # Gauges
        for name, data in metrics["gauges"].items():
            clean_name = name.replace(".", "_").replace(",", "_")
            lines.append(f"# TYPE {clean_name} gauge")
            lines.append(f"{clean_name} {data['value']}")

        # Histograms
        for name, stats in metrics["histograms"].items():
            clean_name = name.replace(".", "_").replace(",", "_")
            lines.append(f"# TYPE {clean_name} histogram")

            # Buckets
            for bucket, count in stats["buckets"].items():
                lines.append(f'{clean_name}_bucket{{le="{bucket}"}} {count}')

            lines.append(f'{clean_name}_bucket{{le="+Inf"}} {stats["count"]}')
            lines.append(f'{clean_name}_sum {stats["sum"]}')
            lines.append(f'{clean_name}_count {stats["count"]}')

        return "\n".join(lines)


# Metric utilities


class Counter:
    """Counter metric helper."""

    def __init__(
        self,
        collector: IMetricsCollector,
        name: str,
        tags: Optional[List[MetricTag]] = None,
    ):
        """Initialize counter."""
        self.collector = collector
        self.name = name
        self.tags = tags or []

    def increment(self, value: float = 1) -> None:
        """Increment the counter."""
        self.collector.increment(self.name, value, self.tags)

    def with_tags(self, **kwargs) -> "Counter":
        """Create a new counter with additional tags."""
        new_tags = self.tags.copy()
        new_tags.extend(MetricTag(k, str(v)) for k, v in kwargs.items())
        return Counter(self.collector, self.name, new_tags)


class Gauge:
    """Gauge metric helper."""

    def __init__(
        self,
        collector: IMetricsCollector,
        name: str,
        tags: Optional[List[MetricTag]] = None,
    ):
        """Initialize gauge."""
        self.collector = collector
        self.name = name
        self.tags = tags or []

    def set(self, value: float) -> None:
        """Set the gauge value."""
        self.collector.gauge(self.name, value, self.tags)

    def increment(self, delta: float = 1) -> None:
        """Increment gauge value."""
        # Note: In production, would track current value
        self.collector.gauge(self.name, delta, self.tags)

    def decrement(self, delta: float = 1) -> None:
        """Decrement gauge value."""
        self.increment(-delta)


class Histogram:
    """Histogram metric helper."""

    def __init__(
        self,
        collector: IMetricsCollector,
        name: str,
        tags: Optional[List[MetricTag]] = None,
    ):
        """Initialize histogram."""
        self.collector = collector
        self.name = name
        self.tags = tags or []

    def observe(self, value: float) -> None:
        """Record an observation."""
        self.collector.histogram(self.name, value, self.tags)


class Timer:
    """Timer metric helper with context manager support."""

    def __init__(
        self,
        collector: IMetricsCollector,
        name: str,
        tags: Optional[List[MetricTag]] = None,
    ):
        """Initialize timer."""
        self.collector = collector
        self.name = name
        self.tags = tags or []
        self._start_time = None

    @contextmanager
    def time(self):
        """Context manager for timing."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.collector.timer(self.name, duration, self.tags)

    def start(self) -> None:
        """Start timing."""
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timing and record."""
        if self._start_time is None:
            raise ValueError("Timer not started")

        duration = time.perf_counter() - self._start_time
        self.collector.timer(self.name, duration, self.tags)
        self._start_time = None

        return duration


# Global metrics configuration
_metrics_collector: Optional[IMetricsCollector] = None


def configure_metrics(
    app_name: str = "app", config: Optional[MetricConfig] = None
) -> None:
    """Configure global metrics collection."""
    global _metrics_collector

    if config is None:
        config = MetricConfig(prefix=app_name)

    _metrics_collector = PrometheusMetricsCollector(config)


def get_metrics_collector() -> IMetricsCollector:
    """Get the global metrics collector."""
    if _metrics_collector is None:
        configure_metrics()

    return _metrics_collector


# Decorators for metrics


def track_metrics(
    name: str, record_args: bool = False, record_result: bool = False
) -> Callable:
    """
    Decorator to track function metrics.

    Args:
        name: Metric name
        record_args: Whether to record arguments as tags
        record_result: Whether to record result size
    """

    def decorator(func: Callable) -> Callable:
        collector = get_metrics_collector()

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Track call count
            counter = Counter(collector, f"{name}.calls")
            counter.increment()

            # Track timing
            timer = Timer(collector, f"{name}.duration")

            try:
                with timer.time():
                    result = await func(*args, **kwargs)

                # Track success
                Counter(collector, f"{name}.success").increment()

                return result

            except Exception as e:
                # Track errors
                error_counter = Counter(collector, f"{name}.errors").with_tags(
                    error_type=type(e).__name__
                )
                error_counter.increment()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Track call count
            counter = Counter(collector, f"{name}.calls")
            counter.increment()

            # Track timing
            timer = Timer(collector, f"{name}.duration")

            try:
                with timer.time():
                    result = func(*args, **kwargs)

                # Track success
                Counter(collector, f"{name}.success").increment()

                return result

            except Exception as e:
                # Track errors
                error_counter = Counter(collector, f"{name}.errors").with_tags(
                    error_type=type(e).__name__
                )
                error_counter.increment()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def measure_time(name: str) -> Timer:
    """
    Create a timer for manual time measurement.

    Example:
        timer = measure_time("database.query")
        timer.start()
        # ... do work ...
        timer.stop()
    """
    return Timer(get_metrics_collector(), name)
