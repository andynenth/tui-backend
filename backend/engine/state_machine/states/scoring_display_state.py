# backend/engine/state_machine/states/scoring_display_state.py

import asyncio
from typing import Dict, Any, Optional, List
from ..base_state import GameState
from ..core import GamePhase, ActionType, GameAction


class ScoringDisplayState(GameState):
    """
    Handles the Scoring Display Phase.
    
    Responsibilities:
    - Display score breakdown to players
    - Show round results and total scores
    - Auto-advance to next round or game end after timeout
    - Allow manual advance via user interaction
    """
    
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.SCORING_DISPLAY
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.PREPARATION, GamePhase.GAME_END]  # Next round or game end
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.CONTINUE_ROUND,      # Manual advance to next phase
            ActionType.VIEW_SCORES,         # View detailed scores
            ActionType.GAME_STATE_UPDATE,   # View current state
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT
        }
        
        # Phase-specific state
        self.round_scores: Dict[str, Dict[str, Any]] = {}
        self.total_scores: Dict[str, int] = {}
        self.game_complete: bool = False
        self.winners: List[str] = []
        self.auto_advance_complete: bool = False
        
    async def _setup_phase(self) -> None:
        """Initialize scoring display"""
        try:
            self.logger.info("Setting up Scoring Display Phase")
            
            # Get scoring data from game object
            game = self.state_machine.game
            self.round_scores = getattr(game, 'round_scores', {})
            self.game_complete = getattr(game, 'game_over', False)
            self.winners = getattr(game, 'winners', [])
            
            # Build total scores
            self.total_scores = {}
            if hasattr(game, 'players') and game.players:
                for player in game.players:
                    self.total_scores[player.name] = getattr(player, 'score', 0)
            
            # Prepare display data for frontend
            scoring_display_data = {
                'round_scores': self.round_scores,
                'total_scores': self.total_scores,
                'game_complete': self.game_complete,
                'winners': self.winners,
                'round_number': getattr(game, 'round_number', 1),
                'redeal_multiplier': getattr(game, 'redeal_multiplier', 1),
                'next_phase': 'game_end' if self.game_complete else 'preparation'
            }
            
            print(f"📊 SCORING_DISPLAY_DEBUG: Display data:")
            print(f"   🏆 Total scores: {self.total_scores}")
            print(f"   🏁 Game complete: {self.game_complete}")
            print(f"   👑 Winners: {self.winners}")
            print(f"   ➡️  Next phase: {'game_end' if self.game_complete else 'preparation'}")
            
            # Add player details for UI
            players_data = []
            if hasattr(game, 'players') and game.players:
                for player in game.players:
                    player_round_score = self.round_scores.get(player.name, {})
                    players_data.append({
                        'name': player.name,
                        'is_bot': player.name.startswith('Bot'),
                        'declared': player_round_score.get('declared', 0),
                        'actual': player_round_score.get('actual', 0),
                        'round_score': player_round_score.get('final_score', 0),
                        'total_score': getattr(player, 'score', 0)
                    })
            
            scoring_display_data['players'] = players_data
            
            # 🚀 ENTERPRISE: Use automatic broadcasting system
            await self.update_phase_data(scoring_display_data, 
                f"Scoring display ready - round {getattr(game, 'round_number', 1)} complete")
            
            # Start auto-advance timer (7 seconds for users to see scores)
            asyncio.create_task(self._start_auto_advance())
            
        except Exception as e:
            self.logger.error(f"Error setting up Scoring Display Phase: {e}")
            raise
    
    async def _cleanup_phase(self) -> None:
        """Clean up scoring display state"""
        try:
            # No cleanup needed - scoring data should persist
            self.logger.info("Scoring Display cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Scoring Display Phase: {e}")
    
    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action for scoring display phase"""
        if action.action_type in {ActionType.CONTINUE_ROUND, ActionType.VIEW_SCORES, 
                                ActionType.GAME_STATE_UPDATE, ActionType.PLAYER_DISCONNECT, 
                                ActionType.PLAYER_RECONNECT, ActionType.TIMEOUT}:
            return True
        
        return False
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid actions for scoring display phase"""
        result = {"success": False, "message": "", "data": {}}
        
        try:
            if action.action_type == ActionType.CONTINUE_ROUND:
                result = await self._handle_continue_round(action)
            elif action.action_type == ActionType.VIEW_SCORES:
                result = await self._handle_view_scores(action)
            elif action.action_type == ActionType.GAME_STATE_UPDATE:
                result = await self._handle_view_scores(action)  # Same as view scores
            elif action.action_type in {ActionType.PLAYER_DISCONNECT, ActionType.PLAYER_RECONNECT}:
                result = {"success": True, "message": f"{action.action_type} handled", "data": {}}
            elif action.action_type == ActionType.TIMEOUT:
                result = {"success": True, "message": "Timeout handled", "data": {}}
            else:
                result["message"] = f"Action {action.action_type} not supported in Scoring Display Phase"
                
        except Exception as e:
            self.logger.error(f"Error processing action {action.action_type}: {e}")
            result["message"] = f"Error processing action: {str(e)}"
        
        return result
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """🚀 ENTERPRISE: Event-driven transitions - determine next phase"""
        
        # Don't transition until auto-advance timer completes
        if not self.auto_advance_complete:
            return None
        
        # Transition based on whether game is complete
        if self.game_complete:
            return GamePhase.GAME_END
        else:
            return GamePhase.PREPARATION  # Next round
    
    # Action Handlers
    
    async def _handle_continue_round(self, action: GameAction) -> Dict[str, Any]:
        """Handle manual advance to next phase"""
        try:
            # Mark auto-advance as complete to allow transition
            self.auto_advance_complete = True
            
            # Trigger immediate transition check
            next_phase = await self.check_transition_conditions()
            if next_phase:
                await self.state_machine.trigger_transition(
                    next_phase, 
                    f"Manual advance by {action.player_name}"
                )
            
            return {
                "success": True,
                "message": "Advanced to next phase",
                "data": {"next_phase": next_phase.value if next_phase else None}
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error advancing: {str(e)}"}
    
    async def _handle_view_scores(self, action: GameAction) -> Dict[str, Any]:
        """Handle request to view detailed scores"""
        return {
            "success": True,
            "message": "Scores retrieved",
            "data": {
                "round_scores": self.round_scores,
                "total_scores": self.total_scores,
                "game_complete": self.game_complete,
                "winners": self.winners,
                "round_number": getattr(self.state_machine.game, 'round_number', 1)
            }
        }
    
    # Helper Methods
    
    async def _start_auto_advance(self) -> None:
        """🚀 ENTERPRISE: Auto-advance timer without race conditions"""
        try:
            print(f"⏰ SCORING_DISPLAY_AUTO: Starting 7-second auto-advance timer...")
            await asyncio.sleep(7.0)  # 7 second display time
            
            # 🚀 RACE_CONDITION_FIX: Check if we're still the active state
            if self.state_machine.current_phase != GamePhase.SCORING_DISPLAY:
                print(f"🚀 SCORING_DISPLAY_FIX: Not in scoring display phase anymore, skipping auto-advance")
                return
            
            self.auto_advance_complete = True
            print(f"⏰ SCORING_DISPLAY_AUTO: Auto-advance timer complete")
            self.logger.info("Scoring display auto-advance timer complete")
            
            # 🚀 ENTERPRISE: Event-driven transition
            next_phase = await self.check_transition_conditions()
            if next_phase:
                print(f"🎆 ENTERPRISE_TRANSITION: Auto-advancing to {next_phase.value}")
                await self.state_machine.trigger_transition(
                    next_phase,
                    "Scoring display auto-advance after 7 seconds"
                )
            
        except Exception as e:
            self.logger.error(f"Error in auto-advance timer: {e}")