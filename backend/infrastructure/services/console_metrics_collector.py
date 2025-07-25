"""
Console-based metrics collector implementation.

This module provides a simple implementation of the MetricsCollector
interface that logs metrics to the console for development.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict, deque

from application.interfaces import MetricsCollector

logger = logging.getLogger(__name__)


class ConsoleMetricsCollector(MetricsCollector):
    """
    Metrics collector that logs to console.
    
    This is a simple implementation for development. In production,
    this would be replaced with Prometheus, StatsD, or similar.
    """
    
    def __init__(self, log_every_n: int = 100):
        """
        Initialize the metrics collector.
        
        Args:
            log_every_n: Log summary every N operations
        """
        self._log_every_n = log_every_n
        self._counters = defaultdict(int)
        self._gauges = {}
        self._histograms = defaultdict(lambda: deque(maxlen=1000))
        self._timings = defaultdict(lambda: deque(maxlen=1000))
        self._operation_count = 0
        
    def increment(
        self,
        metric_name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Amount to increment by
            tags: Optional tags for the metric
        """
        # Create tagged metric name
        full_name = self._create_metric_name(metric_name, tags)
        
        # Increment counter
        self._counters[full_name] += value
        self._operation_count += 1
        
        # Log if threshold reached
        if self._operation_count % self._log_every_n == 0:
            logger.info(f"Metric: {full_name} = {self._counters[full_name]}")
    
    def gauge(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: The gauge value
            tags: Optional tags for the metric
        """
        # Create tagged metric name
        full_name = self._create_metric_name(metric_name, tags)
        
        # Set gauge value
        self._gauges[full_name] = {
            'value': value,
            'timestamp': datetime.utcnow()
        }
        
        # Always log gauge changes
        logger.debug(f"Gauge: {full_name} = {value}")
    
    def histogram(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram metric.
        
        Args:
            metric_name: Name of the metric
            value: The value to record
            tags: Optional tags for the metric
        """
        # Create tagged metric name
        full_name = self._create_metric_name(metric_name, tags)
        
        # Add to histogram
        self._histograms[full_name].append(value)
    
    def timing(
        self,
        metric_name: str,
        duration_ms: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timing metric.
        
        Args:
            metric_name: Name of the metric
            duration_ms: Duration in milliseconds
            tags: Optional tags for the metric
        """
        # Create tagged metric name
        full_name = self._create_metric_name(metric_name, tags)
        
        # Add to timings
        self._timings[full_name].append(duration_ms)
        
        # Log slow operations
        if duration_ms > 1000:  # More than 1 second
            logger.warning(f"Slow operation: {full_name} took {duration_ms}ms")
    
    def _create_metric_name(
        self,
        metric_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a full metric name including tags."""
        if not tags:
            return metric_name
        
        # Sort tags for consistency
        tag_str = ",".join(
            f"{k}={v}" for k, v in sorted(tags.items())
        )
        return f"{metric_name}{{{tag_str}}}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        # Calculate histogram stats
        histogram_stats = {}
        for name, values in self._histograms.items():
            if values:
                sorted_values = sorted(values)
                histogram_stats[name] = {
                    'count': len(values),
                    'min': sorted_values[0],
                    'max': sorted_values[-1],
                    'p50': sorted_values[len(values) // 2],
                    'p95': sorted_values[int(len(values) * 0.95)],
                    'p99': sorted_values[int(len(values) * 0.99)]
                }
        
        # Calculate timing stats
        timing_stats = {}
        for name, durations in self._timings.items():
            if durations:
                sorted_durations = sorted(durations)
                timing_stats[name] = {
                    'count': len(durations),
                    'min_ms': sorted_durations[0],
                    'max_ms': sorted_durations[-1],
                    'p50_ms': sorted_durations[len(durations) // 2],
                    'p95_ms': sorted_durations[int(len(durations) * 0.95)],
                    'p99_ms': sorted_durations[int(len(durations) * 0.99)]
                }
        
        return {
            'counters': dict(self._counters),
            'gauges': self._gauges,
            'histograms': histogram_stats,
            'timings': timing_stats
        }
    
    def log_summary(self):
        """Log a summary of all metrics."""
        stats = self.get_stats()
        
        logger.info("=== Metrics Summary ===")
        
        # Log counters
        logger.info("Counters:")
        for name, value in stats['counters'].items():
            logger.info(f"  {name}: {value}")
        
        # Log gauges
        logger.info("Gauges:")
        for name, data in stats['gauges'].items():
            logger.info(f"  {name}: {data['value']}")
        
        # Log timing summaries
        logger.info("Timings:")
        for name, timing in stats['timings'].items():
            logger.info(
                f"  {name}: count={timing['count']}, "
                f"p50={timing['p50_ms']}ms, p99={timing['p99_ms']}ms"
            )