"""
Base classes and interfaces for the persistence abstraction layer.

This module provides the foundation for implementing different persistence
backends while maintaining a consistent interface for the application layer.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


# Type variable for entity types
T = TypeVar('T')


class PersistenceBackend(Enum):
    """Available persistence backends."""
    MEMORY = "memory"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    FILESYSTEM = "filesystem"
    S3 = "s3"


@dataclass
class PersistenceConfig:
    """Configuration for persistence backends."""
    backend: PersistenceBackend
    connection_string: Optional[str] = None
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}


class IPersistenceAdapter(ABC, Generic[T]):
    """
    Abstract base class for persistence adapters.
    
    This interface allows different storage backends to be used
    interchangeably without changing the repository implementation.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """
        Retrieve an entity by its key.
        
        Args:
            key: The unique identifier
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """
        Retrieve multiple entities by their keys.
        
        Args:
            keys: List of unique identifiers
            
        Returns:
            Dictionary mapping keys to entities
        """
        pass
    
    @abstractmethod
    async def save(self, key: str, entity: T) -> None:
        """
        Save or update an entity.
        
        Args:
            key: The unique identifier
            entity: The entity to save
        """
        pass
    
    @abstractmethod
    async def save_many(self, entities: Dict[str, T]) -> None:
        """
        Save or update multiple entities.
        
        Args:
            entities: Dictionary mapping keys to entities
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete an entity.
        
        Args:
            key: The unique identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple entities.
        
        Args:
            keys: List of unique identifiers
            
        Returns:
            Number of entities deleted
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if an entity exists.
        
        Args:
            key: The unique identifier
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all entities from storage."""
        pass
    
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get adapter-specific metrics.
        
        Returns:
            Dictionary of metrics
        """
        pass


class ITransactionalAdapter(IPersistenceAdapter[T]):
    """
    Extension of persistence adapter with transaction support.
    
    Not all backends support transactions, so this is a separate interface.
    """
    
    @abstractmethod
    async def begin_transaction(self) -> Any:
        """
        Begin a new transaction.
        
        Returns:
            Transaction handle
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction: Any) -> None:
        """
        Commit a transaction.
        
        Args:
            transaction: Transaction handle from begin_transaction
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction: Any) -> None:
        """
        Rollback a transaction.
        
        Args:
            transaction: Transaction handle from begin_transaction
        """
        pass


class IQueryableAdapter(IPersistenceAdapter[T]):
    """
    Extension of persistence adapter with query support.
    
    For backends that support more complex queries beyond key lookup.
    """
    
    @abstractmethod
    async def query(self, filter_dict: Dict[str, Any]) -> List[T]:
        """
        Query entities by filter criteria.
        
        Args:
            filter_dict: Dictionary of field-value pairs to filter by
            
        Returns:
            List of matching entities
        """
        pass
    
    @abstractmethod
    async def query_sorted(
        self,
        filter_dict: Dict[str, Any],
        sort_field: str,
        ascending: bool = True,
        limit: Optional[int] = None
    ) -> List[T]:
        """
        Query entities with sorting.
        
        Args:
            filter_dict: Dictionary of field-value pairs to filter by
            sort_field: Field to sort by
            ascending: Sort direction
            limit: Maximum number of results
            
        Returns:
            List of matching entities, sorted
        """
        pass
    
    @abstractmethod
    async def count(self, filter_dict: Dict[str, Any]) -> int:
        """
        Count entities matching filter criteria.
        
        Args:
            filter_dict: Dictionary of field-value pairs to filter by
            
        Returns:
            Number of matching entities
        """
        pass


class IArchivableAdapter(IPersistenceAdapter[T]):
    """
    Extension for adapters that support archival operations.
    
    Used for backends that can efficiently store historical data.
    """
    
    @abstractmethod
    async def archive(self, key: str, entity: T, metadata: Dict[str, Any]) -> None:
        """
        Archive an entity with metadata.
        
        Args:
            key: The unique identifier
            entity: The entity to archive
            metadata: Additional metadata (timestamp, reason, etc.)
        """
        pass
    
    @abstractmethod
    async def get_archive_history(
        self,
        key: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Tuple[datetime, T]]:
        """
        Get archive history for an entity.
        
        Args:
            key: The unique identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of (timestamp, entity) tuples
        """
        pass
    
    @abstractmethod
    async def prune_archives(self, before_date: datetime) -> int:
        """
        Remove archives older than specified date.
        
        Args:
            before_date: Remove archives before this date
            
        Returns:
            Number of archives removed
        """
        pass


class BaseRepository(ABC, Generic[T]):
    """
    Base repository class that uses persistence adapters.
    
    This provides a foundation for repositories that can work with
    different storage backends through adapters.
    """
    
    def __init__(self, adapter: IPersistenceAdapter[T]):
        """
        Initialize repository with a persistence adapter.
        
        Args:
            adapter: The persistence adapter to use
        """
        self._adapter = adapter
    
    @property
    def adapter(self) -> IPersistenceAdapter[T]:
        """Get the underlying persistence adapter."""
        return self._adapter
    
    async def switch_adapter(self, new_adapter: IPersistenceAdapter[T]) -> None:
        """
        Switch to a different persistence adapter.
        
        This allows runtime switching of storage backends.
        
        Args:
            new_adapter: The new adapter to use
        """
        # Could add data migration logic here if needed
        self._adapter = new_adapter
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get repository and adapter metrics."""
        return {
            'adapter_type': type(self._adapter).__name__,
            'adapter_metrics': await self._adapter.get_metrics()
        }