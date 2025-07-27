"""
In-memory cache implementation with TTL and eviction policies.

This provides a high-performance cache for single-instance deployments
or as a local cache layer in distributed systems.
"""

import asyncio
from typing import Optional, Dict, Any, List, Set, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
import heapq
import random
from dataclasses import dataclass, field

from .base import (
    IFullCache,
    CacheConfig,
    CacheEntry,
    CacheBackend,
    EvictionPolicy
)


class MemoryCache(IFullCache):
    """
    In-memory cache with configurable eviction policies and TTL support.
    
    Features:
    - Multiple eviction policies (LRU, LFU, FIFO, TTL, Random)
    - Tag-based invalidation
    - Batch operations
    - Background TTL cleanup
    - Thread-safe operations
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize memory cache.
        
        Args:
            config: Cache configuration
        """
        self._config = config or CacheConfig(backend=CacheBackend.MEMORY)
        
        # Storage based on eviction policy
        if self._config.eviction_policy == EvictionPolicy.LRU:
            self._storage: Dict[str, CacheEntry] = OrderedDict()
        else:
            self._storage: Dict[str, CacheEntry] = {}
        
        # Additional structures for different policies
        if self._config.eviction_policy == EvictionPolicy.LFU:
            self._frequency: Dict[str, int] = defaultdict(int)
            self._freq_list: Dict[int, Set[str]] = defaultdict(set)
            self._min_freq = 0
        
        if self._config.eviction_policy == EvictionPolicy.TTL:
            self._expiry_heap: List[Tuple[datetime, str]] = []
        
        # Tag index
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._key_tags: Dict[str, Set[str]] = defaultdict(set)
        
        # Configuration
        self._max_size = self._config.max_size or 10000
        self._default_ttl = self._config.default_ttl
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        if self._config.eviction_policy == EvictionPolicy.TTL or self._default_ttl:
            self._cleanup_task = asyncio.create_task(self._ttl_cleanup_worker())
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            entry = self._storage.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            # Check expiration
            if entry.is_expired():
                await self._remove_entry(key)
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            # Update access metadata
            entry.touch()
            self._stats['hits'] += 1
            
            # Update position based on policy
            if self._config.eviction_policy == EvictionPolicy.LRU:
                # Move to end for LRU
                self._storage.move_to_end(key)
            elif self._config.eviction_policy == EvictionPolicy.LFU:
                # Update frequency
                old_freq = self._frequency[key]
                new_freq = old_freq + 1
                self._frequency[key] = new_freq
                
                # Update frequency lists
                self._freq_list[old_freq].discard(key)
                if not self._freq_list[old_freq] and old_freq == self._min_freq:
                    self._min_freq = new_freq
                self._freq_list[new_freq].add(key)
            
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """Set value in cache."""
        async with self._lock:
            # Check if we need to evict
            if key not in self._storage and len(self._storage) >= self._max_size:
                await self._evict_one()
            
            # Create entry
            now = datetime.utcnow()
            entry = CacheEntry(
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=1,
                ttl=ttl or self._default_ttl,
                tags=tags or set()
            )
            
            # Remove old entry if exists
            if key in self._storage:
                await self._remove_entry(key)
            
            # Store entry
            self._storage[key] = entry
            self._stats['sets'] += 1
            
            # Update policy-specific structures
            if self._config.eviction_policy == EvictionPolicy.LRU:
                self._storage.move_to_end(key)
            elif self._config.eviction_policy == EvictionPolicy.LFU:
                self._frequency[key] = 1
                self._freq_list[1].add(key)
                self._min_freq = 1
            elif self._config.eviction_policy == EvictionPolicy.TTL and entry.ttl:
                expiry_time = entry.created_at + entry.ttl
                heapq.heappush(self._expiry_heap, (expiry_time, key))
            
            # Update tag index
            if tags:
                self._key_tags[key] = tags
                for tag in tags:
                    self._tag_index[tag].add(key)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key not in self._storage:
                return False
            
            await self._remove_entry(key)
            self._stats['deletes'] += 1
            return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        async with self._lock:
            entry = self._storage.get(key)
            if entry is None:
                return False
            
            if entry.is_expired():
                await self._remove_entry(key)
                self._stats['expirations'] += 1
                return False
            
            return True
    
    async def clear(self) -> None:
        """Clear all entries from cache."""
        async with self._lock:
            self._storage.clear()
            self._tag_index.clear()
            self._key_tags.clear()
            
            if self._config.eviction_policy == EvictionPolicy.LFU:
                self._frequency.clear()
                self._freq_list.clear()
                self._min_freq = 0
            elif self._config.eviction_policy == EvictionPolicy.TTL:
                self._expiry_heap.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._storage),
                'max_size': self._max_size,
                'stats': dict(self._stats),
                'hit_rate': hit_rate,
                'eviction_policy': self._config.eviction_policy.value,
                'total_tags': len(self._tag_index),
                'memory_estimate_bytes': len(self._storage) * 1024  # Rough estimate
            }
    
    # IBatchCache implementation
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results
    
    async def set_many(
        self,
        entries: Dict[str, Any],
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """Set multiple values in cache."""
        for key, value in entries.items():
            await self.set(key, value, ttl=ttl, tags=tags)
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values from cache."""
        deleted = 0
        for key in keys:
            if await self.delete(key):
                deleted += 1
        return deleted
    
    # ITaggedCache implementation
    
    async def get_by_tag(self, tag: str) -> Dict[str, Any]:
        """Get all entries with a specific tag."""
        async with self._lock:
            results = {}
            keys = list(self._tag_index.get(tag, set()))
            
            for key in keys:
                entry = self._storage.get(key)
                if entry and not entry.is_expired():
                    results[key] = entry.value
            
            return results
    
    async def delete_by_tag(self, tag: str) -> int:
        """Delete all entries with a specific tag."""
        async with self._lock:
            keys = list(self._tag_index.get(tag, set()))
            deleted = 0
            
            for key in keys:
                if key in self._storage:
                    await self._remove_entry(key)
                    deleted += 1
            
            return deleted
    
    async def get_tags(self, key: str) -> Set[str]:
        """Get tags for a specific key."""
        async with self._lock:
            return self._key_tags.get(key, set()).copy()
    
    # Internal methods
    
    async def _remove_entry(self, key: str) -> None:
        """Remove entry and clean up indexes."""
        if key not in self._storage:
            return
        
        # Remove from storage
        del self._storage[key]
        
        # Clean up tags
        tags = self._key_tags.get(key, set())
        for tag in tags:
            self._tag_index[tag].discard(key)
            if not self._tag_index[tag]:
                del self._tag_index[tag]
        
        if key in self._key_tags:
            del self._key_tags[key]
        
        # Clean up policy-specific structures
        if self._config.eviction_policy == EvictionPolicy.LFU:
            freq = self._frequency.get(key, 0)
            if freq > 0:
                self._freq_list[freq].discard(key)
                if not self._freq_list[freq]:
                    del self._freq_list[freq]
                del self._frequency[key]
    
    async def _evict_one(self) -> None:
        """Evict one entry based on policy."""
        if not self._storage:
            return
        
        key_to_evict = None
        
        if self._config.eviction_policy == EvictionPolicy.LRU:
            # Evict least recently used (first item)
            key_to_evict = next(iter(self._storage))
        
        elif self._config.eviction_policy == EvictionPolicy.LFU:
            # Evict least frequently used
            if self._min_freq in self._freq_list and self._freq_list[self._min_freq]:
                key_to_evict = next(iter(self._freq_list[self._min_freq]))
        
        elif self._config.eviction_policy == EvictionPolicy.FIFO:
            # Evict oldest (first item)
            key_to_evict = next(iter(self._storage))
        
        elif self._config.eviction_policy == EvictionPolicy.TTL:
            # Evict expired or oldest
            # First try to evict expired entries
            while self._expiry_heap:
                expiry_time, key = heapq.heappop(self._expiry_heap)
                if key in self._storage:
                    entry = self._storage[key]
                    if entry.is_expired():
                        key_to_evict = key
                        break
            
            # If no expired entries, evict oldest
            if not key_to_evict:
                oldest_key = None
                oldest_time = datetime.max
                
                for key, entry in self._storage.items():
                    if entry.created_at < oldest_time:
                        oldest_time = entry.created_at
                        oldest_key = key
                
                key_to_evict = oldest_key
        
        elif self._config.eviction_policy == EvictionPolicy.RANDOM:
            # Evict random entry
            key_to_evict = random.choice(list(self._storage.keys()))
        
        if key_to_evict:
            await self._remove_entry(key_to_evict)
            self._stats['evictions'] += 1
    
    async def _ttl_cleanup_worker(self) -> None:
        """Background worker for cleaning up expired entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self._lock:
                    expired_keys = []
                    
                    for key, entry in self._storage.items():
                        if entry.is_expired():
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        await self._remove_entry(key)
                        self._stats['expirations'] += 1
                
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                await asyncio.sleep(5)
    
    async def shutdown(self) -> None:
        """Shutdown cache and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass