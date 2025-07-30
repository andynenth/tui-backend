"""
High-level state persistence management.

Coordinates snapshots, event sourcing, and recovery for state machines.
"""

from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from collections import defaultdict

from .abstractions import (
    IStatePersistence,
    IStateSnapshot,
    IStateTransitionLog,
    IStateRecovery,
    StateTransition,
    PersistedState,
    StateVersion,
    RecoveryPoint,
)
from .snapshot import StateSnapshotManager, SnapshotConfig
from .transition_log import StateTransitionLogger
from .recovery import StateRecoveryManager, RecoveryOptions, RecoveryMode
from .event_sourcing import StateMachineEventStore, EventSourcedStateMachine
from .versioning import StateVersionManager, MigrationRunner, VersionConflictResolver


logger = logging.getLogger(__name__)


class PersistenceStrategy(Enum):
    """Persistence strategies."""

    SNAPSHOT_ONLY = "snapshot_only"
    EVENT_SOURCED = "event_sourced"
    HYBRID = "hybrid"
    VERSIONED = "versioned"


@dataclass
class PersistenceConfig:
    """Configuration for state persistence."""

    strategy: PersistenceStrategy = PersistenceStrategy.HYBRID

    # Snapshot settings
    snapshot_enabled: bool = True
    snapshot_interval: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    max_snapshots_per_state: int = 10
    snapshot_on_shutdown: bool = True

    # Event sourcing settings
    event_sourcing_enabled: bool = True
    max_events_per_state: int = 10000
    compact_events_after: int = 1000

    # Recovery settings
    recovery_enabled: bool = True
    recovery_mode: RecoveryMode = RecoveryMode.HYBRID
    auto_recovery: bool = True

    # Performance settings
    cache_enabled: bool = True
    cache_size: int = 1000
    batch_operations: bool = True
    batch_size: int = 100

    # Archival settings
    archive_completed_states: bool = True
    archive_after: timedelta = field(default_factory=lambda: timedelta(hours=24))
    compression_enabled: bool = True


@dataclass
class AutoPersistencePolicy:
    """Policy for automatic persistence."""

    persist_on_transition: bool = True
    persist_on_update: bool = True
    persist_on_error: bool = True
    persist_interval: Optional[timedelta] = field(
        default_factory=lambda: timedelta(seconds=30)
    )
    persist_on_phase_change: bool = True

    def should_persist(self, event_type: str) -> bool:
        """Check if event should trigger persistence."""
        if event_type == "transition" and self.persist_on_transition:
            return True
        elif event_type == "update" and self.persist_on_update:
            return True
        elif event_type == "error" and self.persist_on_error:
            return True
        elif event_type == "phase_change" and self.persist_on_phase_change:
            return True
        return False


@dataclass
class PersistenceMetrics:
    """Metrics for persistence operations."""

    total_saves: int = 0
    total_loads: int = 0
    total_snapshots: int = 0
    total_recoveries: int = 0
    failed_operations: int = 0
    average_save_time_ms: float = 0.0
    average_load_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    def record_save(self, duration_ms: float) -> None:
        """Record save operation."""
        self.total_saves += 1
        self.average_save_time_ms = (
            self.average_save_time_ms * (self.total_saves - 1) + duration_ms
        ) / self.total_saves

    def record_load(self, duration_ms: float, cache_hit: bool = False) -> None:
        """Record load operation."""
        self.total_loads += 1
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.average_load_time_ms = (
            self.average_load_time_ms * (self.total_loads - 1) + duration_ms
        ) / self.total_loads


@dataclass
class StatePersistenceMetrics:
    """Extended metrics for state persistence."""

    base_metrics: PersistenceMetrics = field(default_factory=PersistenceMetrics)
    by_state_machine: Dict[str, PersistenceMetrics] = field(default_factory=dict)

    def get_metrics(self, state_machine_id: Optional[str] = None) -> PersistenceMetrics:
        """Get metrics for state machine or global."""
        if state_machine_id:
            if state_machine_id not in self.by_state_machine:
                self.by_state_machine[state_machine_id] = PersistenceMetrics()
            return self.by_state_machine[state_machine_id]
        return self.base_metrics


class StatePersistenceManager:
    """
    High-level state persistence manager.

    Features:
    - Multiple persistence strategies
    - Automatic persistence policies
    - Performance optimization
    - Metrics collection
    """

    def __init__(
        self,
        config: PersistenceConfig,
        snapshot_stores: List[IStateSnapshot],
        transition_logs: List[IStateTransitionLog],
        event_store: Optional[StateMachineEventStore] = None,
        migration_runner: Optional[MigrationRunner] = None,
    ):
        """Initialize persistence manager."""
        self.config = config
        self.metrics = StatePersistenceMetrics()

        # Initialize components
        self.snapshot_manager = (
            StateSnapshotManager(
                stores=snapshot_stores,
                config=SnapshotConfig(
                    max_snapshots=config.max_snapshots_per_state,
                    snapshot_interval=config.snapshot_interval,
                    compression_enabled=config.compression_enabled,
                    auto_snapshot=config.snapshot_enabled,
                ),
            )
            if config.snapshot_enabled
            else None
        )

        self.transition_logger = (
            StateTransitionLogger(stores=transition_logs, analyze_patterns=True)
            if config.event_sourcing_enabled
            else None
        )

        self.event_store = event_store
        self.migration_runner = migration_runner or MigrationRunner()

        # Initialize strategy implementations
        self._persistence_impls: Dict[PersistenceStrategy, IStatePersistence] = {}
        self._initialize_strategies()

        # State cache
        self._state_cache: Dict[str, PersistedState] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Auto-persistence tracking
        self._last_persist: Dict[str, datetime] = {}
        self._pending_persists: set = set()

        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown = False

    def _initialize_strategies(self) -> None:
        """Initialize persistence strategy implementations."""
        # Snapshot-only strategy
        if self.config.strategy == PersistenceStrategy.SNAPSHOT_ONLY:
            if not self.snapshot_manager:
                raise ValueError("Snapshot manager required for snapshot-only strategy")

            # Create simple snapshot-based persistence
            self._persistence_impls[PersistenceStrategy.SNAPSHOT_ONLY] = (
                SnapshotBasedPersistence(self.snapshot_manager)
            )

        # Event-sourced strategy
        elif self.config.strategy == PersistenceStrategy.EVENT_SOURCED:
            if not self.event_store:
                raise ValueError("Event store required for event-sourced strategy")

            self._persistence_impls[PersistenceStrategy.EVENT_SOURCED] = (
                EventSourcedStateMachine(self.event_store, self.transition_logger)
            )

        # Hybrid strategy
        elif self.config.strategy == PersistenceStrategy.HYBRID:
            if not self.snapshot_manager or not self.event_store:
                raise ValueError(
                    "Both snapshot and event store required for hybrid strategy"
                )

            self._persistence_impls[PersistenceStrategy.HYBRID] = HybridPersistence(
                self.snapshot_manager,
                EventSourcedStateMachine(self.event_store, self.transition_logger),
            )

        # Versioned strategy
        elif self.config.strategy == PersistenceStrategy.VERSIONED:
            base_impl = self._get_base_persistence()

            self._persistence_impls[PersistenceStrategy.VERSIONED] = (
                StateVersionManager(
                    storage=base_impl,
                    migration_runner=self.migration_runner,
                    conflict_resolver=VersionConflictResolver(),
                )
            )

    def _get_base_persistence(self) -> IStatePersistence:
        """Get base persistence implementation."""
        if self.snapshot_manager and self.event_store:
            return HybridPersistence(
                self.snapshot_manager,
                EventSourcedStateMachine(self.event_store, self.transition_logger),
            )
        elif self.event_store:
            return EventSourcedStateMachine(self.event_store, self.transition_logger)
        elif self.snapshot_manager:
            return SnapshotBasedPersistence(self.snapshot_manager)
        else:
            raise ValueError("No persistence backend available")

    async def save_state(
        self, state_machine_id: str, state: Dict[str, Any], force: bool = False
    ) -> str:
        """Save state with configured strategy."""
        start_time = datetime.utcnow()

        try:
            # Check if persistence needed
            if not force and not await self._should_persist(state_machine_id):
                return f"cached_{state_machine_id}"

            # Get persistence implementation
            impl = self._persistence_impls.get(self.config.strategy)
            if not impl:
                raise ValueError(
                    f"No implementation for strategy: {self.config.strategy}"
                )

            # Save state
            result = await impl.save_state(state_machine_id, state)

            # Update cache
            if self.config.cache_enabled:
                self._update_cache(state_machine_id, state)

            # Update metrics
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.get_metrics(state_machine_id).record_save(duration_ms)
            self.metrics.get_metrics().record_save(duration_ms)

            # Update tracking
            self._last_persist[state_machine_id] = datetime.utcnow()
            self._pending_persists.discard(state_machine_id)

            logger.info(f"Saved state for {state_machine_id} in {duration_ms:.2f}ms")

            return result

        except Exception as e:
            self.metrics.get_metrics(state_machine_id).failed_operations += 1
            self.metrics.get_metrics().failed_operations += 1
            logger.error(f"Error saving state for {state_machine_id}: {e}")
            raise

    async def load_state(
        self, state_machine_id: str, version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """Load state with caching."""
        start_time = datetime.utcnow()
        cache_hit = False

        try:
            # Check cache first
            if self.config.cache_enabled and not version:
                cached = self._get_cached(state_machine_id)
                if cached:
                    cache_hit = True
                    duration_ms = (
                        datetime.utcnow() - start_time
                    ).total_seconds() * 1000
                    self.metrics.get_metrics(state_machine_id).record_load(
                        duration_ms, True
                    )
                    self.metrics.get_metrics().record_load(duration_ms, True)
                    return cached

            # Load from persistence
            impl = self._persistence_impls.get(self.config.strategy)
            if not impl:
                raise ValueError(
                    f"No implementation for strategy: {self.config.strategy}"
                )

            result = await impl.load_state(state_machine_id, version)

            # Update cache
            if result and self.config.cache_enabled and not version:
                self._update_cache(state_machine_id, result.state_data, result)

            # Update metrics
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.get_metrics(state_machine_id).record_load(
                duration_ms, cache_hit
            )
            self.metrics.get_metrics().record_load(duration_ms, cache_hit)

            return result

        except Exception as e:
            self.metrics.get_metrics(state_machine_id).failed_operations += 1
            self.metrics.get_metrics().failed_operations += 1
            logger.error(f"Error loading state for {state_machine_id}: {e}")
            raise

    async def handle_transition(
        self,
        state_machine_id: str,
        transition: StateTransition,
        policy: Optional[AutoPersistencePolicy] = None,
    ) -> None:
        """Handle state transition with persistence."""
        # Log transition if enabled
        if self.transition_logger:
            await self.transition_logger.log_transition(state_machine_id, transition)

        # Check persistence policy
        policy = policy or AutoPersistencePolicy()
        if policy.should_persist("transition"):
            self._pending_persists.add(state_machine_id)

            # Immediate persist for phase changes
            if (
                transition.metadata.get("is_phase_change")
                and policy.persist_on_phase_change
            ):
                # Load current state
                current = await self.load_state(state_machine_id)
                if current:
                    await self.save_state(
                        state_machine_id, current.state_data, force=True
                    )

    async def create_snapshot(self, state_machine_id: str) -> List[str]:
        """Manually create a snapshot."""
        if not self.snapshot_manager:
            return []

        # Load current state
        current = await self.load_state(state_machine_id)
        if not current:
            return []

        # Create snapshot
        snapshot_ids = await self.snapshot_manager.create_snapshot(
            state_machine_id,
            current.state_data,
            {"manual": True, "timestamp": datetime.utcnow().isoformat()},
        )

        self.metrics.get_metrics(state_machine_id).total_snapshots += 1
        self.metrics.get_metrics().total_snapshots += 1

        return snapshot_ids

    async def recover_state(
        self, state_machine_id: str, options: Optional[RecoveryOptions] = None
    ) -> Optional[PersistedState]:
        """Recover state using configured strategy."""
        if not self.config.recovery_enabled:
            return None

        options = options or RecoveryOptions(mode=self.config.recovery_mode)

        # Create recovery manager
        recovery_manager = StateRecoveryManager(
            strategies=[],  # Would be populated based on available components
            validator=self._validate_recovered_state,
        )

        # Attempt recovery
        result = await recovery_manager.recover_with_options(state_machine_id, options)

        if result.is_successful:
            self.metrics.get_metrics(state_machine_id).total_recoveries += 1
            self.metrics.get_metrics().total_recoveries += 1
            return result.recovered_state

        return None

    async def start_background_tasks(self) -> None:
        """Start background persistence tasks."""
        if self.config.batch_operations:
            task = asyncio.create_task(self._batch_persistence_task())
            self._background_tasks.append(task)

        if self.config.archive_completed_states:
            task = asyncio.create_task(self._archival_task())
            self._background_tasks.append(task)

    async def shutdown(self) -> None:
        """Shutdown persistence manager."""
        self._shutdown = True

        # Persist pending states
        if self._pending_persists:
            logger.info(f"Persisting {len(self._pending_persists)} pending states")

            for state_machine_id in list(self._pending_persists):
                try:
                    current = await self.load_state(state_machine_id)
                    if current:
                        await self.save_state(
                            state_machine_id, current.state_data, force=True
                        )
                except Exception as e:
                    logger.error(
                        f"Error persisting {state_machine_id} on shutdown: {e}"
                    )

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def _should_persist(self, state_machine_id: str) -> bool:
        """Check if state should be persisted."""
        # Always persist if not in cache
        if state_machine_id not in self._last_persist:
            return True

        # Check interval
        if self.config.strategy == PersistenceStrategy.SNAPSHOT_ONLY:
            elapsed = datetime.utcnow() - self._last_persist[state_machine_id]
            return elapsed >= self.config.snapshot_interval

        return True

    def _update_cache(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        persisted: Optional[PersistedState] = None,
    ) -> None:
        """Update state cache."""
        if persisted:
            self._state_cache[state_machine_id] = persisted
        else:
            # Create persisted state
            self._state_cache[state_machine_id] = PersistedState(
                state_machine_id=state_machine_id,
                state_type="cached",
                current_state=state.get("current_state", "unknown"),
                state_data=state,
                version=StateVersion(1, 0, 0),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        self._cache_timestamps[state_machine_id] = datetime.utcnow()

        # Enforce cache size
        if len(self._state_cache) > self.config.cache_size:
            # Remove oldest
            oldest = min(self._cache_timestamps.items(), key=lambda x: x[1])
            del self._state_cache[oldest[0]]
            del self._cache_timestamps[oldest[0]]

    def _get_cached(self, state_machine_id: str) -> Optional[PersistedState]:
        """Get cached state."""
        return self._state_cache.get(state_machine_id)

    async def _validate_recovered_state(
        self, state_machine_id: str, state: Dict[str, Any]
    ) -> bool:
        """Validate recovered state."""
        required_fields = ["current_state", "state_data"]
        return all(field in state for field in required_fields)

    async def _batch_persistence_task(self) -> None:
        """Background task for batch persistence."""
        while not self._shutdown:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Get states to persist
                to_persist = []
                for state_machine_id in list(self._pending_persists):
                    if state_machine_id in self._last_persist:
                        elapsed = (
                            datetime.utcnow() - self._last_persist[state_machine_id]
                        )
                        if elapsed >= timedelta(seconds=30):
                            to_persist.append(state_machine_id)
                    else:
                        to_persist.append(state_machine_id)

                # Batch persist
                if to_persist:
                    logger.info(f"Batch persisting {len(to_persist)} states")

                    for batch_start in range(
                        0, len(to_persist), self.config.batch_size
                    ):
                        batch = to_persist[
                            batch_start : batch_start + self.config.batch_size
                        ]

                        tasks = []
                        for state_machine_id in batch:
                            current = await self.load_state(state_machine_id)
                            if current:
                                task = self.save_state(
                                    state_machine_id, current.state_data
                                )
                                tasks.append(task)

                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch persistence task: {e}")

    async def _archival_task(self) -> None:
        """Background task for archiving completed states."""
        while not self._shutdown:
            try:
                await asyncio.sleep(3600)  # Check every hour

                # This would implement archival logic
                # For now, just log
                logger.info("Archival task running")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in archival task: {e}")


class SnapshotBasedPersistence(IStatePersistence):
    """Simple snapshot-based persistence."""

    def __init__(self, snapshot_manager: StateSnapshotManager):
        """Initialize snapshot persistence."""
        super().__init__()
        self.snapshot_manager = snapshot_manager

    async def save_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        version: Optional[StateVersion] = None,
    ) -> str:
        """Save state as snapshot."""
        snapshot_ids = await self.snapshot_manager.create_snapshot(
            state_machine_id, state, {"version": str(version) if version else "1.0.0"}
        )
        return snapshot_ids[0] if snapshot_ids else f"snapshot_{state_machine_id}"

    async def load_state(
        self, state_machine_id: str, version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """Load state from snapshot."""
        return await self.snapshot_manager.restore_latest(state_machine_id)

    async def delete_state(self, state_machine_id: str) -> bool:
        """Delete all snapshots."""
        # Get all snapshots
        for store in self.snapshot_manager.stores:
            snapshots = await store.list_snapshots(state_machine_id)
            for snapshot in snapshots:
                await store.delete_snapshot(snapshot.recovery_id)
        return True

    async def list_versions(self, state_machine_id: str) -> List[StateVersion]:
        """List snapshot versions."""
        versions = []
        for store in self.snapshot_manager.stores:
            snapshots = await store.list_snapshots(state_machine_id)
            for snapshot in snapshots:
                version_str = snapshot.metadata.get("version", "1.0.0")
                parts = version_str.split(".")
                version = StateVersion(
                    major=int(parts[0]) if len(parts) > 0 else 1,
                    minor=int(parts[1]) if len(parts) > 1 else 0,
                    patch=int(parts[2]) if len(parts) > 2 else 0,
                )
                versions.append(version)
        return sorted(set(versions))


class HybridPersistence(IStatePersistence):
    """Hybrid persistence using snapshots and event sourcing."""

    def __init__(
        self,
        snapshot_manager: StateSnapshotManager,
        event_sourced: EventSourcedStateMachine,
    ):
        """Initialize hybrid persistence."""
        super().__init__()
        self.snapshot_manager = snapshot_manager
        self.event_sourced = event_sourced

    async def save_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        version: Optional[StateVersion] = None,
    ) -> str:
        """Save using both strategies."""
        # Save to event store
        event_result = await self.event_sourced.save_state(
            state_machine_id, state, version
        )

        # Check if snapshot needed
        should_snapshot = await self.snapshot_manager.should_snapshot(
            state_machine_id,
            is_major_transition=state.get("_is_major_transition", False),
        )

        if should_snapshot:
            await self.snapshot_manager.create_snapshot(state_machine_id, state)

        return event_result

    async def load_state(
        self, state_machine_id: str, version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """Load using most efficient strategy."""
        # Try snapshot first for current version
        if not version:
            snapshot = await self.snapshot_manager.restore_latest(state_machine_id)
            if snapshot:
                # Get events since snapshot
                # This would replay recent events on top of snapshot
                return snapshot

        # Fall back to event sourcing
        return await self.event_sourced.load_state(state_machine_id, version)

    async def delete_state(self, state_machine_id: str) -> bool:
        """Delete from both stores."""
        snapshot_result = True
        for store in self.snapshot_manager.stores:
            snapshots = await store.list_snapshots(state_machine_id)
            for snapshot in snapshots:
                if not await store.delete_snapshot(snapshot.recovery_id):
                    snapshot_result = False

        event_result = await self.event_sourced.delete_state(state_machine_id)

        return snapshot_result and event_result

    async def list_versions(self, state_machine_id: str) -> List[StateVersion]:
        """List all available versions."""
        snapshot_versions = []
        for store in self.snapshot_manager.stores:
            snapshots = await store.list_snapshots(state_machine_id)
            for snapshot in snapshots:
                version_str = snapshot.metadata.get("version", "1.0.0")
                parts = version_str.split(".")
                version = StateVersion(
                    major=int(parts[0]) if len(parts) > 0 else 1,
                    minor=int(parts[1]) if len(parts) > 1 else 0,
                    patch=int(parts[2]) if len(parts) > 2 else 0,
                )
                snapshot_versions.append(version)

        event_versions = await self.event_sourced.list_versions(state_machine_id)

        return sorted(set(snapshot_versions + event_versions))
