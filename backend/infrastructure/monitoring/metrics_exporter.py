"""
Metrics exporter for state persistence monitoring.

This module exports state management metrics in Prometheus format
for monitoring and alerting.
"""

import time
import logging
from typing import Dict, Optional, Callable, Any
from functools import wraps
from contextlib import contextmanager
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily

logger = logging.getLogger(__name__)

# Create a custom registry for state metrics
state_registry = CollectorRegistry()

# Define metrics
state_transitions_total = Counter(
    "state_transitions_total",
    "Total number of state transitions",
    ["game_id", "from_phase", "to_phase", "success"],
    registry=state_registry
)

state_snapshots_total = Counter(
    "state_snapshots_total",
    "Total number of state snapshots created",
    ["game_id", "trigger", "success"],
    registry=state_registry
)

state_recoveries_total = Counter(
    "state_recoveries_total",
    "Total number of state recovery attempts",
    ["game_id", "recovery_type", "success"],
    registry=state_registry
)

state_operation_duration_ms = Histogram(
    "state_operation_duration_ms",
    "Duration of state operations in milliseconds",
    ["operation", "storage_backend"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
    registry=state_registry
)

state_cache_operations = Counter(
    "state_cache_operations",
    "Cache operations for state management",
    ["operation", "hit"],
    registry=state_registry
)

state_storage_size_bytes = Gauge(
    "state_storage_size_bytes",
    "Size of state storage in bytes",
    ["storage_type", "game_id"],
    registry=state_registry
)

active_games_with_state = Gauge(
    "active_games_with_state",
    "Number of active games with state persistence",
    ["phase"],
    registry=state_registry
)

state_errors_total = Counter(
    "state_errors_total",
    "Total number of state management errors",
    ["operation", "error_type"],
    registry=state_registry
)

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["component"],
    registry=state_registry
)

# Additional detailed metrics
state_validation_errors = Counter(
    "state_validation_errors_total",
    "State validation errors by type",
    ["validation_type", "phase"],
    registry=state_registry
)

state_compression_ratio = Summary(
    "state_compression_ratio",
    "Compression ratio for state snapshots",
    ["compression_type"],
    registry=state_registry
)

state_persistence_info = Info(
    "state_persistence",
    "State persistence configuration info",
    registry=state_registry
)


class StateMetricsExporter:
    """Exports state management metrics."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize the exporter."""
        self.registry = registry or state_registry
        self._last_export = time.time()
        
    def track_transition(
        self,
        game_id: str,
        from_phase: str,
        to_phase: str,
        success: bool = True
    ):
        """Track a state transition."""
        state_transitions_total.labels(
            game_id=game_id,
            from_phase=from_phase,
            to_phase=to_phase,
            success=str(success).lower()
        ).inc()
        
    def track_snapshot(
        self,
        game_id: str,
        trigger: str,
        success: bool = True,
        compression_ratio: Optional[float] = None
    ):
        """Track snapshot creation."""
        state_snapshots_total.labels(
            game_id=game_id,
            trigger=trigger,
            success=str(success).lower()
        ).inc()
        
        if compression_ratio is not None:
            state_compression_ratio.labels(
                compression_type="gzip"
            ).observe(compression_ratio)
            
    def track_recovery(
        self,
        game_id: str,
        recovery_type: str,
        success: bool = True
    ):
        """Track recovery attempt."""
        state_recoveries_total.labels(
            game_id=game_id,
            recovery_type=recovery_type,
            success=str(success).lower()
        ).inc()
        
    @contextmanager
    def track_operation(self, operation: str, storage_backend: str = "redis"):
        """Context manager to track operation duration."""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            state_operation_duration_ms.labels(
                operation=operation,
                storage_backend=storage_backend
            ).observe(duration_ms)
            
    def track_cache_operation(self, operation: str, hit: bool):
        """Track cache operation."""
        state_cache_operations.labels(
            operation=operation,
            hit=str(hit).lower()
        ).inc()
        
    def update_storage_size(self, storage_type: str, game_id: str, size_bytes: int):
        """Update storage size metric."""
        state_storage_size_bytes.labels(
            storage_type=storage_type,
            game_id=game_id
        ).set(size_bytes)
        
    def update_active_games(self, phase_counts: Dict[str, int]):
        """Update active games by phase."""
        for phase, count in phase_counts.items():
            active_games_with_state.labels(phase=phase).set(count)
            
    def track_error(self, operation: str, error_type: str):
        """Track an error."""
        state_errors_total.labels(
            operation=operation,
            error_type=error_type
        ).inc()
        
    def update_circuit_breaker(self, component: str, state: int):
        """Update circuit breaker state."""
        circuit_breaker_state.labels(component=component).set(state)
        
    def track_validation_error(self, validation_type: str, phase: str):
        """Track validation error."""
        state_validation_errors.labels(
            validation_type=validation_type,
            phase=phase
        ).inc()
        
    def set_configuration_info(self, config: Dict[str, str]):
        """Set configuration information."""
        state_persistence_info.info(config)
        
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format."""
        return generate_latest(self.registry)
        
    def get_content_type(self) -> str:
        """Get the content type for metrics."""
        return CONTENT_TYPE_LATEST


# Decorator for automatic metric tracking
def track_state_operation(operation: str, storage_backend: str = "redis"):
    """Decorator to track state operation metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            success = True
            error_type = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_type = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                
                # Track duration
                state_operation_duration_ms.labels(
                    operation=operation,
                    storage_backend=storage_backend
                ).observe(duration_ms)
                
                # Track errors
                if not success and error_type:
                    state_errors_total.labels(
                        operation=operation,
                        error_type=error_type
                    ).inc()
                    
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            success = True
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_type = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                
                # Track duration
                state_operation_duration_ms.labels(
                    operation=operation,
                    storage_backend=storage_backend
                ).observe(duration_ms)
                
                # Track errors
                if not success and error_type:
                    state_errors_total.labels(
                        operation=operation,
                        error_type=error_type
                    ).inc()
                    
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


# Custom collector for dynamic metrics
class StateManagementCollector:
    """Custom collector for dynamic state management metrics."""
    
    def __init__(self, state_manager):
        """Initialize with state manager reference."""
        self.state_manager = state_manager
        
    def collect(self):
        """Collect current metrics."""
        # Collect active game states
        try:
            phase_counts = self.state_manager.get_active_games_by_phase()
            for phase, count in phase_counts.items():
                yield GaugeMetricFamily(
                    "state_active_games_dynamic",
                    "Active games by phase (dynamic)",
                    value=count,
                    labels={"phase": phase}
                )
        except Exception as e:
            logger.error(f"Failed to collect active games: {e}")
            
        # Collect storage metrics
        try:
            storage_stats = self.state_manager.get_storage_statistics()
            yield GaugeMetricFamily(
                "state_storage_utilization_percent",
                "Storage utilization percentage",
                value=storage_stats.get("utilization_percent", 0)
            )
            
            yield GaugeMetricFamily(
                "state_storage_total_bytes",
                "Total storage size in bytes",
                value=storage_stats.get("total_bytes", 0)
            )
        except Exception as e:
            logger.error(f"Failed to collect storage stats: {e}")
            
        # Collect cache metrics
        try:
            cache_stats = self.state_manager.get_cache_statistics()
            if cache_stats:
                yield GaugeMetricFamily(
                    "state_cache_hit_rate",
                    "Cache hit rate",
                    value=cache_stats.get("hit_rate", 0)
                )
                
                yield GaugeMetricFamily(
                    "state_cache_size_entries",
                    "Number of entries in cache",
                    value=cache_stats.get("size", 0)
                )
        except Exception as e:
            logger.error(f"Failed to collect cache stats: {e}")


# Global exporter instance
_exporter: Optional[StateMetricsExporter] = None


def get_metrics_exporter() -> StateMetricsExporter:
    """Get the global metrics exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = StateMetricsExporter()
    return _exporter


def register_state_manager(state_manager):
    """Register state manager for dynamic metrics collection."""
    collector = StateManagementCollector(state_manager)
    state_registry.register(collector)


# Flask/FastAPI integration helpers
def create_metrics_endpoint(app, path: str = "/metrics"):
    """Create metrics endpoint for web framework."""
    exporter = get_metrics_exporter()
    
    if hasattr(app, "route"):  # Flask-like
        @app.route(path)
        def metrics():
            return exporter.export_metrics(), 200, {
                "Content-Type": exporter.get_content_type()
            }
    elif hasattr(app, "get"):  # FastAPI-like
        @app.get(path)
        async def metrics():
            from fastapi.responses import Response
            return Response(
                content=exporter.export_metrics(),
                media_type=exporter.get_content_type()
            )
    else:
        raise ValueError("Unsupported web framework")


# Example usage for testing
if __name__ == "__main__":
    # Test metric tracking
    exporter = get_metrics_exporter()
    
    # Set configuration
    exporter.set_configuration_info({
        "strategy": "hybrid",
        "snapshot_enabled": "true",
        "backend": "redis"
    })
    
    # Track some operations
    with exporter.track_operation("save_state"):
        time.sleep(0.01)  # Simulate work
        
    exporter.track_transition("game-123", "PREPARATION", "DECLARATION", True)
    exporter.track_snapshot("game-123", "scheduled", True, 0.65)
    exporter.track_cache_operation("get", True)
    exporter.track_error("load_state", "ValidationError")
    
    # Update gauges
    exporter.update_active_games({
        "PREPARATION": 150,
        "DECLARATION": 75,
        "TURN": 200,
        "GAME_OVER": 50
    })
    
    exporter.update_circuit_breaker("state_management", 0)  # Closed
    
    # Export metrics
    print(exporter.export_metrics().decode())