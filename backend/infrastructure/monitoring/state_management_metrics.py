"""
Metrics and monitoring for state management integration.

This module defines metrics collection for state management operations
to track performance, errors, and usage patterns.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from dataclasses import dataclass
from datetime import datetime

from application.interfaces import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class StateMetrics:
    """Container for state management metrics."""
    
    # Counters
    transitions_tracked: int = 0
    transitions_failed: int = 0
    snapshots_created: int = 0
    snapshots_failed: int = 0
    recoveries_attempted: int = 0
    recoveries_succeeded: int = 0
    validations_failed: int = 0
    
    # Latency tracking
    total_tracking_time_ms: float = 0.0
    total_snapshot_time_ms: float = 0.0
    total_recovery_time_ms: float = 0.0
    
    # Error tracking
    errors_by_type: Dict[str, int] = None
    
    def __post_init__(self):
        if self.errors_by_type is None:
            self.errors_by_type = {}


class StateManagementMetricsCollector:
    """
    Collects and reports metrics for state management operations.
    """
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize metrics collector.
        
        Args:
            metrics_collector: Optional underlying metrics collector
        """
        self._metrics = metrics_collector
        self._local_metrics = StateMetrics()
        self._start_time = datetime.utcnow()
    
    def track_transition(self, success: bool, duration_ms: float, phase_change: bool = False):
        """
        Track a state transition operation.
        
        Args:
            success: Whether the transition was successful
            duration_ms: Duration of the operation in milliseconds
            phase_change: Whether this was a phase change transition
        """
        if success:
            self._local_metrics.transitions_tracked += 1
            self._local_metrics.total_tracking_time_ms += duration_ms
            
            if self._metrics:
                self._metrics.increment(
                    "state_management.transition.success",
                    tags={"phase_change": str(phase_change).lower()}
                )
                self._metrics.histogram(
                    "state_management.transition.duration_ms",
                    duration_ms,
                    tags={"phase_change": str(phase_change).lower()}
                )
        else:
            self._local_metrics.transitions_failed += 1
            
            if self._metrics:
                self._metrics.increment(
                    "state_management.transition.failure",
                    tags={"phase_change": str(phase_change).lower()}
                )
    
    def track_snapshot(self, success: bool, duration_ms: float, trigger: str = "manual"):
        """
        Track a snapshot creation operation.
        
        Args:
            success: Whether the snapshot was successful
            duration_ms: Duration of the operation in milliseconds
            trigger: What triggered the snapshot
        """
        if success:
            self._local_metrics.snapshots_created += 1
            self._local_metrics.total_snapshot_time_ms += duration_ms
            
            if self._metrics:
                self._metrics.increment(
                    "state_management.snapshot.success",
                    tags={"trigger": trigger}
                )
                self._metrics.histogram(
                    "state_management.snapshot.duration_ms",
                    duration_ms,
                    tags={"trigger": trigger}
                )
        else:
            self._local_metrics.snapshots_failed += 1
            
            if self._metrics:
                self._metrics.increment(
                    "state_management.snapshot.failure",
                    tags={"trigger": trigger}
                )
    
    def track_recovery(self, success: bool, duration_ms: float, recovery_type: str = "full"):
        """
        Track a state recovery operation.
        
        Args:
            success: Whether the recovery was successful
            duration_ms: Duration of the operation in milliseconds
            recovery_type: Type of recovery performed
        """
        self._local_metrics.recoveries_attempted += 1
        
        if success:
            self._local_metrics.recoveries_succeeded += 1
            self._local_metrics.total_recovery_time_ms += duration_ms
            
            if self._metrics:
                self._metrics.increment(
                    "state_management.recovery.success",
                    tags={"type": recovery_type}
                )
                self._metrics.histogram(
                    "state_management.recovery.duration_ms",
                    duration_ms,
                    tags={"type": recovery_type}
                )
        else:
            if self._metrics:
                self._metrics.increment(
                    "state_management.recovery.failure",
                    tags={"type": recovery_type}
                )
    
    def track_validation_failure(self, validation_type: str, reason: str):
        """
        Track a validation failure.
        
        Args:
            validation_type: Type of validation that failed
            reason: Reason for the failure
        """
        self._local_metrics.validations_failed += 1
        
        if self._metrics:
            self._metrics.increment(
                "state_management.validation.failure",
                tags={
                    "type": validation_type,
                    "reason": reason[:50]  # Truncate long reasons
                }
            )
    
    def track_error(self, error_type: str, operation: str):
        """
        Track an error occurrence.
        
        Args:
            error_type: Type of error
            operation: Operation that failed
        """
        if error_type not in self._local_metrics.errors_by_type:
            self._local_metrics.errors_by_type[error_type] = 0
        self._local_metrics.errors_by_type[error_type] += 1
        
        if self._metrics:
            self._metrics.increment(
                "state_management.error",
                tags={
                    "error_type": error_type,
                    "operation": operation
                }
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.
        
        Returns:
            Dictionary of metric summaries
        """
        uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
        
        # Calculate averages
        avg_tracking_ms = 0
        if self._local_metrics.transitions_tracked > 0:
            avg_tracking_ms = (
                self._local_metrics.total_tracking_time_ms / 
                self._local_metrics.transitions_tracked
            )
        
        avg_snapshot_ms = 0
        if self._local_metrics.snapshots_created > 0:
            avg_snapshot_ms = (
                self._local_metrics.total_snapshot_time_ms / 
                self._local_metrics.snapshots_created
            )
        
        recovery_success_rate = 0
        if self._local_metrics.recoveries_attempted > 0:
            recovery_success_rate = (
                self._local_metrics.recoveries_succeeded / 
                self._local_metrics.recoveries_attempted * 100
            )
        
        return {
            "uptime_seconds": uptime_seconds,
            "transitions": {
                "tracked": self._local_metrics.transitions_tracked,
                "failed": self._local_metrics.transitions_failed,
                "success_rate": self._calculate_success_rate(
                    self._local_metrics.transitions_tracked,
                    self._local_metrics.transitions_failed
                ),
                "avg_duration_ms": avg_tracking_ms
            },
            "snapshots": {
                "created": self._local_metrics.snapshots_created,
                "failed": self._local_metrics.snapshots_failed,
                "success_rate": self._calculate_success_rate(
                    self._local_metrics.snapshots_created,
                    self._local_metrics.snapshots_failed
                ),
                "avg_duration_ms": avg_snapshot_ms
            },
            "recoveries": {
                "attempted": self._local_metrics.recoveries_attempted,
                "succeeded": self._local_metrics.recoveries_succeeded,
                "success_rate": recovery_success_rate
            },
            "validations_failed": self._local_metrics.validations_failed,
            "errors": self._local_metrics.errors_by_type
        }
    
    def _calculate_success_rate(self, success_count: int, failure_count: int) -> float:
        """Calculate success rate percentage."""
        total = success_count + failure_count
        if total == 0:
            return 100.0
        return (success_count / total) * 100


def track_state_operation(
    operation_type: str,
    metrics_collector: Optional[StateManagementMetricsCollector] = None
) -> Callable:
    """
    Decorator to track state management operations.
    
    Args:
        operation_type: Type of operation (transition, snapshot, recovery)
        metrics_collector: Optional metrics collector instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                if metrics_collector:
                    metrics_collector.track_error(
                        type(e).__name__,
                        operation_type
                    )
                raise
                
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                if metrics_collector:
                    if operation_type == "transition":
                        phase_change = kwargs.get("phase_change", False)
                        metrics_collector.track_transition(success, duration_ms, phase_change)
                    elif operation_type == "snapshot":
                        trigger = kwargs.get("trigger", "manual")
                        metrics_collector.track_snapshot(success, duration_ms, trigger)
                    elif operation_type == "recovery":
                        recovery_type = kwargs.get("recovery_type", "full")
                        metrics_collector.track_recovery(success, duration_ms, recovery_type)
        
        return wrapper
    return decorator


# Global metrics instance
_metrics_collector: Optional[StateManagementMetricsCollector] = None


def get_state_metrics_collector() -> StateManagementMetricsCollector:
    """Get the global state metrics collector."""
    global _metrics_collector
    
    if _metrics_collector is None:
        # Try to get the main metrics collector
        try:
            from infrastructure.dependencies import get_metrics_collector
            main_metrics = get_metrics_collector()
        except:
            main_metrics = None
        
        _metrics_collector = StateManagementMetricsCollector(main_metrics)
    
    return _metrics_collector


def reset_state_metrics():
    """Reset the global state metrics (mainly for testing)."""
    global _metrics_collector
    _metrics_collector = None