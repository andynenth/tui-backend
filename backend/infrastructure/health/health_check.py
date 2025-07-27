"""
Comprehensive health check system.

Provides health monitoring for all system components.
"""

from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
import time
import logging
from abc import ABC, abstractmethod
import psutil
import aiohttp
import socket


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of system components."""
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL_SERVICE = "internal_service"
    SYSTEM_RESOURCE = "system_resource"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: Optional[float] = None
    checked_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.status == HealthStatus.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'component': self.component_name,
            'type': self.component_type.value,
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'response_time_ms': self.response_time_ms,
            'checked_at': self.checked_at.isoformat()
        }


@dataclass
class HealthCheckConfig:
    """Configuration for health checks."""
    timeout: timedelta = timedelta(seconds=5)
    interval: timedelta = timedelta(seconds=30)
    failure_threshold: int = 3  # Failures before marking unhealthy
    recovery_threshold: int = 2  # Successes before marking healthy
    enabled: bool = True
    
    # Resource thresholds
    cpu_threshold: float = 90.0      # CPU percentage
    memory_threshold: float = 85.0   # Memory percentage
    disk_threshold: float = 90.0     # Disk usage percentage


class HealthCheck(ABC):
    """Abstract base class for health checks."""
    
    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        config: Optional[HealthCheckConfig] = None
    ):
        """Initialize health check."""
        self.name = name
        self.component_type = component_type
        self.config = config or HealthCheckConfig()
        
        # State tracking
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_result: Optional[HealthCheckResult] = None
        self._last_check_time: Optional[datetime] = None
    
    @abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """Perform health check."""
        pass
    
    def should_check(self) -> bool:
        """Determine if check should run."""
        if not self.config.enabled:
            return False
        
        if self._last_check_time is None:
            return True
        
        elapsed = datetime.utcnow() - self._last_check_time
        return elapsed >= self.config.interval
    
    async def run_check(self) -> HealthCheckResult:
        """Run health check with tracking."""
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_health(),
                timeout=self.config.timeout.total_seconds()
            )
            
            # Record response time
            result.response_time_ms = (time.time() - start_time) * 1000
            
            # Update state
            if result.is_healthy():
                self._consecutive_failures = 0
                self._consecutive_successes += 1
            else:
                self._consecutive_successes = 0
                self._consecutive_failures += 1
            
        except asyncio.TimeoutError:
            result = HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.config.timeout.total_seconds()}s"
            )
            self._consecutive_successes = 0
            self._consecutive_failures += 1
            
        except Exception as e:
            result = HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
            self._consecutive_successes = 0
            self._consecutive_failures += 1
        
        # Apply thresholds
        if self._consecutive_failures >= self.config.failure_threshold:
            result.status = HealthStatus.UNHEALTHY
        elif self._consecutive_successes < self.config.recovery_threshold:
            result.status = HealthStatus.DEGRADED
        
        self._last_result = result
        self._last_check_time = datetime.utcnow()
        
        return result
    
    def get_last_result(self) -> Optional[HealthCheckResult]:
        """Get last check result."""
        return self._last_result


# Built-in health checks

class SystemResourceHealthCheck(HealthCheck):
    """Health check for system resources."""
    
    def __init__(self, config: Optional[HealthCheckConfig] = None):
        """Initialize system resource health check."""
        super().__init__(
            "system_resources",
            ComponentType.SYSTEM_RESOURCE,
            config
        )
    
    async def check_health(self) -> HealthCheckResult:
        """Check system resource health."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check thresholds
            issues = []
            
            if cpu_percent > self.config.cpu_threshold:
                issues.append(f"CPU usage high: {cpu_percent:.1f}%")
            
            if memory.percent > self.config.memory_threshold:
                issues.append(f"Memory usage high: {memory.percent:.1f}%")
            
            if disk.percent > self.config.disk_threshold:
                issues.append(f"Disk usage high: {disk.percent:.1f}%")
            
            # Determine status
            if issues:
                status = HealthStatus.DEGRADED if len(issues) == 1 else HealthStatus.UNHEALTHY
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = "All system resources within normal parameters"
            
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=status,
                message=message,
                details={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_mb': memory.available / 1024 / 1024,
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / 1024 / 1024 / 1024
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check system resources: {str(e)}"
            )


class HTTPHealthCheck(HealthCheck):
    """Health check for HTTP endpoints."""
    
    def __init__(
        self,
        name: str,
        url: str,
        expected_status: int = 200,
        config: Optional[HealthCheckConfig] = None
    ):
        """Initialize HTTP health check."""
        super().__init__(name, ComponentType.EXTERNAL_SERVICE, config)
        self.url = url
        self.expected_status = expected_status
    
    async def check_health(self) -> HealthCheckResult:
        """Check HTTP endpoint health."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url,
                    timeout=aiohttp.ClientTimeout(
                        total=self.config.timeout.total_seconds()
                    )
                ) as response:
                    if response.status == self.expected_status:
                        return HealthCheckResult(
                            component_name=self.name,
                            component_type=self.component_type,
                            status=HealthStatus.HEALTHY,
                            message=f"HTTP {response.status}",
                            details={
                                'url': self.url,
                                'status_code': response.status
                            }
                        )
                    else:
                        return HealthCheckResult(
                            component_name=self.name,
                            component_type=self.component_type,
                            status=HealthStatus.UNHEALTHY,
                            message=f"Unexpected status: {response.status}",
                            details={
                                'url': self.url,
                                'status_code': response.status,
                                'expected': self.expected_status
                            }
                        )
                        
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP check failed: {str(e)}",
                details={'url': self.url}
            )


class TCPHealthCheck(HealthCheck):
    """Health check for TCP connections."""
    
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        component_type: ComponentType = ComponentType.EXTERNAL_SERVICE,
        config: Optional[HealthCheckConfig] = None
    ):
        """Initialize TCP health check."""
        super().__init__(name, component_type, config)
        self.host = host
        self.port = port
    
    async def check_health(self) -> HealthCheckResult:
        """Check TCP connection health."""
        try:
            # Try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.timeout.total_seconds())
            
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.HEALTHY,
                    message=f"TCP connection successful",
                    details={
                        'host': self.host,
                        'port': self.port
                    }
                )
            else:
                return HealthCheckResult(
                    component_name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNHEALTHY,
                    message=f"TCP connection failed",
                    details={
                        'host': self.host,
                        'port': self.port,
                        'error_code': result
                    }
                )
                
        except Exception as e:
            return HealthCheckResult(
                component_name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"TCP check failed: {str(e)}",
                details={
                    'host': self.host,
                    'port': self.port
                }
            )


class HealthCheckManager:
    """
    Manager for all health checks.
    
    Coordinates health checks and provides aggregate health status.
    """
    
    def __init__(self):
        """Initialize health check manager."""
        self._checks: Dict[str, HealthCheck] = {}
        self._check_groups: Dict[ComponentType, List[str]] = {}
        self._lock = threading.RLock()
        self._running = False
        self._check_task = None
    
    def register_check(self, check: HealthCheck) -> None:
        """Register a health check."""
        with self._lock:
            self._checks[check.name] = check
            
            # Group by type
            if check.component_type not in self._check_groups:
                self._check_groups[check.component_type] = []
            self._check_groups[check.component_type].append(check.name)
    
    def unregister_check(self, name: str) -> None:
        """Unregister a health check."""
        with self._lock:
            if name in self._checks:
                check = self._checks.pop(name)
                self._check_groups[check.component_type].remove(name)
    
    async def check_component(self, name: str) -> Optional[HealthCheckResult]:
        """Check a specific component."""
        check = self._checks.get(name)
        if check and check.should_check():
            return await check.run_check()
        return check.get_last_result() if check else None
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks."""
        tasks = []
        
        with self._lock:
            for name, check in self._checks.items():
                if check.should_check():
                    tasks.append((name, check.run_check()))
        
        # Run checks concurrently
        results = {}
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {e}")
                results[name] = HealthCheckResult(
                    component_name=name,
                    component_type=ComponentType.UNKNOWN,
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {str(e)}"
                )
        
        return results
    
    async def get_aggregate_health(self) -> HealthCheckResult:
        """Get aggregate health status."""
        results = await self.check_all()
        
        # Count statuses
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for result in results.values():
            status_counts[result.status] += 1
        
        # Determine aggregate status
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            status = HealthStatus.UNHEALTHY
            message = f"{status_counts[HealthStatus.UNHEALTHY]} components unhealthy"
        elif status_counts[HealthStatus.DEGRADED] > 0:
            status = HealthStatus.DEGRADED
            message = f"{status_counts[HealthStatus.DEGRADED]} components degraded"
        elif status_counts[HealthStatus.UNKNOWN] > 0:
            status = HealthStatus.DEGRADED
            message = f"{status_counts[HealthStatus.UNKNOWN]} components in unknown state"
        else:
            status = HealthStatus.HEALTHY
            message = f"All {len(results)} components healthy"
        
        return HealthCheckResult(
            component_name="system",
            component_type=ComponentType.INTERNAL_SERVICE,
            status=status,
            message=message,
            details={
                'component_count': len(results),
                'status_breakdown': {
                    k.value: v for k, v in status_counts.items()
                },
                'components': {
                    name: result.to_dict()
                    for name, result in results.items()
                }
            }
        )
    
    def start_background_checks(self) -> None:
        """Start background health checking."""
        if self._running:
            return
        
        self._running = True
        
        async def check_loop():
            while self._running:
                try:
                    await self.check_all()
                except Exception as e:
                    logger.error(f"Error in health check loop: {e}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
        
        self._check_task = asyncio.create_task(check_loop())
    
    def stop_background_checks(self) -> None:
        """Stop background health checking."""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        with self._lock:
            for name, check in self._checks.items():
                result = check.get_last_result()
                if result:
                    report['checks'][name] = result.to_dict()
        
        # Group by component type
        report['by_type'] = {}
        for comp_type, check_names in self._check_groups.items():
            report['by_type'][comp_type.value] = {
                name: report['checks'].get(name)
                for name in check_names
                if name in report['checks']
            }
        
        return report


# Global health check manager
_health_manager = HealthCheckManager()


def get_health_manager() -> HealthCheckManager:
    """Get global health check manager."""
    return _health_manager


# Convenience functions

def register_health_check(check: HealthCheck) -> None:
    """Register a health check with global manager."""
    _health_manager.register_check(check)


async def check_health(component: Optional[str] = None) -> Dict[str, Any]:
    """
    Check health of system or specific component.
    
    Args:
        component: Optional component name to check
        
    Returns:
        Health check results
    """
    if component:
        result = await _health_manager.check_component(component)
        return result.to_dict() if result else None
    else:
        aggregate = await _health_manager.get_aggregate_health()
        return aggregate.to_dict()