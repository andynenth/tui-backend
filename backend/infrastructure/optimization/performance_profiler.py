"""
Performance profiling tools for optimization.

Provides detailed performance metrics and profiling capabilities.
"""

from typing import Dict, List, Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import threading
import asyncio
import cProfile
import pstats
import io
import functools
import logging
from contextlib import contextmanager
from collections import defaultdict
import tracemalloc
import gc


logger = logging.getLogger(__name__)


@dataclass
class TimingStats:
    """Statistics for a profiled operation."""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    last_time: float = 0.0
    
    def record(self, duration: float) -> None:
        """Record a timing measurement."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.last_time = duration
    
    @property
    def average_time(self) -> float:
        """Get average time."""
        return self.total_time / self.count if self.count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'count': self.count,
            'total_time': self.total_time,
            'average_time': self.average_time,
            'min_time': self.min_time if self.min_time != float('inf') else 0.0,
            'max_time': self.max_time,
            'last_time': self.last_time
        }


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    current: int = 0
    peak: int = 0
    allocated: int = 0
    freed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'current_mb': self.current / 1024 / 1024,
            'peak_mb': self.peak / 1024 / 1024,
            'allocated_mb': self.allocated / 1024 / 1024,
            'freed_mb': self.freed / 1024 / 1024
        }


@dataclass
class ProfileScope:
    """Scope for profiling operations."""
    name: str
    parent: Optional['ProfileScope'] = None
    timing: TimingStats = field(default_factory=TimingStats)
    memory: MemoryStats = field(default_factory=MemoryStats)
    children: Dict[str, 'ProfileScope'] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_child(self, name: str) -> 'ProfileScope':
        """Get or create child scope."""
        if name not in self.children:
            self.children[name] = ProfileScope(name, parent=self)
        return self.children[name]
    
    def get_path(self) -> str:
        """Get full scope path."""
        parts = []
        scope = self
        while scope:
            parts.append(scope.name)
            scope = scope.parent
        return '/'.join(reversed(parts))
    
    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'name': self.name,
            'path': self.get_path(),
            'timing': self.timing.to_dict(),
            'memory': self.memory.to_dict(),
            'metadata': self.metadata
        }
        
        if include_children and self.children:
            result['children'] = {
                name: child.to_dict()
                for name, child in self.children.items()
            }
        
        return result


class PerformanceProfiler:
    """
    Performance profiler for tracking execution metrics.
    
    Provides timing, memory, and CPU profiling capabilities
    with hierarchical scope tracking.
    """
    
    def __init__(self, name: str = "default"):
        """Initialize performance profiler."""
        self.name = name
        self.root_scope = ProfileScope("root")
        self._current_scope = self.root_scope
        self._scope_stack: List[ProfileScope] = [self.root_scope]
        self._lock = threading.RLock()
        self._start_time = time.time()
        self._cpu_profiler: Optional[cProfile.Profile] = None
        self._memory_tracking = False
    
    @contextmanager
    def profile(self, operation: str, **metadata):
        """
        Profile an operation.
        
        Args:
            operation: Operation name
            **metadata: Additional metadata to store
            
        Example:
            with profiler.profile("database_query", query_type="select"):
                # Perform operation
                pass
        """
        with self._lock:
            # Enter scope
            scope = self._current_scope.get_child(operation)
            self._scope_stack.append(scope)
            self._current_scope = scope
            
            # Add metadata
            scope.metadata.update(metadata)
        
        # Track memory if enabled
        if self._memory_tracking:
            mem_before = self._get_memory_usage()
        
        start_time = time.perf_counter()
        
        try:
            yield scope
        finally:
            # Record timing
            duration = time.perf_counter() - start_time
            scope.timing.record(duration)
            
            # Record memory if enabled
            if self._memory_tracking:
                mem_after = self._get_memory_usage()
                scope.memory.current = mem_after
                scope.memory.peak = max(scope.memory.peak, mem_after)
                if mem_after > mem_before:
                    scope.memory.allocated += mem_after - mem_before
                else:
                    scope.memory.freed += mem_before - mem_after
            
            # Exit scope
            with self._lock:
                self._scope_stack.pop()
                self._current_scope = self._scope_stack[-1]
    
    def start_cpu_profiling(self) -> None:
        """Start CPU profiling."""
        if self._cpu_profiler is None:
            self._cpu_profiler = cProfile.Profile()
            self._cpu_profiler.enable()
    
    def stop_cpu_profiling(self) -> str:
        """
        Stop CPU profiling and return results.
        
        Returns:
            Profiling results as string
        """
        if self._cpu_profiler is not None:
            self._cpu_profiler.disable()
            
            # Get stats
            s = io.StringIO()
            ps = pstats.Stats(self._cpu_profiler, stream=s)
            ps.strip_dirs()
            ps.sort_stats('cumulative')
            ps.print_stats(50)  # Top 50 functions
            
            self._cpu_profiler = None
            return s.getvalue()
        
        return "CPU profiling not active"
    
    def start_memory_tracking(self) -> None:
        """Start memory tracking."""
        self._memory_tracking = True
        if not tracemalloc.is_tracing():
            tracemalloc.start()
    
    def stop_memory_tracking(self) -> None:
        """Stop memory tracking."""
        self._memory_tracking = False
        if tracemalloc.is_tracing():
            tracemalloc.stop()
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        if tracemalloc.is_tracing():
            return tracemalloc.get_traced_memory()[0]
        else:
            # Fallback to GC stats
            return sum(obj.__sizeof__() for obj in gc.get_objects())
    
    def get_report(self) -> 'ProfileReport':
        """Get profiling report."""
        return ProfileReport(
            profiler_name=self.name,
            duration=time.time() - self._start_time,
            root_scope=self.root_scope,
            timestamp=datetime.utcnow()
        )
    
    def reset(self) -> None:
        """Reset all profiling data."""
        with self._lock:
            self.root_scope = ProfileScope("root")
            self._current_scope = self.root_scope
            self._scope_stack = [self.root_scope]
            self._start_time = time.time()
    
    def get_hotspots(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N hotspots by total time.
        
        Args:
            top_n: Number of hotspots to return
            
        Returns:
            List of hotspot information
        """
        hotspots = []
        
        def collect_hotspots(scope: ProfileScope, path: str = ""):
            scope_path = f"{path}/{scope.name}" if path else scope.name
            
            if scope.timing.count > 0:
                hotspots.append({
                    'path': scope_path,
                    'total_time': scope.timing.total_time,
                    'count': scope.timing.count,
                    'average_time': scope.timing.average_time,
                    'max_time': scope.timing.max_time
                })
            
            for child in scope.children.values():
                collect_hotspots(child, scope_path)
        
        collect_hotspots(self.root_scope)
        
        # Sort by total time
        hotspots.sort(key=lambda x: x['total_time'], reverse=True)
        
        return hotspots[:top_n]


@dataclass
class ProfileReport:
    """Profiling report with analysis."""
    profiler_name: str
    duration: float
    root_scope: ProfileScope
    timestamp: datetime
    
    def get_summary(self) -> Dict[str, Any]:
        """Get report summary."""
        total_operations = 0
        total_time = 0.0
        
        def count_operations(scope: ProfileScope):
            nonlocal total_operations, total_time
            total_operations += scope.timing.count
            total_time += scope.timing.total_time
            for child in scope.children.values():
                count_operations(child)
        
        count_operations(self.root_scope)
        
        return {
            'profiler_name': self.profiler_name,
            'duration_seconds': self.duration,
            'total_operations': total_operations,
            'total_profiled_time': total_time,
            'overhead_percentage': ((self.duration - total_time) / self.duration * 100) if self.duration > 0 else 0,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'summary': self.get_summary(),
            'scopes': self.root_scope.to_dict()
        }
    
    def to_text(self, indent: int = 2) -> str:
        """Convert report to text format."""
        lines = []
        lines.append(f"Performance Profile Report: {self.profiler_name}")
        lines.append(f"Duration: {self.duration:.2f}s")
        lines.append(f"Generated: {self.timestamp}")
        lines.append("")
        
        def format_scope(scope: ProfileScope, level: int = 0):
            prefix = " " * (level * indent)
            
            if scope.timing.count > 0:
                lines.append(
                    f"{prefix}{scope.name}: "
                    f"{scope.timing.count} calls, "
                    f"total={scope.timing.total_time:.3f}s, "
                    f"avg={scope.timing.average_time:.3f}s, "
                    f"max={scope.timing.max_time:.3f}s"
                )
            
            for child in sorted(scope.children.values(), key=lambda s: s.timing.total_time, reverse=True):
                format_scope(child, level + 1)
        
        format_scope(self.root_scope)
        
        return "\n".join(lines)


# Global profiler registry
_profilers: Dict[str, PerformanceProfiler] = {}
_lock = threading.RLock()


def get_profiler(name: str = "default") -> PerformanceProfiler:
    """Get or create a named profiler."""
    with _lock:
        if name not in _profilers:
            _profilers[name] = PerformanceProfiler(name)
        return _profilers[name]


# Decorator support

T = TypeVar('T')


def profile(
    operation: Optional[str] = None,
    profiler_name: str = "default",
    **metadata
) -> Callable:
    """
    Decorator for profiling functions.
    
    Args:
        operation: Operation name (defaults to function name)
        profiler_name: Name of profiler to use
        **metadata: Additional metadata
        
    Example:
        @profile("database_query", query_type="select")
        def get_user(user_id: int):
            # Function body
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            profiler = get_profiler(profiler_name)
            with profiler.profile(op_name, **metadata):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def profile_async(
    operation: Optional[str] = None,
    profiler_name: str = "default",
    **metadata
) -> Callable:
    """
    Decorator for profiling async functions.
    
    Args:
        operation: Operation name (defaults to function name)
        profiler_name: Name of profiler to use
        **metadata: Additional metadata
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            profiler = get_profiler(profiler_name)
            with profiler.profile(op_name, **metadata):
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Async profiler support

class AsyncPerformanceProfiler(PerformanceProfiler):
    """Async-aware performance profiler."""
    
    def __init__(self, name: str = "async_default"):
        """Initialize async profiler."""
        super().__init__(name)
        self._async_lock = asyncio.Lock()
    
    @contextmanager
    async def profile_async(self, operation: str, **metadata):
        """Async profile context manager."""
        async with self._async_lock:
            scope = self._current_scope.get_child(operation)
            self._scope_stack.append(scope)
            self._current_scope = scope
            scope.metadata.update(metadata)
        
        start_time = time.perf_counter()
        
        try:
            yield scope
        finally:
            duration = time.perf_counter() - start_time
            scope.timing.record(duration)
            
            async with self._async_lock:
                self._scope_stack.pop()
                self._current_scope = self._scope_stack[-1]