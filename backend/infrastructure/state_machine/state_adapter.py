# infrastructure/state_machine/state_adapter.py
"""
Adapter to bridge the existing state machine with the new architecture.
"""

import logging
from typing import Optional, Dict, Any, List
import asyncio
from dataclasses import dataclass

from domain.entities.game import Game
from domain.value_objects.game_state import GamePhase
from domain.interfaces.event_publisher import EventPublisher
from application.interfaces.notification_service import NotificationService

logger = logging.getLogger(__name__)


@dataclass
class StateTransitionResult:
    """Result of a state transition."""
    success: bool
    from_phase: GamePhase
    to_phase: GamePhase
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class StateMachineAdapter:
    """
    Adapts the existing state machine to work with the new architecture.
    
    This adapter:
    - Wraps the existing state machine
    - Translates between old and new interfaces
    - Handles notifications through the NotificationService
    - Publishes domain events
    """
    
    def __init__(
        self,
        game: Game,
        room_id: str,
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._game = game
        self._room_id = room_id
        self._event_publisher = event_publisher
        self._notification_service = notification_service
        
        # Import existing state machine
        from engine.state_machine.game_state_machine import GameStateMachine
        from engine.room import Room as OldRoom
        
        # Create a minimal room wrapper for the old state machine
        self._old_room = OldRoom("dummy_host")
        self._old_room.id = room_id
        self._old_room.game = self._game
        
        # Initialize the old state machine
        self._state_machine = GameStateMachine(self._old_room)
        
        # Override the broadcast method to use our notification service
        self._override_broadcast()
    
    def _override_broadcast(self):
        """Override the state machine's broadcast method."""
        original_broadcast = None
        
        # Try to find and override the broadcast function
        try:
            # Get the state machine's module
            import engine.state_machine.base_state as base_state
            
            # Store original if exists
            if hasattr(base_state, 'broadcast'):
                original_broadcast = base_state.broadcast
            
            # Create our broadcast wrapper
            async def broadcast_wrapper(room_id: str, event_type: str, data: Dict[str, Any]):
                """Wrapper that uses NotificationService instead of direct WebSocket."""
                await self._notification_service.notify_room(
                    room_id,
                    event_type,
                    data
                )
            
            # Replace the broadcast function
            base_state.broadcast = broadcast_wrapper
            
        except Exception as e:
            logger.warning(f"Could not override broadcast: {str(e)}")
    
    async def start(self) -> bool:
        """Start the state machine."""
        try:
            # Transition to preparation phase
            await self._state_machine.transition_to_preparation()
            return True
        except Exception as e:
            logger.error(f"Failed to start state machine: {str(e)}")
            return False
    
    async def process_action(
        self,
        action_type: str,
        payload: Dict[str, Any]
    ) -> StateTransitionResult:
        """
        Process an action through the state machine.
        
        Args:
            action_type: Type of action (e.g., "declare", "play")
            payload: Action data
            
        Returns:
            StateTransitionResult
        """
        try:
            # Get current phase
            from_phase = self._game.current_phase
            
            # Create action for state machine
            from engine.state_machine.action_queue import GameAction
            action = GameAction(
                player_name=payload.get("player", ""),
                action_type=action_type,
                payload=payload
            )
            
            # Process through state machine
            current_state = self._state_machine.get_current_state()
            if current_state:
                await current_state._process_action(action)
            
            # Get new phase
            to_phase = self._game.current_phase
            
            return StateTransitionResult(
                success=True,
                from_phase=from_phase,
                to_phase=to_phase,
                data=payload
            )
            
        except Exception as e:
            logger.error(f"State machine action failed: {str(e)}")
            return StateTransitionResult(
                success=False,
                from_phase=self._game.current_phase,
                to_phase=self._game.current_phase,
                error=str(e)
            )
    
    def get_current_player(self) -> Optional[str]:
        """Get the current player for turn/declaration."""
        current_state = self._state_machine.get_current_state()
        if current_state and hasattr(current_state, 'phase_data'):
            return current_state.phase_data.get('current_player')
        return None
    
    def get_current_declarer(self) -> Optional[str]:
        """Get the current player who should declare."""
        current_state = self._state_machine.get_current_state()
        if current_state and hasattr(current_state, 'phase_data'):
            phase_data = current_state.phase_data
            if 'current_declarer_index' in phase_data:
                players = self._game.get_player_names()
                index = phase_data['current_declarer_index']
                if 0 <= index < len(players):
                    return players[index]
        return None
    
    def get_remaining_declarers(self) -> List[str]:
        """Get list of players who haven't declared yet."""
        current_state = self._state_machine.get_current_state()
        if current_state and hasattr(current_state, 'phase_data'):
            phase_data = current_state.phase_data
            declarations = phase_data.get('declarations', {})
            return [
                p.name for p in self._game.players
                if p.name not in declarations
            ]
        return []
    
    def get_phase_data(self) -> Dict[str, Any]:
        """Get current phase data."""
        current_state = self._state_machine.get_current_state()
        if current_state and hasattr(current_state, 'phase_data'):
            return current_state.phase_data.copy()
        return {}
    
    async def cleanup(self) -> None:
        """Clean up state machine resources."""
        # Nothing to clean up for now
        pass


class StateMachineRepository:
    """
    Repository for managing state machine instances.
    
    This keeps track of active state machines by room ID.
    """
    
    def __init__(
        self,
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._state_machines: Dict[str, StateMachineAdapter] = {}
        self._event_publisher = event_publisher
        self._notification_service = notification_service
        self._lock = asyncio.Lock()
    
    async def create(
        self,
        game: Game,
        room_id: str
    ) -> StateMachineAdapter:
        """Create a new state machine for a game."""
        async with self._lock:
            adapter = StateMachineAdapter(
                game=game,
                room_id=room_id,
                event_publisher=self._event_publisher,
                notification_service=self._notification_service
            )
            
            self._state_machines[room_id] = adapter
            
            logger.info(f"Created state machine for room {room_id}")
            
            return adapter
    
    async def get(self, room_id: str) -> Optional[StateMachineAdapter]:
        """Get state machine for a room."""
        return self._state_machines.get(room_id)
    
    async def delete(self, room_id: str) -> bool:
        """Delete state machine for a room."""
        async with self._lock:
            if room_id in self._state_machines:
                adapter = self._state_machines[room_id]
                await adapter.cleanup()
                del self._state_machines[room_id]
                
                logger.info(f"Deleted state machine for room {room_id}")
                return True
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        return {
            "active_state_machines": len(self._state_machines),
            "rooms": list(self._state_machines.keys())
        }