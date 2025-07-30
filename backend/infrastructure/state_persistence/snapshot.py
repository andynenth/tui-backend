"""
State snapshot implementation for state machine persistence.

Provides efficient snapshot creation, storage, and restoration.
"""

from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import gzip
import hashlib
from pathlib import Path
import asyncio
from collections import OrderedDict
import logging

from .abstractions import (
    IStateSnapshot,
    PersistedState,
    StateVersion,
    RecoveryPoint,
    StatePersistenceBase,
)


logger = logging.getLogger(__name__)


@dataclass
class SnapshotConfig:
    """Configuration for snapshot management."""

    max_snapshots: int = 10
    snapshot_interval: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    compression_enabled: bool = True
    compression_level: int = 6
    retention_period: timedelta = field(default_factory=lambda: timedelta(days=7))
    auto_snapshot: bool = True
    snapshot_on_major_transitions: bool = True


@dataclass
class SnapshotMetadata:
    """Metadata for a state snapshot."""

    snapshot_id: str
    state_machine_id: str
    state_type: str
    version: StateVersion
    created_at: datetime
    size_bytes: int
    compressed: bool
    checksum: str
    transition_count: int = 0
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "state_machine_id": self.state_machine_id,
            "state_type": self.state_type,
            "version": str(self.version),
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "compressed": self.compressed,
            "checksum": self.checksum,
            "transition_count": self.transition_count,
            "tags": list(self.tags),
        }


@dataclass
class CompressedSnapshot:
    """A compressed state snapshot."""

    metadata: SnapshotMetadata
    compressed_data: bytes

    def decompress(self) -> Dict[str, Any]:
        """Decompress the snapshot data."""
        decompressed = gzip.decompress(self.compressed_data)
        return json.loads(decompressed.decode("utf-8"))


class InMemorySnapshotStore(IStateSnapshot):
    """
    In-memory snapshot store for development and testing.

    Features:
    - LRU eviction
    - Compression support
    - Fast access
    """

    def __init__(self, config: Optional[SnapshotConfig] = None):
        """Initialize in-memory store."""
        self.config = config or SnapshotConfig()
        self._snapshots: OrderedDict[str, CompressedSnapshot] = OrderedDict()
        self._by_state_machine: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._snapshot_counter = 0

    async def create_snapshot(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a state snapshot."""
        async with self._lock:
            # Generate snapshot ID
            self._snapshot_counter += 1
            snapshot_id = f"snap_{state_machine_id}_{self._snapshot_counter}"

            # Serialize state
            state_json = json.dumps(state, sort_keys=True)
            state_bytes = state_json.encode("utf-8")

            # Calculate checksum
            checksum = hashlib.sha256(state_bytes).hexdigest()[:16]

            # Compress if enabled
            if self.config.compression_enabled:
                compressed_data = gzip.compress(
                    state_bytes, compresslevel=self.config.compression_level
                )
            else:
                compressed_data = state_bytes

            # Create metadata
            snapshot_metadata = SnapshotMetadata(
                snapshot_id=snapshot_id,
                state_machine_id=state_machine_id,
                state_type=state.get("state_type", "unknown"),
                version=self._extract_version(state),
                created_at=datetime.utcnow(),
                size_bytes=len(compressed_data),
                compressed=self.config.compression_enabled,
                checksum=checksum,
                transition_count=len(state.get("transitions", [])),
                tags=set(metadata.get("tags", [])) if metadata else set(),
            )

            # Store snapshot
            snapshot = CompressedSnapshot(
                metadata=snapshot_metadata, compressed_data=compressed_data
            )

            self._snapshots[snapshot_id] = snapshot

            # Update index
            if state_machine_id not in self._by_state_machine:
                self._by_state_machine[state_machine_id] = set()
            self._by_state_machine[state_machine_id].add(snapshot_id)

            # Enforce max snapshots
            await self._enforce_limits(state_machine_id)

            logger.info(
                f"Created snapshot {snapshot_id} for state machine {state_machine_id}"
            )

            return snapshot_id

    async def restore_snapshot(self, snapshot_id: str) -> Optional[PersistedState]:
        """Restore from snapshot."""
        async with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
            if not snapshot:
                return None

            # Move to end (LRU)
            self._snapshots.move_to_end(snapshot_id)

            # Decompress state
            if snapshot.metadata.compressed:
                state_data = snapshot.decompress()
            else:
                state_data = json.loads(snapshot.compressed_data.decode("utf-8"))

            # Create persisted state
            persisted_state = PersistedState(
                state_machine_id=snapshot.metadata.state_machine_id,
                state_type=snapshot.metadata.state_type,
                current_state=state_data.get("current_state", "unknown"),
                state_data=state_data,
                version=snapshot.metadata.version,
                transitions=state_data.get("transitions", []),
                created_at=snapshot.metadata.created_at,
                updated_at=snapshot.metadata.created_at,
                metadata={
                    "restored_from": snapshot_id,
                    "snapshot_metadata": snapshot.metadata.to_dict(),
                },
            )

            logger.info(f"Restored state from snapshot {snapshot_id}")

            return persisted_state

    async def list_snapshots(
        self, state_machine_id: str, limit: Optional[int] = None
    ) -> List[RecoveryPoint]:
        """List available snapshots."""
        async with self._lock:
            snapshot_ids = self._by_state_machine.get(state_machine_id, set())

            recovery_points = []
            for snapshot_id in sorted(snapshot_ids, reverse=True):
                if snapshot_id not in self._snapshots:
                    continue

                snapshot = self._snapshots[snapshot_id]

                recovery_point = RecoveryPoint(
                    recovery_id=snapshot_id,
                    state_machine_id=state_machine_id,
                    timestamp=snapshot.metadata.created_at,
                    transition_count=snapshot.metadata.transition_count,
                    metadata={
                        "version": str(snapshot.metadata.version),
                        "size_bytes": snapshot.metadata.size_bytes,
                        "compressed": snapshot.metadata.compressed,
                        "checksum": snapshot.metadata.checksum,
                        "tags": list(snapshot.metadata.tags),
                    },
                )

                recovery_points.append(recovery_point)

                if limit and len(recovery_points) >= limit:
                    break

            return recovery_points

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        async with self._lock:
            snapshot = self._snapshots.pop(snapshot_id, None)
            if not snapshot:
                return False

            # Update index
            state_machine_id = snapshot.metadata.state_machine_id
            if state_machine_id in self._by_state_machine:
                self._by_state_machine[state_machine_id].discard(snapshot_id)

                if not self._by_state_machine[state_machine_id]:
                    del self._by_state_machine[state_machine_id]

            logger.info(f"Deleted snapshot {snapshot_id}")

            return True

    async def _enforce_limits(self, state_machine_id: str) -> None:
        """Enforce snapshot limits per state machine."""
        snapshot_ids = list(self._by_state_machine.get(state_machine_id, []))

        if len(snapshot_ids) > self.config.max_snapshots:
            # Sort by creation time
            snapshots_with_time = [
                (sid, self._snapshots[sid].metadata.created_at)
                for sid in snapshot_ids
                if sid in self._snapshots
            ]
            snapshots_with_time.sort(key=lambda x: x[1])

            # Remove oldest snapshots
            to_remove = len(snapshots_with_time) - self.config.max_snapshots
            for snapshot_id, _ in snapshots_with_time[:to_remove]:
                await self.delete_snapshot(snapshot_id)

    def _extract_version(self, state: Dict[str, Any]) -> StateVersion:
        """Extract version from state."""
        version_data = state.get("version", {})
        if isinstance(version_data, dict):
            return StateVersion(
                major=version_data.get("major", 1),
                minor=version_data.get("minor", 0),
                patch=version_data.get("patch", 0),
            )
        return StateVersion(1, 0, 0)


class FileSystemSnapshotStore(IStateSnapshot):
    """
    File system based snapshot store.

    Features:
    - Persistent storage
    - Directory organization
    - Compression support
    - Atomic writes
    """

    def __init__(self, base_path: Path, config: Optional[SnapshotConfig] = None):
        """Initialize file system store."""
        self.base_path = Path(base_path)
        self.config = config or SnapshotConfig()

        # Create directory structure
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.base_path / "metadata"
        self._data_path = self.base_path / "data"
        self._metadata_path.mkdir(exist_ok=True)
        self._data_path.mkdir(exist_ok=True)

        self._lock = asyncio.Lock()

    async def create_snapshot(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a state snapshot."""
        async with self._lock:
            # Generate snapshot ID
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            snapshot_id = f"{state_machine_id}_{timestamp}"

            # Create state machine directory
            sm_dir = self._data_path / state_machine_id
            sm_dir.mkdir(exist_ok=True)

            # Serialize state
            state_json = json.dumps(state, sort_keys=True, indent=2)
            state_bytes = state_json.encode("utf-8")

            # Calculate checksum
            checksum = hashlib.sha256(state_bytes).hexdigest()[:16]

            # Compress if enabled
            if self.config.compression_enabled:
                data_file = sm_dir / f"{snapshot_id}.json.gz"
                compressed_data = gzip.compress(
                    state_bytes, compresslevel=self.config.compression_level
                )
                data_to_write = compressed_data
            else:
                data_file = sm_dir / f"{snapshot_id}.json"
                data_to_write = state_bytes

            # Write data atomically
            temp_file = data_file.with_suffix(".tmp")
            temp_file.write_bytes(data_to_write)
            temp_file.rename(data_file)

            # Create metadata
            snapshot_metadata = SnapshotMetadata(
                snapshot_id=snapshot_id,
                state_machine_id=state_machine_id,
                state_type=state.get("state_type", "unknown"),
                version=self._extract_version(state),
                created_at=datetime.utcnow(),
                size_bytes=len(data_to_write),
                compressed=self.config.compression_enabled,
                checksum=checksum,
                transition_count=len(state.get("transitions", [])),
                tags=set(metadata.get("tags", [])) if metadata else set(),
            )

            # Write metadata
            metadata_file = self._metadata_path / f"{snapshot_id}.json"
            metadata_file.write_text(json.dumps(snapshot_metadata.to_dict(), indent=2))

            # Clean up old snapshots
            await self._cleanup_old_snapshots(state_machine_id)

            logger.info(
                f"Created snapshot {snapshot_id} for state machine {state_machine_id}"
            )

            return snapshot_id

    async def restore_snapshot(self, snapshot_id: str) -> Optional[PersistedState]:
        """Restore from snapshot."""
        async with self._lock:
            # Read metadata
            metadata_file = self._metadata_path / f"{snapshot_id}.json"
            if not metadata_file.exists():
                return None

            metadata_data = json.loads(metadata_file.read_text())

            # Find data file
            state_machine_id = metadata_data["state_machine_id"]
            sm_dir = self._data_path / state_machine_id

            if metadata_data["compressed"]:
                data_file = sm_dir / f"{snapshot_id}.json.gz"
                if not data_file.exists():
                    return None

                compressed_data = data_file.read_bytes()
                state_json = gzip.decompress(compressed_data).decode("utf-8")
            else:
                data_file = sm_dir / f"{snapshot_id}.json"
                if not data_file.exists():
                    return None

                state_json = data_file.read_text()

            state_data = json.loads(state_json)

            # Create persisted state
            version_parts = metadata_data["version"].split(".")
            version = StateVersion(
                major=int(version_parts[0]),
                minor=int(version_parts[1]),
                patch=int(version_parts[2]),
            )

            persisted_state = PersistedState(
                state_machine_id=state_machine_id,
                state_type=metadata_data["state_type"],
                current_state=state_data.get("current_state", "unknown"),
                state_data=state_data,
                version=version,
                transitions=state_data.get("transitions", []),
                created_at=datetime.fromisoformat(metadata_data["created_at"]),
                updated_at=datetime.fromisoformat(metadata_data["created_at"]),
                metadata={
                    "restored_from": snapshot_id,
                    "snapshot_metadata": metadata_data,
                },
            )

            logger.info(f"Restored state from snapshot {snapshot_id}")

            return persisted_state

    async def list_snapshots(
        self, state_machine_id: str, limit: Optional[int] = None
    ) -> List[RecoveryPoint]:
        """List available snapshots."""
        async with self._lock:
            recovery_points = []

            # List metadata files for state machine
            metadata_files = []
            for metadata_file in self._metadata_path.glob("*.json"):
                try:
                    metadata_data = json.loads(metadata_file.read_text())
                    if metadata_data["state_machine_id"] == state_machine_id:
                        metadata_files.append((metadata_file, metadata_data))
                except Exception as e:
                    logger.error(f"Error reading metadata {metadata_file}: {e}")

            # Sort by creation time
            metadata_files.sort(key=lambda x: x[1]["created_at"], reverse=True)

            # Create recovery points
            for metadata_file, metadata_data in metadata_files:
                recovery_point = RecoveryPoint(
                    recovery_id=metadata_data["snapshot_id"],
                    state_machine_id=state_machine_id,
                    timestamp=datetime.fromisoformat(metadata_data["created_at"]),
                    transition_count=metadata_data.get("transition_count", 0),
                    metadata={
                        "version": metadata_data["version"],
                        "size_bytes": metadata_data["size_bytes"],
                        "compressed": metadata_data["compressed"],
                        "checksum": metadata_data["checksum"],
                        "tags": metadata_data.get("tags", []),
                    },
                )

                recovery_points.append(recovery_point)

                if limit and len(recovery_points) >= limit:
                    break

            return recovery_points

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        async with self._lock:
            # Delete metadata
            metadata_file = self._metadata_path / f"{snapshot_id}.json"
            if not metadata_file.exists():
                return False

            metadata_data = json.loads(metadata_file.read_text())
            state_machine_id = metadata_data["state_machine_id"]

            # Delete data file
            sm_dir = self._data_path / state_machine_id
            if metadata_data["compressed"]:
                data_file = sm_dir / f"{snapshot_id}.json.gz"
            else:
                data_file = sm_dir / f"{snapshot_id}.json"

            # Remove files
            metadata_file.unlink()
            if data_file.exists():
                data_file.unlink()

            logger.info(f"Deleted snapshot {snapshot_id}")

            return True

    async def _cleanup_old_snapshots(self, state_machine_id: str) -> None:
        """Clean up old snapshots based on retention policy."""
        snapshots = await self.list_snapshots(state_machine_id)

        # Remove by count
        if len(snapshots) > self.config.max_snapshots:
            for snapshot in snapshots[self.config.max_snapshots :]:
                await self.delete_snapshot(snapshot.recovery_id)

        # Remove by age
        cutoff_time = datetime.utcnow() - self.config.retention_period
        for snapshot in snapshots:
            if snapshot.timestamp < cutoff_time:
                await self.delete_snapshot(snapshot.recovery_id)

    def _extract_version(self, state: Dict[str, Any]) -> StateVersion:
        """Extract version from state."""
        version_data = state.get("version", {})
        if isinstance(version_data, dict):
            return StateVersion(
                major=version_data.get("major", 1),
                minor=version_data.get("minor", 0),
                patch=version_data.get("patch", 0),
            )
        return StateVersion(1, 0, 0)


class StateSnapshotManager:
    """
    High-level snapshot management.

    Features:
    - Automatic snapshots
    - Snapshot policies
    - Multi-store support
    """

    def __init__(
        self, stores: List[IStateSnapshot], config: Optional[SnapshotConfig] = None
    ):
        """Initialize snapshot manager."""
        self.stores = stores
        self.config = config or SnapshotConfig()
        self._last_snapshot: Dict[str, datetime] = {}
        self._transition_counts: Dict[str, int] = {}

    async def should_snapshot(
        self, state_machine_id: str, is_major_transition: bool = False
    ) -> bool:
        """Check if a snapshot should be created."""
        if not self.config.auto_snapshot:
            return False

        # Always snapshot major transitions if configured
        if is_major_transition and self.config.snapshot_on_major_transitions:
            return True

        # Check interval
        last_snapshot = self._last_snapshot.get(state_machine_id)
        if last_snapshot:
            elapsed = datetime.utcnow() - last_snapshot
            if elapsed < self.config.snapshot_interval:
                return False

        return True

    async def create_snapshot(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Create snapshot in all stores."""
        snapshot_ids = []

        for store in self.stores:
            try:
                snapshot_id = await store.create_snapshot(
                    state_machine_id, state, metadata
                )
                snapshot_ids.append(snapshot_id)
            except Exception as e:
                logger.error(f"Error creating snapshot in store: {e}")

        if snapshot_ids:
            self._last_snapshot[state_machine_id] = datetime.utcnow()
            self._transition_counts[state_machine_id] = 0

        return snapshot_ids

    async def restore_latest(self, state_machine_id: str) -> Optional[PersistedState]:
        """Restore from the latest snapshot."""
        for store in self.stores:
            try:
                snapshots = await store.list_snapshots(state_machine_id, limit=1)
                if snapshots:
                    return await store.restore_snapshot(snapshots[0].recovery_id)
            except Exception as e:
                logger.error(f"Error restoring from store: {e}")
                continue

        return None
