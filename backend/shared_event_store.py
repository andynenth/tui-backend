# backend/shared_event_store.py
"""
Shared event store instance for the entire backend.
This module prevents circular imports by providing a single point of access.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Determine which event store to use based on configuration
MIGRATION_MODE = os.getenv("MIGRATION_MODE", "v2_only").lower()

# Use MigrationAdapter for all modes except v1_only
if MIGRATION_MODE != "v1_only":
    logger.debug(f"🔍 DEBUG: shared_event_store.py using MigrationAdapter (mode: {MIGRATION_MODE})")
    from backend.services.migration_adapter import MigrationAdapter

    event_store = MigrationAdapter()
    logger.debug(f"🔍 DEBUG: shared_event_store created MigrationAdapter instance")
else:
    logger.debug("🔍 DEBUG: shared_event_store.py using legacy EventStore (v1_only mode)")
    from backend.api.services.event_store import EventStore

    event_store = EventStore()
    logger.debug(f"🔍 DEBUG: shared_event_store created EventStore instance")

logger.info(f"Shared event store initialized as: {type(event_store).__name__}")

# Export for easy importing
__all__ = ["event_store"]
