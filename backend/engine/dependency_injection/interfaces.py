# backend/engine/dependency_injection/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, Set, Optional, Any, List
from enum import Enum


class IStateMachine(ABC):
    """
    🎯 **State Machine Interface** - Breaks GameStateMachine circular dependencies
    
    Abstract interface for state machine functionality that components can depend on
    without importing the concrete GameStateMachine class.
    """
    
    @abstractmethod
    def get_current_phase(self) -> Optional[str]:
        """Get the current game phase."""
        pass
    
    @abstractmethod
    def get_phase_data(self) -> Dict[str, Any]:
        """Get current phase data."""
        pass
    
    @abstractmethod
    def get_allowed_actions(self) -> Set[str]:
        """Get actions allowed in current state."""
        pass
    
    @abstractmethod
    async def validate_action(self, action: Any) -> Dict[str, Any]:
        """Validate if an action can be executed."""
        pass
    
    @abstractmethod
    async def handle_action(self, action: Any) -> Dict[str, Any]:
        """Handle a game action."""
        pass
    
    @abstractmethod
    async def store_game_event(self, event_type: str, payload: dict, player_id: Optional[str] = None):
        """Store game event for debugging and analytics."""
        pass


class IBroadcaster(ABC):
    """
    🎯 **Broadcaster Interface** - Eliminates socket_manager circular dependencies
    
    Abstract interface for broadcasting events without direct coupling to WebSocket infrastructure.
    """
    
    @abstractmethod
    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        pass
    
    @abstractmethod
    async def broadcast_to_room(self, room_id: str, event_type: str, event_data: Dict[str, Any]):
        """Broadcast event to specific room."""
        pass
    
    @abstractmethod
    async def broadcast_to_player(self, room_id: str, player_name: str, event_type: str, event_data: Dict[str, Any]):
        """Broadcast event to specific player."""
        pass
    
    @abstractmethod
    async def broadcast_phase_change(self, room_id: str, phase: str, phase_data: Dict[str, Any]):
        """Broadcast phase change with proper formatting."""
        pass


class IActionHandler(ABC):
    """
    🎯 **Action Handler Interface** - Breaks action processing circular dependencies
    
    Interface for handling game actions without coupling to specific implementation.
    """
    
    @abstractmethod
    async def validate_action(self, action: Any) -> Dict[str, Any]:
        """Validate action against current game state."""
        pass
    
    @abstractmethod
    async def execute_action(self, action: Any) -> Dict[str, Any]:
        """Execute a validated action."""
        pass
    
    @abstractmethod
    async def handle_action(self, action: Any) -> Dict[str, Any]:
        """Complete action handling pipeline."""
        pass


class IPhaseTransitioner(ABC):
    """
    🎯 **Phase Transition Interface** - Breaks phase management circular dependencies
    
    Interface for phase transitions without coupling to PhaseManager implementation.
    """
    
    @abstractmethod
    async def trigger_transition(self, event: str, target_phase: str, reason: str) -> bool:
        """Trigger immediate phase transition."""
        pass
    
    @abstractmethod
    def can_transition_to(self, target_phase: str) -> bool:
        """Check if transition to target phase is valid."""
        pass
    
    @abstractmethod
    def get_current_phase(self) -> Optional[str]:
        """Get current phase."""
        pass


class IBotNotifier(ABC):
    """
    🎯 **Bot Notifier Interface** - Eliminates bot_manager circular dependencies
    
    Interface for bot notifications without direct coupling to BotManager.
    """
    
    @abstractmethod
    async def notify_phase_change(self, room_id: str, phase: str, phase_data: Dict[str, Any]):
        """Notify bots of phase change."""
        pass
    
    @abstractmethod
    async def notify_action_result(self, room_id: str, action_type: str, player_name: str, 
                                 success: bool, result: Optional[Dict[str, Any]] = None, 
                                 reason: Optional[str] = None):
        """Notify bots of action results."""
        pass
    
    @abstractmethod
    async def notify_data_change(self, room_id: str, data: Dict[str, Any], reason: str):
        """Notify bots of game data changes."""
        pass


class IEventStore(ABC):
    """
    🎯 **Event Store Interface** - Breaks event storage circular dependencies
    
    Interface for storing game events without coupling to specific storage implementation.
    """
    
    @abstractmethod
    async def store_event(self, room_id: str, event_data: Dict[str, Any]):
        """Store game event."""
        pass
    
    @abstractmethod
    async def get_events(self, room_id: str, event_type: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve game events."""
        pass
    
    @abstractmethod
    async def clear_events(self, room_id: str):
        """Clear events for a room."""
        pass


class IGameRepository(ABC):
    """
    🎯 **Game Repository Interface** - Breaks game data access circular dependencies
    
    Interface for game data access without coupling to specific storage.
    """
    
    @abstractmethod
    async def save_game_state(self, room_id: str, game_state: Dict[str, Any]):
        """Save game state."""
        pass
    
    @abstractmethod
    async def load_game_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Load game state."""
        pass
    
    @abstractmethod
    async def delete_game_state(self, room_id: str):
        """Delete game state."""
        pass


class IRoomService(ABC):
    """
    🎯 **Room Service Interface** - Breaks room management circular dependencies
    
    Interface for room management without coupling to specific implementation.
    """
    
    @abstractmethod
    async def create_room(self, room_id: str, host_name: str) -> Dict[str, Any]:
        """Create a new game room."""
        pass
    
    @abstractmethod
    async def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room information."""
        pass
    
    @abstractmethod
    async def join_room(self, room_id: str, player_name: str) -> Dict[str, Any]:
        """Join a player to a room."""
        pass
    
    @abstractmethod
    async def leave_room(self, room_id: str, player_name: str) -> Dict[str, Any]:
        """Remove a player from a room."""
        pass
    
    @abstractmethod
    async def start_game(self, room_id: str) -> Dict[str, Any]:
        """Start the game in a room."""
        pass


# Service identifier enums for type-safe service resolution
class ServiceType(Enum):
    """Service type identifiers for dependency injection."""
    STATE_MACHINE = "state_machine"
    BROADCASTER = "broadcaster" 
    ACTION_HANDLER = "action_handler"
    PHASE_TRANSITIONER = "phase_transitioner"
    BOT_NOTIFIER = "bot_notifier"
    EVENT_STORE = "event_store"
    GAME_REPOSITORY = "game_repository"
    ROOM_SERVICE = "room_service"