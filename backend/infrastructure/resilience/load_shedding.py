"""
Load shedding mechanisms for system protection.

Provides adaptive load shedding to prevent system overload.
"""

from typing import Optional, Dict, List, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import asyncio
import time
import logging
import random
from abc import ABC, abstractmethod
import psutil


logger = logging.getLogger(__name__)


class LoadLevel(Enum):
    """System load levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    OVERLOAD = "overload"


class SheddingStrategy(Enum):
    """Load shedding strategies."""

    RANDOM = "random"  # Random request dropping
    PRIORITY = "priority"  # Drop low priority first
    FAIR_QUEUING = "fair_queuing"  # Fair share per client
    ADAPTIVE = "adaptive"  # Adaptive based on metrics


@dataclass
class LoadMetrics:
    """System load metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    request_rate: float = 0.0  # Requests per second
    response_time_p99: float = 0.0  # 99th percentile response time
    error_rate: float = 0.0  # Error percentage
    queue_depth: int = 0  # Pending requests
    active_connections: int = 0

    timestamp: datetime = field(default_factory=datetime.utcnow)

    def get_load_score(self) -> float:
        """Calculate composite load score (0-100)."""
        # Weighted average of metrics
        weights = {
            "cpu": 0.3,
            "memory": 0.2,
            "response_time": 0.2,
            "error_rate": 0.15,
            "queue_depth": 0.15,
        }

        # Normalize metrics to 0-100 scale
        normalized_response_time = min(
            100, self.response_time_p99 * 10
        )  # Assume 10s is max
        normalized_queue = min(100, self.queue_depth / 10)  # Assume 1000 is max

        score = (
            weights["cpu"] * self.cpu_percent
            + weights["memory"] * self.memory_percent
            + weights["response_time"] * normalized_response_time
            + weights["error_rate"] * self.error_rate * 100
            + weights["queue_depth"] * normalized_queue
        )

        return min(100, max(0, score))

    def get_load_level(self) -> LoadLevel:
        """Determine load level from metrics."""
        score = self.get_load_score()

        if score < 30:
            return LoadLevel.LOW
        elif score < 50:
            return LoadLevel.NORMAL
        elif score < 70:
            return LoadLevel.HIGH
        elif score < 85:
            return LoadLevel.CRITICAL
        else:
            return LoadLevel.OVERLOAD


@dataclass
class SheddingConfig:
    """Configuration for load shedding."""

    strategy: SheddingStrategy = SheddingStrategy.ADAPTIVE

    # Thresholds for load levels
    high_threshold: float = 70.0
    critical_threshold: float = 85.0
    overload_threshold: float = 95.0

    # Shedding rates by load level
    shedding_rates: Dict[LoadLevel, float] = field(
        default_factory=lambda: {
            LoadLevel.LOW: 0.0,
            LoadLevel.NORMAL: 0.0,
            LoadLevel.HIGH: 0.1,  # Drop 10%
            LoadLevel.CRITICAL: 0.3,  # Drop 30%
            LoadLevel.OVERLOAD: 0.5,  # Drop 50%
        }
    )

    # Priority levels (higher = more important)
    priority_levels: int = 3

    # Cooldown period after shedding
    cooldown_period: timedelta = timedelta(seconds=5)

    # Metrics update interval
    update_interval: timedelta = timedelta(seconds=1)


@dataclass
class RequestContext:
    """Context for request evaluation."""

    request_id: str
    priority: int = 1  # 1-N, higher is more important
    client_id: Optional[str] = None
    request_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LoadShedder(ABC):
    """Abstract base class for load shedding."""

    @abstractmethod
    def should_accept(self, context: RequestContext) -> bool:
        """Determine if request should be accepted."""
        pass

    @abstractmethod
    def update_metrics(self, metrics: LoadMetrics) -> None:
        """Update load metrics."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get shedding statistics."""
        pass


class AdaptiveLoadShedder(LoadShedder):
    """
    Adaptive load shedder with multiple strategies.

    Dynamically adjusts shedding based on system metrics
    and supports various shedding strategies.
    """

    def __init__(self, config: Optional[SheddingConfig] = None):
        """Initialize adaptive load shedder."""
        self.config = config or SheddingConfig()

        # Current state
        self._current_metrics = LoadMetrics()
        self._current_level = LoadLevel.NORMAL
        self._shedding_rate = 0.0
        self._last_shed_time = datetime.utcnow()

        # Statistics
        self._total_requests = 0
        self._accepted_requests = 0
        self._shed_requests = 0
        self._shed_by_priority: Dict[int, int] = {}

        # Client tracking for fair queuing
        self._client_requests: Dict[str, int] = {}
        self._client_accepts: Dict[str, int] = {}

        # Synchronization
        self._lock = threading.RLock()

        # Start metrics collection
        self._metrics_task = None
        self._running = True
        self._start_metrics_collection()

    def _start_metrics_collection(self) -> None:
        """Start background metrics collection."""

        def collect_metrics():
            while self._running:
                try:
                    # Collect system metrics
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory = psutil.virtual_memory()

                    with self._lock:
                        self._current_metrics.cpu_percent = cpu_percent
                        self._current_metrics.memory_percent = memory.percent
                        self._current_metrics.timestamp = datetime.utcnow()

                        # Update load level
                        self._current_level = self._current_metrics.get_load_level()
                        self._shedding_rate = self.config.shedding_rates.get(
                            self._current_level, 0.0
                        )

                except Exception as e:
                    logger.error(f"Error collecting metrics: {e}")

                time.sleep(self.config.update_interval.total_seconds())

        self._metrics_task = threading.Thread(target=collect_metrics, daemon=True)
        self._metrics_task.start()

    def should_accept(self, context: RequestContext) -> bool:
        """Determine if request should be accepted."""
        with self._lock:
            self._total_requests += 1

            # Track client requests
            if context.client_id:
                self._client_requests[context.client_id] = (
                    self._client_requests.get(context.client_id, 0) + 1
                )

            # Check if in cooldown
            if (datetime.utcnow() - self._last_shed_time) < self.config.cooldown_period:
                # More aggressive during cooldown
                effective_rate = min(1.0, self._shedding_rate * 1.5)
            else:
                effective_rate = self._shedding_rate

            # Apply shedding strategy
            should_shed = self._apply_strategy(context, effective_rate)

            if should_shed:
                self._shed_requests += 1
                self._shed_by_priority[context.priority] = (
                    self._shed_by_priority.get(context.priority, 0) + 1
                )
                self._last_shed_time = datetime.utcnow()

                logger.debug(
                    f"Shed request {context.request_id} "
                    f"(priority={context.priority}, rate={effective_rate:.2f})"
                )
                return False

            # Accept request
            self._accepted_requests += 1
            if context.client_id:
                self._client_accepts[context.client_id] = (
                    self._client_accepts.get(context.client_id, 0) + 1
                )

            return True

    def _apply_strategy(self, context: RequestContext, shedding_rate: float) -> bool:
        """Apply shedding strategy to determine if request should be shed."""
        if shedding_rate <= 0:
            return False

        if self.config.strategy == SheddingStrategy.RANDOM:
            # Random shedding
            return random.random() < shedding_rate

        elif self.config.strategy == SheddingStrategy.PRIORITY:
            # Priority-based shedding
            # Adjust rate based on priority (lower priority = higher shed rate)
            priority_factor = (
                self.config.priority_levels - context.priority + 1
            ) / self.config.priority_levels
            adjusted_rate = shedding_rate * priority_factor
            return random.random() < adjusted_rate

        elif self.config.strategy == SheddingStrategy.FAIR_QUEUING:
            # Fair queuing - limit requests per client
            if not context.client_id:
                return random.random() < shedding_rate

            # Calculate client's fair share
            client_requests = self._client_requests.get(context.client_id, 0)
            client_accepts = self._client_accepts.get(context.client_id, 0)

            if client_requests > 0:
                client_accept_rate = client_accepts / client_requests
                # Shed if client is over fair share
                if client_accept_rate > (1 - shedding_rate):
                    return True

            return random.random() < shedding_rate

        elif self.config.strategy == SheddingStrategy.ADAPTIVE:
            # Adaptive strategy combining multiple factors
            factors = []

            # Priority factor
            priority_factor = (
                self.config.priority_levels - context.priority + 1
            ) / self.config.priority_levels
            factors.append(priority_factor)

            # Request age factor (older requests less likely to be shed)
            age = (datetime.utcnow() - context.timestamp).total_seconds()
            age_factor = 1.0 - min(1.0, age / 10.0)  # 10 seconds max
            factors.append(age_factor)

            # Client fairness factor
            if context.client_id:
                client_requests = self._client_requests.get(context.client_id, 0)
                total_clients = len(self._client_requests)
                if total_clients > 0 and self._total_requests > 0:
                    fair_share = self._total_requests / total_clients
                    client_factor = min(1.0, client_requests / fair_share)
                    factors.append(client_factor)

            # Combine factors
            combined_factor = sum(factors) / len(factors)
            adjusted_rate = shedding_rate * combined_factor

            return random.random() < adjusted_rate

        else:
            # Default to random
            return random.random() < shedding_rate

    def update_metrics(self, metrics: LoadMetrics) -> None:
        """Update load metrics."""
        with self._lock:
            # Update non-system metrics
            self._current_metrics.request_rate = metrics.request_rate
            self._current_metrics.response_time_p99 = metrics.response_time_p99
            self._current_metrics.error_rate = metrics.error_rate
            self._current_metrics.queue_depth = metrics.queue_depth
            self._current_metrics.active_connections = metrics.active_connections

            # Recalculate load level
            self._current_level = self._current_metrics.get_load_level()
            self._shedding_rate = self.config.shedding_rates.get(
                self._current_level, 0.0
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get shedding statistics."""
        with self._lock:
            accept_rate = (
                self._accepted_requests / self._total_requests
                if self._total_requests > 0
                else 1.0
            )

            return {
                "current_level": self._current_level.value,
                "current_rate": self._shedding_rate,
                "load_score": self._current_metrics.get_load_score(),
                "metrics": {
                    "cpu_percent": self._current_metrics.cpu_percent,
                    "memory_percent": self._current_metrics.memory_percent,
                    "request_rate": self._current_metrics.request_rate,
                    "response_time_p99": self._current_metrics.response_time_p99,
                    "error_rate": self._current_metrics.error_rate,
                    "queue_depth": self._current_metrics.queue_depth,
                    "active_connections": self._current_metrics.active_connections,
                },
                "totals": {
                    "requests": self._total_requests,
                    "accepted": self._accepted_requests,
                    "shed": self._shed_requests,
                    "accept_rate": accept_rate,
                },
                "shed_by_priority": dict(self._shed_by_priority),
                "top_clients": sorted(
                    [
                        {
                            "client_id": client_id,
                            "requests": requests,
                            "accepts": self._client_accepts.get(client_id, 0),
                            "accept_rate": self._client_accepts.get(client_id, 0)
                            / requests,
                        }
                        for client_id, requests in self._client_requests.items()
                    ],
                    key=lambda x: x["requests"],
                    reverse=True,
                )[:10],
            }

    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            self._total_requests = 0
            self._accepted_requests = 0
            self._shed_requests = 0
            self._shed_by_priority.clear()
            self._client_requests.clear()
            self._client_accepts.clear()

    def shutdown(self) -> None:
        """Shutdown load shedder."""
        self._running = False
        if self._metrics_task:
            self._metrics_task.join(timeout=5)


# Global load shedder
_load_shedder: Optional[AdaptiveLoadShedder] = None
_lock = threading.RLock()


def get_load_shedder(config: Optional[SheddingConfig] = None) -> AdaptiveLoadShedder:
    """Get global load shedder."""
    global _load_shedder
    with _lock:
        if _load_shedder is None:
            _load_shedder = AdaptiveLoadShedder(config)
        return _load_shedder


# Decorator support


def load_shed(
    priority: int = 1,
    client_id_getter: Optional[Callable] = None,
    request_type: Optional[str] = None,
) -> Callable:
    """
    Decorator for load shedding protection.

    Args:
        priority: Request priority (1-N, higher is more important)
        client_id_getter: Function to extract client ID from args
        request_type: Type of request

    Example:
        @load_shed(priority=2)
        def handle_request(request):
            # Handle request
            pass
    """

    def decorator(func: Callable) -> Callable:
        import functools
        import uuid

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            shedder = get_load_shedder()

            # Extract client ID if getter provided
            client_id = None
            if client_id_getter:
                try:
                    client_id = client_id_getter(*args, **kwargs)
                except Exception:
                    pass

            # Create request context
            context = RequestContext(
                request_id=str(uuid.uuid4()),
                priority=priority,
                client_id=client_id,
                request_type=request_type or func.__name__,
            )

            # Check if should accept
            if not shedder.should_accept(context):
                raise Exception(
                    f"Request shed due to high load (level={shedder._current_level.value})"
                )

            # Execute function
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            shedder = get_load_shedder()

            # Extract client ID if getter provided
            client_id = None
            if client_id_getter:
                try:
                    client_id = client_id_getter(*args, **kwargs)
                except Exception:
                    pass

            # Create request context
            context = RequestContext(
                request_id=str(uuid.uuid4()),
                priority=priority,
                client_id=client_id,
                request_type=request_type or func.__name__,
            )

            # Check if should accept
            if not shedder.should_accept(context):
                raise Exception(
                    f"Request shed due to high load (level={shedder._current_level.value})"
                )

            # Execute function
            return await func(*args, **kwargs)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator
