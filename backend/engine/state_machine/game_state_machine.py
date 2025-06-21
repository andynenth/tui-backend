# backend/engin/state_machine/game_state_machine.py

import asyncio
import logging
from typing import Optional, Dict, Any, Set, List
from .core import GamePhase, ActionType, GameAction
from .action_queue import ActionQueue
from .states.declaration_state import DeclarationState

class GameStateMachine:
    def __init__(self, game):
        self.game = game
        self.current_state = None
        self.action_queue = ActionQueue()
        self.transition_lock = asyncio.Lock()
        self.logger = logging.getLogger("game.state_machine")
        self._processing_task = None
        
        # Initialize states (start with just declaration for testing)
        self.states = {
            GamePhase.DECLARATION: DeclarationState(self)
        }
        
    async def start(self, initial_phase: GamePhase = GamePhase.DECLARATION) -> None:
        await self.transition_to(initial_phase)
        # Start background task for processing actions
        self._processing_task = asyncio.create_task(self._process_action_queue())
    
    async def stop(self) -> None:
        """Stop the state machine and clean up"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
    
    async def handle_action(self, action: GameAction) -> None:
        await self.action_queue.add_action(action)
        # Give the processing loop a chance to run
        await asyncio.sleep(0.01)
    
    async def process_pending_actions(self) -> None:
        """
        FIX: Synchronously process all pending actions.
        Useful for testing to ensure all actions are processed.
        """
        actions = await self.action_queue.process_actions()
        for action in actions:
            try:
                result = await self._handle_single_action(action)
                if result:
                    await self._broadcast_action_result(action, result)
                
                await self._check_auto_transition()
                
            except Exception as e:
                self.logger.error(f"Error processing action {action}: {e}")
    
    async def _process_action_queue(self) -> None:
        """Background task for processing actions"""
        while True:
            try:
                if self.action_queue.has_pending_actions():
                    await self.process_pending_actions()
                
                # Wait a bit before checking again
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in action processing loop: {e}")
    
    async def _handle_single_action(self, action: GameAction) -> Optional[Dict[str, Any]]:
        if self.current_state is None:
            self.logger.error("No current state to handle action")
            return None
        
        return await self.current_state.handle_action(action)
    
    async def transition_to(self, target_phase: GamePhase) -> bool:
        async with self.transition_lock:
            if self.current_state and not self.current_state.can_transition_to(target_phase):
                self.logger.warning(f"Invalid transition to {target_phase.value}")
                return False
            
            try:
                if self.current_state:
                    await self.current_state.on_exit()
                
                new_state = self.states[target_phase]
                await new_state.on_enter()
                self.current_state = new_state
                
                self.logger.info(f"Transitioned to {target_phase.value} phase")
                await self._broadcast_phase_change(target_phase)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error during transition to {target_phase.value}: {e}")
                return False
    
    async def _check_auto_transition(self) -> None:
        if self.current_state:
            next_phase = await self.current_state.check_transition_conditions()
            if next_phase and next_phase in self.states:
                await self.transition_to(next_phase)
    
    async def _broadcast_action_result(self, action: GameAction, result: Dict[str, Any]) -> None:
        # Placeholder - implement based on your WebSocket system
        self.logger.info(f"Broadcasting result: {result}")
    
    async def _broadcast_phase_change(self, new_phase: GamePhase) -> None:
        # Placeholder - implement based on your WebSocket system  
        self.logger.info(f"Broadcasting phase change: {new_phase.value}")
    
    def get_current_phase(self) -> Optional[GamePhase]:
        return self.current_state.phase_name if self.current_state else None
    
    def get_allowed_actions(self) -> Set[ActionType]:
        return self.current_state.allowed_actions if self.current_state else set()