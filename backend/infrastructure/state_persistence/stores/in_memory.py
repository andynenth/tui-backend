"""
In-memory implementations of state persistence stores.

These are simple implementations for development and testing.
In production, you would use Redis, DynamoDB, or similar.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import logging

from ..abstractions import (
    IStatePersistence,
    IStateSnapshot,
    IStateTransitionLog,
    PersistedState,
    StateTransition,
    StateVersion,
    RecoveryPoint,
)

logger = logging.getLogger(__name__)


class InMemoryStateStore(IStatePersistence):
    """In-memory state persistence."""

    def __init__(self):
        """Initialize store."""
        self._states: Dict[str, PersistedState] = {}
        self._versions: Dict[str, List[StateVersion]] = {}

    async def save_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        version: Optional[StateVersion] = None,
    ) -> str:
        """Save state in memory."""
        if not version:
            version = StateVersion(major=1, minor=0, patch=0)

        persisted = PersistedState(
            state_machine_id=state_machine_id,
            state_type=state.get("type", "unknown"),
            current_state=state.get("current_state", "unknown"),
            state_data=state,
            version=version,
        )

        self._states[state_machine_id] = persisted

        # Track versions
        if state_machine_id not in self._versions:
            self._versions[state_machine_id] = []
        self._versions[state_machine_id].append(version)

        logger.debug(f"Saved state for {state_machine_id}")
        return state_machine_id

    async def load_state(
        self, state_machine_id: str, version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """Load state from memory."""
        return self._states.get(state_machine_id)

    async def delete_state(self, state_machine_id: str) -> bool:
        """Delete state from memory."""
        if state_machine_id in self._states:
            del self._states[state_machine_id]
            if state_machine_id in self._versions:
                del self._versions[state_machine_id]
            return True
        return False

    async def list_versions(self, state_machine_id: str) -> List[StateVersion]:
        """List available versions."""
        return self._versions.get(state_machine_id, [])


class InMemorySnapshotStore(IStateSnapshot):
    """In-memory snapshot store."""

    def __init__(self):
        """Initialize store."""
        self._snapshots: Dict[str, PersistedState] = {}
        self._recovery_points: Dict[str, List[RecoveryPoint]] = {}

    async def create_snapshot(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a snapshot in memory."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:8]}"

        persisted = PersistedState(
            state_machine_id=state_machine_id,
            state_type="snapshot",
            current_state=state.get("current_state", "unknown"),
            state_data=state,
            version=StateVersion(major=1, minor=0, patch=0),
            metadata=metadata or {},
        )

        self._snapshots[snapshot_id] = persisted

        # Create recovery point
        recovery_point = RecoveryPoint(
            recovery_id=snapshot_id,
            state_machine_id=state_machine_id,
            timestamp=datetime.utcnow(),
            state_snapshot=state,
            metadata=metadata or {},
        )

        if state_machine_id not in self._recovery_points:
            self._recovery_points[state_machine_id] = []
        self._recovery_points[state_machine_id].append(recovery_point)

        logger.debug(f"Created snapshot {snapshot_id} for {state_machine_id}")
        return snapshot_id

    async def restore_snapshot(self, snapshot_id: str) -> Optional[PersistedState]:
        """Restore from snapshot."""
        return self._snapshots.get(snapshot_id)

    async def list_snapshots(
        self, state_machine_id: str, limit: Optional[int] = None
    ) -> List[RecoveryPoint]:
        """List available snapshots."""
        points = self._recovery_points.get(state_machine_id, [])
        if limit:
            return points[-limit:]
        return points

    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        if snapshot_id in self._snapshots:
            del self._snapshots[snapshot_id]
            return True
        return False


class InMemoryTransitionLog(IStateTransitionLog):
    """In-memory transition log."""

    def __init__(self):
        """Initialize store."""
        self._transitions: Dict[str, List[StateTransition]] = {}

    async def log_transition(
        self, state_machine_id: str, transition: StateTransition
    ) -> None:
        """Log a transition."""
        if state_machine_id not in self._transitions:
            self._transitions[state_machine_id] = []
        self._transitions[state_machine_id].append(transition)
        logger.debug(
            f"Logged transition for {state_machine_id}: {transition.from_state} -> {transition.to_state}"
        )

    async def get_transitions(
        self,
        state_machine_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[StateTransition]:
        """Get transitions for a state machine."""
        transitions = self._transitions.get(state_machine_id, [])

        # Filter by timestamp
        if from_timestamp:
            transitions = [t for t in transitions if t.timestamp >= from_timestamp]
        if to_timestamp:
            transitions = [t for t in transitions if t.timestamp <= to_timestamp]

        # Apply limit
        if limit:
            transitions = transitions[-limit:]

        return transitions

    async def replay_transitions(
        self,
        state_machine_id: str,
        from_state: Dict[str, Any],
        transitions: List[StateTransition],
    ) -> Dict[str, Any]:
        """Replay transitions (simplified for in-memory)."""
        # In a real implementation, this would actually replay the transitions
        # For now, just return the last state if we have transitions
        if transitions:
            last_transition = transitions[-1]
            return {
                "current_state": last_transition.to_state,
                "last_action": last_transition.action,
                "replayed": True,
            }
        return from_state

    async def compact_log(
        self, state_machine_id: str, before_timestamp: datetime
    ) -> int:
        """Compact the log by removing old entries."""
        if state_machine_id not in self._transitions:
            return 0

        original_count = len(self._transitions[state_machine_id])
        self._transitions[state_machine_id] = [
            t
            for t in self._transitions[state_machine_id]
            if t.timestamp >= before_timestamp
        ]
        removed = original_count - len(self._transitions[state_machine_id])
        
        if removed > 0:
            logger.debug(f"Compacted {removed} transitions for {state_machine_id}")
        
        return removed


class InMemoryEventStore:
    """In-memory event store for event sourcing."""

    def __init__(self):
        """Initialize store."""
        self._events: Dict[str, List[Dict[str, Any]]] = {}
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    async def append_events(
        self, state_machine_id: str, events: List[Dict[str, Any]]
    ) -> None:
        """Append events to the store."""
        if state_machine_id not in self._events:
            self._events[state_machine_id] = []
        self._events[state_machine_id].extend(events)
        logger.debug(f"Appended {len(events)} events for {state_machine_id}")

    async def get_events(
        self,
        state_machine_id: str,
        from_sequence: Optional[int] = None,
        to_sequence: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get events for a state machine."""
        events = self._events.get(state_machine_id, [])

        if from_sequence is not None:
            events = events[from_sequence:]
        if to_sequence is not None:
            events = events[:to_sequence]

        return events

    async def save_snapshot(
        self, state_machine_id: str, sequence: int, state: Dict[str, Any]
    ) -> None:
        """Save a snapshot at a specific sequence."""
        self._snapshots[state_machine_id] = {
            "sequence": sequence,
            "state": state,
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.debug(f"Saved snapshot at sequence {sequence} for {state_machine_id}")

    async def get_latest_snapshot(
        self, state_machine_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot."""
        return self._snapshots.get(state_machine_id)

    async def compact_events(
        self, state_machine_id: str, before_sequence: int
    ) -> int:
        """Compact events before a sequence number."""
        if state_machine_id not in self._events:
            return 0

        original_count = len(self._events[state_machine_id])
        self._events[state_machine_id] = self._events[state_machine_id][before_sequence:]
        removed = original_count - len(self._events[state_machine_id])

        if removed > 0:
            logger.debug(f"Compacted {removed} events for {state_machine_id}")

        return removed