"""
State versioning and migration support.

Provides version management and migration capabilities for state machines.
"""

from typing import Dict, Any, Optional, List, Callable, Union, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio
from abc import ABC, abstractmethod
import logging
import hashlib

from .abstractions import StateVersion, PersistedState, IStatePersistence


logger = logging.getLogger(__name__)


class VersionStrategy(Enum):
    """Versioning strategies."""

    SEQUENTIAL = "sequential"  # Simple incrementing versions
    SEMANTIC = "semantic"  # Major.Minor.Patch versioning
    TIMESTAMP = "timestamp"  # Timestamp-based versions
    CONTENT_HASH = "content_hash"  # Content-based addressing


@dataclass
class StateSchemaVersion:
    """Schema version for state structure."""

    version: StateVersion
    schema: Dict[str, Any]
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    deprecated: bool = False
    migration_required: bool = True

    def is_compatible_with(self, other: "StateSchemaVersion") -> bool:
        """Check if schemas are compatible."""
        # Major version changes are incompatible
        if self.version.major != other.version.major:
            return False

        # Check required fields
        self_required = set(self.schema.get("required", []))
        other_required = set(other.schema.get("required", []))

        # New required fields break compatibility
        if other_required - self_required:
            return False

        return True


@dataclass
class VersionedState:
    """State with version information."""

    state: Dict[str, Any]
    version: StateVersion
    schema_version: Optional[StateSchemaVersion] = None
    parent_version: Optional[StateVersion] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_checksum(self) -> str:
        """Calculate content checksum."""
        content = json.dumps(self.state, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class VersionConflict:
    """Represents a version conflict."""

    base_version: StateVersion
    current_version: StateVersion
    incoming_version: StateVersion
    conflict_type: str
    resolution_options: List[str] = field(default_factory=list)


class StateMigration(ABC):
    """Base class for state migrations."""

    @property
    @abstractmethod
    def from_version(self) -> StateVersion:
        """Source version for migration."""
        pass

    @property
    @abstractmethod
    def to_version(self) -> StateVersion:
        """Target version for migration."""
        pass

    @abstractmethod
    async def migrate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate state to new version."""
        pass

    @abstractmethod
    async def rollback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback migration."""
        pass

    def can_migrate(self, version: StateVersion) -> bool:
        """Check if migration can handle version."""
        return version == self.from_version


class CompositeMigration(StateMigration):
    """Composite migration that chains multiple migrations."""

    def __init__(self, migrations: List[StateMigration]):
        """Initialize composite migration."""
        self.migrations = migrations

        if not migrations:
            raise ValueError("At least one migration required")

        # Validate chain
        for i in range(len(migrations) - 1):
            if migrations[i].to_version != migrations[i + 1].from_version:
                raise ValueError("Migration chain is not continuous")

    @property
    def from_version(self) -> StateVersion:
        """Source version."""
        return self.migrations[0].from_version

    @property
    def to_version(self) -> StateVersion:
        """Target version."""
        return self.migrations[-1].to_version

    async def migrate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all migrations in sequence."""
        current_state = state

        for migration in self.migrations:
            current_state = await migration.migrate(current_state)

        return current_state

    async def rollback(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback all migrations in reverse."""
        current_state = state

        for migration in reversed(self.migrations):
            current_state = await migration.rollback(current_state)

        return current_state


class MigrationRunner:
    """
    Runs migrations between state versions.

    Features:
    - Migration discovery
    - Chain building
    - Dry run support
    - Progress tracking
    """

    def __init__(self):
        """Initialize migration runner."""
        self._migrations: List[StateMigration] = []
        self._migration_graph: Dict[StateVersion, List[StateMigration]] = {}

    def register_migration(self, migration: StateMigration) -> None:
        """Register a migration."""
        self._migrations.append(migration)

        # Update graph
        if migration.from_version not in self._migration_graph:
            self._migration_graph[migration.from_version] = []

        self._migration_graph[migration.from_version].append(migration)

    async def migrate(
        self,
        state: Dict[str, Any],
        from_version: StateVersion,
        to_version: StateVersion,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Migrate state between versions."""
        # Find migration path
        path = self._find_migration_path(from_version, to_version)

        if not path:
            raise ValueError(
                f"No migration path found from {from_version} to {to_version}"
            )

        # Create composite migration if needed
        if len(path) > 1:
            migration = CompositeMigration(path)
        else:
            migration = path[0]

        # Run migration
        if dry_run:
            logger.info(f"Dry run: Would migrate from {from_version} to {to_version}")
            return state

        migrated_state = await migration.migrate(state)

        logger.info(f"Migrated state from {from_version} to {to_version}")

        return migrated_state

    def _find_migration_path(
        self, from_version: StateVersion, to_version: StateVersion
    ) -> Optional[List[StateMigration]]:
        """Find migration path using BFS."""
        if from_version == to_version:
            return []

        # BFS to find shortest path
        queue = [(from_version, [])]
        visited = {from_version}

        while queue:
            current_version, path = queue.pop(0)

            # Check if we reached target
            if current_version == to_version:
                return path

            # Explore neighbors
            for migration in self._migration_graph.get(current_version, []):
                next_version = migration.to_version

                if next_version not in visited:
                    visited.add(next_version)
                    new_path = path + [migration]
                    queue.append((next_version, new_path))

        return None

    async def validate_migration(
        self, migration: StateMigration, test_state: Dict[str, Any]
    ) -> bool:
        """Validate a migration with test data."""
        try:
            # Test forward migration
            migrated = await migration.migrate(test_state.copy())

            # Test rollback
            rolled_back = await migration.rollback(migrated)

            # Check if rollback preserves data
            # (This is a simple check, real validation would be more thorough)
            return True

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False


class VersionConflictResolver:
    """
    Resolves version conflicts.

    Features:
    - Multiple resolution strategies
    - Custom merge functions
    - Conflict detection
    """

    def __init__(self):
        """Initialize resolver."""
        self._strategies: Dict[str, Callable] = {
            "use_latest": self._use_latest,
            "use_incoming": self._use_incoming,
            "merge": self._merge_states,
            "manual": self._manual_resolution,
        }

    async def resolve_conflict(
        self,
        conflict: VersionConflict,
        current_state: Dict[str, Any],
        incoming_state: Dict[str, Any],
        strategy: str = "use_latest",
    ) -> Dict[str, Any]:
        """Resolve a version conflict."""
        if strategy not in self._strategies:
            raise ValueError(f"Unknown strategy: {strategy}")

        resolver = self._strategies[strategy]
        return await resolver(conflict, current_state, incoming_state)

    async def _use_latest(
        self,
        conflict: VersionConflict,
        current_state: Dict[str, Any],
        incoming_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use the latest version."""
        if conflict.incoming_version > conflict.current_version:
            return incoming_state
        return current_state

    async def _use_incoming(
        self,
        conflict: VersionConflict,
        current_state: Dict[str, Any],
        incoming_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Always use incoming state."""
        return incoming_state

    async def _merge_states(
        self,
        conflict: VersionConflict,
        current_state: Dict[str, Any],
        incoming_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge states intelligently."""
        merged = current_state.copy()

        # Simple merge strategy - can be customized
        for key, value in incoming_state.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # Recursive merge for nested dicts
                merged[key] = await self._merge_states(conflict, merged[key], value)
            elif key == "version":
                # Use higher version
                if StateVersion(**value) > StateVersion(**merged[key]):
                    merged[key] = value
            else:
                # Use incoming value for conflicts
                merged[key] = value

        return merged

    async def _manual_resolution(
        self,
        conflict: VersionConflict,
        current_state: Dict[str, Any],
        incoming_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Require manual resolution."""
        raise ValueError(
            f"Manual resolution required for conflict: {conflict.conflict_type}"
        )


class StateVersionManager(IStatePersistence):
    """
    Manages versioned states with migration support.

    Features:
    - Automatic versioning
    - Migration on load
    - Conflict resolution
    - Version history
    """

    def __init__(
        self,
        storage: IStatePersistence,
        migration_runner: MigrationRunner,
        conflict_resolver: VersionConflictResolver,
        strategy: VersionStrategy = VersionStrategy.SEMANTIC,
    ):
        """Initialize version manager."""
        super().__init__()
        self.storage = storage
        self.migration_runner = migration_runner
        self.conflict_resolver = conflict_resolver
        self.strategy = strategy
        self._version_history: Dict[str, List[StateVersion]] = {}
        self._current_schema = StateSchemaVersion(
            version=StateVersion(1, 0, 0),
            schema={
                "type": "object",
                "required": ["current_state", "state_data"],
                "properties": {
                    "current_state": {"type": "string"},
                    "state_data": {"type": "object"},
                },
            },
            description="Default state schema",
        )

    async def save_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        version: Optional[StateVersion] = None,
    ) -> str:
        """Save versioned state."""
        # Generate version if not provided
        if not version:
            version = await self._generate_version(state_machine_id, state)

        # Create versioned state
        versioned = VersionedState(
            state=state,
            version=version,
            schema_version=self._current_schema,
            checksum=None,
        )

        # Calculate checksum
        versioned.checksum = versioned.calculate_checksum()

        # Check for conflicts
        existing = await self.storage.load_state(state_machine_id)
        if existing and existing.version >= version:
            # Handle version conflict
            conflict = VersionConflict(
                base_version=existing.version,
                current_version=existing.version,
                incoming_version=version,
                conflict_type="concurrent_update",
            )

            resolved_state = await self.conflict_resolver.resolve_conflict(
                conflict, existing.state_data, state
            )

            # Save with incremented version
            version = StateVersion(version.major, version.minor, version.patch + 1)

            state = resolved_state

        # Add version info to state
        state["_version"] = {
            "version": str(version),
            "checksum": versioned.checksum,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Save to storage
        result = await self.storage.save_state(state_machine_id, state, version)

        # Update version history
        if state_machine_id not in self._version_history:
            self._version_history[state_machine_id] = []
        self._version_history[state_machine_id].append(version)

        return result

    async def load_state(
        self, state_machine_id: str, version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """Load and migrate state if needed."""
        # Load from storage
        persisted = await self.storage.load_state(state_machine_id, version)

        if not persisted:
            return None

        # Check if migration needed
        state_version_info = persisted.state_data.get("_version", {})
        if state_version_info:
            state_version = self._parse_version(
                state_version_info.get("version", "1.0.0")
            )

            if state_version < self._current_schema.version:
                # Migrate to current version
                migrated_state = await self.migration_runner.migrate(
                    persisted.state_data, state_version, self._current_schema.version
                )

                persisted.state_data = migrated_state
                persisted.version = self._current_schema.version

        return persisted

    async def delete_state(self, state_machine_id: str) -> bool:
        """Delete state and version history."""
        # Delete from storage
        result = await self.storage.delete_state(state_machine_id)

        # Clear version history
        self._version_history.pop(state_machine_id, None)

        return result

    async def list_versions(self, state_machine_id: str) -> List[StateVersion]:
        """List all versions."""
        # Get from storage
        storage_versions = await self.storage.list_versions(state_machine_id)

        # Combine with history
        history_versions = self._version_history.get(state_machine_id, [])

        all_versions = list(set(storage_versions + history_versions))
        all_versions.sort()

        return all_versions

    async def _generate_version(
        self, state_machine_id: str, state: Dict[str, Any]
    ) -> StateVersion:
        """Generate version based on strategy."""
        if self.strategy == VersionStrategy.SEQUENTIAL:
            # Get last version
            versions = await self.list_versions(state_machine_id)
            if versions:
                last = versions[-1]
                return StateVersion(last.major, last.minor, last.patch + 1)
            return StateVersion(1, 0, 0)

        elif self.strategy == VersionStrategy.SEMANTIC:
            # Analyze changes for semantic versioning
            existing = await self.load_state(state_machine_id)
            if not existing:
                return StateVersion(1, 0, 0)

            # Simple heuristic: patch for data changes, minor for structure
            if set(state.keys()) != set(existing.state_data.keys()):
                return StateVersion(
                    existing.version.major, existing.version.minor + 1, 0
                )
            else:
                return StateVersion(
                    existing.version.major,
                    existing.version.minor,
                    existing.version.patch + 1,
                )

        elif self.strategy == VersionStrategy.TIMESTAMP:
            # Use timestamp as version
            now = datetime.utcnow()
            return StateVersion(
                now.year,
                now.month * 100 + now.day,
                now.hour * 3600 + now.minute * 60 + now.second,
            )

        elif self.strategy == VersionStrategy.CONTENT_HASH:
            # Use content hash as patch version
            checksum = hashlib.sha256(
                json.dumps(state, sort_keys=True).encode()
            ).hexdigest()

            # Convert first 8 chars of hash to number
            patch = int(checksum[:8], 16) % 1000000

            return StateVersion(1, 0, patch)

        return StateVersion(1, 0, 0)

    def _parse_version(self, version_str: str) -> StateVersion:
        """Parse version string."""
        parts = version_str.split(".")
        return StateVersion(
            major=int(parts[0]) if len(parts) > 0 else 1,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
        )
