# backend/engine/state_machine/phase_manager.py

import asyncio
import logging
import time
from typing import Dict, Optional, TYPE_CHECKING
from datetime import datetime

from .core import GamePhase

if TYPE_CHECKING:
    from .game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class PhaseManager:
    """
    🎯 **PhaseManager** - Extracted from GameStateMachine
    
    Handles all phase transitions and state management.
    Part of Phase 2.2 God Class Decomposition.
    
    Responsibilities:
    - Phase transition logic and validation
    - State coordination between phases
    - Transition cooldown and race condition prevention
    - Phase-specific validation and cleanup
    """
    
    def __init__(self, state_machine: 'GameStateMachine'):
        self.state_machine = state_machine
        self.transition_lock = asyncio.Lock()
        self._transition_depth = 0
        self._last_transition_time = 0
        self._transition_cooldown = 0.5  # 500ms minimum between transitions
        
    async def trigger_immediate_transition(self, event: str, target_state: GamePhase, reason: str) -> bool:
        """
        Triggers an immediate transition to a new phase if conditions are met.
        
        Args:
            event: The event triggering the transition
            target_state: The phase to transition to
            reason: Human-readable reason for the transition
            
        Returns:
            bool: True if transition was triggered, False otherwise
        """
        logger.info(f"🔄 TRANSITION_REQUEST: {event} requesting transition to {target_state.name} - {reason}")
        
        # Validate transition is allowed for this event
        if not self._validate_transition_for_event(target_state):
            logger.warning(f"❌ TRANSITION_BLOCKED: Transition to {target_state.name} not allowed for event {event}")
            return False
        
        # Check transition cooldown
        current_time = time.time()
        if current_time - self._last_transition_time < self._transition_cooldown:
            logger.warning(f"⏳ TRANSITION_COOLDOWN: Transition too soon, waiting...")
            return False
        
        # Perform the transition
        await self._immediate_transition_to(target_state, reason)
        return True
    
    def _validate_transition_for_event(self, target_state: GamePhase) -> bool:
        """Validates if a transition to target_state is allowed."""
        current_phase = self.state_machine.current_phase
        
        # Allow any transition if no current phase
        if not current_phase:
            return True
        
        # Define valid transition rules
        valid_transitions = {
            GamePhase.PREPARATION: [GamePhase.DECLARATION, GamePhase.SCORING],
            GamePhase.DECLARATION: [GamePhase.TURN, GamePhase.PREPARATION],
            GamePhase.TURN: [GamePhase.SCORING, GamePhase.PREPARATION],
            GamePhase.SCORING: [GamePhase.PREPARATION]
        }
        
        allowed_targets = valid_transitions.get(current_phase, [])
        return target_state in allowed_targets
    
    async def _immediate_transition_to(self, new_phase: GamePhase, reason: str):
        """
        Performs an immediate transition to a new phase.
        
        This bypasses normal state completion checks and forces a transition.
        Used for emergency transitions or phase corrections.
        """
        async with self.transition_lock:
            if self._transition_depth > 0:
                logger.warning(f"⚠️ NESTED_TRANSITION: Already transitioning (depth: {self._transition_depth})")
                return
            
            try:
                self._transition_depth += 1
                logger.info(f"🚀 IMMEDIATE_TRANSITION: {self.state_machine.current_phase} → {new_phase} ({reason})")
                
                await self._do_transition(new_phase, reason)
                
                # Update transition timing
                self._last_transition_time = time.time()
                
            finally:
                self._transition_depth -= 1
    
    async def _do_transition(self, new_phase: GamePhase, reason: str):
        """
        Core transition logic that coordinates all aspects of a phase change.
        """
        old_phase = self.state_machine.current_phase
        
        logger.info(f"🔄 PHASE_TRANSITION: Starting transition from {old_phase} to {new_phase}")
        logger.info(f"📝 TRANSITION_REASON: {reason}")
        
        try:
            # Step 1: Cleanup current state
            if self.state_machine.current_state:
                logger.debug("🧹 CLEANUP: Cleaning up current state")
                # Allow current state to perform cleanup
                if hasattr(self.state_machine.current_state, 'cleanup'):
                    await self.state_machine.current_state.cleanup()
            
            # Step 2: Update state machine references
            self.state_machine.current_phase = new_phase
            self.state_machine.current_state = self.state_machine.states[new_phase]
            
            logger.info(f"✅ PHASE_ACTIVE: Now in {new_phase.name} phase")
            
            # Step 3: Initialize new state
            if hasattr(self.state_machine.current_state, 'initialize'):
                logger.debug("🎯 INITIALIZE: Initializing new state")
                await self.state_machine.current_state.initialize()
            
            # Step 4: Phase-specific validations and setup
            await self._setup_new_phase(new_phase, old_phase)
            
            # Step 5: Broadcast phase change
            await self.state_machine.event_broadcaster.broadcast_phase_change_with_hands(new_phase)
            
            # Step 6: Store phase change event
            await self._store_phase_change_event(old_phase, new_phase)
            
            # Step 7: Notify bot manager
            await self._notify_bot_manager(new_phase)
            
            logger.info(f"🎉 TRANSITION_COMPLETE: Successfully transitioned to {new_phase.name}")
            
        except Exception as e:
            logger.error(f"❌ TRANSITION_ERROR: Failed to transition to {new_phase}: {str(e)}")
            # Try to recover by staying in current phase
            if old_phase and old_phase != new_phase:
                logger.warning(f"🔄 RECOVERY: Attempting to recover to {old_phase}")
                self.state_machine.current_phase = old_phase
                self.state_machine.current_state = self.state_machine.states[old_phase]
            raise
    
    async def _setup_new_phase(self, new_phase: GamePhase, old_phase: Optional[GamePhase]):
        """
        Performs phase-specific setup and validation.
        """
        # Special handling for each phase
        if new_phase == GamePhase.PREPARATION:
            await self._setup_preparation_phase()
        elif new_phase == GamePhase.DECLARATION:
            await self._setup_declaration_phase()
        elif new_phase == GamePhase.TURN:
            await self._setup_turn_phase()
        elif new_phase == GamePhase.SCORING:
            await self._setup_scoring_phase()
    
    async def _setup_preparation_phase(self):
        """Setup logic specific to preparation phase."""
        logger.debug("🎯 SETUP: Configuring preparation phase")
        
        # Verify all hands are empty before starting new round
        if self.state_machine.game and self.state_machine.game.round_number > 0:
            all_empty = await self._verify_all_hands_empty()
            if not all_empty:
                logger.warning("⚠️ PREPARATION_WARNING: Some players still have cards")
    
    async def _setup_declaration_phase(self):
        """Setup logic specific to declaration phase."""
        logger.debug("🎯 SETUP: Configuring declaration phase")
        # Declaration phase setup handled by state itself
        pass
    
    async def _setup_turn_phase(self):
        """Setup logic specific to turn phase."""
        logger.debug("🎯 SETUP: Configuring turn phase")
        # Turn phase setup handled by state itself
        pass
    
    async def _setup_scoring_phase(self):
        """Setup logic specific to scoring phase."""
        logger.debug("🎯 SETUP: Configuring scoring phase")
        # Scoring phase setup handled by state itself
        pass
    
    async def _verify_all_hands_empty(self) -> bool:
        """
        Verifies that all players have empty hands.
        Used during phase transitions to ensure game state consistency.
        """
        if not self.state_machine.game or not self.state_machine.game.players:
            return True
            
        for player in self.state_machine.game.players:
            if player and hasattr(player, 'hand') and player.hand:
                logger.warning(f"⚠️ HAND_CHECK: Player {player.name} still has {len(player.hand)} cards")
                return False
        
        logger.debug("✅ HAND_CHECK: All player hands are empty")
        return True
    
    async def _store_phase_change_event(self, old_phase: Optional[GamePhase], new_phase: GamePhase):
        """Store phase change event for debugging and analytics."""
        try:
            phase_change_data = {
                "old_phase": old_phase.name if old_phase else None,
                "new_phase": new_phase.name,
                "timestamp": datetime.now().isoformat(),
                "game_round": getattr(self.state_machine.game, 'round_number', 0),
                "players": [
                    {
                        "name": p.name,
                        "hand_size": len(p.hand) if hasattr(p, 'hand') and p.hand else 0,
                        "is_bot": getattr(p, 'is_bot', False)
                    }
                    for p in (self.state_machine.game.players if self.state_machine.game else [])
                    if p is not None
                ]
            }
            
            await self.state_machine.store_game_event("phase_change", phase_change_data)
            logger.debug(f"📊 EVENT_STORED: Phase change event recorded")
            
        except Exception as e:
            logger.error(f"❌ EVENT_STORAGE: Failed to store phase change event: {str(e)}")
    
    async def _notify_bot_manager(self, new_phase: GamePhase):
        """Notify bot manager of phase changes."""
        try:
            from ..bot_manager import BotManager
            bot_manager = BotManager()
            room_id = getattr(self.state_machine, 'room_id', None)
            
            if room_id:
                phase_data = self.state_machine.get_phase_data()
                await bot_manager.notify_phase_change(room_id, new_phase.name, phase_data)
                logger.debug(f"🤖 BOT_NOTIFICATION: Notified bot manager of phase change to {new_phase.name}")
            else:
                logger.warning(f"⚠️ BOT_NOTIFICATION: No room_id available for bot notification")
                
        except Exception as e:
            logger.error(f"❌ BOT_NOTIFICATION: Error notifying bot manager: {str(e)}")
    
    def get_current_phase(self) -> Optional[GamePhase]:
        """Get the current game phase."""
        return self.state_machine.current_phase
    
    def get_phase_data(self) -> Dict:
        """Get current phase data from active state."""
        if not self.state_machine.current_state:
            return {}
        
        try:
            # Try different method names for compatibility
            if hasattr(self.state_machine.current_state, 'get_state_data'):
                return self.state_machine.current_state.get_state_data()
            elif hasattr(self.state_machine.current_state, 'get_phase_data'):
                return self.state_machine.current_state.get_phase_data()
            else:
                # Fallback to basic state info
                return {
                    "phase": self.state_machine.current_phase.name if self.state_machine.current_phase else None,
                    "game_round": getattr(self.state_machine.game, 'round_number', 0) if self.state_machine.game else 0
                }
        except Exception as e:
            logger.error(f"❌ PHASE_DATA: Error getting phase data: {str(e)}")
            return {}