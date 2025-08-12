# backend/services/realtime_game_system.py

import logging
import os
from typing import Dict, Any, Optional

from backend.api.services.event_store import event_store
from backend.services.event_store_v2 import EventStoreV2
from backend.services.game_cache import (
    GameCache,
    initialize_game_cache,
    shutdown_game_cache,
)
from backend.services.cached_event_store import CachedEventStore
from backend.services.historical_writer import (
    HistoricalWriter,
    initialize_historical_writer,
    shutdown_historical_writer,
)
from backend.services.cached_game_recovery import CachedGameRecoveryService

logger = logging.getLogger(__name__)


class RealtimeGameSystem:
    """
    Integrated real-time game system with caching and async writes.

    Phase 4 of database optimization - Combines all components for
    <100ms game response times with efficient historical storage.

    Components:
    - GameCache: In-memory cache for active games
    - CachedEventStore: Write-through cache integration
    - HistoricalWriter: Async batch writing for historical data
    - CachedGameRecovery: Fast game recovery from cache
    """

    def __init__(self):
        """Initialize the real-time game system."""
        self.cache: Optional[GameCache] = None
        self.cached_store: Optional[CachedEventStore] = None
        self.historical_writer: Optional[HistoricalWriter] = None
        self.recovery_service: Optional[CachedGameRecoveryService] = None

        # Configuration
        self.use_v2 = os.getenv("DB_V2_PRIMARY", "false").lower() == "true"
        self.cache_enabled = (
            os.getenv("REALTIME_CACHE_ENABLED", "true").lower() == "true"
        )
        self.async_writes = (
            os.getenv("ASYNC_HISTORICAL_WRITES", "true").lower() == "true"
        )

        # Cache configuration
        self.cache_size = int(os.getenv("GAME_CACHE_SIZE", "100"))
        self.cache_ttl = int(os.getenv("GAME_CACHE_TTL", "3600"))

        # Historical writer configuration
        self.batch_size = int(os.getenv("HISTORICAL_BATCH_SIZE", "50"))
        self.batch_interval = float(os.getenv("HISTORICAL_BATCH_INTERVAL", "5.0"))

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all system components."""
        if self._initialized:
            return

        logger.info("Initializing RealtimeGameSystem...")

        # Initialize cache if enabled
        if self.cache_enabled:
            self.cache = await initialize_game_cache(
                max_size=self.cache_size, ttl_seconds=self.cache_ttl
            )
        else:
            logger.info("Cache disabled by configuration")

        # Initialize v2 store if enabled
        v2_store = None
        if self.use_v2:
            v2_store = EventStoreV2()

        # Initialize cached event store
        self.cached_store = CachedEventStore(
            cache=self.cache,
            v1_store=event_store if not self.use_v2 else None,
            v2_store=v2_store,
            use_v2=self.use_v2,
        )

        # Initialize historical writer if async writes enabled
        if self.async_writes:
            self.historical_writer = await initialize_historical_writer(
                v1_store=event_store if not self.use_v2 else None,
                v2_store=v2_store,
                batch_size=self.batch_size,
                batch_interval=self.batch_interval,
            )
        else:
            logger.info("Async historical writes disabled by configuration")

        # Initialize recovery service
        self.recovery_service = CachedGameRecoveryService(self.cached_store)

        # Preload active games into cache
        if self.cache_enabled:
            await self.cached_store.preload_active_games()

        self._initialized = True
        logger.info("RealtimeGameSystem initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown all system components."""
        if not self._initialized:
            return

        logger.info("Shutting down RealtimeGameSystem...")

        # Shutdown historical writer (flushes pending writes)
        if self.historical_writer:
            await shutdown_historical_writer()

        # Shutdown cache
        if self.cache:
            await shutdown_game_cache()

        self._initialized = False
        logger.info("RealtimeGameSystem shutdown complete")

    async def store_game_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
        priority: bool = False,
    ) -> None:
        """
        Store a game event with real-time caching.

        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
            player_id: Optional player identifier
            priority: Whether this is a priority event
        """
        if not self._initialized:
            await self.initialize()

        # Determine if this is a real-time critical event
        is_realtime = self._is_realtime_event(event_type)

        if is_realtime or not self.async_writes:
            # Write through cache for real-time events
            await self.cached_store.store_event(room_id, event_type, payload, player_id)
        else:
            # Queue for async write for historical events
            if self.historical_writer:
                await self.historical_writer.queue_event(
                    room_id, event_type, payload, priority
                )
            else:
                # Fallback to synchronous write
                await self.cached_store.store_event(
                    room_id, event_type, payload, player_id
                )

    def _is_realtime_event(self, event_type: str) -> bool:
        """Determine if an event requires real-time processing."""
        realtime_events = {
            "game_started",
            "phase_change",
            "player_action",
            "turn_completed",
            "round_completed",
            "game_completed",
            "game_over",
        }
        return event_type in realtime_events

    async def get_game_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get game state from cache or database.

        Args:
            room_id: Room identifier

        Returns:
            Game state or None
        """
        if not self._initialized:
            await self.initialize()

        return await self.cached_store.get_game_state(room_id)

    async def recover_game(self, room_id: str):
        """
        Recover a game using the cached recovery service.

        Args:
            room_id: Room identifier

        Returns:
            Recovered game instance or None
        """
        if not self._initialized:
            await self.initialize()

        return await self.recovery_service.recover_game(room_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        metrics = {
            "initialized": self._initialized,
            "cache_enabled": self.cache_enabled,
            "async_writes": self.async_writes,
            "use_v2": self.use_v2,
        }

        if self.cached_store:
            metrics["event_store"] = self.cached_store.get_metrics()

        if self.historical_writer:
            metrics["historical_writer"] = self.historical_writer.get_metrics()

        if self.recovery_service:
            metrics["recovery"] = self.recovery_service.get_metrics()

        return metrics

    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health = {
            "status": "healthy" if self._initialized else "not_initialized",
            "components": {},
        }

        # Check cache
        if self.cache:
            cache_metrics = self.cache.get_metrics()
            health["components"]["cache"] = {
                "status": "healthy",
                "size": cache_metrics["size"],
                "hit_rate": cache_metrics["hit_rate"],
            }

        # Check historical writer
        if self.historical_writer:
            writer_metrics = self.historical_writer.get_metrics()
            queue_size = writer_metrics["total_queue_size"]
            health["components"]["historical_writer"] = {
                "status": "healthy" if queue_size < 1000 else "backlogged",
                "queue_size": queue_size,
                "write_errors": writer_metrics["write_errors"],
            }

        # Overall status
        if any(c.get("status") != "healthy" for c in health["components"].values()):
            health["status"] = "degraded"

        return health


# Global instance
_realtime_system: Optional[RealtimeGameSystem] = None


def get_realtime_system() -> RealtimeGameSystem:
    """Get the global real-time game system instance."""
    global _realtime_system
    if _realtime_system is None:
        _realtime_system = RealtimeGameSystem()
    return _realtime_system


async def initialize_realtime_system() -> RealtimeGameSystem:
    """Initialize the global real-time game system."""
    system = get_realtime_system()
    await system.initialize()
    return system


async def shutdown_realtime_system() -> None:
    """Shutdown the global real-time game system."""
    global _realtime_system
    if _realtime_system:
        await _realtime_system.shutdown()
        _realtime_system = None
