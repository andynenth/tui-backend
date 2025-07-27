"""
Core abstractions for state machine persistence.

Defines interfaces and base types for persisting game state machines.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


T = TypeVar('T')


class PersistenceMode(Enum):
    """Modes of state persistence."""
    SNAPSHOT = "snapshot"
    EVENT_SOURCED = "event_sourced"
    HYBRID = "hybrid"


@dataclass
class StateVersion:
    """Version information for a persisted state."""
    major: int
    minor: int
    patch: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'StateVersion') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


@dataclass
class StateTransition:
    """Represents a state machine transition."""
    from_state: str
    to_state: str
    action: str
    payload: Dict[str, Any]
    actor_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_state': self.from_state,
            'to_state': self.to_state,
            'action': self.action,
            'payload': self.payload,
            'actor_id': self.actor_id,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class PersistedState:
    """A persisted state machine state."""
    state_machine_id: str
    state_type: str
    current_state: str
    state_data: Dict[str, Any]
    version: StateVersion
    transitions: List[StateTransition] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_transition(self, transition: StateTransition) -> None:
        """Add a transition to the history."""
        self.transitions.append(transition)
        self.updated_at = datetime.utcnow()


@dataclass
class RecoveryPoint:
    """Point from which state can be recovered."""
    recovery_id: str
    state_machine_id: str
    timestamp: datetime
    state_snapshot: Optional[Dict[str, Any]] = None
    transition_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class IStatePersistence(ABC):
    """Interface for state persistence operations."""
    
    @abstractmethod
    async def save_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        version: Optional[StateVersion] = None
    ) -> str:
        """
        Save state machine state.
        
        Args:
            state_machine_id: Unique identifier for the state machine
            state: Current state data
            version: Optional version information
            
        Returns:
            Persistence identifier
        """
        pass
    
    @abstractmethod
    async def load_state(
        self,
        state_machine_id: str,
        version: Optional[StateVersion] = None
    ) -> Optional[PersistedState]:
        """
        Load state machine state.
        
        Args:
            state_machine_id: State machine identifier
            version: Optional specific version to load
            
        Returns:
            Persisted state if found
        """
        pass
    
    @abstractmethod
    async def delete_state(self, state_machine_id: str) -> bool:
        """
        Delete persisted state.
        
        Args:
            state_machine_id: State machine identifier
            
        Returns:
            True if deleted
        """
        pass
    
    @abstractmethod
    async def list_versions(
        self,
        state_machine_id: str
    ) -> List[StateVersion]:
        """
        List available versions for a state machine.
        
        Args:
            state_machine_id: State machine identifier
            
        Returns:
            List of available versions
        """
        pass


class IStateSnapshot(ABC):
    """Interface for state snapshot operations."""
    
    @abstractmethod
    async def create_snapshot(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a state snapshot.
        
        Args:
            state_machine_id: State machine identifier
            state: State to snapshot
            metadata: Optional metadata
            
        Returns:
            Snapshot identifier
        """
        pass
    
    @abstractmethod
    async def restore_snapshot(
        self,
        snapshot_id: str
    ) -> Optional[PersistedState]:
        """
        Restore from snapshot.
        
        Args:
            snapshot_id: Snapshot identifier
            
        Returns:
            Restored state if found
        """
        pass
    
    @abstractmethod
    async def list_snapshots(
        self,
        state_machine_id: str,
        limit: Optional[int] = None
    ) -> List[RecoveryPoint]:
        """
        List available snapshots.
        
        Args:
            state_machine_id: State machine identifier
            limit: Maximum number of snapshots to return
            
        Returns:
            List of recovery points
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: Snapshot identifier
            
        Returns:
            True if deleted
        """
        pass


class IStateTransitionLog(ABC):
    """Interface for state transition logging."""
    
    @abstractmethod
    async def log_transition(
        self,
        state_machine_id: str,
        transition: StateTransition
    ) -> None:
        """
        Log a state transition.
        
        Args:
            state_machine_id: State machine identifier
            transition: Transition to log
        """
        pass
    
    @abstractmethod
    async def get_transitions(
        self,
        state_machine_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[StateTransition]:
        """
        Get transitions for a state machine.
        
        Args:
            state_machine_id: State machine identifier
            from_timestamp: Start timestamp filter
            to_timestamp: End timestamp filter
            limit: Maximum number of transitions
            
        Returns:
            List of transitions
        """
        pass
    
    @abstractmethod
    async def replay_transitions(
        self,
        state_machine_id: str,
        from_state: Dict[str, Any],
        transitions: List[StateTransition]
    ) -> Dict[str, Any]:
        """
        Replay transitions from a base state.
        
        Args:
            state_machine_id: State machine identifier
            from_state: Starting state
            transitions: Transitions to replay
            
        Returns:
            Final state after replay
        """
        pass
    
    @abstractmethod
    async def compact_log(
        self,
        state_machine_id: str,
        before_timestamp: datetime
    ) -> int:
        """
        Compact transition log by removing old entries.
        
        Args:
            state_machine_id: State machine identifier
            before_timestamp: Remove transitions before this time
            
        Returns:
            Number of transitions removed
        """
        pass


class IStateRecovery(ABC):
    """Interface for state recovery operations."""
    
    @abstractmethod
    async def create_recovery_point(
        self,
        state_machine_id: str,
        state: Dict[str, Any]
    ) -> RecoveryPoint:
        """
        Create a recovery point.
        
        Args:
            state_machine_id: State machine identifier
            state: Current state
            
        Returns:
            Recovery point
        """
        pass
    
    @abstractmethod
    async def recover_state(
        self,
        recovery_point: RecoveryPoint
    ) -> Optional[PersistedState]:
        """
        Recover state from a recovery point.
        
        Args:
            recovery_point: Point to recover from
            
        Returns:
            Recovered state if successful
        """
        pass
    
    @abstractmethod
    async def list_recovery_points(
        self,
        state_machine_id: str,
        limit: Optional[int] = None
    ) -> List[RecoveryPoint]:
        """
        List available recovery points.
        
        Args:
            state_machine_id: State machine identifier
            limit: Maximum number of points
            
        Returns:
            List of recovery points
        """
        pass
    
    @abstractmethod
    async def validate_recovery(
        self,
        state_machine_id: str,
        recovered_state: Dict[str, Any]
    ) -> bool:
        """
        Validate a recovered state.
        
        Args:
            state_machine_id: State machine identifier
            recovered_state: State to validate
            
        Returns:
            True if state is valid
        """
        pass


class StatePersistenceBase(IStatePersistence):
    """Base implementation with common functionality."""
    
    def __init__(self):
        """Initialize base persistence."""
        self._version_counter = 0
    
    def _generate_version(self) -> StateVersion:
        """Generate a new version."""
        self._version_counter += 1
        return StateVersion(
            major=1,
            minor=0,
            patch=self._version_counter
        )
    
    def _validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate state structure."""
        required_fields = ['current_state', 'state_data']
        return all(field in state for field in required_fields)