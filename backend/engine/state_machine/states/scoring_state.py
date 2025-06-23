# backend/engine/state_machine/states/scoring_state.py

from typing import Dict, Any, Optional, List
from ..base_state import GameState
from ..core import GamePhase, ActionType, GameAction


class ScoringState(GameState):
    """
    Handles the Scoring Phase of the game.
    
    Responsibilities:
    - Calculate scores based on declared vs actual piles
    - Apply redeal multipliers
    - Check for game winner (≥50 points)
    - Transition to next round or end game
    """
    
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.SCORING
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.PREPARATION]  # Next round or game end
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.GAME_STATE_UPDATE,  # For viewing scores
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT
        }
        
        # Phase-specific state
        self.round_scores: Dict[str, Dict[str, Any]] = {}
        self.game_complete: bool = False
        self.winners: List[str] = []
        self.scores_calculated: bool = False
        
    async def _setup_phase(self) -> None:
        """Initialize scoring phase - calculate all scores"""
        try:
            self.logger.info("Setting up Scoring Phase")
            
            # Calculate scores for all players
            await self._calculate_round_scores()
            
            # Check for game winner
            await self._check_game_winner()
            
            self.scores_calculated = True
            self.logger.info(f"Scoring complete. Game over: {self.game_complete}")
            
        except Exception as e:
            self.logger.error(f"Error setting up Scoring Phase: {e}")
            raise
    
    async def _cleanup_phase(self) -> None:
        """Save scoring results to game object"""
        try:
            game = self.state_machine.game
            
            # Update game object with final state
            game.round_scores = self.round_scores.copy()
            
            if self.game_complete:
                game.game_over = True
                game.winners = self.winners.copy()
                self.logger.info(f"Game completed. Winners: {self.winners}")
            else:
                # Prepare for next round
                self._prepare_next_round()
                self.logger.info("Prepared for next round")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up Scoring Phase: {e}")
            raise
    
    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action for scoring phase"""
        # All allowed actions are valid in scoring phase
        if action.action_type == ActionType.GAME_STATE_UPDATE:
            return True
        elif action.action_type in {ActionType.PLAYER_DISCONNECT, ActionType.PLAYER_RECONNECT, ActionType.TIMEOUT}:
            return True
        
        # Action not supported in this phase
        return False
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid actions for scoring phase"""
        result = {"success": False, "message": "", "data": {}}
        
        try:
            if action.action_type == ActionType.GAME_STATE_UPDATE:
                result = await self._handle_view_scores(action)
            elif action.action_type == ActionType.PLAYER_DISCONNECT:
                result = await self._handle_player_disconnect(action)
            elif action.action_type == ActionType.PLAYER_RECONNECT:
                result = await self._handle_player_reconnect(action)
            elif action.action_type == ActionType.TIMEOUT:
                result = {"success": True, "message": "Timeout handled", "data": {}}
            else:
                result["message"] = f"Action {action.action_type} not supported in Scoring Phase"
                
        except Exception as e:
            self.logger.error(f"Error processing action {action.action_type}: {e}")
            result["message"] = f"Error processing action: {str(e)}"
        
        return result
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition to next phase"""
        if not self.scores_calculated:
            return None
        
        if self.game_complete:
            # Game is over, no transition
            return None
        
        # Can transition to next round (Preparation)
        return GamePhase.PREPARATION
    
    # Action Handlers
    
    async def _handle_view_scores(self, action: GameAction) -> Dict[str, Any]:
        """Handle request to view current scores"""
        game = self.state_machine.game
        return {
            "success": True,
            "message": "Score data retrieved",
            "data": {
                "round_scores": self.round_scores,
                "total_scores": {p.name: p.score for p in game.players} if hasattr(game, 'players') else {},
                "game_complete": self.game_complete,
                "winners": self.winners,
                "redeal_multiplier": getattr(game, 'redeal_multiplier', 1)
            }
        }
    
    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during scoring"""
        game = self.state_machine.game
        player_name = action.payload.get("player_name")
        if not player_name:
            return {"success": False, "message": "Player name required"}
        
        # Find player and mark as disconnected
        if hasattr(game, 'players'):
            for player in game.players:
                if player.name == player_name:
                    player.connected = False
                    self.logger.info(f"Player {player_name} disconnected during Scoring Phase")
                    break
        
        return {
            "success": True,
            "message": f"Player {player_name} disconnected",
            "data": {"disconnected_player": player_name}
        }
    
    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during scoring"""
        game = self.state_machine.game
        player_name = action.payload.get("player_name")
        if not player_name:
            return {"success": False, "message": "Player name required"}
        
        # Find player and mark as connected
        if hasattr(game, 'players'):
            for player in game.players:
                if player.name == player_name:
                    player.connected = True
                    self.logger.info(f"Player {player_name} reconnected during Scoring Phase")
                    break
        
        return {
            "success": True,
            "message": f"Player {player_name} reconnected",
            "data": {
                "reconnected_player": player_name,
                "round_scores": self.round_scores,
                "game_complete": self.game_complete
            }
        }
    
    # Core Scoring Logic
    
    async def _calculate_round_scores(self) -> None:
        """Calculate scores for all players this round"""
        game = self.state_machine.game
        self.round_scores = {}
        
        if not hasattr(game, 'players'):
            self.logger.warning("Game has no players attribute")
            return
        
        for player in game.players:
            declared = getattr(player, 'declared_piles', 0)
            actual = getattr(player, 'captured_piles', 0)
            
            # Calculate base score
            base_score = self._calculate_base_score(declared, actual)
            
            # Apply redeal multiplier
            multiplier = getattr(game, 'redeal_multiplier', 1)
            final_score = base_score * multiplier
            
            # Update player's total score
            current_score = getattr(player, 'score', 0)
            player.score = current_score + final_score
            
            # Store round score data
            self.round_scores[player.name] = {
                "declared": declared,
                "actual": actual,
                "base_score": base_score,
                "multiplier": multiplier,
                "final_score": final_score,
                "total_score": player.score
            }
            
            self.logger.info(f"Player {player.name}: declared {declared}, actual {actual}, "
                           f"base {base_score}, final {final_score} (×{multiplier}), "
                           f"total {player.score}")
    
    def _calculate_base_score(self, declared: int, actual: int) -> int:
        """
        Calculate base score before multiplier.
        
        Rules:
        - Declared 0, got 0: +3 bonus
        - Declared 0, got >0: -actual (penalty)
        - Declared X, got X: X + 5 bonus (perfect)
        - Declared X, got ≠X: -|difference| (missed target)
        """
        if declared == 0:
            if actual == 0:
                return 3  # Perfect zero declaration
            else:
                return -actual  # Broke zero declaration
        else:
            if actual == declared:
                return declared + 5  # Perfect prediction
            else:
                return -abs(declared - actual)  # Missed target penalty
    
    async def _check_game_winner(self) -> None:
        """Check if any player has won the game (≥50 points)"""
        game = self.state_machine.game
        WIN_THRESHOLD = 50
        
        if not hasattr(game, 'players'):
            return
        
        # Find players with winning scores
        winning_players = []
        max_score = -999
        
        for player in game.players:
            player_score = getattr(player, 'score', 0)
            if player_score >= WIN_THRESHOLD:
                if player_score > max_score:
                    max_score = player_score
                    winning_players = [player.name]
                elif player_score == max_score:
                    winning_players.append(player.name)
        
        if winning_players:
            self.game_complete = True
            self.winners = winning_players
            self.logger.info(f"Game completed! Winners: {winning_players} with {max_score} points")
        else:
            self.game_complete = False
            self.winners = []
    
    def _prepare_next_round(self) -> None:
        """Prepare game state for next round"""
        game = self.state_machine.game
        
        # Increment round number
        current_round = getattr(game, 'round_number', 1)
        game.round_number = current_round + 1
        
        # Reset round-specific data
        if hasattr(game, 'players'):
            for player in game.players:
                player.hand = []
                player.captured_piles = 0
                player.declared_piles = 0
        
        # Reset redeal multiplier for next round
        game.redeal_multiplier = 1
        
        # Clear turn-related data
        game.turn_results = []
        game.current_turn_starter = None
        
        self.logger.info(f"Prepared for round {game.round_number}")