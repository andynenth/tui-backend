"""
State transition logging for state machine persistence.

Provides detailed logging of all state transitions for audit and recovery.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from collections import deque
from pathlib import Path
import aiofiles
import logging

from .abstractions import IStateTransitionLog, StateTransition, StateVersion


logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Types of state transitions."""

    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    TIMEOUT = "timeout"
    ERROR_RECOVERY = "error_recovery"
    ADMIN_OVERRIDE = "admin_override"


@dataclass
class TransitionEvent:
    """Extended transition information."""

    transition: StateTransition
    sequence_number: int
    transaction_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causality_id: Optional[str] = None  # ID of causing event
    transition_type: TransitionType = TransitionType.USER_ACTION
    duration_ms: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transition": self.transition.to_dict(),
            "sequence_number": self.sequence_number,
            "transaction_id": self.transaction_id,
            "correlation_id": self.correlation_id,
            "causality_id": self.causality_id,
            "transition_type": self.transition_type.value,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass
class TransitionQuery:
    """Query parameters for transition log."""

    state_machine_id: Optional[str] = None
    from_timestamp: Optional[datetime] = None
    to_timestamp: Optional[datetime] = None
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    action: Optional[str] = None
    actor_id: Optional[str] = None
    transition_type: Optional[TransitionType] = None
    limit: Optional[int] = None
    offset: int = 0


class TransitionLogStore:
    """Base class for transition log storage."""

    def __init__(self):
        """Initialize store."""
        self._sequence_counter = 0
        self._lock = asyncio.Lock()

    def _next_sequence(self) -> int:
        """Get next sequence number."""
        self._sequence_counter += 1
        return self._sequence_counter

    async def _apply_transition(
        self, state: Dict[str, Any], transition: StateTransition
    ) -> Dict[str, Any]:
        """
        Apply a transition to a state.

        This is a simplified implementation. In practice, this would
        delegate to the actual state machine implementation.
        """
        new_state = state.copy()

        # Update current state
        new_state["current_state"] = transition.to_state

        # Merge payload into state data
        if "state_data" not in new_state:
            new_state["state_data"] = {}

        new_state["state_data"].update(transition.payload)

        # Update timestamp
        new_state["last_updated"] = transition.timestamp.isoformat()

        return new_state


class InMemoryTransitionLog(TransitionLogStore, IStateTransitionLog):
    """
    In-memory transition log implementation.

    Features:
    - Fast access
    - Query support
    - Automatic cleanup
    """

    def __init__(self, max_transitions: int = 10000):
        """Initialize in-memory log."""
        super().__init__()
        self.max_transitions = max_transitions
        self._transitions: deque[TransitionEvent] = deque(maxlen=max_transitions)
        self._by_state_machine: Dict[str, List[int]] = {}
        self._state_machines: Dict[str, Dict[str, Any]] = {}

    async def log_transition(
        self, state_machine_id: str, transition: StateTransition
    ) -> None:
        """Log a state transition."""
        async with self._lock:
            # Create transition event
            event = TransitionEvent(
                transition=transition,
                sequence_number=self._next_sequence(),
                transition_type=self._determine_type(transition),
            )

            # Add to log
            self._transitions.append(event)

            # Update index
            if state_machine_id not in self._by_state_machine:
                self._by_state_machine[state_machine_id] = []

            self._by_state_machine[state_machine_id].append(len(self._transitions) - 1)

            # Update state machine tracking
            if state_machine_id in self._state_machines:
                self._state_machines[state_machine_id] = await self._apply_transition(
                    self._state_machines[state_machine_id], transition
                )

            logger.debug(
                f"Logged transition {transition.from_state} -> {transition.to_state} "
                f"for state machine {state_machine_id}"
            )

    async def get_transitions(
        self,
        state_machine_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[StateTransition]:
        """Get transitions for a state machine."""
        async with self._lock:
            indices = self._by_state_machine.get(state_machine_id, [])

            transitions = []
            for idx in reversed(indices):  # Most recent first
                if idx >= len(self._transitions):
                    continue

                event = self._transitions[idx]
                transition = event.transition

                # Apply filters
                if from_timestamp and transition.timestamp < from_timestamp:
                    continue

                if to_timestamp and transition.timestamp > to_timestamp:
                    continue

                transitions.append(transition)

                if limit and len(transitions) >= limit:
                    break

            return transitions

    async def replay_transitions(
        self,
        state_machine_id: str,
        from_state: Dict[str, Any],
        transitions: List[StateTransition],
    ) -> Dict[str, Any]:
        """Replay transitions from a base state."""
        current_state = from_state.copy()

        for transition in transitions:
            try:
                current_state = await self._apply_transition(current_state, transition)
            except Exception as e:
                logger.error(f"Error replaying transition {transition.action}: {e}")
                # Continue with other transitions

        # Store final state
        async with self._lock:
            self._state_machines[state_machine_id] = current_state

        return current_state

    async def compact_log(
        self, state_machine_id: str, before_timestamp: datetime
    ) -> int:
        """Compact transition log by removing old entries."""
        async with self._lock:
            indices = self._by_state_machine.get(state_machine_id, [])

            removed = 0
            new_indices = []

            for idx in indices:
                if idx >= len(self._transitions):
                    continue

                event = self._transitions[idx]

                if event.transition.timestamp < before_timestamp:
                    removed += 1
                else:
                    new_indices.append(idx)

            self._by_state_machine[state_machine_id] = new_indices

            logger.info(
                f"Compacted {removed} transitions for state machine {state_machine_id}"
            )

            return removed

    async def query_transitions(self, query: TransitionQuery) -> List[TransitionEvent]:
        """Query transitions with complex filters."""
        async with self._lock:
            results = []

            # Determine which transitions to check
            if query.state_machine_id:
                indices = self._by_state_machine.get(query.state_machine_id, [])
                events_to_check = [
                    self._transitions[idx]
                    for idx in indices
                    if idx < len(self._transitions)
                ]
            else:
                events_to_check = list(self._transitions)

            # Apply filters
            for event in events_to_check:
                transition = event.transition

                if query.from_timestamp and transition.timestamp < query.from_timestamp:
                    continue

                if query.to_timestamp and transition.timestamp > query.to_timestamp:
                    continue

                if query.from_state and transition.from_state != query.from_state:
                    continue

                if query.to_state and transition.to_state != query.to_state:
                    continue

                if query.action and transition.action != query.action:
                    continue

                if query.actor_id and transition.actor_id != query.actor_id:
                    continue

                if (
                    query.transition_type
                    and event.transition_type != query.transition_type
                ):
                    continue

                results.append(event)

            # Apply pagination
            start = query.offset
            end = start + query.limit if query.limit else None

            return results[start:end]

    def _determine_type(self, transition: StateTransition) -> TransitionType:
        """Determine transition type from metadata."""
        if transition.metadata.get("is_timeout"):
            return TransitionType.TIMEOUT
        elif transition.metadata.get("is_error_recovery"):
            return TransitionType.ERROR_RECOVERY
        elif transition.metadata.get("is_admin"):
            return TransitionType.ADMIN_OVERRIDE
        elif transition.actor_id and transition.actor_id.startswith("system"):
            return TransitionType.SYSTEM_EVENT
        else:
            return TransitionType.USER_ACTION


class FileSystemTransitionLog(TransitionLogStore, IStateTransitionLog):
    """
    File system based transition log.

    Features:
    - Persistent storage
    - Append-only log files
    - Rotation support
    - Efficient querying
    """

    def __init__(
        self,
        base_path: Path,
        max_file_size_mb: int = 100,
        max_files_per_state_machine: int = 10,
    ):
        """Initialize file system log."""
        super().__init__()
        self.base_path = Path(base_path)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files_per_state_machine

        # Create directory structure
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Track current log files
        self._current_files: Dict[str, Path] = {}
        self._file_sizes: Dict[Path, int] = {}

    async def log_transition(
        self, state_machine_id: str, transition: StateTransition
    ) -> None:
        """Log a state transition."""
        async with self._lock:
            # Get or create log file
            log_file = await self._get_log_file(state_machine_id)

            # Create transition event
            event = TransitionEvent(
                transition=transition,
                sequence_number=self._next_sequence(),
                transition_type=self._determine_type(transition),
            )

            # Append to log file
            log_entry = json.dumps(event.to_dict()) + "\n"

            async with aiofiles.open(log_file, "a") as f:
                await f.write(log_entry)

            # Update file size tracking
            self._file_sizes[log_file] = self._file_sizes.get(log_file, 0) + len(
                log_entry
            )

            # Check if rotation needed
            if self._file_sizes[log_file] > self.max_file_size:
                await self._rotate_log_file(state_machine_id)

            logger.debug(
                f"Logged transition to {log_file} for state machine {state_machine_id}"
            )

    async def get_transitions(
        self,
        state_machine_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[StateTransition]:
        """Get transitions for a state machine."""
        transitions = []

        # Get all log files for state machine
        sm_dir = self.base_path / state_machine_id
        if not sm_dir.exists():
            return transitions

        log_files = sorted(
            sm_dir.glob("*.log"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,  # Most recent first
        )

        for log_file in log_files:
            file_transitions = await self._read_transitions_from_file(
                log_file,
                from_timestamp,
                to_timestamp,
                limit - len(transitions) if limit else None,
            )

            transitions.extend(file_transitions)

            if limit and len(transitions) >= limit:
                break

        return transitions

    async def replay_transitions(
        self,
        state_machine_id: str,
        from_state: Dict[str, Any],
        transitions: List[StateTransition],
    ) -> Dict[str, Any]:
        """Replay transitions from a base state."""
        current_state = from_state.copy()

        for transition in transitions:
            try:
                current_state = await self._apply_transition(current_state, transition)
            except Exception as e:
                logger.error(f"Error replaying transition {transition.action}: {e}")

        return current_state

    async def compact_log(
        self, state_machine_id: str, before_timestamp: datetime
    ) -> int:
        """Compact transition log by removing old entries."""
        sm_dir = self.base_path / state_machine_id
        if not sm_dir.exists():
            return 0

        removed = 0

        # Process each log file
        for log_file in sorted(sm_dir.glob("*.log")):
            # Create new file with non-expired entries
            new_file = log_file.with_suffix(".tmp")
            kept_entries = []

            async with aiofiles.open(log_file, "r") as f:
                async for line in f:
                    try:
                        event_data = json.loads(line)
                        timestamp = datetime.fromisoformat(
                            event_data["transition"]["timestamp"]
                        )

                        if timestamp >= before_timestamp:
                            kept_entries.append(line)
                        else:
                            removed += 1
                    except Exception as e:
                        logger.error(f"Error processing log line: {e}")

            # Write kept entries
            if kept_entries:
                async with aiofiles.open(new_file, "w") as f:
                    await f.writelines(kept_entries)

                # Replace original file
                new_file.rename(log_file)
            else:
                # Remove empty file
                log_file.unlink()

        logger.info(
            f"Compacted {removed} transitions for state machine {state_machine_id}"
        )

        return removed

    async def _get_log_file(self, state_machine_id: str) -> Path:
        """Get current log file for state machine."""
        if state_machine_id in self._current_files:
            return self._current_files[state_machine_id]

        # Create state machine directory
        sm_dir = self.base_path / state_machine_id
        sm_dir.mkdir(exist_ok=True)

        # Find latest log file
        log_files = sorted(sm_dir.glob("*.log"))

        if log_files:
            current_file = log_files[-1]
            # Check size
            if current_file.stat().st_size < self.max_file_size:
                self._current_files[state_machine_id] = current_file
                return current_file

        # Create new log file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        new_file = sm_dir / f"transitions_{timestamp}.log"
        new_file.touch()

        self._current_files[state_machine_id] = new_file
        self._file_sizes[new_file] = 0

        return new_file

    async def _rotate_log_file(self, state_machine_id: str) -> None:
        """Rotate log file when it gets too large."""
        # Remove from current files
        self._current_files.pop(state_machine_id, None)

        # Clean up old files if needed
        sm_dir = self.base_path / state_machine_id
        log_files = sorted(sm_dir.glob("*.log"), key=lambda f: f.stat().st_mtime)

        if len(log_files) > self.max_files:
            # Remove oldest files
            for old_file in log_files[: -self.max_files]:
                old_file.unlink()
                self._file_sizes.pop(old_file, None)

    async def _read_transitions_from_file(
        self,
        log_file: Path,
        from_timestamp: Optional[datetime],
        to_timestamp: Optional[datetime],
        limit: Optional[int],
    ) -> List[StateTransition]:
        """Read transitions from a log file."""
        transitions = []

        async with aiofiles.open(log_file, "r") as f:
            async for line in f:
                try:
                    event_data = json.loads(line)
                    transition_data = event_data["transition"]

                    # Parse transition
                    transition = StateTransition(
                        from_state=transition_data["from_state"],
                        to_state=transition_data["to_state"],
                        action=transition_data["action"],
                        payload=transition_data["payload"],
                        actor_id=transition_data.get("actor_id"),
                        timestamp=datetime.fromisoformat(transition_data["timestamp"]),
                        metadata=transition_data.get("metadata", {}),
                    )

                    # Apply filters
                    if from_timestamp and transition.timestamp < from_timestamp:
                        continue

                    if to_timestamp and transition.timestamp > to_timestamp:
                        continue

                    transitions.append(transition)

                    if limit and len(transitions) >= limit:
                        break

                except Exception as e:
                    logger.error(f"Error reading transition: {e}")

        return transitions

    def _determine_type(self, transition: StateTransition) -> TransitionType:
        """Determine transition type from metadata."""
        if transition.metadata.get("is_timeout"):
            return TransitionType.TIMEOUT
        elif transition.metadata.get("is_error_recovery"):
            return TransitionType.ERROR_RECOVERY
        elif transition.metadata.get("is_admin"):
            return TransitionType.ADMIN_OVERRIDE
        elif transition.actor_id and transition.actor_id.startswith("system"):
            return TransitionType.SYSTEM_EVENT
        else:
            return TransitionType.USER_ACTION


class StateTransitionLogger:
    """
    High-level transition logging with analysis capabilities.

    Features:
    - Multi-store support
    - Transition analysis
    - Anomaly detection
    """

    def __init__(
        self, stores: List[IStateTransitionLog], analyze_patterns: bool = True
    ):
        """Initialize transition logger."""
        self.stores = stores
        self.analyze_patterns = analyze_patterns
        self._pattern_analyzer = (
            TransitionPatternAnalyzer() if analyze_patterns else None
        )

    async def log_transition(
        self,
        state_machine_id: str,
        transition: StateTransition,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Log transition to all stores."""
        # Enhance transition with duration
        if duration_ms is not None:
            transition.metadata["duration_ms"] = duration_ms

        # Log to all stores
        for store in self.stores:
            try:
                await store.log_transition(state_machine_id, transition)
            except Exception as e:
                logger.error(f"Error logging to store: {e}")

        # Analyze pattern if enabled
        if self._pattern_analyzer:
            await self._pattern_analyzer.analyze_transition(
                state_machine_id, transition
            )

    async def get_transition_stats(
        self, state_machine_id: str, time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get statistics about transitions."""
        from_timestamp = None
        if time_window:
            from_timestamp = datetime.utcnow() - time_window

        # Get transitions from first available store
        transitions = []
        for store in self.stores:
            try:
                transitions = await store.get_transitions(
                    state_machine_id, from_timestamp=from_timestamp
                )
                break
            except Exception as e:
                logger.error(f"Error getting transitions: {e}")

        if not transitions:
            return {
                "total_transitions": 0,
                "unique_paths": 0,
                "most_common_transition": None,
                "average_per_day": 0,
            }

        # Calculate statistics
        transition_counts = {}
        unique_states = set()

        for transition in transitions:
            path = f"{transition.from_state} -> {transition.to_state}"
            transition_counts[path] = transition_counts.get(path, 0) + 1
            unique_states.add(transition.from_state)
            unique_states.add(transition.to_state)

        # Time range
        time_range = transitions[0].timestamp - transitions[-1].timestamp
        days = max(1, time_range.days)

        return {
            "total_transitions": len(transitions),
            "unique_paths": len(transition_counts),
            "unique_states": len(unique_states),
            "most_common_transition": (
                max(transition_counts.items(), key=lambda x: x[1])
                if transition_counts
                else None
            ),
            "average_per_day": len(transitions) / days,
            "transition_distribution": transition_counts,
        }


class TransitionPatternAnalyzer:
    """Analyzes patterns in state transitions."""

    def __init__(self):
        """Initialize analyzer."""
        self._patterns: Dict[str, List[str]] = {}
        self._anomalies: List[Dict[str, Any]] = []

    async def analyze_transition(
        self, state_machine_id: str, transition: StateTransition
    ) -> None:
        """Analyze a transition for patterns."""
        # Track transition sequences
        if state_machine_id not in self._patterns:
            self._patterns[state_machine_id] = []

        pattern_key = (
            f"{transition.from_state}:{transition.action}:{transition.to_state}"
        )
        self._patterns[state_machine_id].append(pattern_key)

        # Keep only recent patterns
        if len(self._patterns[state_machine_id]) > 100:
            self._patterns[state_machine_id] = self._patterns[state_machine_id][-100:]

        # Check for anomalies
        await self._check_anomalies(state_machine_id, transition)

    async def _check_anomalies(
        self, state_machine_id: str, transition: StateTransition
    ) -> None:
        """Check for anomalous transitions."""
        # Example: Check for loops
        recent_patterns = self._patterns.get(state_machine_id, [])[-10:]
        pattern_key = (
            f"{transition.from_state}:{transition.action}:{transition.to_state}"
        )

        if recent_patterns.count(pattern_key) > 3:
            self._anomalies.append(
                {
                    "type": "excessive_loops",
                    "state_machine_id": state_machine_id,
                    "pattern": pattern_key,
                    "timestamp": datetime.utcnow(),
                }
            )

    def get_anomalies(self) -> List[Dict[str, Any]]:
        """Get detected anomalies."""
        return self._anomalies.copy()
