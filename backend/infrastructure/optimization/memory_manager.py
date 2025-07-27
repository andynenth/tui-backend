"""
Memory management and optimization utilities.

Provides memory tracking, limits, and optimization strategies.
"""

from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import asyncio
import gc
import weakref
import psutil
import logging
import functools
from contextlib import contextmanager
from collections import defaultdict
import tracemalloc
import sys


logger = logging.getLogger(__name__)


@dataclass
class MemoryAllocation:
    """Represents a memory allocation."""
    size: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    traceback: Optional[List[str]] = None
    tag: Optional[str] = None
    
    def get_age(self) -> timedelta:
        """Get age of allocation."""
        return datetime.utcnow() - self.timestamp


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    used: int = 0
    available: int = 0
    total: int = 0
    percent: float = 0.0
    
    # Process-specific
    rss: int = 0  # Resident Set Size
    vms: int = 0  # Virtual Memory Size
    shared: int = 0
    
    # Allocations
    allocations: int = 0
    deallocations: int = 0
    current_allocations: int = 0
    peak_allocations: int = 0
    
    def update_from_system(self) -> None:
        """Update stats from system."""
        # System memory
        mem = psutil.virtual_memory()
        self.total = mem.total
        self.available = mem.available
        self.used = mem.used
        self.percent = mem.percent
        
        # Process memory
        process = psutil.Process()
        mem_info = process.memory_info()
        self.rss = mem_info.rss
        self.vms = mem_info.vms
        if hasattr(mem_info, 'shared'):
            self.shared = mem_info.shared
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'system': {
                'used_mb': self.used / 1024 / 1024,
                'available_mb': self.available / 1024 / 1024,
                'total_mb': self.total / 1024 / 1024,
                'percent': self.percent
            },
            'process': {
                'rss_mb': self.rss / 1024 / 1024,
                'vms_mb': self.vms / 1024 / 1024,
                'shared_mb': self.shared / 1024 / 1024
            },
            'allocations': {
                'total': self.allocations,
                'deallocations': self.deallocations,
                'current': self.current_allocations,
                'peak': self.peak_allocations
            }
        }


class MemoryLimit(Exception):
    """Raised when memory limit is exceeded."""
    pass


class MemoryManager:
    """
    Memory manager for tracking and optimizing memory usage.
    
    Provides memory limits, tracking, and garbage collection optimization.
    """
    
    def __init__(
        self,
        soft_limit_mb: Optional[int] = None,
        hard_limit_mb: Optional[int] = None,
        check_interval: timedelta = timedelta(seconds=10)
    ):
        """
        Initialize memory manager.
        
        Args:
            soft_limit_mb: Soft memory limit (triggers GC)
            hard_limit_mb: Hard memory limit (raises exception)
            check_interval: Interval for memory checks
        """
        self.soft_limit_bytes = soft_limit_mb * 1024 * 1024 if soft_limit_mb else None
        self.hard_limit_bytes = hard_limit_mb * 1024 * 1024 if hard_limit_mb else None
        self.check_interval = check_interval
        
        self.stats = MemoryStats()
        self._allocations: Dict[int, MemoryAllocation] = {}
        self._allocation_tags: Dict[str, List[int]] = defaultdict(list)
        self._tracked_objects: weakref.WeakSet = weakref.WeakSet()
        
        self._lock = threading.RLock()
        self._last_check = datetime.utcnow()
        self._gc_count = 0
        self._tracking_enabled = False
        
        # GC tuning
        self._original_gc_thresholds = gc.get_threshold()
        self._gc_tuned = False
    
    def start_tracking(self) -> None:
        """Start memory tracking."""
        self._tracking_enabled = True
        if not tracemalloc.is_tracing():
            tracemalloc.start()
    
    def stop_tracking(self) -> None:
        """Stop memory tracking."""
        self._tracking_enabled = False
        if tracemalloc.is_tracing():
            tracemalloc.stop()
    
    def check_limits(self) -> None:
        """Check memory limits and take action if needed."""
        # Update stats
        self.stats.update_from_system()
        
        # Check soft limit
        if self.soft_limit_bytes and self.stats.rss > self.soft_limit_bytes:
            logger.warning(
                f"Soft memory limit exceeded: {self.stats.rss / 1024 / 1024:.1f}MB / "
                f"{self.soft_limit_bytes / 1024 / 1024}MB"
            )
            self.force_gc()
        
        # Check hard limit
        if self.hard_limit_bytes and self.stats.rss > self.hard_limit_bytes:
            raise MemoryLimit(
                f"Hard memory limit exceeded: {self.stats.rss / 1024 / 1024:.1f}MB / "
                f"{self.hard_limit_bytes / 1024 / 1024}MB"
            )
    
    def force_gc(self, full: bool = True) -> int:
        """
        Force garbage collection.
        
        Args:
            full: Whether to run full collection
            
        Returns:
            Number of objects collected
        """
        with self._lock:
            before = len(gc.get_objects())
            
            if full:
                # Full collection of all generations
                collected = gc.collect(2)
            else:
                # Quick collection of youngest generation
                collected = gc.collect(0)
            
            after = len(gc.get_objects())
            self._gc_count += 1
            
            logger.info(
                f"GC collected {collected} objects "
                f"(objects: {before} -> {after})"
            )
            
            return collected
    
    def optimize_gc(self) -> None:
        """Optimize GC settings for performance."""
        if not self._gc_tuned:
            # Increase thresholds for less frequent GC
            # This can improve performance at the cost of memory
            gc.set_threshold(700, 10, 10)  # Default is (700, 10, 10)
            self._gc_tuned = True
            logger.info("GC thresholds optimized for performance")
    
    def restore_gc(self) -> None:
        """Restore original GC settings."""
        if self._gc_tuned:
            gc.set_threshold(*self._original_gc_thresholds)
            self._gc_tuned = False
            logger.info("GC thresholds restored to defaults")
    
    def track_allocation(
        self,
        size: int,
        tag: Optional[str] = None,
        obj: Optional[Any] = None
    ) -> int:
        """
        Track a memory allocation.
        
        Args:
            size: Size of allocation
            tag: Optional tag for grouping
            obj: Optional object to track
            
        Returns:
            Allocation ID
        """
        if not self._tracking_enabled:
            return -1
        
        with self._lock:
            # Get traceback if available
            tb = None
            if tracemalloc.is_tracing():
                tb = tracemalloc.get_object_traceback(obj) if obj else None
                if tb:
                    tb = tb.format()
            
            # Create allocation record
            alloc_id = id(obj) if obj else id(self)
            allocation = MemoryAllocation(
                size=size,
                traceback=tb,
                tag=tag
            )
            
            self._allocations[alloc_id] = allocation
            self.stats.allocations += 1
            self.stats.current_allocations = len(self._allocations)
            self.stats.peak_allocations = max(
                self.stats.peak_allocations,
                self.stats.current_allocations
            )
            
            # Track by tag
            if tag:
                self._allocation_tags[tag].append(alloc_id)
            
            # Track object if provided
            if obj:
                self._tracked_objects.add(obj)
            
            # Check limits periodically
            if datetime.utcnow() - self._last_check > self.check_interval:
                self.check_limits()
                self._last_check = datetime.utcnow()
            
            return alloc_id
    
    def track_deallocation(self, alloc_id: int) -> None:
        """Track a memory deallocation."""
        if not self._tracking_enabled:
            return
        
        with self._lock:
            if alloc_id in self._allocations:
                allocation = self._allocations.pop(alloc_id)
                self.stats.deallocations += 1
                self.stats.current_allocations = len(self._allocations)
                
                # Remove from tag tracking
                if allocation.tag:
                    self._allocation_tags[allocation.tag].remove(alloc_id)
    
    def get_allocations_by_tag(self, tag: str) -> List[MemoryAllocation]:
        """Get all allocations with a specific tag."""
        with self._lock:
            return [
                self._allocations[alloc_id]
                for alloc_id in self._allocation_tags.get(tag, [])
                if alloc_id in self._allocations
            ]
    
    def get_memory_leaks(
        self,
        age_threshold: timedelta = timedelta(minutes=5)
    ) -> List[Dict[str, Any]]:
        """
        Find potential memory leaks.
        
        Args:
            age_threshold: Minimum age to consider a leak
            
        Returns:
            List of potential leaks
        """
        leaks = []
        
        with self._lock:
            for alloc_id, allocation in self._allocations.items():
                if allocation.get_age() > age_threshold:
                    leaks.append({
                        'id': alloc_id,
                        'size': allocation.size,
                        'age_seconds': allocation.get_age().total_seconds(),
                        'tag': allocation.tag,
                        'traceback': allocation.traceback
                    })
        
        # Sort by size
        leaks.sort(key=lambda x: x['size'], reverse=True)
        
        return leaks
    
    def get_memory_profile(self) -> Dict[str, Any]:
        """Get detailed memory profile."""
        self.stats.update_from_system()
        
        profile = {
            'stats': self.stats.to_dict(),
            'gc': {
                'count': self._gc_count,
                'thresholds': gc.get_threshold(),
                'generations': [
                    {
                        'objects': gc.get_count()[i],
                        'collected': gc.get_stats()[i].get('collected', 0),
                        'collections': gc.get_stats()[i].get('collections', 0)
                    }
                    for i in range(gc.get_count().__len__())
                ]
            },
            'tracking': {
                'enabled': self._tracking_enabled,
                'tracked_objects': len(self._tracked_objects),
                'allocations': self.stats.current_allocations
            }
        }
        
        # Add top allocations by tag
        if self._allocation_tags:
            tag_sizes = {}
            for tag, alloc_ids in self._allocation_tags.items():
                total_size = sum(
                    self._allocations[aid].size
                    for aid in alloc_ids
                    if aid in self._allocations
                )
                tag_sizes[tag] = total_size
            
            profile['top_tags'] = sorted(
                tag_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        
        return profile
    
    def clear_cache(self) -> None:
        """Clear various caches to free memory."""
        # Clear functools caches
        gc.collect()
        
        # Clear module caches
        for module in sys.modules.values():
            if hasattr(module, '__dict__'):
                for attr_name in dir(module):
                    attr = getattr(module, attr_name, None)
                    if hasattr(attr, 'cache_clear'):
                        try:
                            attr.cache_clear()
                        except Exception:
                            pass


# Global memory manager
_memory_manager: Optional[MemoryManager] = None
_lock = threading.RLock()


def get_memory_manager() -> MemoryManager:
    """Get global memory manager."""
    global _memory_manager
    with _lock:
        if _memory_manager is None:
            _memory_manager = MemoryManager()
        return _memory_manager


# Context managers

@contextmanager
def memory_limit(soft_mb: int, hard_mb: Optional[int] = None):
    """
    Context manager for memory limits.
    
    Example:
        with memory_limit(100, 200):  # 100MB soft, 200MB hard
            # Memory-intensive operation
            pass
    """
    manager = get_memory_manager()
    
    # Save original limits
    original_soft = manager.soft_limit_bytes
    original_hard = manager.hard_limit_bytes
    
    # Set new limits
    manager.soft_limit_bytes = soft_mb * 1024 * 1024
    manager.hard_limit_bytes = hard_mb * 1024 * 1024 if hard_mb else None
    
    try:
        manager.check_limits()
        yield manager
    finally:
        # Restore original limits
        manager.soft_limit_bytes = original_soft
        manager.hard_limit_bytes = original_hard


@contextmanager
def track_memory(tag: str):
    """
    Context manager for tracking memory allocations.
    
    Example:
        with track_memory("data_processing"):
            # Process data
            pass
    """
    manager = get_memory_manager()
    
    if not manager._tracking_enabled:
        manager.start_tracking()
        should_stop = True
    else:
        should_stop = False
    
    # Get memory before
    before_rss = psutil.Process().memory_info().rss
    
    try:
        yield manager
    finally:
        # Get memory after
        after_rss = psutil.Process().memory_info().rss
        delta = after_rss - before_rss
        
        if delta > 0:
            manager.track_allocation(delta, tag)
        
        if should_stop:
            manager.stop_tracking()


# Decorators

def memory_tracked(tag: Optional[str] = None):
    """
    Decorator for tracking function memory usage.
    
    Args:
        tag: Tag for allocation (defaults to function name)
        
    Example:
        @memory_tracked("expensive_operation")
        def process_data():
            # Function body
            pass
    """
    def decorator(func: Callable) -> Callable:
        allocation_tag = tag or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with track_memory(allocation_tag):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator