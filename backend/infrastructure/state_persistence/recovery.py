"""
State recovery mechanisms for state machine persistence.

Provides various strategies for recovering state machines from persistence.
"""

from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from abc import ABC, abstractmethod

from .abstractions import (
    IStateRecovery,
    IStateSnapshot,
    IStateTransitionLog,
    PersistedState,
    RecoveryPoint,
    StateTransition,
    StateVersion
)
from .snapshot import StateSnapshotManager
from .transition_log import StateTransitionLogger


logger = logging.getLogger(__name__)


class RecoveryStatus(Enum):
    """Status of recovery operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    NOT_FOUND = "not_found"


class RecoveryMode(Enum):
    """Modes of state recovery."""
    LATEST = "latest"           # Most recent state
    SNAPSHOT = "snapshot"       # From specific snapshot
    POINT_IN_TIME = "point_in_time"  # At specific time
    BEFORE_ERROR = "before_error"    # Before last error


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""
    status: RecoveryStatus
    recovered_state: Optional[PersistedState] = None
    recovery_point: Optional[RecoveryPoint] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_successful(self) -> bool:
        """Check if recovery was successful."""
        return self.status in (RecoveryStatus.SUCCESS, RecoveryStatus.PARTIAL)


@dataclass
class RecoveryOptions:
    """Options for state recovery."""
    mode: RecoveryMode = RecoveryMode.LATEST
    target_timestamp: Optional[datetime] = None
    snapshot_id: Optional[str] = None
    validate_state: bool = True
    include_transitions: bool = True
    max_transitions_to_replay: int = 1000


class RecoveryStrategy(ABC):
    """Base class for recovery strategies."""
    
    @abstractmethod
    async def recover(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover state using this strategy."""
        pass
    
    @abstractmethod
    def supports_mode(self, mode: RecoveryMode) -> bool:
        """Check if strategy supports recovery mode."""
        pass


class SnapshotRecovery(RecoveryStrategy):
    """
    Recovery strategy using snapshots.
    
    Features:
    - Fast recovery from snapshots
    - Multiple snapshot sources
    - Validation support
    """
    
    def __init__(
        self,
        snapshot_stores: List[IStateSnapshot],
        validator: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        """Initialize snapshot recovery."""
        self.snapshot_stores = snapshot_stores
        self.validator = validator
    
    async def recover(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover state from snapshot."""
        try:
            if options.mode == RecoveryMode.SNAPSHOT and options.snapshot_id:
                # Recover specific snapshot
                return await self._recover_specific_snapshot(
                    options.snapshot_id,
                    options
                )
            
            elif options.mode == RecoveryMode.LATEST:
                # Recover latest snapshot
                return await self._recover_latest_snapshot(
                    state_machine_id,
                    options
                )
            
            elif options.mode == RecoveryMode.POINT_IN_TIME and options.target_timestamp:
                # Find snapshot closest to target time
                return await self._recover_point_in_time(
                    state_machine_id,
                    options.target_timestamp,
                    options
                )
            
            else:
                return RecoveryResult(
                    status=RecoveryStatus.FAILED,
                    error=f"Unsupported recovery mode: {options.mode}"
                )
                
        except Exception as e:
            logger.error(f"Error during snapshot recovery: {e}")
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                error=str(e)
            )
    
    def supports_mode(self, mode: RecoveryMode) -> bool:
        """Check if strategy supports recovery mode."""
        return mode in (
            RecoveryMode.LATEST,
            RecoveryMode.SNAPSHOT,
            RecoveryMode.POINT_IN_TIME
        )
    
    async def _recover_specific_snapshot(
        self,
        snapshot_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover from specific snapshot."""
        for store in self.snapshot_stores:
            try:
                state = await store.restore_snapshot(snapshot_id)
                if state:
                    # Validate if requested
                    if options.validate_state and self.validator:
                        if not self.validator(state.state_machine_id, state.state_data):
                            continue
                    
                    return RecoveryResult(
                        status=RecoveryStatus.SUCCESS,
                        recovered_state=state,
                        recovery_point=RecoveryPoint(
                            recovery_id=snapshot_id,
                            state_machine_id=state.state_machine_id,
                            timestamp=state.created_at,
                            state_snapshot=state.state_data
                        )
                    )
            except Exception as e:
                logger.error(f"Error restoring from store: {e}")
                continue
        
        return RecoveryResult(
            status=RecoveryStatus.NOT_FOUND,
            error=f"Snapshot {snapshot_id} not found"
        )
    
    async def _recover_latest_snapshot(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover from latest snapshot."""
        latest_snapshot = None
        latest_point = None
        
        for store in self.snapshot_stores:
            try:
                snapshots = await store.list_snapshots(state_machine_id, limit=1)
                if snapshots and (
                    not latest_point or
                    snapshots[0].timestamp > latest_point.timestamp
                ):
                    latest_point = snapshots[0]
                    latest_snapshot = store
            except Exception as e:
                logger.error(f"Error listing snapshots: {e}")
        
        if latest_point and latest_snapshot:
            state = await latest_snapshot.restore_snapshot(latest_point.recovery_id)
            if state:
                return RecoveryResult(
                    status=RecoveryStatus.SUCCESS,
                    recovered_state=state,
                    recovery_point=latest_point
                )
        
        return RecoveryResult(
            status=RecoveryStatus.NOT_FOUND,
            error=f"No snapshots found for {state_machine_id}"
        )
    
    async def _recover_point_in_time(
        self,
        state_machine_id: str,
        target_timestamp: datetime,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover from snapshot closest to target time."""
        best_snapshot = None
        best_point = None
        best_store = None
        
        for store in self.snapshot_stores:
            try:
                snapshots = await store.list_snapshots(state_machine_id)
                
                for point in snapshots:
                    if point.timestamp <= target_timestamp:
                        if not best_point or point.timestamp > best_point.timestamp:
                            best_point = point
                            best_store = store
                            
            except Exception as e:
                logger.error(f"Error finding point-in-time snapshot: {e}")
        
        if best_point and best_store:
            state = await best_store.restore_snapshot(best_point.recovery_id)
            if state:
                return RecoveryResult(
                    status=RecoveryStatus.SUCCESS,
                    recovered_state=state,
                    recovery_point=best_point,
                    metadata={
                        'target_timestamp': target_timestamp.isoformat(),
                        'actual_timestamp': best_point.timestamp.isoformat(),
                        'time_difference': (target_timestamp - best_point.timestamp).total_seconds()
                    }
                )
        
        return RecoveryResult(
            status=RecoveryStatus.NOT_FOUND,
            error=f"No suitable snapshot found for {target_timestamp}"
        )


class EventSourcedRecovery(RecoveryStrategy):
    """
    Recovery strategy using event sourcing.
    
    Features:
    - Rebuild state from events
    - Point-in-time recovery
    - Selective event replay
    """
    
    def __init__(
        self,
        transition_logs: List[IStateTransitionLog],
        initial_state_provider: Callable[[str], Dict[str, Any]],
        transition_applier: Optional[Callable[[Dict[str, Any], StateTransition], Dict[str, Any]]] = None
    ):
        """Initialize event sourced recovery."""
        self.transition_logs = transition_logs
        self.initial_state_provider = initial_state_provider
        self.transition_applier = transition_applier or self._default_apply_transition
    
    async def recover(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover state by replaying events."""
        try:
            # Get initial state
            initial_state = self.initial_state_provider(state_machine_id)
            
            # Get transitions to replay
            transitions = await self._get_transitions_to_replay(
                state_machine_id,
                options
            )
            
            if not transitions and options.mode != RecoveryMode.LATEST:
                return RecoveryResult(
                    status=RecoveryStatus.NOT_FOUND,
                    error="No transitions found to replay"
                )
            
            # Replay transitions
            current_state = initial_state
            for transition in transitions:
                try:
                    current_state = self.transition_applier(current_state, transition)
                except Exception as e:
                    logger.error(f"Error applying transition: {e}")
                    return RecoveryResult(
                        status=RecoveryStatus.PARTIAL,
                        recovered_state=self._create_persisted_state(
                            state_machine_id,
                            current_state,
                            transitions[:transitions.index(transition)]
                        ),
                        error=f"Recovery stopped at transition: {e}"
                    )
            
            # Create persisted state
            recovered_state = self._create_persisted_state(
                state_machine_id,
                current_state,
                transitions if options.include_transitions else []
            )
            
            return RecoveryResult(
                status=RecoveryStatus.SUCCESS,
                recovered_state=recovered_state,
                metadata={
                    'transitions_replayed': len(transitions),
                    'recovery_method': 'event_sourcing'
                }
            )
            
        except Exception as e:
            logger.error(f"Error during event sourced recovery: {e}")
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                error=str(e)
            )
    
    def supports_mode(self, mode: RecoveryMode) -> bool:
        """Check if strategy supports recovery mode."""
        return mode in (
            RecoveryMode.LATEST,
            RecoveryMode.POINT_IN_TIME,
            RecoveryMode.BEFORE_ERROR
        )
    
    async def _get_transitions_to_replay(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> List[StateTransition]:
        """Get transitions to replay based on options."""
        for log in self.transition_logs:
            try:
                if options.mode == RecoveryMode.LATEST:
                    # Get all transitions
                    return await log.get_transitions(
                        state_machine_id,
                        limit=options.max_transitions_to_replay
                    )
                
                elif options.mode == RecoveryMode.POINT_IN_TIME:
                    # Get transitions up to target time
                    return await log.get_transitions(
                        state_machine_id,
                        to_timestamp=options.target_timestamp,
                        limit=options.max_transitions_to_replay
                    )
                
                elif options.mode == RecoveryMode.BEFORE_ERROR:
                    # Get transitions and find last error
                    all_transitions = await log.get_transitions(
                        state_machine_id,
                        limit=options.max_transitions_to_replay
                    )
                    
                    # Find last error transition
                    error_index = None
                    for i, transition in enumerate(all_transitions):
                        if transition.metadata.get('is_error'):
                            error_index = i
                    
                    if error_index is not None:
                        return all_transitions[:error_index]
                    else:
                        return all_transitions
                        
            except Exception as e:
                logger.error(f"Error getting transitions: {e}")
                continue
        
        return []
    
    def _default_apply_transition(
        self,
        state: Dict[str, Any],
        transition: StateTransition
    ) -> Dict[str, Any]:
        """Default transition application."""
        new_state = state.copy()
        new_state['current_state'] = transition.to_state
        
        if 'state_data' not in new_state:
            new_state['state_data'] = {}
        
        new_state['state_data'].update(transition.payload)
        new_state['last_transition'] = transition.to_dict()
        new_state['last_updated'] = datetime.utcnow().isoformat()
        
        return new_state
    
    def _create_persisted_state(
        self,
        state_machine_id: str,
        state: Dict[str, Any],
        transitions: List[StateTransition]
    ) -> PersistedState:
        """Create persisted state from recovered data."""
        return PersistedState(
            state_machine_id=state_machine_id,
            state_type=state.get('state_type', 'unknown'),
            current_state=state.get('current_state', 'unknown'),
            state_data=state,
            version=StateVersion(1, 0, len(transitions)),
            transitions=transitions,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


class HybridRecovery(RecoveryStrategy):
    """
    Hybrid recovery strategy combining snapshots and event sourcing.
    
    Features:
    - Fast recovery from snapshots
    - Event replay for recent changes
    - Best of both approaches
    """
    
    def __init__(
        self,
        snapshot_recovery: SnapshotRecovery,
        event_recovery: EventSourcedRecovery,
        snapshot_age_threshold: timedelta = timedelta(hours=1)
    ):
        """Initialize hybrid recovery."""
        self.snapshot_recovery = snapshot_recovery
        self.event_recovery = event_recovery
        self.snapshot_age_threshold = snapshot_age_threshold
    
    async def recover(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover using hybrid approach."""
        try:
            # Try snapshot recovery first
            snapshot_result = await self.snapshot_recovery.recover(
                state_machine_id,
                RecoveryOptions(
                    mode=RecoveryMode.LATEST,
                    validate_state=options.validate_state
                )
            )
            
            if not snapshot_result.is_successful:
                # Fall back to event sourcing
                return await self.event_recovery.recover(state_machine_id, options)
            
            # Check snapshot age
            snapshot_age = datetime.utcnow() - snapshot_result.recovered_state.created_at
            
            if snapshot_age < self.snapshot_age_threshold:
                # Recent snapshot, use as is
                return snapshot_result
            
            # Replay events since snapshot
            transitions = await self._get_transitions_since_snapshot(
                state_machine_id,
                snapshot_result.recovered_state.created_at
            )
            
            if transitions:
                # Apply transitions to snapshot state
                current_state = snapshot_result.recovered_state.state_data
                
                for transition in transitions:
                    try:
                        current_state = self.event_recovery.transition_applier(
                            current_state,
                            transition
                        )
                    except Exception as e:
                        logger.error(f"Error applying transition: {e}")
                        break
                
                # Update recovered state
                snapshot_result.recovered_state.state_data = current_state
                snapshot_result.recovered_state.transitions.extend(transitions)
                snapshot_result.recovered_state.updated_at = datetime.utcnow()
                
                snapshot_result.metadata['hybrid_recovery'] = True
                snapshot_result.metadata['transitions_applied'] = len(transitions)
            
            return snapshot_result
            
        except Exception as e:
            logger.error(f"Error during hybrid recovery: {e}")
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                error=str(e)
            )
    
    def supports_mode(self, mode: RecoveryMode) -> bool:
        """Check if strategy supports recovery mode."""
        return self.snapshot_recovery.supports_mode(mode) or \
               self.event_recovery.supports_mode(mode)
    
    async def _get_transitions_since_snapshot(
        self,
        state_machine_id: str,
        snapshot_timestamp: datetime
    ) -> List[StateTransition]:
        """Get transitions since snapshot."""
        for log in self.event_recovery.transition_logs:
            try:
                return await log.get_transitions(
                    state_machine_id,
                    from_timestamp=snapshot_timestamp
                )
            except Exception as e:
                logger.error(f"Error getting transitions: {e}")
                continue
        
        return []


class StateRecoveryManager(IStateRecovery):
    """
    Main state recovery manager.
    
    Features:
    - Multiple recovery strategies
    - Automatic strategy selection
    - Recovery validation
    """
    
    def __init__(
        self,
        strategies: List[RecoveryStrategy],
        default_strategy: Optional[RecoveryStrategy] = None,
        validator: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        """Initialize recovery manager."""
        self.strategies = strategies
        self.default_strategy = default_strategy or strategies[0]
        self.validator = validator
        self._recovery_history: List[RecoveryResult] = []
    
    async def create_recovery_point(
        self,
        state_machine_id: str,
        state: Dict[str, Any]
    ) -> RecoveryPoint:
        """Create a recovery point."""
        return RecoveryPoint(
            recovery_id=f"recovery_{state_machine_id}_{datetime.utcnow().timestamp()}",
            state_machine_id=state_machine_id,
            timestamp=datetime.utcnow(),
            state_snapshot=state,
            metadata={
                'created_by': 'recovery_manager',
                'state_size': len(str(state))
            }
        )
    
    async def recover_state(
        self,
        recovery_point: RecoveryPoint
    ) -> Optional[PersistedState]:
        """Recover state from a recovery point."""
        if recovery_point.state_snapshot:
            # Direct recovery from snapshot
            return PersistedState(
                state_machine_id=recovery_point.state_machine_id,
                state_type='recovered',
                current_state=recovery_point.state_snapshot.get('current_state', 'unknown'),
                state_data=recovery_point.state_snapshot,
                version=StateVersion(1, 0, 0),
                created_at=recovery_point.timestamp,
                updated_at=datetime.utcnow(),
                metadata={'recovery_point_id': recovery_point.recovery_id}
            )
        
        # Try recovery strategies
        options = RecoveryOptions(
            mode=RecoveryMode.SNAPSHOT,
            snapshot_id=recovery_point.recovery_id
        )
        
        result = await self.recover_with_options(
            recovery_point.state_machine_id,
            options
        )
        
        return result.recovered_state if result.is_successful else None
    
    async def list_recovery_points(
        self,
        state_machine_id: str,
        limit: Optional[int] = None
    ) -> List[RecoveryPoint]:
        """List available recovery points."""
        recovery_points = []
        
        # Collect from all strategies that support listing
        for strategy in self.strategies:
            if hasattr(strategy, 'list_recovery_points'):
                try:
                    points = await strategy.list_recovery_points(
                        state_machine_id,
                        limit
                    )
                    recovery_points.extend(points)
                except Exception as e:
                    logger.error(f"Error listing recovery points: {e}")
        
        # Sort by timestamp
        recovery_points.sort(key=lambda p: p.timestamp, reverse=True)
        
        if limit:
            recovery_points = recovery_points[:limit]
        
        return recovery_points
    
    async def validate_recovery(
        self,
        state_machine_id: str,
        recovered_state: Dict[str, Any]
    ) -> bool:
        """Validate a recovered state."""
        if self.validator:
            return self.validator(state_machine_id, recovered_state)
        
        # Basic validation
        required_fields = ['current_state', 'state_data']
        return all(field in recovered_state for field in required_fields)
    
    async def recover_with_options(
        self,
        state_machine_id: str,
        options: RecoveryOptions
    ) -> RecoveryResult:
        """Recover state with specific options."""
        # Find suitable strategy
        strategy = self._select_strategy(options.mode)
        
        if not strategy:
            return RecoveryResult(
                status=RecoveryStatus.FAILED,
                error=f"No strategy supports mode: {options.mode}"
            )
        
        # Attempt recovery
        result = await strategy.recover(state_machine_id, options)
        
        # Validate if requested
        if result.is_successful and options.validate_state and result.recovered_state:
            is_valid = await self.validate_recovery(
                state_machine_id,
                result.recovered_state.state_data
            )
            
            if not is_valid:
                result.status = RecoveryStatus.PARTIAL
                result.error = "State validation failed"
        
        # Record in history
        self._recovery_history.append(result)
        
        return result
    
    def _select_strategy(self, mode: RecoveryMode) -> Optional[RecoveryStrategy]:
        """Select strategy based on recovery mode."""
        for strategy in self.strategies:
            if strategy.supports_mode(mode):
                return strategy
        
        return self.default_strategy if self.default_strategy.supports_mode(mode) else None
    
    def get_recovery_history(self) -> List[RecoveryResult]:
        """Get recovery history."""
        return self._recovery_history.copy()