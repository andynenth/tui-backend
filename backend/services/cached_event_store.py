# backend/services/cached_event_store.py

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.api.services.event_store import EventStore
from backend.services.event_store_v2 import EventStoreV2
from backend.services.game_cache import GameCache, CachedGameState
from backend.models.semantic_events import SemanticEventType

logger = logging.getLogger(__name__)


class CachedEventStore:
    """
    Event store with integrated caching for real-time performance.

    Phase 4 of database optimization - Combines write-through cache
    with event storage for <100ms response times.

    Features:
    - Write-through caching for active games
    - Automatic cache invalidation on game events
    - Seamless fallback to database for cache misses
    - Integration with both v1 and v2 event stores
    """

    def __init__(
        self,
        cache: GameCache,
        v1_store: Optional[EventStore] = None,
        v2_store: Optional[EventStoreV2] = None,
        use_v2: bool = False,
    ):
        """
        Initialize cached event store.

        Args:
            cache: GameCache instance
            v1_store: EventStore v1 instance
            v2_store: EventStore v2 instance
            use_v2: Whether to use v2 store as primary
        """
        self.cache = cache
        self.v1_store = v1_store
        self.v2_store = v2_store
        self.use_v2 = use_v2

        # Metrics
        self._cache_writes = 0
        self._db_writes = 0
        self._cache_reads = 0
        self._db_reads = 0

        logger.info(f"CachedEventStore initialized (use_v2={use_v2})")

    async def get_game_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get game state from cache or database.

        Args:
            room_id: Room identifier

        Returns:
            Game state or None if not found
        """
        # Try cache first
        state = await self.cache.get(room_id)
        if state:
            self._cache_reads += 1
            logger.debug(f"Retrieved game state from cache for room {room_id}")
            return state

        # Cache miss - load from database
        self._db_reads += 1
        state = await self._load_from_database(room_id)

        if state:
            # Populate cache for next time
            await self.cache.set(room_id, state, write_through=False)
            logger.debug(f"Loaded game state from database for room {room_id}")

        return state

    async def store_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Store event and update cache.

        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
            player_id: Optional player identifier
        """
        # Store in database
        self._db_writes += 1
        if self.use_v2 and self.v2_store:
            await self._store_v2_event(room_id, event_type, payload)
        elif self.v1_store:
            await self.v1_store.store_event_buffered(
                room_id, event_type, payload, player_id
            )

        # Update cache based on event type
        await self._update_cache_for_event(room_id, event_type, payload)
        self._cache_writes += 1

    async def _store_v2_event(
        self, room_id: str, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """Store event in v2 schema."""
        if event_type == "game_started":
            players = payload.get("players", [])
            await self.v2_store.store_game_started(room_id, players)

        elif event_type in ["game_completed", "game_over"]:
            final_scores = payload.get("final_scores", {})
            winner = payload.get("winner", "")
            await self.v2_store.store_game_completed(room_id, final_scores, winner)

        elif event_type == "round_completed":
            # Store round snapshot
            round_data = await self._build_round_snapshot(room_id, payload)
            if round_data:
                round_number = round_data.get("round_number", 1)
                await self.v2_store.store_round_snapshot(
                    room_id, round_number, round_data
                )

    async def _update_cache_for_event(
        self, room_id: str, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """
        Update cached game state based on event.

        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
        """
        # Get current state
        state = await self.cache.get(room_id)
        if not state:
            # Not in cache, no need to update
            return

        # Update state based on event type
        if event_type == "game_started":
            state["status"] = "active"
            state["players"] = payload.get("players", [])
            state["started_at"] = datetime.now().isoformat()

        elif event_type == "phase_change":
            state["current_phase"] = payload.get("new_phase")
            state["phase_data"] = payload.get("phase_data", {})

        elif event_type == "round_completed":
            state["round_number"] = payload.get("round_number", 1)
            state["scores"] = payload.get("total_scores", {})

        elif event_type in ["game_completed", "game_over"]:
            state["status"] = "completed"
            state["final_scores"] = payload.get("final_scores", {})
            state["winner"] = payload.get("winner")
            state["completed_at"] = datetime.now().isoformat()

            # Completed games can be evicted from cache
            await self.cache.invalidate(room_id)
            return

        # Update cache with new state
        await self.cache.set(room_id, state)

    async def _load_from_database(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Load game state from database.

        Args:
            room_id: Room identifier

        Returns:
            Game state or None if not found
        """
        if self.use_v2 and self.v2_store:
            # Load from v2 schema
            summary = await self.v2_store.get_game_summary(room_id)
            if summary:
                # Get latest round data
                rounds = await self.v2_store.get_round_snapshots(room_id)
                latest_round = rounds[-1] if rounds else None

                return {
                    "room_id": room_id,
                    "status": "active" if summary["is_active"] else "completed",
                    "players": summary["players"],
                    "round_number": summary["total_rounds"],
                    "current_phase": (
                        latest_round.get("phase") if latest_round else "WAITING"
                    ),
                    "phase_data": (
                        latest_round.get("phase_data") if latest_round else {}
                    ),
                    "scores": (
                        latest_round.get("cumulative_scores") if latest_round else {}
                    ),
                    "started_at": summary["started_at"],
                    "completed_at": summary.get("completed_at"),
                }

        elif self.v1_store:
            # Load from v1 by reconstructing from events
            events = await self.v1_store.get_room_events(room_id, limit=1000)
            if not events:
                return None

            # Reconstruct state from events
            state = {"room_id": room_id}
            for event in events:
                # Apply event to state (simplified)
                if event.event_type == "game_started":
                    state["status"] = "active"
                    state["players"] = event.payload.get("players", [])
                elif event.event_type == "phase_change":
                    state["current_phase"] = event.payload.get("new_phase")
                    state["phase_data"] = event.payload.get("phase_data", {})
                # ... etc

            return state

        return None

    async def _build_round_snapshot(
        self, room_id: str, round_complete_payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Build round snapshot from current game state."""
        # Get current state from cache
        state = await self.cache.get(room_id)
        if not state:
            return None

        return {
            "round_number": round_complete_payload.get("round_number", 1),
            "starter_player": state.get("starter_player", ""),
            "starter_reason": state.get("starter_reason", "default"),
            "initial_hands": state.get("initial_hands", {}),
            "declarations": state.get("declarations", {}),
            "turn_sequence": state.get("turn_sequence", []),
            "round_scores": round_complete_payload.get("scores", {}),
            "cumulative_scores": round_complete_payload.get("total_scores", {}),
        }

    async def get_active_games(self) -> List[str]:
        """Get list of active game room IDs."""
        if self.use_v2 and self.v2_store:
            games = await self.v2_store.get_active_games()
            return [g["room_id"] for g in games]
        else:
            # For v1, this would need to be tracked separately
            return []

    async def preload_active_games(self) -> None:
        """Preload active games into cache on startup."""
        active_games = await self.get_active_games()
        if active_games:
            logger.info(f"Preloading {len(active_games)} active games")
            room_ids = set(active_games[: self.cache.max_size])  # Limit to cache size
            await self.cache.preload(room_ids)

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        total_reads = self._cache_reads + self._db_reads
        cache_hit_rate = self._cache_reads / total_reads if total_reads > 0 else 0.0

        return {
            "cache_reads": self._cache_reads,
            "db_reads": self._db_reads,
            "cache_writes": self._cache_writes,
            "db_writes": self._db_writes,
            "cache_hit_rate": cache_hit_rate,
            "cache_metrics": self.cache.get_metrics(),
        }

    async def get_cached_game_state(self, room_id: str) -> Optional[CachedGameState]:
        """
        Get a CachedGameState wrapper for convenient updates.

        Args:
            room_id: Room identifier

        Returns:
            CachedGameState or None if game not found
        """
        state = await self.get_game_state(room_id)
        if state:
            return CachedGameState(room_id, self.cache, state)
        return None
