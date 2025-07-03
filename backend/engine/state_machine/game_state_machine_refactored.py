# backend/engine/state_machine/game_state_machine_refactored.py

import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime

from .core import GamePhase, ActionType, GameAction
from .action_queue import ActionQueue
from .base_state import GameState
from .states import PreparationState, DeclarationState, TurnState, ScoringState

# Import extracted components
from .action_processor import ActionProcessor
from .phase_manager import PhaseManager
from .event_broadcaster import EventBroadcaster

logger = logging.getLogger(__name__)


class GameStateMachine:
    """
    🎯 **Refactored GameStateMachine** - Phase 2 God Class Decomposition
    
    Now acts as a lightweight coordinator that delegates to specialized components:
    - ActionProcessor: Handles action validation, execution, and bot notifications
    - PhaseManager: Manages phase transitions and state coordination
    - EventBroadcaster: Handles all WebSocket broadcasting and events
    
    Reduced from 854 lines to ~200 lines by extracting responsibilities.
    """
    
    def __init__(self, game, broadcast_callback=None):
        # Core game reference and configuration
        self.game = game
        self.broadcast_callback = broadcast_callback
        
        # State tracking
        self.current_state: Optional[GameState] = None
        self.current_phase: Optional[GamePhase] = None
        self.is_running = False
        
        # Initialize extracted components
        self.action_processor = ActionProcessor(self)
        self.phase_manager = PhaseManager(self)
        self.event_broadcaster = EventBroadcaster(self)
        
        # Action queue for event storage
        room_id = getattr(game, 'room_id', None) if game else None
        self.action_queue = ActionQueue(room_id=room_id)
        
        # Event processing
        from .events import EventProcessor
        self.event_processor = EventProcessor(self)
        
        # Task management
        self.active_tasks = set()
        
        # Initialize all available states
        self.states: Dict[GamePhase, GameState] = {
            GamePhase.PREPARATION: PreparationState(self),
            GamePhase.DECLARATION: DeclarationState(self),
            GamePhase.TURN: TurnState(self),
            GamePhase.SCORING: ScoringState(self),
        }
        
        # Legacy support for room_id (needed by extracted components)
        self.room_id = room_id
    
    # === Lifecycle Management ===
    
    async def start(self, initial_phase: GamePhase = GamePhase.PREPARATION):
        """Start the state machine in event-driven mode."""
        if self.is_running:
            logger.warning("State machine already running")
            return
        
        logger.info(f"🚀 Starting state machine in {initial_phase} phase")
        self.is_running = True
        
        # Enter initial phase
        await self.phase_manager._immediate_transition_to(initial_phase, "Initial state machine start")
    
    async def stop(self):
        """Stop the state machine and clean up resources."""
        logger.info("🛑 Stopping state machine")
        self.is_running = False
        
        # Clean up managed async tasks
        await self.cleanup_all_tasks()
        
        # Exit current state
        if self.current_state:
            await self.current_state.on_exit()
    
    # === Action Handling (Delegated to ActionProcessor) ===
    
    async def validate_action(self, action: GameAction) -> Dict:
        """Validate action without executing."""
        return await self.action_processor.validate_action(action)
    
    async def execute_action(self, action: GameAction) -> Dict:
        """Execute a pre-validated action."""
        return await self.action_processor.execute_action(action)
    
    async def handle_action(self, action: GameAction) -> Dict:
        """Main entry point for all game actions."""
        return await self.action_processor.handle_action(action)
    
    # === Phase Management (Delegated to PhaseManager) ===
    
    async def trigger_immediate_transition(self, event: str, target_state: GamePhase, reason: str) -> bool:
        """Trigger immediate phase transition."""
        return await self.phase_manager.trigger_immediate_transition(event, target_state, reason)
    
    def get_current_phase(self) -> Optional[GamePhase]:
        """Get current game phase."""
        return self.phase_manager.get_current_phase()
    
    def get_phase_data(self) -> Dict:
        """Get current phase data."""
        return self.phase_manager.get_phase_data()
    
    # === Event Broadcasting (Delegated to EventBroadcaster) ===
    
    async def broadcast_event(self, event_type: str, event_data: Dict):
        """Broadcast event to all connected clients."""
        await self.event_broadcaster.broadcast_event(event_type, event_data)
    
    async def broadcast_turn_completion(self, turn_data: Dict):
        """Broadcast turn completion."""
        await self.event_broadcaster.broadcast_turn_completion(turn_data)
    
    async def broadcast_scoring_completion(self, scores: Dict):
        """Broadcast scoring completion."""
        await self.event_broadcaster.broadcast_scoring_completion(scores)
    
    # === State Information ===
    
    def get_allowed_actions(self) -> Set[ActionType]:
        """Get actions allowed in current state."""
        if not self.current_state:
            return set()
        
        try:
            return self.current_state.get_allowed_actions()
        except Exception as e:
            logger.error(f"❌ Error getting allowed actions: {str(e)}")
            return set()
    
    # === Task Management ===
    
    async def create_managed_task(self, coro, task_name: str) -> asyncio.Task:
        """Create a managed asyncio task that gets cleaned up on shutdown."""
        task = asyncio.create_task(coro, name=task_name)
        self.active_tasks.add(task)
        
        # Remove task from set when it completes
        def cleanup_task(t):
            self.active_tasks.discard(t)
        
        task.add_done_callback(cleanup_task)
        return task
    
    async def cleanup_all_tasks(self):
        """Cancel and cleanup all managed tasks."""
        if not self.active_tasks:
            return
        
        logger.info(f"🧹 Cleaning up {len(self.active_tasks)} active tasks")
        
        # Cancel all tasks
        for task in self.active_tasks:
            task.cancel()
        
        # Wait for all tasks to complete cancellation
        await asyncio.gather(*self.active_tasks, return_exceptions=True)
        self.active_tasks.clear()
    
    # === Event Storage (For debugging and analytics) ===
    
    async def store_game_event(self, event_type: str, payload: dict, player_id: Optional[str] = None):
        """Store game event for debugging and analytics."""
        try:
            event_data = {
                "event_type": event_type,
                "payload": payload,
                "player_id": player_id,
                "timestamp": datetime.now().isoformat(),
                "phase": self.current_phase.name if self.current_phase else None,
                "round": getattr(self.game, 'round_number', 0) if self.game else 0
            }
            
            # Store in action queue for persistence
            await self.action_queue.store_event(event_data)
            
        except Exception as e:
            logger.error(f"❌ Error storing game event {event_type}: {str(e)}")
    
    # === Legacy Compatibility ===
    
    # These properties maintain compatibility with existing code
    @property
    def transition_lock(self):
        """Legacy compatibility - access phase manager's lock."""
        return self.phase_manager.transition_lock
    
    # These methods are now thin wrappers around the extracted components
    async def _immediate_transition_to(self, new_phase: GamePhase, reason: str):
        """Legacy method - delegates to phase manager."""
        await self.phase_manager._immediate_transition_to(new_phase, reason)
    
    async def _broadcast_phase_change_with_hands(self, phase: GamePhase):
        """Legacy method - delegates to event broadcaster."""
        await self.event_broadcaster.broadcast_phase_change_with_hands(phase)


# Export the refactored version
__all__ = ['GameStateMachine']