"""
Filesystem-based persistence adapter for development and testing.

This adapter stores entities as JSON files on the filesystem,
suitable for development environments and small-scale deployments.
"""

import os
import json
import asyncio
import aiofiles
from typing import Optional, List, Dict, Any, Tuple, TypeVar, Generic
from datetime import datetime
from pathlib import Path
import hashlib
from collections import defaultdict

from .base import (
    IPersistenceAdapter,
    IQueryableAdapter,
    IArchivableAdapter,
    PersistenceConfig,
    PersistenceBackend
)


T = TypeVar('T')


class FilesystemAdapter(IPersistenceAdapter[T], IQueryableAdapter[T], IArchivableAdapter[T], Generic[T]):
    """
    Filesystem-based persistence adapter.
    
    Features:
    - Stores entities as JSON files
    - Supports directories for organization
    - Archive support with timestamped versions
    - Async file operations for non-blocking I/O
    - Simple indexing for queries
    """
    
    def __init__(self, config: Optional[PersistenceConfig] = None):
        """
        Initialize filesystem adapter.
        
        Args:
            config: Configuration with options:
                - base_path: Root directory for storage
                - archive_path: Directory for archives
                - use_compression: Whether to compress files
                - index_fields: Fields to index for queries
        """
        self._config = config or PersistenceConfig(backend=PersistenceBackend.FILESYSTEM)
        
        # Configuration
        self._base_path = Path(self._config.options.get('base_path', './data/persistence'))
        self._archive_path = Path(self._config.options.get('archive_path', './data/archives'))
        self._use_compression = self._config.options.get('use_compression', False)
        self._index_fields = self._config.options.get('index_fields', [])
        
        # Create directories
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._archive_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory index for queries (rebuilt on startup)
        self._index: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self._lock = asyncio.Lock()
        
        # Metrics
        self._operations = {
            'reads': 0,
            'writes': 0,
            'deletes': 0,
            'queries': 0
        }
        
        # Initialize index
        asyncio.create_task(self._rebuild_index())
    
    # IPersistenceAdapter implementation
    
    async def get(self, key: str) -> Optional[T]:
        """Get entity from filesystem."""
        async with self._lock:
            self._operations['reads'] += 1
            
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return None
            
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    data = await f.read()
                    return self._deserialize(json.loads(data))
            except Exception:
                return None
    
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple entities efficiently."""
        tasks = [self.get(key) for key in keys]
        results = await asyncio.gather(*tasks)
        
        return {
            key: result
            for key, result in zip(keys, results)
            if result is not None
        }
    
    async def save(self, key: str, entity: T) -> None:
        """Save entity to filesystem."""
        async with self._lock:
            self._operations['writes'] += 1
            
            # Archive previous version if exists
            file_path = self._get_file_path(key)
            if file_path.exists():
                await self._archive_file(key, file_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize and save
            data = json.dumps(self._serialize(entity), indent=2)
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(data)
            
            # Update index
            await self._update_index_for_entity(key, entity)
    
    async def save_many(self, entities: Dict[str, T]) -> None:
        """Save multiple entities."""
        tasks = [self.save(key, entity) for key, entity in entities.items()]
        await asyncio.gather(*tasks)
    
    async def delete(self, key: str) -> bool:
        """Delete entity from filesystem."""
        async with self._lock:
            self._operations['deletes'] += 1
            
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return False
            
            # Archive before deletion
            await self._archive_file(key, file_path)
            
            # Delete file
            file_path.unlink()
            
            # Update index
            await self._remove_from_index(key)
            
            return True
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple entities."""
        results = await asyncio.gather(
            *[self.delete(key) for key in keys]
        )
        return sum(1 for result in results if result)
    
    async def exists(self, key: str) -> bool:
        """Check if entity exists."""
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix filter."""
        keys = []
        
        for file_path in self._base_path.rglob("*.json"):
            key = self._extract_key_from_path(file_path)
            if key and (not prefix or key.startswith(prefix)):
                keys.append(key)
        
        return sorted(keys)
    
    async def clear(self) -> None:
        """Clear all data and archives."""
        async with self._lock:
            # Clear main storage
            for file_path in self._base_path.rglob("*.json"):
                file_path.unlink()
            
            # Clear archives
            for file_path in self._archive_path.rglob("*.json"):
                file_path.unlink()
            
            # Clear index
            self._index.clear()
            
            # Reset metrics
            for key in self._operations:
                self._operations[key] = 0
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        # Count files
        total_files = sum(1 for _ in self._base_path.rglob("*.json"))
        archive_files = sum(1 for _ in self._archive_path.rglob("*.json"))
        
        # Calculate size
        total_size = sum(
            f.stat().st_size for f in self._base_path.rglob("*.json")
        )
        
        return {
            'total_items': total_files,
            'total_archives': archive_files,
            'operations': dict(self._operations),
            'storage_size_bytes': total_size,
            'index_size': sum(len(items) for field_index in self._index.values() 
                            for items in field_index.values()),
            'backend': 'filesystem',
            'base_path': str(self._base_path),
            'use_compression': self._use_compression
        }
    
    # IQueryableAdapter implementation
    
    async def query(self, filter_dict: Dict[str, Any]) -> List[T]:
        """Query entities by filter criteria."""
        async with self._lock:
            self._operations['queries'] += 1
            
            # If no filter, return all
            if not filter_dict:
                keys = await self.list_keys()
                entities = await self.get_many(keys)
                return list(entities.values())
            
            # Use index for indexed fields
            candidate_keys = None
            for field, value in filter_dict.items():
                if field in self._index:
                    field_keys = set(self._index[field].get(str(value), []))
                    if candidate_keys is None:
                        candidate_keys = field_keys
                    else:
                        candidate_keys &= field_keys
            
            # If we have candidates from index, use them
            if candidate_keys is not None:
                entities = await self.get_many(list(candidate_keys))
                results = []
                for entity in entities.values():
                    if entity and self._matches_filter(entity, filter_dict):
                        results.append(entity)
                return results
            
            # Otherwise, scan all entities
            results = []
            keys = await self.list_keys()
            for key in keys:
                entity = await self.get(key)
                if entity and self._matches_filter(entity, filter_dict):
                    results.append(entity)
            
            return results
    
    async def query_sorted(
        self,
        filter_dict: Dict[str, Any],
        sort_field: str,
        ascending: bool = True,
        limit: Optional[int] = None
    ) -> List[T]:
        """Query with sorting and limit."""
        # Get filtered results
        results = await self.query(filter_dict)
        
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
        results = await self.query(filter_dict)
        return len(results)
    
    # IArchivableAdapter implementation
    
    async def archive(self, key: str, entity: T, metadata: Dict[str, Any]) -> None:
        """Archive entity with metadata."""
        timestamp = metadata.get('timestamp', datetime.utcnow())
        
        # Create archive file path
        archive_dir = self._archive_path / self._get_key_directory(key)
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archive_file = archive_dir / f"{key}_{timestamp.isoformat()}.json"
        
        # Save archive with metadata
        archive_data = {
            'entity': self._serialize(entity),
            'metadata': metadata,
            'archived_at': timestamp.isoformat()
        }
        
        async with aiofiles.open(archive_file, 'w') as f:
            await f.write(json.dumps(archive_data, indent=2))
    
    async def get_archive_history(
        self,
        key: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Tuple[datetime, T]]:
        """Get archive history for an entity."""
        archive_dir = self._archive_path / self._get_key_directory(key)
        if not archive_dir.exists():
            return []
        
        history = []
        
        for archive_file in sorted(archive_dir.glob(f"{key}_*.json")):
            # Extract timestamp from filename
            timestamp_str = archive_file.stem.replace(f"{key}_", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue
            
            # Apply date filters
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue
            
            # Load archive
            try:
                async with aiofiles.open(archive_file, 'r') as f:
                    data = json.loads(await f.read())
                    entity = self._deserialize(data['entity'])
                    history.append((timestamp, entity))
            except Exception:
                continue
        
        return history
    
    async def prune_archives(self, before_date: datetime) -> int:
        """Remove old archives."""
        pruned = 0
        
        for archive_file in self._archive_path.rglob("*.json"):
            # Extract timestamp from filename
            try:
                parts = archive_file.stem.split('_')
                if len(parts) >= 2:
                    timestamp_str = parts[-1]
                    timestamp = datetime.fromisoformat(timestamp_str)
                    
                    if timestamp < before_date:
                        archive_file.unlink()
                        pruned += 1
            except (ValueError, IndexError):
                continue
        
        return pruned
    
    # Helper methods
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key."""
        # Use subdirectories to avoid too many files in one directory
        key_dir = self._get_key_directory(key)
        return self._base_path / key_dir / f"{key}.json"
    
    def _get_key_directory(self, key: str) -> str:
        """Get subdirectory for a key using hash."""
        # Use first 2 chars of hash for directory structure
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{key_hash[:2]}/{key_hash[2:4]}"
    
    def _extract_key_from_path(self, path: Path) -> Optional[str]:
        """Extract key from file path."""
        if path.suffix == '.json':
            return path.stem
        return None
    
    async def _archive_file(self, key: str, file_path: Path) -> None:
        """Archive a file before modification or deletion."""
        if not file_path.exists():
            return
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                data = json.loads(await f.read())
                entity = self._deserialize(data)
                
            await self.archive(key, entity, {
                'timestamp': datetime.utcnow(),
                'reason': 'auto_archive'
            })
        except Exception:
            pass
    
    async def _rebuild_index(self) -> None:
        """Rebuild the index from filesystem."""
        async with self._lock:
            self._index.clear()
            
            keys = await self.list_keys()
            for key in keys:
                entity = await self.get(key)
                if entity:
                    await self._update_index_for_entity(key, entity)
    
    async def _update_index_for_entity(self, key: str, entity: T) -> None:
        """Update index entries for an entity."""
        # Remove old entries
        await self._remove_from_index(key)
        
        # Add new entries for indexed fields
        for field in self._index_fields:
            value = self._get_field_value(entity, field)
            if value is not None:
                self._index[field][str(value)].append(key)
    
    async def _remove_from_index(self, key: str) -> None:
        """Remove entity from all indexes."""
        for field_index in self._index.values():
            for value_list in field_index.values():
                if key in value_list:
                    value_list.remove(key)
    
    def _serialize(self, entity: T) -> Dict[str, Any]:
        """Serialize entity to JSON-compatible format."""
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        elif hasattr(entity, '__dict__'):
            return self._serialize_object(entity)
        else:
            return {'value': str(entity)}
    
    def _serialize_object(self, obj: Any) -> Any:
        """Recursively serialize an object."""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_object(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._serialize_object(v) for k, v in obj.items()}
        elif hasattr(obj, '__dict__'):
            return {
                '__type__': obj.__class__.__name__,
                **{k: self._serialize_object(v) for k, v in obj.__dict__.items()
                   if not k.startswith('_')}
            }
        else:
            return str(obj)
    
    def _deserialize(self, data: Dict[str, Any]) -> T:
        """Deserialize entity from JSON format."""
        # This is a simple implementation
        # In practice, you'd use the entity class to reconstruct
        return data  # Return as dict for now
    
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