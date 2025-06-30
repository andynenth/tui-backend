# backend/engine/state_machine/states/turn_results_state.py

import asyncio
from typing import Dict, Any, Optional, List
from ..base_state import GameState
from ..core import GamePhase, ActionType, GameAction


class TurnResultsState(GameState):
    """
    Handles the Turn Results Display Phase.
    
    Responsibilities:
    - Display turn winner and pieces won
    - Show turn breakdown for players to review
    - Auto-advance to next turn or scoring after timeout
    - Allow manual advance via user interaction
    """
    
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.TURN_RESULTS
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.TURN, GamePhase.SCORING]  # Next turn or scoring
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.CONTINUE_ROUND,      # Manual advance to next phase
            ActionType.GAME_STATE_UPDATE,   # View current state
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT
        }
        
        # Phase-specific state
        self.turn_winner: Optional[str] = None
        self.pieces_won: List[str] = []
        self.turn_plays: Dict[str, Any] = {}
        self.auto_advance_complete: bool = False
        self.hands_empty: bool = False
        self._auto_advance_task: Optional[asyncio.Task] = None
        
    async def _setup_phase(self) -> None:
        """Initialize turn results display"""
        try:
            self.logger.info("Setting up Turn Results Display Phase")
            
            # Get turn result data from game object
            game = self.state_machine.game
            self.turn_winner = getattr(game, 'last_turn_winner', None)
            self.pieces_won = getattr(game, 'last_turn_pieces', [])
            self.turn_plays = getattr(game, 'last_turn_plays', {})
            
            # Check if all hands are empty (determines next transition)
            self.hands_empty = self._check_hands_empty()
            
            # Prepare display data for frontend (ensure JSON serializable)
            json_safe_turn_plays = {}
            for player, play_data in self.turn_plays.items():
                if isinstance(play_data, dict):
                    safe_play_data = {}
                    for key, value in play_data.items():
                        if key == 'pieces' and isinstance(value, list):
                            # Convert Piece objects to strings
                            safe_play_data[key] = [str(piece) for piece in value]
                        else:
                            safe_play_data[key] = value
                    json_safe_turn_plays[player] = safe_play_data
                else:
                    json_safe_turn_plays[player] = str(play_data)
            
            turn_result_data = {
                'winner': self.turn_winner,
                'pieces_won': [str(piece) for piece in self.pieces_won],
                'turn_plays': json_safe_turn_plays,
                'hands_empty': self.hands_empty,
                'next_phase': 'scoring' if self.hands_empty else 'turn',
                'turn_number': getattr(game, 'turn_number', 0)
            }
            
            print(f"🎭 TURN_RESULTS_DEBUG: Display data:")
            print(f"   🏆 Winner: {self.turn_winner}")
            print(f"   🎯 Pieces won: {len(self.pieces_won)}")
            print(f"   👐 Hands empty: {self.hands_empty}")
            print(f"   ➡️  Next phase: {'scoring' if self.hands_empty else 'turn'}")
            
            # 🚀 ENTERPRISE: Use automatic broadcasting system
            await self.update_phase_data(turn_result_data, 
                f"Turn results ready - winner: {self.turn_winner}")
            
            # 🚀 IMMEDIATE TRANSITION: Skip delay and transition immediately
            print(f"🚀 TURN_RESULTS_IMMEDIATE: Skipping delay - transitioning immediately")
            self.auto_advance_complete = True
            
            # 🚀 ENTERPRISE: Immediate transition to next phase
            next_phase = await self.check_transition_conditions()
            if next_phase:
                print(f"🎆 IMMEDIATE_TRANSITION: Transitioning to {next_phase.value}")
                await self.state_machine.trigger_transition(
                    next_phase,
                    "Turn results immediate transition - no delay"
                )
            else:
                print(f"🚫 IMMEDIATE_TRANSITION: No next phase determined")
            
        except Exception as e:
            self.logger.error(f"Error setting up Turn Results Phase: {e}")
            raise
    
    async def _cleanup_phase(self) -> None:
        """Clean up turn results state"""
        try:
            # Cancel auto-advance task if still running
            if self._auto_advance_task and not self._auto_advance_task.done():
                print(f"🚀 TURN_RESULTS_CLEANUP: Cancelling auto-advance task")
                self._auto_advance_task.cancel()
                try:
                    await self._auto_advance_task
                except asyncio.CancelledError:
                    pass
                    
            # Clear turn result data from game object
            game = self.state_machine.game
            if hasattr(game, 'last_turn_winner'):
                delattr(game, 'last_turn_winner')
            if hasattr(game, 'last_turn_pieces'):
                delattr(game, 'last_turn_pieces')
            if hasattr(game, 'last_turn_plays'):
                delattr(game, 'last_turn_plays')
                
            self.logger.info("Turn Results Display cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Turn Results Phase: {e}")
    
    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action for turn results phase"""
        if action.action_type == ActionType.CONTINUE_ROUND:
            return True
        elif action.action_type in {ActionType.GAME_STATE_UPDATE, ActionType.PLAYER_DISCONNECT, 
                                  ActionType.PLAYER_RECONNECT, ActionType.TIMEOUT}:
            return True
        
        return False
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid actions for turn results phase"""
        result = {"success": False, "message": "", "data": {}}
        
        try:
            if action.action_type == ActionType.CONTINUE_ROUND:
                result = await self._handle_continue_round(action)
            elif action.action_type == ActionType.GAME_STATE_UPDATE:
                result = await self._handle_view_results(action)
            elif action.action_type in {ActionType.PLAYER_DISCONNECT, ActionType.PLAYER_RECONNECT}:
                result = {"success": True, "message": f"{action.action_type} handled", "data": {}}
            elif action.action_type == ActionType.TIMEOUT:
                result = {"success": True, "message": "Timeout handled", "data": {}}
            else:
                result["message"] = f"Action {action.action_type} not supported in Turn Results Phase"
                
        except Exception as e:
            self.logger.error(f"Error processing action {action.action_type}: {e}")
            result["message"] = f"Error processing action: {str(e)}"
        
        return result
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """🚀 ENTERPRISE: Event-driven transitions - determine next phase"""
        
        # Don't transition until auto-advance timer completes
        if not self.auto_advance_complete:
            return None
        
        # Transition based on whether hands are empty
        if self.hands_empty:
            return GamePhase.SCORING
        else:
            return GamePhase.TURN
    
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
    
    async def _handle_view_results(self, action: GameAction) -> Dict[str, Any]:
        """Handle request to view turn results"""
        return {
            "success": True,
            "message": "Turn results retrieved",
            "data": {
                "winner": self.turn_winner,
                "pieces_won": [str(piece) for piece in self.pieces_won],
                "turn_plays": self.turn_plays,
                "hands_empty": self.hands_empty,
                "next_phase": 'scoring' if self.hands_empty else 'turn'
            }
        }
    
    # Helper Methods
    
    def _check_hands_empty(self) -> bool:
        """Check if all players have empty hands"""
        game = self.state_machine.game
        if not hasattr(game, 'players'):
            return False
        
        for player in game.players:
            hand = getattr(player, 'hand', [])
            if hand:  # If any player has cards remaining
                return False
        
        return True  # All hands are empty
    
    async def _start_auto_advance(self) -> None:
        """🚀 ENTERPRISE: Auto-advance timer without race conditions"""
        try:
            print(f"⏰ TURN_RESULTS_AUTO: Starting 7-second auto-advance timer...")
            await asyncio.sleep(7.0)  # 7 second display time
            
            print(f"⏰ TURN_RESULTS_AUTO: 7-second timer completed!")
            
            # 🚀 RACE_CONDITION_FIX: Check if we're still the active state
            current_phase = self.state_machine.current_phase
            print(f"🚀 TURN_RESULTS_FIX: Current phase check: {current_phase}")
            if current_phase != GamePhase.TURN_RESULTS:
                print(f"🚀 TURN_RESULTS_FIX: Not in turn results phase anymore (now {current_phase}), skipping auto-advance")
                return
            
            self.auto_advance_complete = True
            print(f"⏰ TURN_RESULTS_AUTO: Auto-advance timer complete, auto_advance_complete = True")
            self.logger.info("Turn results auto-advance timer complete")
            
            # 🚀 ENTERPRISE: Event-driven transition
            print(f"🎆 TURN_RESULTS_AUTO: Checking transition conditions...")
            next_phase = await self.check_transition_conditions()
            print(f"🎆 TURN_RESULTS_AUTO: Next phase determined: {next_phase}")
            if next_phase:
                print(f"🎆 ENTERPRISE_TRANSITION: Auto-advancing to {next_phase.value}")
                await self.state_machine.trigger_transition(
                    next_phase,
                    "Turn results auto-advance after 7 seconds"
                )
                print(f"🎆 ENTERPRISE_TRANSITION: Transition triggered successfully!")
            else:
                print(f"🚫 TURN_RESULTS_AUTO: No next phase determined, staying in TURN_RESULTS")
            
        except asyncio.CancelledError:
            print(f"🚫 TURN_RESULTS_AUTO: Auto-advance task was cancelled")
            raise
        except Exception as e:
            print(f"🚫 TURN_RESULTS_AUTO: Error in auto-advance timer: {e}")
            self.logger.error(f"Error in auto-advance timer: {e}")
            import traceback
            traceback.print_exc()