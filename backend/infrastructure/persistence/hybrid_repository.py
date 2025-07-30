"""
Hybrid repository implementation that combines memory and async persistence.

This implementation provides:
- Fast in-memory access for active entities
- Async archival for completed/inactive entities
- Seamless fallback between backends
- No performance impact on real-time operations
"""

import asyncio
from typing import Optional, List, Dict, Any, TypeVar, Generic, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from enum import Enum

from .base import (
    IPersistenceAdapter,
    IQueryableAdapter,
    IArchivableAdapter,
    BaseRepository,
)
from .memory_adapter import MemoryAdapter


T = TypeVar("T")


class EntityState(Enum):
    """State of an entity in the hybrid system."""

    ACTIVE = "active"  # In memory, frequently accessed
    ARCHIVED = "archived"  # In persistent storage only
    CACHED = "cached"  # In both memory and storage


class ArchivalPolicy(ABC):
    """
    Abstract base class for archival policies.

    Determines when entities should be moved from memory to persistence.
    """

    @abstractmethod
    def should_archive(self, entity: Any, metadata: Dict[str, Any]) -> bool:
        """
        Determine if an entity should be archived.

        Args:
            entity: The entity to check
            metadata: Additional metadata (last_access, created_at, etc.)

        Returns:
            True if entity should be archived
        """
        pass


class TimeBasedArchivalPolicy(ArchivalPolicy):
    """Archive entities based on age or last access time."""

    def __init__(
        self,
        max_age: Optional[timedelta] = None,
        max_idle_time: Optional[timedelta] = None,
    ):
        self.max_age = max_age
        self.max_idle_time = max_idle_time

    def should_archive(self, entity: Any, metadata: Dict[str, Any]) -> bool:
        now = datetime.utcnow()

        # Check age
        if self.max_age and "created_at" in metadata:
            created_at = metadata["created_at"]
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if now - created_at > self.max_age:
                return True

        # Check idle time
        if self.max_idle_time and "last_access" in metadata:
            last_access = metadata["last_access"]
            if isinstance(last_access, str):
                last_access = datetime.fromisoformat(last_access)
            if now - last_access > self.max_idle_time:
                return True

        return False


class CompletionBasedArchivalPolicy(ArchivalPolicy):
    """Archive entities when they're marked as completed."""

    def __init__(self, completion_field: str = "is_completed"):
        self.completion_field = completion_field

    def should_archive(self, entity: Any, metadata: Dict[str, Any]) -> bool:
        # Check entity attribute
        if hasattr(entity, self.completion_field):
            return bool(getattr(entity, self.completion_field))

        # Check entity dict
        if isinstance(entity, dict) and self.completion_field in entity:
            return bool(entity[self.completion_field])

        # Check metadata
        return metadata.get(self.completion_field, False)


class HybridRepository(BaseRepository[T], Generic[T]):
    """
    Hybrid repository that combines fast memory access with async persistence.

    This repository:
    - Keeps active entities in memory for fast access
    - Archives completed/inactive entities to persistent storage
    - Provides transparent access to both layers
    - Maintains performance for real-time operations
    """

    def __init__(
        self,
        memory_adapter: IPersistenceAdapter[T],
        persistent_adapter: Optional[IPersistenceAdapter[T]] = None,
        archival_policy: Optional[ArchivalPolicy] = None,
        archive_batch_size: int = 100,
        archive_interval: float = 60.0,
    ):
        """
        Initialize hybrid repository.

        Args:
            memory_adapter: Fast in-memory adapter
            persistent_adapter: Optional persistent storage adapter
            archival_policy: Policy for determining when to archive
            archive_batch_size: Number of entities to archive at once
            archive_interval: Seconds between archive runs
        """
        super().__init__(memory_adapter)

        self._memory = memory_adapter
        self._persistent = persistent_adapter
        self._policy = archival_policy or TimeBasedArchivalPolicy(
            max_idle_time=timedelta(hours=1)
        )

        # Archive queue and configuration
        self._archive_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._archive_batch_size = archive_batch_size
        self._archive_interval = archive_interval

        # Entity metadata tracking
        self._metadata: Dict[str, Dict[str, Any]] = {}

        # Background task for archival
        self._archive_task: Optional[asyncio.Task] = None

        # Metrics
        self._metrics = {
            "memory_hits": 0,
            "persistent_hits": 0,
            "archives_queued": 0,
            "archives_completed": 0,
            "archive_failures": 0,
        }

    async def start(self) -> None:
        """Start background archival process."""
        if self._persistent and not self._archive_task:
            self._archive_task = asyncio.create_task(self._archive_worker())

    async def stop(self) -> None:
        """Stop background archival process."""
        if self._archive_task:
            self._archive_task.cancel()
            try:
                await self._archive_task
            except asyncio.CancelledError:
                pass
            self._archive_task = None

    # Repository interface implementation

    async def get(self, key: str) -> Optional[T]:
        """
        Get entity by key, checking memory first then persistence.

        Fast path: Memory hit (microseconds)
        Slow path: Persistent storage hit (milliseconds)
        """
        # Try memory first (fast path)
        entity = await self._memory.get(key)
        if entity is not None:
            self._metrics["memory_hits"] += 1
            self._update_metadata(key, {"last_access": datetime.utcnow()})
            return entity

        # Try persistent storage if available (slow path)
        if self._persistent:
            entity = await self._persistent.get(key)
            if entity is not None:
                self._metrics["persistent_hits"] += 1

                # Optionally restore to memory cache
                # This is configurable based on access patterns
                await self._memory.save(key, entity)
                self._update_metadata(
                    key,
                    {
                        "last_access": datetime.utcnow(),
                        "restored_from_persistent": True,
                    },
                )

                return entity

        return None

    async def save(self, key: str, entity: T) -> None:
        """
        Save entity to memory and optionally queue for persistence.

        Always saves to memory first for immediate availability.
        """
        # Always save to memory first
        await self._memory.save(key, entity)

        # Update metadata
        metadata = self._metadata.get(key, {})
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.utcnow()
        metadata["last_modified"] = datetime.utcnow()
        metadata["last_access"] = datetime.utcnow()
        self._metadata[key] = metadata

        # Check if should archive immediately
        if self._should_archive_immediately(entity, metadata):
            await self._queue_for_archive(key, entity, metadata)

    async def delete(self, key: str) -> bool:
        """Delete from both memory and persistent storage."""
        # Delete from memory
        memory_deleted = await self._memory.delete(key)

        # Delete from persistent storage
        persistent_deleted = False
        if self._persistent:
            persistent_deleted = await self._persistent.delete(key)

        # Clean up metadata
        self._metadata.pop(key, None)

        return memory_deleted or persistent_deleted

    async def query(
        self,
        filter_fn: Optional[Callable[[T], bool]] = None,
        include_archived: bool = False,
    ) -> List[T]:
        """
        Query entities with optional filter.

        By default queries only memory (fast).
        Set include_archived=True to also query persistent storage.
        """
        results = []

        # Query memory
        if hasattr(self._memory, "query"):
            memory_results = await self._memory.query({})
            if filter_fn:
                memory_results = [e for e in memory_results if filter_fn(e)]
            results.extend(memory_results)

        # Optionally query persistent storage
        if include_archived and self._persistent and hasattr(self._persistent, "query"):
            persistent_results = await self._persistent.query({})
            if filter_fn:
                persistent_results = [e for e in persistent_results if filter_fn(e)]

            # Deduplicate (memory takes precedence)
            memory_keys = {self._get_key(e) for e in results}
            for entity in persistent_results:
                if self._get_key(entity) not in memory_keys:
                    results.append(entity)

        return results

    # Archival methods

    async def archive_now(self, key: str) -> bool:
        """
        Force immediate archival of an entity.

        Useful for explicitly moving completed entities to storage.
        """
        entity = await self._memory.get(key)
        if entity is None:
            return False

        metadata = self._metadata.get(key, {})
        return await self._queue_for_archive(key, entity, metadata)

    async def restore_from_archive(self, key: str) -> bool:
        """
        Restore an entity from archive to memory.

        Returns True if restored, False if not found.
        """
        if not self._persistent:
            return False

        entity = await self._persistent.get(key)
        if entity is None:
            return False

        await self._memory.save(key, entity)
        self._update_metadata(
            key, {"last_access": datetime.utcnow(), "restored_at": datetime.utcnow()}
        )

        return True

    # Background archival

    async def _archive_worker(self) -> None:
        """Background worker for processing archive queue."""
        while True:
            try:
                # Collect batch of items to archive
                batch = []
                deadline = asyncio.get_event_loop().time() + self._archive_interval

                while len(batch) < self._archive_batch_size:
                    timeout = max(0, deadline - asyncio.get_event_loop().time())
                    if timeout <= 0:
                        break

                    try:
                        item = await asyncio.wait_for(
                            self._archive_queue.get(), timeout=timeout
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                # Process batch
                if batch:
                    await self._process_archive_batch(batch)

                # Also check for entities that should be archived
                await self._scan_for_archival()

            except asyncio.CancelledError:
                # Graceful shutdown
                break
            except Exception as e:
                # Log error and continue
                self._metrics["archive_failures"] += 1
                await asyncio.sleep(5)  # Brief pause on error

    async def _process_archive_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Process a batch of archive operations."""
        if not self._persistent:
            return

        # Group by operation type for efficiency
        entities_to_save = {}

        for item in batch:
            key = item["key"]
            entity = item["entity"]
            entities_to_save[key] = entity

        # Batch save to persistent storage
        if entities_to_save:
            if hasattr(self._persistent, "save_many"):
                await self._persistent.save_many(entities_to_save)
            else:
                # Fallback to individual saves
                for key, entity in entities_to_save.items():
                    await self._persistent.save(key, entity)

            self._metrics["archives_completed"] += len(entities_to_save)

        # Optionally remove from memory after successful archive
        # This depends on the specific use case
        for item in batch:
            if item.get("remove_from_memory", False):
                await self._memory.delete(item["key"])

    async def _scan_for_archival(self) -> None:
        """Scan memory for entities that should be archived."""
        if not self._persistent:
            return

        # Get all keys from memory
        keys = await self._memory.list_keys()

        for key in keys:
            metadata = self._metadata.get(key, {})

            # Skip if recently accessed
            last_access = metadata.get("last_access")
            if last_access:
                if isinstance(last_access, str):
                    last_access = datetime.fromisoformat(last_access)
                if datetime.utcnow() - last_access < timedelta(minutes=5):
                    continue

            # Check archival policy
            entity = await self._memory.get(key)
            if entity and self._policy.should_archive(entity, metadata):
                await self._queue_for_archive(key, entity, metadata)

    async def _queue_for_archive(
        self, key: str, entity: T, metadata: Dict[str, Any]
    ) -> bool:
        """Queue an entity for archival."""
        if not self._persistent:
            return False

        try:
            archive_item = {
                "key": key,
                "entity": entity,
                "metadata": metadata,
                "queued_at": datetime.utcnow(),
                "remove_from_memory": self._should_remove_from_memory(entity, metadata),
            }

            self._archive_queue.put_nowait(archive_item)
            self._metrics["archives_queued"] += 1
            return True

        except asyncio.QueueFull:
            # Queue is full, skip this archive
            return False

    # Helper methods

    def _should_archive_immediately(self, entity: T, metadata: Dict[str, Any]) -> bool:
        """Check if entity should be archived immediately on save."""
        # For game entities, archive completed games immediately
        if hasattr(entity, "is_completed") and entity.is_completed:
            return True

        # Otherwise use the configured policy
        return self._policy.should_archive(entity, metadata)

    def _should_remove_from_memory(self, entity: T, metadata: Dict[str, Any]) -> bool:
        """Check if entity should be removed from memory after archival."""
        # Keep frequently accessed entities in memory
        access_count = metadata.get("access_count", 0)
        if access_count > 10:
            return False

        # Remove completed entities
        if hasattr(entity, "is_completed") and entity.is_completed:
            return True

        # Remove old entities
        last_access = metadata.get("last_access", datetime.utcnow())
        if isinstance(last_access, str):
            last_access = datetime.fromisoformat(last_access)

        return datetime.utcnow() - last_access > timedelta(hours=1)

    def _update_metadata(self, key: str, updates: Dict[str, Any]) -> None:
        """Update entity metadata."""
        if key not in self._metadata:
            self._metadata[key] = {}

        self._metadata[key].update(updates)

        # Increment access count
        self._metadata[key]["access_count"] = (
            self._metadata[key].get("access_count", 0) + 1
        )

    def _get_key(self, entity: T) -> str:
        """Extract key from entity (implementation-specific)."""
        # This would be customized per entity type
        if hasattr(entity, "id"):
            return str(entity.id)
        elif hasattr(entity, "key"):
            return str(entity.key)
        elif isinstance(entity, dict):
            return str(entity.get("id") or entity.get("key", ""))
        else:
            return str(hash(entity))

    async def get_metrics(self) -> Dict[str, Any]:
        """Get repository metrics."""
        base_metrics = await super().get_metrics()

        hybrid_metrics = {
            "hybrid_metrics": dict(self._metrics),
            "archive_queue_size": self._archive_queue.qsize(),
            "metadata_entries": len(self._metadata),
            "archive_worker_running": self._archive_task is not None
            and not self._archive_task.done(),
        }

        # Add memory adapter metrics
        if hasattr(self._memory, "get_metrics"):
            hybrid_metrics["memory_adapter"] = await self._memory.get_metrics()

        # Add persistent adapter metrics
        if self._persistent and hasattr(self._persistent, "get_metrics"):
            hybrid_metrics["persistent_adapter"] = await self._persistent.get_metrics()

        return {**base_metrics, **hybrid_metrics}
