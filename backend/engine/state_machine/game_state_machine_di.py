# backend/engine/state_machine/game_state_machine_di.py

import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime

from .core import GamePhase, ActionType, GameAction
from .action_queue import ActionQueue
from .base_state import GameState
from .states import PreparationState, DeclarationState, TurnState, ScoringState

# Import dependency injection components
from ..dependency_injection.interfaces import IBroadcaster, IBotNotifier, IEventStore, IStateMachine
from .action_processor_di import ActionProcessor
from .phase_manager_di import PhaseManager
from .event_broadcaster_di import EventBroadcaster

logger = logging.getLogger(__name__)


class GameStateMachine(IStateMachine):
    """
    🎯 **GameStateMachine with Dependency Injection** - Phase 3 Circular Dependency Resolution
    
    Now acts as a lightweight coordinator with NO circular dependencies:
    - Uses dependency injection for all external services
    - Implements IStateMachine interface for loose coupling
    - Delegates to specialized components with injected dependencies
    - Clean import hierarchy with no circular references
    
    Eliminated circular dependencies by:
    1. Using IBroadcaster interface instead of direct socket_manager import
    2. Using IBotNotifier interface instead of direct bot_manager import  
    3. Using IEventStore interface instead of direct event storage access
    4. Dependency injection for all component construction
    """
    
    def __init__(
        self, 
        game, 
        broadcaster: IBroadcaster,
        bot_notifier: IBotNotifier,
        event_store: IEventStore,
        broadcast_callback=None  # Legacy support
    ):
        # Core game reference and configuration
        self.game = game
        self.broadcast_callback = broadcast_callback  # Legacy support
        
        # State tracking
        self.current_state: Optional[GameState] = None
        self.current_phase: Optional[GamePhase] = None
        self.is_running = False
        
        # Initialize extracted components with dependency injection
        self.action_processor = ActionProcessor(self, bot_notifier, event_store)
        self.phase_manager = PhaseManager(self, broadcaster, bot_notifier, event_store)
        self.event_broadcaster = EventBroadcaster(self, broadcaster, bot_notifier)
        
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
        
        # Room ID for component access (no longer creates circular dependency)
        self.room_id = room_id
        
        # Store injected dependencies for component access
        self._broadcaster = broadcaster
        self._bot_notifier = bot_notifier
        self._event_store = event_store
    
    # === IStateMachine Interface Implementation ===
    
    def get_current_phase(self) -> Optional[str]:
        """Get the current game phase."""
        return self.current_phase.name if self.current_phase else None
    
    def get_phase_data(self) -> Dict:
        """Get current phase data."""
        return self.phase_manager.get_phase_data()
    
    def get_allowed_actions(self) -> Set[str]:
        """Get actions allowed in current state."""
        if not self.current_state:
            return set()
        
        try:
            action_types = self.current_state.get_allowed_actions()
            return {action_type.value for action_type in action_types}
        except Exception as e:
            logger.error(f"❌ Error getting allowed actions: {str(e)}")
            return set()
    
    async def validate_action(self, action: GameAction) -> Dict:
        """Validate action without executing."""
        return await self.action_processor.validate_action(action)
    
    async def handle_action(self, action: GameAction) -> Dict:
        """Main entry point for all game actions."""
        return await self.action_processor.handle_action(action)
    
    async def store_game_event(self, event_type: str, payload: dict, player_id: Optional[str] = None):
        """Store game event for debugging and analytics."""
        try:
            if self.room_id:
                event_data = {
                    "event_type": event_type,
                    "payload": payload,
                    "player_id": player_id,
                    "timestamp": datetime.now().isoformat(),
                    "phase": self.current_phase.name if self.current_phase else None,
                    "round": getattr(self.game, 'round_number', 0) if self.game else 0
                }
                
                await self._event_store.store_event(self.room_id, event_data)
            
        except Exception as e:
            logger.error(f"❌ Error storing game event {event_type}: {str(e)}")
    
    # === Lifecycle Management ===
    
    async def start(self, initial_phase: GamePhase = GamePhase.PREPARATION):
        """Start the state machine in event-driven mode."""
        if self.is_running:
            logger.warning("State machine already running")
            return
        
        logger.info(f"🚀 Starting DI-enabled state machine in {initial_phase} phase")
        self.is_running = True
        
        # Enter initial phase
        await self.phase_manager._immediate_transition_to(initial_phase, "Initial state machine start")
    
    async def stop(self):
        """Stop the state machine and clean up resources."""
        logger.info("🛑 Stopping DI-enabled state machine")
        self.is_running = False
        
        # Clean up managed async tasks
        await self.cleanup_all_tasks()
        
        # Exit current state
        if self.current_state:
            await self.current_state.on_exit()
    
    # === Action Handling (Delegated to ActionProcessor) ===
    
    async def execute_action(self, action: GameAction) -> Dict:
        """Execute a pre-validated action."""
        return await self.action_processor.execute_action(action)
    
    # === Phase Management (Delegated to PhaseManager) ===
    
    async def trigger_immediate_transition(self, event: str, target_state: GamePhase, reason: str) -> bool:
        """Trigger immediate phase transition."""
        return await self.phase_manager.trigger_immediate_transition(event, target_state, reason)
    
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
    
    # === Component Factory Methods ===
    
    @classmethod
    def create_with_dependencies(
        cls,
        game,
        broadcaster: IBroadcaster,
        bot_notifier: IBotNotifier,
        event_store: IEventStore,
        broadcast_callback=None
    ) -> 'GameStateMachine':
        """
        Factory method to create GameStateMachine with dependency injection.
        
        This is the preferred way to create instances in the new architecture.
        """
        logger.info("🏭 Creating GameStateMachine with dependency injection")
        return cls(game, broadcaster, bot_notifier, event_store, broadcast_callback)
    
    @classmethod
    async def create_from_container(
        cls,
        game,
        container,
        room_id: str,
        broadcast_callback=None
    ) -> 'GameStateMachine':
        """
        Factory method to create GameStateMachine using DI container.
        
        Args:
            game: The Game instance
            container: DI container with registered services
            room_id: Room ID for scoped services
            broadcast_callback: Legacy callback support
        """
        logger.info(f"🏭 Creating GameStateMachine from DI container for room {room_id}")
        
        # Create a scope for this room
        scope = container.create_scope(room_id)
        
        try:
            # Resolve dependencies from container
            broadcaster = await scope.resolve(IBroadcaster)
            bot_notifier = await scope.resolve(IBotNotifier)
            event_store = await scope.resolve(IEventStore)
            
            # Create instance with resolved dependencies
            return cls(game, broadcaster, bot_notifier, event_store, broadcast_callback)
            
        except Exception as e:
            logger.error(f"❌ Failed to create GameStateMachine from container: {str(e)}")
            await scope.dispose()
            raise


# Export the dependency injection-enabled version
__all__ = ['GameStateMachine']