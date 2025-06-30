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
        self.logger.info(f"Entering {self.phase_name.value} phase")
        self.phase_data.clear()
        await self._setup_phase()
        
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
        pass
    
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
        
        # 🚀 ENTERPRISE: Automatic transition checking after state changes
        # This implements Option B - state changes automatically trigger condition checks
        await self._check_and_trigger_transitions(reason)
    
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
                    for i, player in enumerate(game.players):
                        player_name = getattr(player, 'name', str(player))
                        player_hand = getattr(player, 'hand', [])
                        # 🔧 FIX: Include all player properties needed by frontend
                        players_data[player_name] = {
                            'hand': [str(piece) for piece in player_hand],
                            'hand_size': len(player_hand),
                            'is_bot': getattr(player, 'is_bot', False),
                            'is_host': i == 0,  # First player is always host
                            'declared': getattr(player, 'declared', 0),
                            'captured_piles': getattr(player, 'captured_piles', 0),
                            'zero_declares_in_a_row': getattr(player, 'zero_declares_in_a_row', 0)
                        }
            
            # Convert phase_data to JSON-safe format with recursive handling
            json_safe_phase_data = self._make_json_safe(self.phase_data)
            
            # Get current round number from game
            current_round = 1  # Default to round 1
            if hasattr(self.state_machine, 'game') and self.state_machine.game:
                current_round = getattr(self.state_machine.game, 'round_number', 1)
            
            # 🚀 RACE_CONDITION_FIX: Use state machine's current phase, not this state's phase name
            current_machine_phase = getattr(self.state_machine, 'current_phase', self.phase_name)
            print(f"🔍 BROADCAST_DEBUG: State {self.phase_name.value} attempting broadcast - machine phase: {current_machine_phase.value if current_machine_phase else 'None'}")
            
            if current_machine_phase != self.phase_name:
                print(f"🚀 BROADCAST_FIX: State {self.phase_name.value} skipping broadcast - machine is in {current_machine_phase.value}")
                return
            
            # Broadcast complete phase change event
            broadcast_data = {
                "phase": current_machine_phase.value,
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
            
            await broadcast(room_id, event_type, enhanced_data)
            
            self.logger.info(f"📤 Custom broadcast: {event_type} to room {room_id} - {reason}")
            
        except Exception as e:
            self.logger.error(f"❌ Custom broadcast failed: {e}", exc_info=True)
    
    async def _check_and_trigger_transitions(self, reason: str) -> None:
        """
        🚀 ENTERPRISE: Automatic transition checking after state changes (Option B)
        
        This implements the fail-safe event-driven transition system where any state change
        automatically triggers a check for transition conditions. This ensures transitions
        happen reliably without developers having to remember to trigger them manually.
        
        Args:
            reason: The reason for the state change that triggered this check
        """
        try:
            # 🚀 TIMING SAFETY: Check if external systems are ready before auto-transitions
            if not await self._are_external_systems_ready():
                self.logger.info(f"⏳ Auto-transition delayed - external systems not ready yet")
                return
            
            # Check if this state should transition to another phase
            next_phase = await self.check_transition_conditions()
            
            if next_phase:
                transition_reason = f"Auto-transition triggered by: {reason}"
                self.logger.info(f"🔄 Auto-transition detected: {self.phase_name.value} → {next_phase.value}")
                self.logger.info(f"   Trigger: {reason}")
                
                # Trigger the transition through the state machine
                await self.state_machine.trigger_transition(next_phase, transition_reason)
                
        except Exception as e:
            self.logger.error(f"❌ Auto-transition check failed: {e}", exc_info=True)
            # Don't let transition failures break the main flow
            pass
    
    async def _are_external_systems_ready(self) -> bool:
        """
        🚀 TIMING SAFETY: Check if external systems are ready for auto-transitions
        
        This prevents race conditions where auto-transitions happen before
        external dependencies (like bot manager) are properly initialized.
        
        Returns:
            bool: True if all external systems are ready, False otherwise
        """
        try:
            # Check if bot manager is properly registered (most critical dependency)
            room_id = getattr(self.state_machine, 'room_id', None)
            if room_id:
                # Import bot manager to check registration
                try:
                    from engine.bot_manager import BotManager
                    bot_manager = BotManager()
                    
                    # Check if room is registered in bot manager
                    if room_id not in bot_manager.active_games:
                        self.logger.debug(f"🔍 Bot manager not ready: room {room_id} not registered")
                        return False
                        
                except Exception as e:
                    self.logger.debug(f"🔍 Bot manager check failed: {e}")
                    # If we can't check bot manager, proceed anyway (might be in test)
                    pass
            
            # Check if state machine is fully initialized
            if not hasattr(self.state_machine, 'is_running') or not self.state_machine.is_running:
                self.logger.debug(f"🔍 State machine not running yet")
                return False
            
            # Add more readiness checks here as needed
            
            return True
            
        except Exception as e:
            self.logger.debug(f"🔍 External systems readiness check failed: {e}")
            # Default to ready if we can't check (fail open for robustness)
            return True