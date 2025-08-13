# backend/services/migration_adapter.py

import logging
from typing import Dict, Any, Optional

from backend.services.optimized_event_store import OptimizedEventStore

logger = logging.getLogger(__name__)


class MigrationAdapter:
    """
    Adapter for v2 event storage system.
    
    This adapter provides a consistent interface to the OptimizedEventStore
    which uses compression, buffering, and an optimized database schema.
    """

    def __init__(self):
        """Initialize adapter with v2 OptimizedEventStore."""
        logger.info("🔍 DEBUG: MigrationAdapter.__init__ called")
        
        # Always use v2_only mode
        self.mode = "v2_only"
        self.v2_store = OptimizedEventStore()
        
        logger.info("MigrationAdapter initialized in v2_only mode")
        logger.info("MigrationAdapter: Initialized v2 OptimizedEventStore")

    async def store_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Store event using v2 OptimizedEventStore.
        """
        logger.info(
            f"🔍 DEBUG: MigrationAdapter.store_event - room: {room_id}, type: {event_type}"
        )
        logger.debug(
            f"🔍 DEBUG: MigrationAdapter payload keys: {list(payload.keys()) if payload else 'None'}"
        )
        logger.debug(f"🔍 DEBUG: MigrationAdapter player_id: {player_id}")
        
        # Always use v2 store
        await self.v2_store.store_event(room_id, event_type, payload, player_id)

    async def store_event_buffered(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Compatibility method for buffered storage.
        V2 OptimizedEventStore handles buffering internally.
        """
        # V2 handles buffering internally
        await self.v2_store.store_event(room_id, event_type, payload, player_id)

    async def flush_room(self, room_id: str) -> None:
        """Flush any pending events for a room."""
        await self.v2_store.flush_room(room_id)

    async def shutdown(self) -> None:
        """Graceful shutdown of v2 store."""
        logger.info("MigrationAdapter shutting down...")
        
        try:
            await self.v2_store.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down v2 store: {e}")
            
        logger.info("MigrationAdapter shutdown complete")

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from v2 store."""
        return {
            "migration_mode": self.mode,
            "stores_active": {
                "v1": False,
                "v2": True,
            },
            "v2_metrics": self.v2_store.get_metrics()
        }

    # Properties for compatibility
    @property
    def db_path(self):
        """Get database path for compatibility."""
        return self.v2_store.v2_store.db_path
