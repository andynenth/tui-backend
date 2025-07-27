"""
Archive manager for coordinating hybrid persistence.

Provides high-level interface for archival operations with monitoring.
"""

from typing import Dict, List, Optional, Any, Set, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
from collections import defaultdict
from enum import Enum


from .archive_strategy import (
    ArchivalPolicy, ArchivalRequest, ArchivalResult,
    ArchivalTrigger, ArchivalPriority, ArchivalStrategy,
    GameArchivalStrategy, DEFAULT_GAME_POLICY, DEFAULT_ROOM_POLICY
)
from .archive_worker import ArchivalWorker
from .archive_backends import (
    FileSystemArchiveBackend, IArchivalBackend
)


logger = logging.getLogger(__name__)


@dataclass
class ArchiveQuery:
    """Query parameters for searching archives."""
    entity_type: Optional[str] = None
    entity_ids: Optional[Set[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: Optional[Dict[str, str]] = None
    limit: int = 100
    offset: int = 0


@dataclass
class ArchiveStats:
    """Statistics about archive system."""
    total_entities: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_size_bytes: int = 0
    compression_ratio: float = 0.0
    oldest_archive: Optional[datetime] = None
    newest_archive: Optional[datetime] = None
    
    by_status: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_backend: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    worker_stats: Optional[Dict[str, Any]] = None
    backend_stats: Optional[Dict[str, Any]] = None


class IEntityProvider(Protocol):
    """Protocol for providing entities to archive."""
    
    async def get_entity(self, entity_id: str, entity_type: str) -> Any:
        """Get entity by ID and type."""
        ...
    
    async def list_entities(self, entity_type: str, 
                          filter_func: Optional[callable] = None) -> List[Any]:
        """List entities of given type with optional filter."""
        ...
    
    async def delete_entity(self, entity_id: str, entity_type: str) -> bool:
        """Delete entity from provider."""
        ...


class ArchiveManager:
    """
    Central manager for archive operations.
    
    Coordinates policies, strategies, workers, and backends.
    """
    
    def __init__(
        self,
        entity_provider: IEntityProvider,
        backend: Optional[IArchivalBackend] = None,
        policies: Optional[Dict[str, ArchivalPolicy]] = None,
        enable_worker: bool = True,
        enable_monitoring: bool = True
    ):
        """
        Initialize archive manager.
        
        Args:
            entity_provider: Provider for entities to archive
            backend: Archive backend (defaults to filesystem)
            policies: Archival policies by entity type
            enable_worker: Whether to enable background worker
            enable_monitoring: Whether to enable monitoring
        """
        self.entity_provider = entity_provider
        
        # Setup backend
        self.backend = backend or FileSystemArchiveBackend()
        
        # Setup policies
        self.policies = policies or {
            'game': DEFAULT_GAME_POLICY,
            'room': DEFAULT_ROOM_POLICY
        }
        
        # Setup strategy
        self.strategy = GameArchivalStrategy(self.backend)
        
        # Setup worker
        self.worker = None
        if enable_worker:
            self.worker = ArchivalWorker(
                strategy=self.strategy,
                policies=self.policies
            )
        
        # State tracking
        self._active_archives: Dict[str, ArchivalResult] = {}
        self._archive_index: Dict[str, str] = {}  # entity_id -> location
        
        # Monitoring
        self._enable_monitoring = enable_monitoring
        self._monitor_task = None
        self._stats = ArchiveStats()
    
    async def start(self) -> None:
        """Start archive manager and worker."""
        logger.info("Starting archive manager")
        
        # Start worker
        if self.worker:
            await self.worker.start()
        
        # Start monitoring
        if self._enable_monitoring:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        # Initial scan for entities to archive
        await self._scan_for_archival()
    
    async def stop(self) -> None:
        """Stop archive manager and worker."""
        logger.info("Stopping archive manager")
        
        # Stop monitoring
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop worker
        if self.worker:
            await self.worker.stop()
    
    async def archive_entity(
        self,
        entity_id: str,
        entity_type: str,
        trigger: ArchivalTrigger = ArchivalTrigger.MANUAL,
        priority: ArchivalPriority = ArchivalPriority.NORMAL
    ) -> bool:
        """
        Archive a specific entity.
        
        Args:
            entity_id: Entity ID to archive
            entity_type: Type of entity
            trigger: What triggered the archival
            priority: Priority for archival
            
        Returns:
            True if archival was initiated
        """
        try:
            # Get entity from provider
            entity = await self.entity_provider.get_entity(entity_id, entity_type)
            
            if not entity:
                logger.warning(f"Entity not found: {entity_type}:{entity_id}")
                return False
            
            # Create archival request
            request = ArchivalRequest(
                entity_id=entity_id,
                entity_type=entity_type,
                entity=entity,
                trigger=trigger,
                priority=priority
            )
            
            # Submit to worker or process directly
            if self.worker:
                return await self.worker.submit(request)
            else:
                # Process synchronously
                policy = self.policies.get(entity_type)
                if not policy:
                    logger.warning(f"No policy for entity type: {entity_type}")
                    return False
                
                result = await self.strategy.archive_entity(request, policy)
                
                if result.success:
                    self._update_index(entity_id, result.archive_location)
                    # Optionally delete from provider
                    if trigger == ArchivalTrigger.GAME_COMPLETED:
                        await self.entity_provider.delete_entity(entity_id, entity_type)
                
                return result.success
                
        except Exception as e:
            logger.error(f"Failed to archive entity {entity_id}: {e}")
            return False
    
    async def retrieve_entity(
        self,
        entity_id: str,
        entity_type: str
    ) -> Optional[Any]:
        """
        Retrieve an archived entity.
        
        Args:
            entity_id: Entity ID to retrieve
            entity_type: Type of entity
            
        Returns:
            Retrieved entity or None
        """
        try:
            # Check if we have the location
            location = self._archive_index.get(entity_id)
            
            if not location:
                # Search in backend
                archives = await self.backend.list_archives(
                    entity_type=entity_type
                )
                
                # Look for matching entity
                for archive in archives:
                    if entity_id in archive:
                        location = archive
                        break
            
            if not location:
                logger.warning(f"Archive not found for {entity_id}")
                return None
            
            # Retrieve from backend
            entity = await self.strategy.retrieve_entity(entity_id, location)
            
            # Update stats
            self._stats.by_status['retrieved'] += 1
            
            return entity
            
        except Exception as e:
            logger.error(f"Failed to retrieve entity {entity_id}: {e}")
            return None
    
    async def query_archives(self, query: ArchiveQuery) -> List[Dict[str, Any]]:
        """
        Query archived entities.
        
        Args:
            query: Query parameters
            
        Returns:
            List of archive metadata
        """
        results = []
        
        try:
            # Get archives from backend
            archives = await self.backend.list_archives(
                entity_type=query.entity_type or 'game',
                start_date=query.start_date,
                end_date=query.end_date
            )
            
            # Apply filters
            for archive_location in archives:
                # Skip if not in requested IDs
                if query.entity_ids:
                    found = False
                    for entity_id in query.entity_ids:
                        if entity_id in archive_location:
                            found = True
                            break
                    if not found:
                        continue
                
                # Get metadata (mock for now)
                metadata = {
                    'location': archive_location,
                    'entity_type': query.entity_type,
                    'archived_at': datetime.utcnow().isoformat()
                }
                
                results.append(metadata)
                
                # Apply limit
                if len(results) >= query.limit:
                    break
            
            return results[query.offset:query.offset + query.limit]
            
        except Exception as e:
            logger.error(f"Failed to query archives: {e}")
            return []
    
    async def cleanup_old_archives(
        self,
        entity_type: Optional[str] = None,
        older_than: Optional[timedelta] = None
    ) -> int:
        """
        Clean up old archives based on retention policies.
        
        Args:
            entity_type: Specific entity type to clean
            older_than: Override retention period
            
        Returns:
            Number of archives deleted
        """
        deleted = 0
        
        try:
            # Determine entity types to process
            entity_types = [entity_type] if entity_type else list(self.policies.keys())
            
            for etype in entity_types:
                policy = self.policies.get(etype)
                if not policy:
                    continue
                
                # Determine cutoff date
                retention = older_than or policy.retention_period
                if not retention:
                    continue
                
                cutoff_date = datetime.utcnow() - retention
                
                # Get old archives
                archives = await self.backend.list_archives(
                    entity_type=etype,
                    end_date=cutoff_date
                )
                
                # Delete old archives
                for archive_location in archives:
                    if await self.backend.delete(archive_location):
                        deleted += 1
                        logger.info(f"Deleted old archive: {archive_location}")
            
            self._stats.by_status['deleted'] += deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup archives: {e}")
        
        return deleted
    
    async def compress_archives(
        self,
        entity_type: Optional[str] = None,
        compress_after: Optional[timedelta] = None
    ) -> int:
        """
        Compress old archives for storage efficiency.
        
        Args:
            entity_type: Specific entity type to compress
            compress_after: Override compression age
            
        Returns:
            Number of archives compressed
        """
        compressed = 0
        
        # Note: Compression is handled by backends
        # This is a placeholder for triggering compression
        
        logger.info(f"Archive compression requested for {entity_type or 'all'}")
        
        return compressed
    
    async def backup_archives(
        self,
        destination: str,
        entity_type: Optional[str] = None
    ) -> int:
        """
        Backup archives to another location.
        
        Args:
            destination: Backup destination
            entity_type: Specific entity type to backup
            
        Returns:
            Number of archives backed up
        """
        backed_up = 0
        
        logger.info(f"Archive backup requested to {destination}")
        
        # Note: Backup implementation depends on backend
        # This is a placeholder
        
        return backed_up
    
    async def get_stats(self) -> ArchiveStats:
        """Get comprehensive archive statistics."""
        # Update stats
        self._stats.worker_stats = self.worker.get_status() if self.worker else None
        
        # Get backend metrics if available
        if hasattr(self.backend, 'get_metrics'):
            self._stats.backend_stats = self.backend.get_metrics()
        
        # Get archive counts by type
        for entity_type in self.policies.keys():
            archives = await self.backend.list_archives(entity_type)
            self._stats.total_entities[entity_type] = len(archives)
        
        return self._stats
    
    async def _scan_for_archival(self) -> None:
        """Scan entities and submit for archival based on policies."""
        try:
            for entity_type, policy in self.policies.items():
                # Get entities from provider
                entities = await self.entity_provider.list_entities(entity_type)
                
                current_time = datetime.utcnow()
                submitted = 0
                
                for entity in entities:
                    # Check if should archive
                    if policy.should_archive(entity, current_time):
                        # Determine trigger
                        trigger = ArchivalTrigger.TIME_BASED
                        if hasattr(entity, 'status') and entity.status == 'completed':
                            trigger = ArchivalTrigger.GAME_COMPLETED
                        
                        # Submit for archival
                        success = await self.archive_entity(
                            entity_id=entity.id,
                            entity_type=entity_type,
                            trigger=trigger
                        )
                        
                        if success:
                            submitted += 1
                
                if submitted > 0:
                    logger.info(
                        f"Submitted {submitted} {entity_type} entities for archival"
                    )
                    
        except Exception as e:
            logger.error(f"Error scanning for archival: {e}")
    
    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                # Periodic scan for archival
                await self._scan_for_archival()
                
                # Periodic cleanup
                if datetime.utcnow().hour == 2:  # Run at 2 AM
                    deleted = await self.cleanup_old_archives()
                    if deleted > 0:
                        logger.info(f"Cleaned up {deleted} old archives")
                
                # Log stats periodically
                stats = await self.get_stats()
                total_entities = sum(stats.total_entities.values())
                
                if total_entities > 0:
                    logger.info(
                        f"Archive stats: {total_entities} total entities, "
                        f"worker: {stats.worker_stats['state'] if stats.worker_stats else 'disabled'}"
                    )
                
                # Sleep for monitoring interval
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    def _update_index(self, entity_id: str, location: str) -> None:
        """Update archive index."""
        self._archive_index[entity_id] = location
        self._stats.by_status['archived'] += 1