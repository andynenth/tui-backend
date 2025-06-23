# backend/engine/state_machine/game_state_machine.py

import asyncio
import logging
from typing import Dict, Optional, List, Set
from datetime import datetime

from .core import GamePhase, ActionType, GameAction
from .action_queue import ActionQueue
from .base_state import GameState
from .states import PreparationState, DeclarationState, TurnState, ScoringState


logger = logging.getLogger(__name__)


class GameStateMachine:
    """
    Central coordinator for game state management.
    Manages phase transitions and delegates action handling to appropriate states.
    """
    
    def __init__(self, game):
        self.game = game
        self.action_queue = ActionQueue()
        self.current_state: Optional[GameState] = None
        self.current_phase: Optional[GamePhase] = None
        self.is_running = False
        self._process_task: Optional[asyncio.Task] = None
        
        # Initialize all available states
        self.states: Dict[GamePhase, GameState] = {
            GamePhase.PREPARATION: PreparationState(self),
            GamePhase.DECLARATION: DeclarationState(self),
            GamePhase.TURN: TurnState(self), 
            GamePhase.SCORING: ScoringState(self), 
        }
        
        # Transition validation map
        self._valid_transitions = {
            GamePhase.PREPARATION: {GamePhase.DECLARATION},
            GamePhase.DECLARATION: {GamePhase.TURN},
            GamePhase.TURN: {GamePhase.SCORING},
            GamePhase.SCORING: {GamePhase.PREPARATION}  # Next round
        }
    
    async def start(self, initial_phase: GamePhase = GamePhase.PREPARATION):
        """Start the state machine with initial phase"""
        if self.is_running:
            logger.warning("State machine already running")
            return
        
        logger.info(f"🚀 Starting state machine in {initial_phase} phase")
        self.is_running = True
        
        # Start processing loop
        self._process_task = asyncio.create_task(self._process_loop())
        
        # Enter initial phase
        await self._transition_to(initial_phase)
    
    async def stop(self):
        """Stop the state machine"""
        logger.info("🛑 Stopping state machine")
        self.is_running = False
        
        # Cancel processing task
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        # Exit current state
        if self.current_state:
            await self.current_state.on_exit()
    
    async def handle_action(self, action: GameAction) -> Dict:
        """
        Add action to queue for processing.
        Returns immediately with acknowledgment.
        """
        if not self.is_running:
            return {"success": False, "error": "State machine not running"}
        
        await self.action_queue.add_action(action)
        return {"success": True, "queued": True}
    
    async def _process_loop(self):
        """Main processing loop for queued actions"""
        while self.is_running:
            try:
                # Process any pending actions
                await self.process_pending_actions()
                
                # Check for phase transitions
                if self.current_state:
                    next_phase = await self.current_state.check_transition_conditions()
                    if next_phase:
                        await self._transition_to(next_phase)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in process loop: {e}", exc_info=True)
    
    async def process_pending_actions(self):
        """Process all actions in queue"""
        if not self.current_state:
            return
        
        actions = await self.action_queue.process_actions()
        for action in actions:
            try:
                await self.current_state.handle_action(action)
            except Exception as e:
                logger.error(f"Error processing action: {e}", exc_info=True)
    
    async def _transition_to(self, new_phase: GamePhase):
        """Transition to a new phase"""
        # Validate transition (skip validation for initial transition)
        if self.current_phase and new_phase not in self._valid_transitions.get(self.current_phase, set()):
            logger.error(f"❌ Invalid transition: {self.current_phase} -> {new_phase}")
            return
        
        # Get new state
        new_state = self.states.get(new_phase)
        if not new_state:
            logger.error(f"❌ No state handler for phase: {new_phase}")
            return
        
        logger.info(f"🔄 Transitioning: {self.current_phase} -> {new_phase}")
        
        # Exit current state
        if self.current_state:
            await self.current_state.on_exit()
        
        # Update phase and state
        self.current_phase = new_phase
        self.current_state = new_state
        
        # Enter new state
        await self.current_state.on_enter()
    
    def get_current_phase(self) -> Optional[GamePhase]:
        """Get current game phase"""
        return self.current_phase
    
    def get_allowed_actions(self) -> Set[ActionType]:
        """Get currently allowed action types"""
        if not self.current_state:
            return set()
        return self.current_state.allowed_actions
    
    def get_phase_data(self) -> Dict:
        """Get current phase-specific data"""
        if not self.current_state:
            return {}
        return self.current_state.phase_data.copy()