"""
Enhanced Transition Validation for Foundation-First Development

Provides comprehensive validation of state transitions to ensure game integrity
and prevent invalid state changes that could break the game flow.
"""

import logging
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

from .core import GamePhase

logger = logging.getLogger(__name__)

@dataclass
class TransitionRule:
    """Rule for validating a specific transition"""
    from_phase: GamePhase
    to_phase: GamePhase
    conditions: List[str]  # List of condition names that must be met
    description: str

class TransitionValidationResult:
    """Result of transition validation"""
    
    def __init__(self, valid: bool, reason: str = "", failed_conditions: List[str] = None):
        self.valid = valid
        self.reason = reason
        self.failed_conditions = failed_conditions or []
        self.timestamp = time.time()

class TransitionValidator:
    """Enhanced transition validator with comprehensive game state checks"""
    
    def __init__(self):
        self.validation_history: List[Dict[str, Any]] = []
        self.setup_validation_rules()
    
    def setup_validation_rules(self):
        """Setup validation rules for each transition"""
        self.rules = [
            # PREPARATION -> DECLARATION
            TransitionRule(
                from_phase=GamePhase.PREPARATION,
                to_phase=GamePhase.DECLARATION,
                conditions=["cards_dealt", "no_weak_hands_or_resolved", "starter_determined"],
                description="All players have cards, weak hands resolved, starter chosen"
            ),
            
            # DECLARATION -> TURN
            TransitionRule(
                from_phase=GamePhase.DECLARATION, 
                to_phase=GamePhase.TURN,
                conditions=["all_players_declared", "valid_declaration_totals"],
                description="All players have made valid declarations"
            ),
            
            # TURN -> SCORING
            TransitionRule(
                from_phase=GamePhase.TURN,
                to_phase=GamePhase.SCORING,
                conditions=["all_hands_empty", "all_turns_complete"],
                description="All players have played all their pieces"
            ),
            
            # SCORING -> PREPARATION (next round)
            TransitionRule(
                from_phase=GamePhase.SCORING,
                to_phase=GamePhase.PREPARATION, 
                conditions=["scores_calculated", "game_not_over"],
                description="Round scored and game continues"
            ),
        ]
        
        # Build lookup map for fast access
        self.rule_map = {}
        for rule in self.rules:
            key = (rule.from_phase, rule.to_phase)
            self.rule_map[key] = rule
    
    async def validate_transition(self, from_phase: Optional[GamePhase], to_phase: GamePhase, 
                                game_state) -> TransitionValidationResult:
        """
        Validate a state transition with comprehensive checks
        
        Args:
            from_phase: Current phase (None for initial transition)
            to_phase: Target phase
            game_state: Current game state for validation
            
        Returns:
            TransitionValidationResult with validation outcome
        """
        logger.info(f"🔍 Validating transition: {from_phase} -> {to_phase}")
        
        # Allow initial transition to any phase
        if from_phase is None:
            result = TransitionValidationResult(True, "Initial transition allowed")
            self._record_validation(from_phase, to_phase, result)
            return result
        
        # Check if transition rule exists
        rule_key = (from_phase, to_phase)
        if rule_key not in self.rule_map:
            result = TransitionValidationResult(
                False, 
                f"No transition rule defined for {from_phase} -> {to_phase}"
            )
            self._record_validation(from_phase, to_phase, result)
            return result
        
        rule = self.rule_map[rule_key]
        
        # Validate all conditions for this transition
        failed_conditions = []
        for condition in rule.conditions:
            if not await self._check_condition(condition, game_state):
                failed_conditions.append(condition)
        
        if failed_conditions:
            result = TransitionValidationResult(
                False,
                f"Transition blocked: {', '.join(failed_conditions)} not met",
                failed_conditions
            )
        else:
            result = TransitionValidationResult(
                True,
                f"All conditions met: {rule.description}"
            )
        
        self._record_validation(from_phase, to_phase, result)
        return result
    
    async def _check_condition(self, condition: str, game_state) -> bool:
        """Check a specific condition against game state"""
        try:
            if condition == "cards_dealt":
                return await self._check_cards_dealt(game_state)
            elif condition == "no_weak_hands_or_resolved":
                return await self._check_weak_hands_resolved(game_state)
            elif condition == "starter_determined":
                return await self._check_starter_determined(game_state)
            elif condition == "all_players_declared":
                return await self._check_all_players_declared(game_state)
            elif condition == "valid_declaration_totals":
                return await self._check_valid_declaration_totals(game_state)
            elif condition == "all_hands_empty":
                return await self._check_all_hands_empty(game_state)
            elif condition == "all_turns_complete":
                return await self._check_all_turns_complete(game_state)
            elif condition == "scores_calculated":
                return await self._check_scores_calculated(game_state)
            elif condition == "game_not_over":
                return await self._check_game_not_over(game_state)
            else:
                logger.warning(f"Unknown condition: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking condition {condition}: {e}")
            return False
    
    async def _check_cards_dealt(self, game_state) -> bool:
        """Check that all players have been dealt cards"""
        game = getattr(game_state, 'game', None)
        if not game or not hasattr(game, 'players'):
            return False
            
        for player in game.players:
            if not hasattr(player, 'hand') or len(player.hand) != 8:
                logger.debug(f"Player {getattr(player, 'name', player)} doesn't have 8 cards")
                return False
        
        logger.debug("✅ All players have 8 cards")
        return True
    
    async def _check_weak_hands_resolved(self, game_state) -> bool:
        """Check that weak hands have been resolved"""
        # If we're in preparation state, check for weak hands
        if hasattr(game_state, 'current_state') and game_state.current_state:
            phase_data = getattr(game_state.current_state, 'phase_data', {})
            weak_players = phase_data.get('weak_players', set())
            redeal_in_progress = phase_data.get('redeal_in_progress', False)
            
            if weak_players and redeal_in_progress:
                logger.debug(f"Redeal in progress for weak players: {weak_players}")
                return False
        
        logger.debug("✅ No weak hands or resolved")
        return True
    
    async def _check_starter_determined(self, game_state) -> bool:
        """Check that round starter has been determined"""
        game = getattr(game_state, 'game', None)
        if not game:
            return False
            
        starter = getattr(game, 'round_starter', None) or getattr(game, 'current_player', None)
        if not starter:
            logger.debug("No round starter determined")
            return False
        
        logger.debug(f"✅ Round starter: {starter}")
        return True
    
    async def _check_all_players_declared(self, game_state) -> bool:
        """Check that all players have made declarations"""
        if not hasattr(game_state, 'current_state') or not game_state.current_state:
            return False
            
        phase_data = getattr(game_state.current_state, 'phase_data', {})
        declarations = phase_data.get('declarations', {})
        
        game = getattr(game_state, 'game', None)
        if not game or not hasattr(game, 'players'):
            return False
        
        for player in game.players:
            player_name = getattr(player, 'name', str(player))
            if player_name not in declarations:
                logger.debug(f"Player {player_name} has not declared")
                return False
        
        logger.debug("✅ All players have declared")
        return True
    
    async def _check_valid_declaration_totals(self, game_state) -> bool:
        """Check that declaration totals are valid (sum ≠ 8)"""
        if not hasattr(game_state, 'current_state') or not game_state.current_state:
            return False
            
        phase_data = getattr(game_state.current_state, 'phase_data', {})
        declarations = phase_data.get('declarations', {})
        
        if not declarations:
            return False
        
        total = sum(declarations.values())
        if total == 8:
            logger.debug(f"Invalid declaration total: {total} (cannot equal 8)")
            return False
        
        logger.debug(f"✅ Valid declaration total: {total}")
        return True
    
    async def _check_all_hands_empty(self, game_state) -> bool:
        """Check that all players have empty hands"""
        game = getattr(game_state, 'game', None)
        if not game or not hasattr(game, 'players'):
            return False
            
        for player in game.players:
            if hasattr(player, 'hand') and len(player.hand) > 0:
                logger.debug(f"Player {getattr(player, 'name', player)} still has {len(player.hand)} cards")
                return False
        
        logger.debug("✅ All hands are empty")
        return True
    
    async def _check_all_turns_complete(self, game_state) -> bool:
        """Check that all turns in the round are complete"""
        if not hasattr(game_state, 'current_state') or not game_state.current_state:
            return False
            
        phase_data = getattr(game_state.current_state, 'phase_data', {})
        
        # Check if we have 8 completed turns (8 pieces per player, 4 players = 8 turns total)
        turn_number = phase_data.get('current_turn_number', 0)
        
        # All turns complete when we've had 8 turns
        if turn_number >= 8:
            logger.debug(f"✅ All {turn_number} turns complete")
            return True
        
        logger.debug(f"Only {turn_number} turns complete, need 8")
        return False
    
    async def _check_scores_calculated(self, game_state) -> bool:
        """Check that scores have been calculated for the round"""
        if not hasattr(game_state, 'current_state') or not game_state.current_state:
            return False
            
        phase_data = getattr(game_state.current_state, 'phase_data', {})
        scores_calculated = phase_data.get('scores_calculated', False)
        
        if scores_calculated:
            logger.debug("✅ Scores calculated")
            return True
        
        logger.debug("Scores not yet calculated")
        return False
    
    async def _check_game_not_over(self, game_state) -> bool:
        """Check that game is not over (no winner yet)"""
        game = getattr(game_state, 'game', None)
        if not game:
            return True  # Assume game continues if we can't check
        
        # Check for win conditions
        if hasattr(game, 'winner') and game.winner:
            logger.debug(f"Game over: winner is {game.winner}")
            return False
        
        # Check round limit
        round_number = getattr(game, 'round_number', 1)
        if round_number >= 20:  # Max rounds
            logger.debug(f"Game over: reached max rounds ({round_number})")
            return False
        
        logger.debug("✅ Game continues")
        return True
    
    def _record_validation(self, from_phase: Optional[GamePhase], to_phase: GamePhase, 
                          result: TransitionValidationResult):
        """Record validation result for debugging"""
        record = {
            'timestamp': result.timestamp,
            'from_phase': from_phase.value if from_phase else None,
            'to_phase': to_phase.value,
            'valid': result.valid,
            'reason': result.reason,
            'failed_conditions': result.failed_conditions
        }
        
        self.validation_history.append(record)
        
        # Keep only last 100 validations
        if len(self.validation_history) > 100:
            self.validation_history.pop(0)
        
        if result.valid:
            logger.info(f"✅ Transition validation passed: {result.reason}")
        else:
            logger.warning(f"❌ Transition validation failed: {result.reason}")
    
    def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent validation history"""
        return self.validation_history[-limit:]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        if not self.validation_history:
            return {
                'total_validations': 0,
                'success_rate': 0.0,
                'most_common_failures': []
            }
        
        total = len(self.validation_history)
        successful = sum(1 for record in self.validation_history if record['valid'])
        
        # Count failure reasons
        failure_counts = {}
        for record in self.validation_history:
            if not record['valid']:
                reason = record['reason']
                failure_counts[reason] = failure_counts.get(reason, 0) + 1
        
        most_common_failures = sorted(
            failure_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            'total_validations': total,
            'successful_validations': successful,
            'failed_validations': total - successful,
            'success_rate': successful / total,
            'most_common_failures': most_common_failures
        }