# backend/services/migration_adapter.py

import logging
import os
from typing import Dict, Any, Optional

from backend.api.services.event_store import EventStore
from backend.services.optimized_event_store import OptimizedEventStore

logger = logging.getLogger(__name__)


class MigrationAdapter:
    """
    Manages migration from v1 to v2 event storage.
    
    Supports multiple migration strategies:
    - v1_only: Use only old schema (rollback mode)
    - v2_only: Use only new optimized schema
    - dual_write: Write to both schemas (migration mode)
    - dual_read_v1: Write to both, read from v1 (testing mode)
    - dual_read_v2: Write to both, read from v2 (validation mode)
    """
    
    def __init__(self):
        """Initialize migration adapter based on environment configuration."""
        
        # Get migration mode
        self.mode = os.getenv("MIGRATION_MODE", "v2_only").lower()
        
        # Initialize stores based on mode
        if self.mode in ["v1_only", "dual_write", "dual_read_v1", "dual_read_v2"]:
            self.v1_store = EventStore()
            logger.info("MigrationAdapter: Initialized v1 EventStore")
        else:
            self.v1_store = None
            
        if self.mode in ["v2_only", "dual_write", "dual_read_v1", "dual_read_v2"]:
            self.v2_store = OptimizedEventStore()
            logger.info("MigrationAdapter: Initialized v2 OptimizedEventStore")
        else:
            self.v2_store = None
        
        logger.info(f"MigrationAdapter initialized in '{self.mode}' mode")
        
        # Validate configuration
        if not self.v1_store and not self.v2_store:
            raise ValueError(f"Invalid migration mode: {self.mode}")
    
    async def store_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None
    ) -> None:
        """
        Store event based on migration mode.
        """
        
        if self.mode == "v1_only":
            # Only write to v1 (rollback mode)
            await self.v1_store.store_event(room_id, event_type, payload, player_id)
            
        elif self.mode == "v2_only":
            # Only write to v2 (full migration)
            await self.v2_store.store_event(room_id, event_type, payload, player_id)
            
        elif self.mode in ["dual_write", "dual_read_v1", "dual_read_v2"]:
            # Write to both schemas
            errors = []
            
            # Try v1 write
            if self.v1_store:
                try:
                    await self.v1_store.store_event(room_id, event_type, payload, player_id)
                except Exception as e:
                    logger.error(f"Failed to write to v1 store: {e}")
                    errors.append(("v1", e))
            
            # Try v2 write
            if self.v2_store:
                try:
                    await self.v2_store.store_event(room_id, event_type, payload, player_id)
                except Exception as e:
                    logger.error(f"Failed to write to v2 store: {e}")
                    errors.append(("v2", e))
            
            # If both writes failed, raise exception
            if len(errors) == 2:
                raise Exception(f"Both v1 and v2 writes failed: {errors}")
    
    async def store_event_buffered(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None
    ) -> None:
        """
        Compatibility method for buffered storage.
        Routes to appropriate store based on mode.
        """
        
        if self.mode == "v1_only" and self.v1_store:
            await self.v1_store.store_event_buffered(room_id, event_type, payload, player_id)
        elif self.mode == "v2_only" and self.v2_store:
            await self.v2_store.store_event(room_id, event_type, payload, player_id)
        else:
            # Dual mode - use store_event which handles both
            await self.store_event(room_id, event_type, payload, player_id)
    
    async def flush_room(self, room_id: str) -> None:
        """Flush any pending events for a room."""
        
        if self.v2_store:
            await self.v2_store.flush_room(room_id)
        # v1 store doesn't have room-specific flush
    
    async def shutdown(self) -> None:
        """Graceful shutdown of all stores."""
        
        logger.info("MigrationAdapter shutting down...")
        
        if self.v1_store and hasattr(self.v1_store, 'shutdown'):
            try:
                await self.v1_store.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down v1 store: {e}")
        
        if self.v2_store:
            try:
                await self.v2_store.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down v2 store: {e}")
        
        logger.info("MigrationAdapter shutdown complete")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all active stores."""
        
        metrics = {
            'migration_mode': self.mode,
            'stores_active': {
                'v1': self.v1_store is not None,
                'v2': self.v2_store is not None
            }
        }
        
        if self.v1_store and hasattr(self.v1_store, 'get_metrics'):
            metrics['v1_metrics'] = self.v1_store.get_metrics()
        
        if self.v2_store:
            metrics['v2_metrics'] = self.v2_store.get_metrics()
        
        return metrics
    
    # Properties for compatibility
    @property
    def db_path(self):
        """Get database path for compatibility."""
        if self.v2_store:
            return self.v2_store.v2_store.db_path
        elif self.v1_store:
            return self.v1_store.db_path
        return None