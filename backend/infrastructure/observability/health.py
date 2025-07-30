"""
Health check framework for monitoring system components.

Provides extensible health checks with detailed status reporting.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import time
import psutil
import os
from pathlib import Path


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of system components."""

    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    EXTERNAL_API = "external_api"
    DISK_SPACE = "disk_space"
    MEMORY = "memory"
    CPU = "cpu"
    CUSTOM = "custom"


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""

    timeout_seconds: float = 5.0
    interval_seconds: float = 30.0
    failure_threshold: int = 3
    success_threshold: int = 1
    include_details: bool = True
    include_metrics: bool = True


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    component_type: ComponentType
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "component_type": self.component_type.value,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.message:
            result["message"] = self.message
        if self.details:
            result["details"] = self.details
        if self.metrics:
            result["metrics"] = self.metrics
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.error:
            result["error"] = self.error

        return result


class IHealthCheck(ABC):
    """Interface for health checks."""

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """Perform health check."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get health check name."""
        pass

    @abstractmethod
    def get_component_type(self) -> ComponentType:
        """Get component type."""
        pass


class IHealthCheckRegistry(ABC):
    """Interface for health check registry."""

    @abstractmethod
    def register(self, health_check: IHealthCheck) -> None:
        """Register a health check."""
        pass

    @abstractmethod
    def unregister(self, name: str) -> None:
        """Unregister a health check."""
        pass

    @abstractmethod
    async def check_all(self) -> List[HealthCheckResult]:
        """Run all health checks."""
        pass

    @abstractmethod
    async def check_component(
        self, component_type: ComponentType
    ) -> List[HealthCheckResult]:
        """Run health checks for specific component type."""
        pass


class BaseHealthCheck(IHealthCheck):
    """Base implementation for health checks."""

    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize health check."""
        self.name = name
        self.component_type = component_type
        self.config = config or HealthCheckConfig()

    def get_name(self) -> str:
        """Get health check name."""
        return self.name

    def get_component_type(self) -> ComponentType:
        """Get component type."""
        return self.component_type

    async def check(self) -> HealthCheckResult:
        """Perform health check with timeout."""
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self._perform_check(), timeout=self.config.timeout_seconds
            )

            # Add duration
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms

            return result

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                component_type=self.component_type,
                message="Health check timed out",
                error=f"Timeout after {self.config.timeout_seconds}s",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                component_type=self.component_type,
                message="Health check failed",
                error=str(e),
                duration_ms=duration_ms,
            )

    @abstractmethod
    async def _perform_check(self) -> HealthCheckResult:
        """Perform the actual health check."""
        pass


class HealthCheckRegistry(IHealthCheckRegistry):
    """
    Registry for managing health checks.

    Features:
    - Concurrent health check execution
    - Result caching
    - Automatic retries
    """

    def __init__(self, config: Optional[HealthCheckConfig] = None):
        """Initialize registry."""
        self.config = config or HealthCheckConfig()
        self._checks: Dict[str, IHealthCheck] = {}
        self._cache: Dict[str, HealthCheckResult] = {}
        self._lock = asyncio.Lock()

    def register(self, health_check: IHealthCheck) -> None:
        """Register a health check."""
        self._checks[health_check.get_name()] = health_check

    def unregister(self, name: str) -> None:
        """Unregister a health check."""
        self._checks.pop(name, None)
        self._cache.pop(name, None)

    async def check_all(self) -> List[HealthCheckResult]:
        """Run all health checks concurrently."""
        checks = list(self._checks.values())

        # Run checks concurrently
        tasks = [check.check() for check in checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result
                check = checks[i]
                processed_results.append(
                    HealthCheckResult(
                        name=check.get_name(),
                        status=HealthStatus.UNHEALTHY,
                        component_type=check.get_component_type(),
                        message="Health check failed",
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)
                # Cache result
                async with self._lock:
                    self._cache[result.name] = result

        return processed_results

    async def check_component(
        self, component_type: ComponentType
    ) -> List[HealthCheckResult]:
        """Run health checks for specific component type."""
        checks = [
            check
            for check in self._checks.values()
            if check.get_component_type() == component_type
        ]

        tasks = [check.check() for check in checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                check = checks[i]
                processed_results.append(
                    HealthCheckResult(
                        name=check.get_name(),
                        status=HealthStatus.UNHEALTHY,
                        component_type=check.get_component_type(),
                        message="Health check failed",
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    def get_cached_results(self) -> List[HealthCheckResult]:
        """Get cached results."""
        return list(self._cache.values())

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self._cache:
            return HealthStatus.UNKNOWN

        statuses = [result.status for result in self._cache.values()]

        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class CompositeHealthCheck(BaseHealthCheck):
    """
    Composite health check that combines multiple checks.

    Useful for checking related components together.
    """

    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        checks: List[IHealthCheck],
        config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize composite health check."""
        super().__init__(name, component_type, config)
        self.checks = checks

    async def _perform_check(self) -> HealthCheckResult:
        """Perform all sub-checks."""
        # Run checks concurrently
        tasks = [check.check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        sub_results = []
        overall_status = HealthStatus.HEALTHY
        messages = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                sub_results.append(
                    {
                        "name": self.checks[i].get_name(),
                        "status": HealthStatus.UNHEALTHY.value,
                        "error": str(result),
                    }
                )
                overall_status = HealthStatus.UNHEALTHY
                messages.append(f"{self.checks[i].get_name()}: {result}")
            else:
                sub_results.append(result.to_dict())

                if result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif (
                    result.status == HealthStatus.DEGRADED
                    and overall_status == HealthStatus.HEALTHY
                ):
                    overall_status = HealthStatus.DEGRADED

                if result.message:
                    messages.append(f"{result.name}: {result.message}")

        return HealthCheckResult(
            name=self.name,
            status=overall_status,
            component_type=self.component_type,
            message="; ".join(messages) if messages else None,
            details={"sub_checks": sub_results},
        )


# Built-in health checks


class DiskSpaceHealthCheck(BaseHealthCheck):
    """Health check for disk space."""

    def __init__(
        self,
        name: str = "disk_space",
        path: str = "/",
        warning_threshold_gb: float = 5.0,
        critical_threshold_gb: float = 1.0,
        config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize disk space health check."""
        super().__init__(name, ComponentType.DISK_SPACE, config)
        self.path = path
        self.warning_threshold_gb = warning_threshold_gb
        self.critical_threshold_gb = critical_threshold_gb

    async def _perform_check(self) -> HealthCheckResult:
        """Check disk space."""
        usage = psutil.disk_usage(self.path)

        free_gb = usage.free / (1024**3)
        used_percent = usage.percent

        if free_gb < self.critical_threshold_gb:
            status = HealthStatus.UNHEALTHY
            message = f"Critical: Only {free_gb:.2f}GB free"
        elif free_gb < self.warning_threshold_gb:
            status = HealthStatus.DEGRADED
            message = f"Warning: Only {free_gb:.2f}GB free"
        else:
            status = HealthStatus.HEALTHY
            message = f"{free_gb:.2f}GB free"

        return HealthCheckResult(
            name=self.name,
            status=status,
            component_type=self.component_type,
            message=message,
            details={
                "path": self.path,
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": free_gb,
                "used_percent": used_percent,
            },
            metrics={
                "disk_free_bytes": float(usage.free),
                "disk_used_bytes": float(usage.used),
                "disk_total_bytes": float(usage.total),
                "disk_used_percent": used_percent,
            },
        )


class MemoryHealthCheck(BaseHealthCheck):
    """Health check for memory usage."""

    def __init__(
        self,
        name: str = "memory",
        warning_threshold_percent: float = 80.0,
        critical_threshold_percent: float = 90.0,
        config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize memory health check."""
        super().__init__(name, ComponentType.MEMORY, config)
        self.warning_threshold_percent = warning_threshold_percent
        self.critical_threshold_percent = critical_threshold_percent

    async def _perform_check(self) -> HealthCheckResult:
        """Check memory usage."""
        memory = psutil.virtual_memory()

        if memory.percent > self.critical_threshold_percent:
            status = HealthStatus.UNHEALTHY
            message = f"Critical: {memory.percent:.1f}% memory used"
        elif memory.percent > self.warning_threshold_percent:
            status = HealthStatus.DEGRADED
            message = f"Warning: {memory.percent:.1f}% memory used"
        else:
            status = HealthStatus.HEALTHY
            message = f"{memory.percent:.1f}% memory used"

        return HealthCheckResult(
            name=self.name,
            status=status,
            component_type=self.component_type,
            message=message,
            details={
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "percent": memory.percent,
            },
            metrics={
                "memory_total_bytes": float(memory.total),
                "memory_available_bytes": float(memory.available),
                "memory_used_bytes": float(memory.used),
                "memory_percent": memory.percent,
            },
        )


class DatabaseHealthCheck(BaseHealthCheck):
    """Health check for database connectivity."""

    def __init__(
        self,
        name: str = "database",
        check_func: Optional[Callable[[], asyncio.Future[bool]]] = None,
        config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize database health check."""
        super().__init__(name, ComponentType.DATABASE, config)
        self.check_func = check_func

    async def _perform_check(self) -> HealthCheckResult:
        """Check database connectivity."""
        if self.check_func is None:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                component_type=self.component_type,
                message="No database check function configured",
            )

        try:
            start = time.time()
            is_healthy = await self.check_func()
            latency_ms = (time.time() - start) * 1000

            if is_healthy:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    component_type=self.component_type,
                    message="Database is responsive",
                    metrics={"latency_ms": latency_ms},
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    component_type=self.component_type,
                    message="Database check failed",
                )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                component_type=self.component_type,
                message="Database connection error",
                error=str(e),
            )


class RedisHealthCheck(BaseHealthCheck):
    """Health check for Redis connectivity."""

    def __init__(
        self,
        name: str = "redis",
        check_func: Optional[Callable[[], asyncio.Future[bool]]] = None,
        config: Optional[HealthCheckConfig] = None,
    ):
        """Initialize Redis health check."""
        super().__init__(name, ComponentType.CACHE, config)
        self.check_func = check_func

    async def _perform_check(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        if self.check_func is None:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                component_type=self.component_type,
                message="No Redis check function configured",
            )

        try:
            start = time.time()
            is_healthy = await self.check_func()
            latency_ms = (time.time() - start) * 1000

            if is_healthy:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    component_type=self.component_type,
                    message="Redis is responsive",
                    metrics={"latency_ms": latency_ms},
                )
            else:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    component_type=self.component_type,
                    message="Redis check failed",
                )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                component_type=self.component_type,
                message="Redis connection error",
                error=str(e),
            )


# Global health check registry
_health_check_registry: Optional[HealthCheckRegistry] = None


def get_health_check_registry() -> HealthCheckRegistry:
    """Get the global health check registry."""
    global _health_check_registry
    if _health_check_registry is None:
        _health_check_registry = HealthCheckRegistry()
    return _health_check_registry


def register_health_check(health_check: IHealthCheck) -> None:
    """Register a health check globally."""
    get_health_check_registry().register(health_check)


async def run_health_checks() -> List[HealthCheckResult]:
    """Run all registered health checks."""
    return await get_health_check_registry().check_all()
