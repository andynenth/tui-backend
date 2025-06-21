# backend/engine/state_machine/base_state.py

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from .core import GamePhase, ActionType, GameAction

class GameState(ABC):
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.logger = logging.getLogger(f"game.state.{self.phase_name.value}")
        self.allowed_actions: Set[ActionType] = set()
        self.phase_data: Dict[str, Any] = {}
        
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