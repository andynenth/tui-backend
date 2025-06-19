# backend/engine/phase_manager.py

import asyncio
import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class GamePhase(Enum):
    """All game phases with their allowed actions"""
    WAITING = "waiting"
    REDEAL = "redeal"
    DECLARATION = "declaration"
    TURN = "turn"
    SCORING = "scoring"

@dataclass
class PhaseTransition:
    """Represents a valid phase transition"""
    from_phase: GamePhase
    to_phase: GamePhase
    condition: Optional[Callable] = None

@dataclass
class PhaseAction:
    """Represents an action that can be performed in a phase"""
    name: str
    phase: GamePhase
    validator: Optional[Callable] = None

class PhaseManager:
    """
    Comprehensive phase management system for all game phases
    Enforces phase boundaries and manages transitions
    """
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.current_phase = GamePhase.WAITING
        self.phase_start_time = time.time()
        self.transition_lock = asyncio.Lock()
        self.action_queue = {phase: [] for phase in GamePhase}
        self.phase_data = {}
        
        # Define valid transitions
        self.valid_transitions = [
            PhaseTransition(GamePhase.WAITING, GamePhase.REDEAL),
            PhaseTransition(GamePhase.REDEAL, GamePhase.DECLARATION),
            PhaseTransition(GamePhase.DECLARATION, GamePhase.TURN),
            PhaseTransition(GamePhase.TURN, GamePhase.SCORING),
            PhaseTransition(GamePhase.SCORING, GamePhase.REDEAL),  # Next round
            PhaseTransition(GamePhase.SCORING, GamePhase.WAITING),  # Game end
        ]
        
        # Define allowed actions per phase
        self.phase_actions = {
            GamePhase.WAITING: [
                PhaseAction("start_game", GamePhase.WAITING),
                PhaseAction("player_join", GamePhase.WAITING),
                PhaseAction("player_leave", GamePhase.WAITING),
            ],
            GamePhase.REDEAL: [
                PhaseAction("redeal_decision", GamePhase.REDEAL),
                PhaseAction("check_weak_hand", GamePhase.REDEAL),
            ],
            GamePhase.DECLARATION: [
                PhaseAction("declare", GamePhase.DECLARATION),
                PhaseAction("get_valid_options", GamePhase.DECLARATION),
            ],
            GamePhase.TURN: [
                PhaseAction("play_pieces", GamePhase.TURN),
                PhaseAction("get_turn_state", GamePhase.TURN),
            ],
            GamePhase.SCORING: [
                PhaseAction("calculate_scores", GamePhase.SCORING),
                PhaseAction("check_game_end", GamePhase.SCORING),
            ],
        }
        
        # Phase entry/exit handlers
        self.phase_handlers = {
            GamePhase.WAITING: {
                "enter": self._enter_waiting,
                "exit": self._exit_waiting,
            },
            GamePhase.REDEAL: {
                "enter": self._enter_redeal,
                "exit": self._exit_redeal,
            },
            GamePhase.DECLARATION: {
                "enter": self._enter_declaration,
                "exit": self._exit_declaration,
            },
            GamePhase.TURN: {
                "enter": self._enter_turn,
                "exit": self._exit_turn,
            },
            GamePhase.SCORING: {
                "enter": self._enter_scoring,
                "exit": self._exit_scoring,
            },
        }
        
        logger.info(f"PhaseManager initialized for room {room_id}")
    
    # ==================== PHASE TRANSITION MANAGEMENT ====================
    
    async def transition_to(self, new_phase: GamePhase, force: bool = False) -> bool:
        """
        Transition to a new phase with validation
        """
        async with self.transition_lock:
            # Validate transition
            if not force and not self._is_valid_transition(self.current_phase, new_phase):
                logger.warning(
                    f"Invalid transition: {self.current_phase.value} -> {new_phase.value}"
                )
                return False
            
            old_phase = self.current_phase
            
            try:
                # Exit current phase
                await self._exit_phase(old_phase)
                
                # Update phase
                self.current_phase = new_phase
                self.phase_start_time = time.time()
                
                # Enter new phase
                await self._enter_phase(new_phase)
                
                # Process queued actions for new phase
                await self._process_queued_actions(new_phase)
                
                logger.info(
                    f"Room {self.room_id}: Transitioned {old_phase.value} -> {new_phase.value}"
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Phase transition failed: {e}")
                # Rollback on error
                self.current_phase = old_phase
                return False
    
    def _is_valid_transition(self, from_phase: GamePhase, to_phase: GamePhase) -> bool:
        """Check if a phase transition is valid"""
        for transition in self.valid_transitions:
            if transition.from_phase == from_phase and transition.to_phase == to_phase:
                if transition.condition:
                    return transition.condition()
                return True
        return False
    
    async def _enter_phase(self, phase: GamePhase):
        """Execute phase entry logic"""
        handler = self.phase_handlers.get(phase, {}).get("enter")
        if handler:
            await handler()
    
    async def _exit_phase(self, phase: GamePhase):
        """Execute phase exit logic"""
        handler = self.phase_handlers.get(phase, {}).get("exit")
        if handler:
            await handler()
    
    # ==================== ACTION VALIDATION ====================
    
    def validate_action(self, action: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if an action can be performed in current phase
        """
        # Check if action is allowed in current phase
        allowed_actions = [a.name for a in self.phase_actions.get(self.current_phase, [])]
        
        if action not in allowed_actions:
            return {
                "valid": False,
                "error": f"Action '{action}' not allowed in phase '{self.current_phase.value}'",
                "current_phase": self.current_phase.value,
                "allowed_actions": allowed_actions,
            }
        
        # Get specific action validator if exists
        action_obj = next(
            (a for a in self.phase_actions[self.current_phase] if a.name == action),
            None
        )
        
        if action_obj and action_obj.validator:
            validation_result = action_obj.validator(player_data, self.phase_data)
            if not validation_result.get("valid", True):
                return validation_result
        
        return {"valid": True}
    
    def queue_action(self, action: str, data: Dict[str, Any], target_phase: GamePhase):
        """Queue an action for a specific phase"""
        self.action_queue[target_phase].append({
            "action": action,
            "data": data,
            "timestamp": time.time(),
        })
        logger.info(f"Queued action '{action}' for phase {target_phase.value}")
    
    async def _process_queued_actions(self, phase: GamePhase):
        """Process actions queued for a phase"""
        actions = self.action_queue.get(phase, [])
        
        for action_data in actions:
            # Skip old actions (older than 30 seconds)
            if time.time() - action_data["timestamp"] > 30:
                continue
            
            logger.info(f"Processing queued action: {action_data['action']}")
            # Process action through normal flow
            # This would call your game logic with the queued action
        
        # Clear processed actions
        self.action_queue[phase] = []
    
    # ==================== PHASE-SPECIFIC HANDLERS ====================
    
    async def _enter_waiting(self):
        """Enter waiting phase"""
        logger.info(f"Room {self.room_id}: Entered WAITING phase")
        self.phase_data = {"players_ready": set()}
    
    async def _exit_waiting(self):
        """Exit waiting phase"""
        pass
    
    async def _enter_redeal(self):
        """Enter redeal phase"""
        logger.info(f"Room {self.room_id}: Entered REDEAL phase")
        self.phase_data = {
            "pending_decisions": set(),
            "decisions_made": {},
            "redeal_complete": False,
        }
    
    async def _exit_redeal(self):
        """Exit redeal phase"""
        # Clear any pending redeal state
        self.phase_data = {}
    
    async def _enter_declaration(self):
        """Enter declaration phase"""
        logger.info(f"Room {self.room_id}: Entered DECLARATION phase")
        self.phase_data = {
            "declarations": {},
            "declaration_order": [],
            "all_declared": False,
        }
    
    async def _exit_declaration(self):
        """Exit declaration phase"""
        pass
    
    async def _enter_turn(self):
        """Enter turn phase"""
        logger.info(f"Room {self.room_id}: Entered TURN phase")
        self.phase_data = {
            "current_turn": 1,
            "turn_plays": {},
            "pile_counts": {},
        }
    
    async def _exit_turn(self):
        """Exit turn phase"""
        pass
    
    async def _enter_scoring(self):
        """Enter scoring phase"""
        logger.info(f"Room {self.room_id}: Entered SCORING phase")
        self.phase_data = {
            "round_scores": {},
            "scoring_complete": False,
        }
    
    async def _exit_scoring(self):
        """Exit scoring phase"""
        pass
    
    # ==================== PHASE STATE QUERIES ====================
    
    def get_phase_info(self) -> Dict[str, Any]:
        """Get current phase information"""
        return {
            "current_phase": self.current_phase.value,
            "phase_duration": time.time() - self.phase_start_time,
            "phase_data": self.phase_data.copy(),
            "allowed_actions": [a.name for a in self.phase_actions.get(self.current_phase, [])],
        }
    
    def is_action_allowed(self, action: str) -> bool:
        """Quick check if action is allowed in current phase"""
        allowed = [a.name for a in self.phase_actions.get(self.current_phase, [])]
        return action in allowed
    
    def get_phase_progress(self) -> Dict[str, Any]:
        """Get progress information for current phase"""
        progress = {
            "phase": self.current_phase.value,
            "duration": time.time() - self.phase_start_time,
        }
        
        # Add phase-specific progress
        if self.current_phase == GamePhase.DECLARATION:
            total_players = self.phase_data.get("total_players", 4)
            declared = len(self.phase_data.get("declarations", {}))
            progress["progress"] = f"{declared}/{total_players} declared"
            
        elif self.current_phase == GamePhase.TURN:
            progress["turn_number"] = self.phase_data.get("current_turn", 1)
            
        elif self.current_phase == GamePhase.REDEAL:
            pending = len(self.phase_data.get("pending_decisions", set()))
            progress["pending_decisions"] = pending
        
        return progress