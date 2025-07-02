# backend/engine/state_machine/base_state.py

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from .core import GamePhase, ActionType, GameAction

class GameState(ABC):
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.logger = logging.getLogger(f"game.state.{self.phase_name.value}")
        self.allowed_actions: Set[ActionType] = set()
        self.phase_data: Dict[str, Any] = {}
        
        # Enterprise Architecture: Automatic Broadcasting System
        self._auto_broadcast_enabled = True
        self._sequence_number = 0
        self._change_history = []
        
    @property
    @abstractmethod
    def phase_name(self) -> GamePhase:
        pass
    
    @property
    @abstractmethod
    def next_phases(self) -> List[GamePhase]:
        pass
    
    # Lifecycle methods
    async def on_enter(self) -> None:
        print(f"🔧 BASE_STATE_DEBUG: on_enter() called for {self.phase_name.value} phase")
        
        try:
            self.logger.info(f"Entering {self.phase_name.value} phase")
            print(f"🔧 BASE_STATE_DEBUG: Clearing phase_data")
            self.phase_data.clear()
            
            print(f"🔧 BASE_STATE_DEBUG: About to call _setup_phase() for {self.phase_name.value}")
            await self._setup_phase()
            print(f"🔧 BASE_STATE_DEBUG: _setup_phase() completed successfully for {self.phase_name.value}")
            
        except Exception as e:
            print(f"❌ BASE_STATE_DEBUG: Exception in on_enter() for {self.phase_name.value}: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    async def on_exit(self) -> None:
        self.logger.info(f"Exiting {self.phase_name.value} phase")
        await self._cleanup_phase()
        self.phase_data.clear()
    
    @abstractmethod
    async def _setup_phase(self) -> None:
        pass
    
    @abstractmethod
    async def _cleanup_phase(self) -> None:
        pass
    
    # Action handling
    async def handle_action(self, action: GameAction) -> Optional[Dict[str, Any]]:
        if action.action_type not in self.allowed_actions:
            self.logger.warning(f"Action {action.action_type.value} not allowed in {self.phase_name.value}")
            return None
            
        if not await self._validate_action(action):
            self.logger.warning(f"Invalid action: {action}")
            return None
            
        return await self._process_action(action)
    
    @abstractmethod
    async def _validate_action(self, action: GameAction) -> bool:
        pass
    
    @abstractmethod 
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Legacy polling-based transition check - TO BE REMOVED in Phase 3.2"""
        pass
    
    # ===== EVENT-DRIVEN ARCHITECTURE METHODS =====
    
    async def process_event(self, event) -> "EventResult":
        """
        Process event and return immediate result - REPLACES POLLING
        
        This method should be implemented by states converted to event-driven architecture.
        States not yet converted will fall back to legacy action processing.
        """
        # Import here to avoid circular imports
        from .events.event_types import EventResult
        
        # Default implementation: not yet converted to event-driven
        return EventResult(
            success=False,
            reason=f"State {self.__class__.__name__} not yet converted to event-driven processing"
        )
    
    def get_immediate_transition_conditions(self) -> Dict[str, callable]:
        """
        Return conditions that trigger immediate transitions - REPLACES POLLING
        
        Returns:
            Dict mapping event triggers to condition functions
        """
        return {}
    
    def get_valid_system_events(self) -> List[str]:
        """Return list of valid system events for this state"""
        return [
            "turn_complete",
            "round_complete", 
            "all_declared",
            "scores_calculated",
            "game_complete"
        ]
    
    def can_transition_to(self, target_phase: GamePhase) -> bool:
        return target_phase in self.next_phases
    
    # ===== ENTERPRISE ARCHITECTURE: AUTOMATIC BROADCASTING SYSTEM =====
    
    async def update_phase_data(self, updates: Dict[str, Any], reason: str = "", broadcast: bool = True) -> None:
        """
        🚀 ENTERPRISE: Centralized phase data updates with automatic broadcasting
        
        This implements the guaranteed automatic broadcasting system from BENEFITS_GUARANTEE.md
        All state changes go through this method to ensure consistency and automatic sync.
        
        Args:
            updates: Dictionary of phase data updates
            reason: Human-readable reason for the change (for debugging)
            broadcast: Whether to automatically broadcast (default True)
        """
        # 🔧 SOLUTION 2: Validate that we're still in the expected phase
        if self.state_machine.current_phase != self.phase_name:
            self.logger.warning(f"Phase mismatch: current={self.state_machine.current_phase}, expected={self.phase_name}")
            self.logger.warning(f"Skipping update to prevent conflicting broadcasts. Reason: {reason}")
            print(f"🔧 PHASE_MISMATCH_DEBUG: Blocked update - current phase {self.state_machine.current_phase} != {self.phase_name}")
            return  # Don't broadcast if phase has changed
        
        old_data = self.phase_data.copy()
        
        # Apply updates
        self.phase_data.update(updates)
        
        # Track change for debugging/event sourcing
        self._sequence_number += 1
        change_record = {
            'sequence': self._sequence_number,
            'timestamp': time.time(),
            'reason': reason or f"Phase data updated: {list(updates.keys())}",
            'old_data': old_data,
            'new_data': self.phase_data.copy(),
            'updates': updates.copy()
        }
        self._change_history.append(change_record)
        
        # Keep history manageable (last 50 changes)
        if len(self._change_history) > 50:
            self._change_history.pop(0)
        
        # Log the change
        self.logger.info(f"🎮 Phase Data Update: {reason}")
        self.logger.debug(f"   Updates: {updates}")
        
        # Automatic broadcasting (enterprise guarantee)
        if broadcast and self._auto_broadcast_enabled:
            await self._auto_broadcast_phase_change(reason)
    
    async def _auto_broadcast_phase_change(self, reason: str) -> None:
        """
        🚀 ENTERPRISE: Automatic phase change broadcasting
        
        This implements the automatic broadcasting guarantee from BENEFITS_GUARANTEE.md
        No manual broadcast calls needed - all phase data changes are automatically broadcast.
        """
        try:
            # Import here to avoid circular imports
            try:
                from backend.socket_manager import broadcast
            except ImportError:
                # Handle different import paths
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from socket_manager import broadcast
            
            room_id = getattr(self.state_machine, 'room_id', 'unknown')
            
            # Get player data if available (JSON-safe)
            players_data = {}
            if hasattr(self.state_machine, 'game') and self.state_machine.game:
                game = self.state_machine.game
                if hasattr(game, 'players') and game.players:
                    for player in game.players:
                        player_name = getattr(player, 'name', str(player))
                        player_hand = getattr(player, 'hand', [])
                        players_data[player_name] = {
                            'hand': [str(piece) for piece in player_hand],
                            'hand_size': len(player_hand)
                        }
            
            # Convert phase_data to JSON-safe format with recursive handling
            json_safe_phase_data = self._make_json_safe(self.phase_data)
            
            # Get current round number from game
            current_round = 1  # Default to round 1
            if hasattr(self.state_machine, 'game') and self.state_machine.game:
                current_round = getattr(self.state_machine.game, 'round_number', 1)
            
            # Broadcast complete phase change event
            broadcast_data = {
                "phase": self.phase_name.value,
                "allowed_actions": [action.value for action in self.allowed_actions],
                "phase_data": json_safe_phase_data,
                "players": players_data,
                "round": current_round,  # 🔢 ROUND_FIX: Add round number to broadcast data
                "reason": reason,
                "sequence": self._sequence_number,
                "timestamp": time.time()
            }
            
            await broadcast(room_id, "phase_change", broadcast_data)
            
            self.logger.info(f"📤 Auto-broadcast: phase_change to room {room_id} - {reason}")
            
            # 🚀 ENTERPRISE: Notify bot manager about phase data changes for automatic bot triggering
            if hasattr(self.state_machine, '_notify_bot_manager_data_change'):
                await self.state_machine._notify_bot_manager_data_change(json_safe_phase_data, reason)
            
        except Exception as e:
            self.logger.error(f"❌ Auto-broadcast failed: {e}", exc_info=True)
    
    def get_change_history(self) -> List[Dict[str, Any]]:
        """Get phase data change history for debugging"""
        return self._change_history.copy()
    
    def _make_json_safe(self, data: Any) -> Any:
        """
        🚀 ENTERPRISE: Recursively convert data to JSON-safe format
        
        Handles nested dictionaries, lists, Piece objects, and datetime objects that can't be JSON serialized.
        """
        from datetime import datetime
        
        if isinstance(data, dict):
            # Recursively handle dictionary values
            return {key: self._make_json_safe(value) for key, value in data.items()}
        elif isinstance(data, list):
            # Recursively handle list items
            return [self._make_json_safe(item) for item in data]
        elif isinstance(data, datetime):
            # Convert datetime objects to timestamps
            return data.timestamp()
        elif hasattr(data, '__dict__') and not isinstance(data, (str, int, float, bool, type(None))):
            # Convert objects with attributes (like Piece objects) to string
            return str(data)
        else:
            # Already JSON-safe (str, int, float, bool, None)
            return data
    
    def enable_auto_broadcast(self, enabled: bool = True) -> None:
        """Enable or disable automatic broadcasting"""
        self._auto_broadcast_enabled = enabled
        self.logger.info(f"🎮 Auto-broadcast {'enabled' if enabled else 'disabled'}")
    
    async def broadcast_custom_event(self, event_type: str, data: Dict[str, Any], reason: str = "") -> None:
        """
        🚀 ENTERPRISE: Broadcast custom events through the centralized system
        
        Use this instead of manual broadcast calls to maintain enterprise architecture.
        """
        try:
            try:
                from backend.socket_manager import broadcast
            except ImportError:
                # Handle different import paths
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from socket_manager import broadcast
            
            room_id = getattr(self.state_machine, 'room_id', 'unknown')
            
            # Add enterprise metadata and make JSON-safe
            self._sequence_number += 1
            enhanced_data = {
                **self._make_json_safe(data),
                "phase": self.phase_name.value,
                "sequence": self._sequence_number,
                "timestamp": time.time(),
                "reason": reason
            }
            
            # 🔧 DEADLOCK_FIX: Use fire-and-forget to prevent EventProcessor blocking
            import asyncio
            broadcast_task = asyncio.create_task(broadcast(room_id, event_type, enhanced_data))
            # Don't await - let broadcast run in background to prevent deadlock
            
            self.logger.info(f"📤 Custom broadcast: {event_type} to room {room_id} - {reason}")
            
        except Exception as e:
            self.logger.error(f"❌ Custom broadcast failed: {e}", exc_info=True)