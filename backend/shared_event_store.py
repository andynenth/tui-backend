# backend/shared_event_store.py
"""
Shared event store instance for the entire backend.
This module prevents circular imports by providing a single point of access.
"""

import logging
from backend.services.migration_adapter import MigrationAdapter

logger = logging.getLogger(__name__)

# Create the shared event store instance
# MigrationAdapter provides the interface to the v2 OptimizedEventStore
event_store = MigrationAdapter()

logger.info(
    "Shared event store initialized as MigrationAdapter (v2 OptimizedEventStore)"
)

# Export for easy importing
__all__ = ["event_store"]
