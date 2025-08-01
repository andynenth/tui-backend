"""
State Management Adapter - Bridge pattern for gradual integration.

This adapter provides a clean interface between use cases and the state persistence
infrastructure, allowing for feature-flag-controlled gradual rollout.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
import time
from datetime import datetime, timedelta

from infrastructure.state_persistence.persistence_manager import (
    StatePersistenceManager,
    AutoPersistencePolicy,
)
from infrastructure.state_persistence.abstractions import (
    StateTransition,
    PersistedState,
    RecoveryPoint,
)
from infrastructure.feature_flags import get_feature_flags
from domain.entities.game import GamePhase as DomainGamePhase
from infrastructure.resilience.circuit_breaker import (
    get_circuit_breaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
)
from infrastructure.monitoring.state_management_metrics import (
    get_state_metrics_collector,
    track_state_operation,
)


logger = logging.getLogger(__name__)


@dataclass
class StateTransitionContext:
    """Context for state transitions."""
    
    game_id: str
    room_id: str
    actor_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StateManagementAdapter:
    """
    Adapter that bridges use cases with state persistence infrastructure.
    
    This adapter:
    1. Provides a simple interface for use cases
    2. Handles feature flag checks
    3. Maps between domain and state machine concepts
    4. Provides fallback behavior when disabled
    5. Logs all state transitions for debugging
    """
    
    def __init__(
        self,
        state_manager: Optional[StatePersistenceManager] = None,
        enabled: Optional[bool] = None
    ):
        """
        Initialize the adapter.
        
        Args:
            state_manager: The state persistence manager (optional)
            enabled: Force enable/disable (overrides feature flag)
        """
        self._state_manager = state_manager
        self._feature_flags = get_feature_flags()
        self._forced_enabled = enabled
        
        # Default persistence policy
        self._default_policy = AutoPersistencePolicy(
            persist_on_transition=True,
            persist_on_phase_change=True,
            persist_on_error=True,
        )
        
        # Track if we've logged the disabled message
        self._logged_disabled = False
        
        # Set up circuit breaker for resilience
        cb_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=timedelta(seconds=30),
            success_threshold=3
        )
        self._circuit_breaker = get_circuit_breaker("state_management", cb_config)
        
        # Set up metrics collector
        self._metrics = get_state_metrics_collector()
    
    @property
    def enabled(self) -> bool:
        """Check if state management is enabled."""
        if self._forced_enabled is not None:
            return self._forced_enabled
            
        # Check feature flag
        return self._feature_flags.is_enabled("USE_STATE_PERSISTENCE", {})
    
    async def track_game_start(
        self,
        game_id: str,
        room_id: str,
        players: List[str],
        starting_player: Optional[str] = None
    ) -> bool:
        """
        Track game start transition.
        
        Args:
            game_id: Game identifier
            room_id: Room identifier
            players: List of player names
            starting_player: Optional starting player
            
        Returns:
            True if tracked successfully (or disabled)
        """
        if not self.enabled or not self._state_manager:
            self._log_disabled("track_game_start")
            return True
            
        start_time = time.time()
        try:
            transition = StateTransition(
                from_state="NOT_STARTED",
                to_state="PREPARATION",
                action="start_game",
                payload={
                    "players": players,
                    "player_count": len(players),
                    "starting_player": starting_player,
                    "timestamp": datetime.utcnow().isoformat()
                },
                actor_id=starting_player,
                metadata={"is_phase_change": True}
            )
            
            # Use circuit breaker for resilience
            await self._circuit_breaker.call_async(
                self._state_manager.handle_transition,
                state_machine_id=game_id,
                transition=transition,
                policy=self._default_policy
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self._metrics.track_transition(True, duration_ms, phase_change=True)
            
            logger.info(f"State transition tracked: NOT_STARTED → PREPARATION for game {game_id}")
            return True
            
        except CircuitBreakerError:
            logger.warning(f"Circuit breaker OPEN - skipping state tracking for game {game_id}")
            self._metrics.track_error("CircuitBreakerOpen", "track_game_start")
            return False
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._metrics.track_transition(False, duration_ms, phase_change=True)
            logger.error(f"Failed to track game start for {game_id}: {e}")
            # Don't fail the game start due to state tracking failure
            return False
    
    async def track_phase_change(
        self,
        context: StateTransitionContext,
        from_phase: DomainGamePhase,
        to_phase: DomainGamePhase,
        trigger: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track a phase change transition.
        
        Args:
            context: Transition context
            from_phase: Current phase
            to_phase: New phase
            trigger: What triggered the transition
            payload: Additional data
            
        Returns:
            True if tracked successfully (or disabled)
        """
        if not self.enabled or not self._state_manager:
            self._log_disabled("track_phase_change")
            return True
            
        try:
            # Map domain phases to state machine phases
            from_state = self._map_domain_to_state_phase(from_phase)
            to_state = self._map_domain_to_state_phase(to_phase)
            
            transition_payload = {
                "trigger": trigger,
                "room_id": context.room_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if payload:
                transition_payload.update(payload)
            
            transition = StateTransition(
                from_state=from_state,
                to_state=to_state,
                action=trigger,
                payload=transition_payload,
                actor_id=context.actor_id,
                metadata={
                    "is_phase_change": True,
                    **context.metadata
                }
            )
            
            await self._state_manager.handle_transition(
                state_machine_id=context.game_id,
                transition=transition,
                policy=self._default_policy
            )
            
            logger.info(f"Phase change tracked: {from_state} → {to_state} for game {context.game_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track phase change for {context.game_id}: {e}")
            return False
    
    async def track_player_action(
        self,
        context: StateTransitionContext,
        action: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Track a player action (not necessarily a phase change).
        
        Args:
            context: Transition context
            action: Action type (e.g., "declare", "play_pieces")
            payload: Action data
            
        Returns:
            True if tracked successfully (or disabled)
        """
        if not self.enabled or not self._state_manager:
            self._log_disabled("track_player_action")
            return True
            
        try:
            # Get current state from context or load it
            current_state = context.metadata.get("current_phase", "UNKNOWN")
            
            transition = StateTransition(
                from_state=current_state,
                to_state=current_state,  # Same state (no phase change)
                action=action,
                payload={
                    **payload,
                    "room_id": context.room_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                actor_id=context.actor_id,
                metadata=context.metadata
            )
            
            # Use a lighter policy for non-phase-change actions
            action_policy = AutoPersistencePolicy(
                persist_on_transition=False,  # Don't persist every action
                persist_on_phase_change=True,
                persist_on_error=True,
            )
            
            await self._state_manager.handle_transition(
                state_machine_id=context.game_id,
                transition=transition,
                policy=action_policy
            )
            
            logger.debug(f"Player action tracked: {action} for game {context.game_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track player action for {context.game_id}: {e}")
            return False
    
    async def create_snapshot(self, game_id: str, reason: str = "manual") -> Optional[str]:
        """
        Create a manual snapshot of current game state.
        
        Args:
            game_id: Game identifier
            reason: Reason for snapshot
            
        Returns:
            Snapshot ID if successful
        """
        if not self.enabled or not self._state_manager:
            self._log_disabled("create_snapshot")
            return None
            
        try:
            snapshot_ids = await self._state_manager.create_snapshot(game_id)
            snapshot_id = snapshot_ids[0] if snapshot_ids else None
            
            if snapshot_id:
                logger.info(f"Snapshot created for game {game_id}: {snapshot_id} (reason: {reason})")
                
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Failed to create snapshot for {game_id}: {e}")
            return None
    
    async def recover_game_state(
        self,
        game_id: str,
        recovery_point: Optional[RecoveryPoint] = None
    ) -> Optional[PersistedState]:
        """
        Recover game state from persistence.
        
        Args:
            game_id: Game identifier
            recovery_point: Specific recovery point (optional)
            
        Returns:
            Recovered state if successful
        """
        if not self.enabled or not self._state_manager:
            self._log_disabled("recover_game_state")
            return None
            
        try:
            recovered = await self._state_manager.recover_state(game_id)
            
            if recovered:
                logger.info(f"Game state recovered for {game_id} at phase {recovered.current_state}")
                
            return recovered
            
        except Exception as e:
            logger.error(f"Failed to recover game state for {game_id}: {e}")
            return None
    
    def _map_domain_to_state_phase(self, domain_phase: DomainGamePhase) -> str:
        """
        Map domain GamePhase to state machine phase.
        
        This handles the enum mismatch between architectures.
        """
        # Direct mappings
        mapping = {
            DomainGamePhase.NOT_STARTED: "NOT_STARTED",
            DomainGamePhase.PREPARATION: "PREPARATION",
            DomainGamePhase.DECLARATION: "DECLARATION",
            DomainGamePhase.TURN: "TURN",
            DomainGamePhase.SCORING: "SCORING",
            DomainGamePhase.GAME_OVER: "GAME_OVER",
        }
        
        return mapping.get(domain_phase, str(domain_phase.value))
    
    def _log_disabled(self, operation: str) -> None:
        """Log that state management is disabled (only once)."""
        if not self._logged_disabled:
            logger.debug(f"State management disabled - {operation} not tracked")
            self._logged_disabled = True
    
    async def get_game_history(
        self,
        game_id: str,
        limit: Optional[int] = None
    ) -> List[StateTransition]:
        """
        Get game state transition history.
        
        Args:
            game_id: Game identifier
            limit: Maximum transitions to return
            
        Returns:
            List of state transitions
        """
        if not self.enabled or not self._state_manager:
            return []
            
        try:
            # This would need to be implemented in StatePersistenceManager
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Failed to get game history for {game_id}: {e}")
            return []
    
    def create_context(
        self,
        game_id: str,
        room_id: str,
        player_id: Optional[str] = None,
        **metadata
    ) -> StateTransitionContext:
        """
        Helper to create transition context.
        
        Args:
            game_id: Game identifier
            room_id: Room identifier
            player_id: Acting player
            **metadata: Additional metadata
            
        Returns:
            Transition context
        """
        return StateTransitionContext(
            game_id=game_id,
            room_id=room_id,
            actor_id=player_id,
            metadata=metadata
        )