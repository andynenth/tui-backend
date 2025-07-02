"""
Circuit Breaker Pattern for Foundation-First Development

Prevents infinite loops and system overload by monitoring operation frequency
and temporarily blocking operations that exceed safe thresholds.
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped, blocking operations  
    HALF_OPEN = "half_open"  # Testing if issue is resolved

@dataclass
class CircuitConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 10      # Failures before opening circuit
    success_threshold: int = 3       # Successes needed to close circuit  
    timeout: float = 30.0           # Seconds before trying half-open
    window_size: float = 60.0       # Time window for counting failures
    max_operations_per_second: int = 50  # Rate limiting

class CircuitBreaker:
    """Circuit breaker implementation for preventing infinite loops and overload"""
    
    def __init__(self, name: str, config: Optional[CircuitConfig] = None):
        self.name = name
        self.config = config or CircuitConfig()
        
        # Circuit state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.opened_time = 0.0
        
        # Rate limiting
        self.operation_times = []
        
        # Statistics
        self.total_operations = 0
        self.total_failures = 0
        self.total_blocks = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._check_circuit()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None:
            await self._record_success()
        else:
            await self._record_failure(str(exc_val))
            
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self:
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
    
    async def _check_circuit(self):
        """Check if operation should be allowed"""
        self.total_operations += 1
        current_time = time.time()
        
        # Rate limiting check
        if not self._check_rate_limit(current_time):
            self.total_blocks += 1
            raise CircuitBreakerException(
                f"Rate limit exceeded for {self.name}: "
                f">{self.config.max_operations_per_second} ops/sec"
            )
        
        # Circuit state check
        if self.state == CircuitState.CLOSED:
            # Normal operation
            return
            
        elif self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if current_time - self.opened_time >= self.config.timeout:
                logger.info(f"🔄 Circuit {self.name}: Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                self.total_blocks += 1
                raise CircuitBreakerException(
                    f"Circuit {self.name} is OPEN: "
                    f"timeout in {self.config.timeout - (current_time - self.opened_time):.1f}s"
                )
                
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited operations to test recovery
            pass
    
    def _check_rate_limit(self, current_time: float) -> bool:
        """Check if operation exceeds rate limit"""
        # Clean old entries
        cutoff_time = current_time - 1.0  # 1 second window
        self.operation_times = [t for t in self.operation_times if t > cutoff_time]
        
        # Add current operation
        self.operation_times.append(current_time)
        
        # Check rate
        return len(self.operation_times) <= self.config.max_operations_per_second
    
    async def _record_success(self):
        """Record successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(f"✅ Circuit {self.name}: Transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Decay failure count on success
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _record_failure(self, error_msg: str):
        """Record failed operation"""
        self.total_failures += 1
        current_time = time.time()
        
        # Clean old failures outside window
        if current_time - self.last_failure_time > self.config.window_size:
            self.failure_count = 0
            
        self.failure_count += 1
        self.last_failure_time = current_time
        
        logger.warning(f"⚠️ Circuit {self.name}: Failure {self.failure_count}/{self.config.failure_threshold} - {error_msg}")
        
        # Check if circuit should open
        if self.failure_count >= self.config.failure_threshold:
            logger.error(f"🚨 Circuit {self.name}: Opening circuit due to {self.failure_count} failures")
            self.state = CircuitState.OPEN
            self.opened_time = current_time
            self.success_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        current_time = time.time()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_operations": self.total_operations,
            "total_failures": self.total_failures,
            "total_blocks": self.total_blocks,
            "failure_rate": self.total_failures / max(1, self.total_operations),
            "current_ops_per_sec": len([t for t in self.operation_times if current_time - t <= 1.0]),
            "time_since_last_failure": current_time - self.last_failure_time if self.last_failure_time > 0 else None,
            "time_until_retry": max(0, self.config.timeout - (current_time - self.opened_time)) if self.state == CircuitState.OPEN else None
        }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        logger.info(f"🔄 Circuit {self.name}: Manual reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.opened_time = 0.0
        self.operation_times.clear()

class CircuitBreakerException(Exception):
    """Exception raised when circuit breaker blocks operation"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers for different system components"""
    
    def __init__(self):
        self.circuits: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitConfig()
    
    def get_circuit(self, name: str, config: Optional[CircuitConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for component"""
        if name not in self.circuits:
            self.circuits[name] = CircuitBreaker(name, config or self.default_config)
            logger.info(f"🔌 Created circuit breaker: {name}")
        return self.circuits[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: circuit.get_stats() for name, circuit in self.circuits.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for circuit in self.circuits.values():
            circuit.reset()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        all_stats = self.get_all_stats()
        
        total_operations = sum(stats["total_operations"] for stats in all_stats.values())
        total_failures = sum(stats["total_failures"] for stats in all_stats.values())
        total_blocks = sum(stats["total_blocks"] for stats in all_stats.values())
        
        open_circuits = [name for name, stats in all_stats.items() if stats["state"] == "open"]
        half_open_circuits = [name for name, stats in all_stats.items() if stats["state"] == "half_open"]
        
        return {
            "total_circuits": len(self.circuits),
            "open_circuits": len(open_circuits),
            "half_open_circuits": len(half_open_circuits),
            "healthy_circuits": len(self.circuits) - len(open_circuits) - len(half_open_circuits),
            "total_operations": total_operations,
            "total_failures": total_failures,
            "total_blocks": total_blocks,
            "overall_failure_rate": total_failures / max(1, total_operations),
            "problematic_circuits": open_circuits + half_open_circuits
        }

# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()

# Convenience functions
def get_circuit(name: str, config: Optional[CircuitConfig] = None) -> CircuitBreaker:
    """Get circuit breaker for component"""
    return circuit_manager.get_circuit(name, config)

async def protected_call(circuit_name: str, func, *args, **kwargs):
    """Execute function with circuit breaker protection"""
    circuit = get_circuit(circuit_name)
    return await circuit.call(func, *args, **kwargs)