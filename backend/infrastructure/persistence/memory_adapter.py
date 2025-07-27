"""
In-memory implementation of persistence adapters.

This provides high-performance memory-based storage that implements
the persistence adapter interfaces.
"""

import asyncio
from typing import Optional, List, Dict, Any, Tuple, TypeVar, Generic
from datetime import datetime
from collections import OrderedDict, defaultdict
from copy import deepcopy

from .base import (
    IPersistenceAdapter,
    IQueryableAdapter,
    IArchivableAdapter,
    PersistenceConfig,
    PersistenceBackend
)


T = TypeVar('T')


class MemoryAdapter(IPersistenceAdapter[T], IQueryableAdapter[T], IArchivableAdapter[T], Generic[T]):
    """
    In-memory persistence adapter with full feature support.
    
    This adapter provides:
    - O(1) key-based operations
    - Query support with filtering and sorting
    - Archive history tracking
    - Thread-safe operations
    - LRU eviction when memory limit is reached
    """
    
    def __init__(self, config: Optional[PersistenceConfig] = None):
        """
        Initialize memory adapter.
        
        Args:
            config: Optional configuration with options:
                - max_items: Maximum number of items to store
                - enable_archives: Whether to track archives
                - archive_limit: Maximum archives per entity
        """
        self._config = config or PersistenceConfig(backend=PersistenceBackend.MEMORY)
        
        # Primary storage with LRU ordering
        self._data: OrderedDict[str, T] = OrderedDict()
        
        # Archive storage: key -> list of (timestamp, entity)
        self._archives: Dict[str, List[Tuple[datetime, T]]] = defaultdict(list)
        
        # Configuration
        self._max_items = self._config.options.get('max_items', 100000)
        self._enable_archives = self._config.options.get('enable_archives', True)
        self._archive_limit = self._config.options.get('archive_limit', 100)
        
        # Thread safety
        self._lock = asyncio.Lock()
        
        # Metrics
        self._operations = {
            'gets': 0,
            'saves': 0,
            'deletes': 0,
            'queries': 0
        }
    
    # IPersistenceAdapter implementation
    
    async def get(self, key: str) -> Optional[T]:
        """Get entity by key with O(1) performance."""
        async with self._lock:
            self._operations['gets'] += 1
            
            if key in self._data:
                # Move to end for LRU
                self._data.move_to_end(key)
                # Return deep copy to prevent external modifications
                return deepcopy(self._data[key])
            return None
    
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple entities efficiently."""
        async with self._lock:
            self._operations['gets'] += len(keys)
            
            result = {}
            for key in keys:
                if key in self._data:
                    self._data.move_to_end(key)
                    result[key] = deepcopy(self._data[key])
            return result
    
    async def save(self, key: str, entity: T) -> None:
        """Save entity with LRU eviction if needed."""
        async with self._lock:
            self._operations['saves'] += 1
            
            # Archive previous version if exists
            if self._enable_archives and key in self._data:
                await self._archive_internal(key, self._data[key])
            
            # Check capacity and evict if needed
            if len(self._data) >= self._max_items and key not in self._data:
                # Evict oldest (first item in OrderedDict)
                evicted_key = next(iter(self._data))
                del self._data[evicted_key]
            
            # Save entity
            self._data[key] = deepcopy(entity)
            self._data.move_to_end(key)
    
    async def save_many(self, entities: Dict[str, T]) -> None:
        """Save multiple entities efficiently."""
        async with self._lock:
            self._operations['saves'] += len(entities)
            
            for key, entity in entities.items():
                # Archive previous versions
                if self._enable_archives and key in self._data:
                    await self._archive_internal(key, self._data[key])
                
                # Save without individual locking
                self._data[key] = deepcopy(entity)
                self._data.move_to_end(key)
            
            # Evict excess items if needed
            while len(self._data) > self._max_items:
                evicted_key = next(iter(self._data))
                del self._data[evicted_key]
    
    async def delete(self, key: str) -> bool:
        """Delete entity by key."""
        async with self._lock:
            self._operations['deletes'] += 1
            
            if key in self._data:
                # Archive before deletion
                if self._enable_archives:
                    await self._archive_internal(key, self._data[key])
                
                del self._data[key]
                return True
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple entities."""
        async with self._lock:
            self._operations['deletes'] += len(keys)
            
            deleted = 0
            for key in keys:
                if key in self._data:
                    # Archive before deletion
                    if self._enable_archives:
                        await self._archive_internal(key, self._data[key])
                    
                    del self._data[key]
                    deleted += 1
            return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if entity exists."""
        async with self._lock:
            return key in self._data
    
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix filter."""
        async with self._lock:
            if prefix:
                return [k for k in self._data.keys() if k.startswith(prefix)]
            return list(self._data.keys())
    
    async def clear(self) -> None:
        """Clear all data and archives."""
        async with self._lock:
            self._data.clear()
            self._archives.clear()
            # Reset metrics
            for key in self._operations:
                self._operations[key] = 0
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        async with self._lock:
            return {
                'total_items': len(self._data),
                'total_archives': sum(len(archives) for archives in self._archives.values()),
                'operations': dict(self._operations),
                'memory_estimate_bytes': len(self._data) * 1024,  # Rough estimate
                'capacity_percentage': (len(self._data) / self._max_items * 100),
                'backend': 'memory'
            }
    
    # IQueryableAdapter implementation
    
    async def query(self, filter_dict: Dict[str, Any]) -> List[T]:
        """Query entities by filter criteria."""
        async with self._lock:
            self._operations['queries'] += 1
            
            results = []
            for entity in self._data.values():
                if self._matches_filter(entity, filter_dict):
                    results.append(deepcopy(entity))
            
            return results
    
    async def query_sorted(
        self,
        filter_dict: Dict[str, Any],
        sort_field: str,
        ascending: bool = True,
        limit: Optional[int] = None
    ) -> List[T]:
        """Query with sorting and limit."""
        async with self._lock:
            self._operations['queries'] += 1
            
            # Filter first
            results = []
            for entity in self._data.values():
                if self._matches_filter(entity, filter_dict):
                    results.append(deepcopy(entity))
            
            # Sort
            results.sort(
                key=lambda e: self._get_field_value(e, sort_field),
                reverse=not ascending
            )
            
            # Limit
            if limit:
                results = results[:limit]
            
            return results
    
    async def count(self, filter_dict: Dict[str, Any]) -> int:
        """Count entities matching filter."""
        async with self._lock:
            count = 0
            for entity in self._data.values():
                if self._matches_filter(entity, filter_dict):
                    count += 1
            return count
    
    # IArchivableAdapter implementation
    
    async def archive(self, key: str, entity: T, metadata: Dict[str, Any]) -> None:
        """Archive entity with metadata."""
        async with self._lock:
            timestamp = metadata.get('timestamp', datetime.utcnow())
            await self._archive_internal(key, entity, timestamp)
    
    async def get_archive_history(
        self,
        key: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Tuple[datetime, T]]:
        """Get archive history for an entity."""
        async with self._lock:
            if key not in self._archives:
                return []
            
            history = self._archives[key]
            
            # Filter by date range if specified
            if start_date or end_date:
                filtered = []
                for timestamp, entity in history:
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                    filtered.append((timestamp, deepcopy(entity)))
                return filtered
            
            # Return all history
            return [(ts, deepcopy(entity)) for ts, entity in history]
    
    async def prune_archives(self, before_date: datetime) -> int:
        """Remove old archives."""
        async with self._lock:
            pruned = 0
            
            for key in list(self._archives.keys()):
                original_count = len(self._archives[key])
                
                # Keep only archives after the cutoff date
                self._archives[key] = [
                    (ts, entity) for ts, entity in self._archives[key]
                    if ts >= before_date
                ]
                
                pruned += original_count - len(self._archives[key])
                
                # Remove key if no archives left
                if not self._archives[key]:
                    del self._archives[key]
            
            return pruned
    
    # Helper methods
    
    async def _archive_internal(
        self,
        key: str,
        entity: T,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Internal method to archive an entity."""
        if not self._enable_archives:
            return
        
        timestamp = timestamp or datetime.utcnow()
        self._archives[key].append((timestamp, deepcopy(entity)))
        
        # Limit archive history per entity
        if len(self._archives[key]) > self._archive_limit:
            self._archives[key] = self._archives[key][-self._archive_limit:]
    
    def _matches_filter(self, entity: T, filter_dict: Dict[str, Any]) -> bool:
        """Check if entity matches filter criteria."""
        for field, expected_value in filter_dict.items():
            actual_value = self._get_field_value(entity, field)
            if actual_value != expected_value:
                return False
        return True
    
    def _get_field_value(self, entity: T, field: str) -> Any:
        """Get field value from entity, supporting nested fields."""
        # Support dot notation for nested fields
        fields = field.split('.')
        value = entity
        
        for f in fields:
            if hasattr(value, f):
                value = getattr(value, f)
            elif isinstance(value, dict) and f in value:
                value = value[f]
            else:
                return None
        
        return value