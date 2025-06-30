# backend/engine/state_machine/states/game_end_state.py

from typing import Dict, Any, Optional, List
from ..core import GamePhase, ActionType, GameAction
from ..base_state import GameState
import time
import asyncio


class GameEndState(GameState):
    """
    Game End Phase State
    
    🚀 ENTERPRISE ARCHITECTURE COMPLIANT
    
    Handles:
    - Display final game results and winner announcement
    - Show game statistics (total rounds, duration)
    - Handle player navigation back to lobby
    - No automatic transitions (user-controlled exit)
    """
    
    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.GAME_END
    
    @property
    def next_phases(self) -> List[GamePhase]:
        return []  # No automatic transitions - user controls exit
    
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.NAVIGATE_TO_LOBBY,
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT
        }
        
        # Phase-specific state
        self.game_start_time: Optional[float] = None
        self.game_end_time: Optional[float] = None
        self.final_rankings: List[Dict[str, Any]] = []
        self.game_statistics: Dict[str, Any] = {}
    
    async def _setup_phase(self) -> None:
        """Initialize game end phase - prepare final results"""
        print(f"🏆 GAME_END_SETUP: Preparing final game results")
        
        game = self.state_machine.game
        self.game_end_time = time.time()
        
        # Calculate final rankings (sorted by score, highest first)
        self._calculate_final_rankings()
        
        # Calculate game statistics
        self._calculate_game_statistics()
        
        # 🚀 ENTERPRISE: Use automatic broadcasting system
        await self.update_phase_data({
            'final_rankings': self.final_rankings,
            'game_statistics': self.game_statistics,
            'winners': [player['name'] for player in self.final_rankings if player['rank'] == 1],
            'game_complete': True
        }, "Game ended - displaying final results")
        
        self.logger.info(f"🏆 Game ended - Winners: {[p['name'] for p in self.final_rankings if p['rank'] == 1]}")
        print(f"🏆 GAME_END_SETUP: Final results prepared and broadcasted")
    
    async def _cleanup_phase(self) -> None:
        """Clean up game end phase"""
        self.logger.info("🏁 Game end phase complete")
        print(f"🏁 GAME_END_CLEANUP: Game end phase complete")
    
    async def _validate_action(self, action: GameAction) -> bool:
        """Validate actions in game end phase"""
        # All allowed actions are valid
        return action.action_type in self.allowed_actions
    
    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process valid actions"""
        print(f"🏆 GAME_END_DEBUG: Processing action {action.action_type.value} from {action.player_name}")
        
        if action.action_type == ActionType.NAVIGATE_TO_LOBBY:
            return await self._handle_navigate_to_lobby(action)
        elif action.action_type == ActionType.PLAYER_DISCONNECT:
            return await self._handle_player_disconnect(action)
        elif action.action_type == ActionType.PLAYER_RECONNECT:
            return await self._handle_player_reconnect(action)
        else:
            return {'status': 'handled', 'action': action.action_type.value}
    
    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """🚀 ENTERPRISE: No automatic transitions - user controls exit"""
        # Game end state does not transition automatically
        # Players navigate away via frontend action (NAVIGATE_TO_LOBBY)
        return None
    
    def _calculate_final_rankings(self) -> None:
        """Calculate final player rankings sorted by score"""
        game = self.state_machine.game
        
        if not hasattr(game, 'players') or not game.players:
            self.final_rankings = []
            return
        
        # Create player ranking data
        players_with_scores = []
        for player in game.players:
            players_with_scores.append({
                'name': getattr(player, 'name', str(player)),
                'score': getattr(player, 'score', 0)
            })
        
        # Sort by score (highest first)
        players_with_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks (handle ties)
        self.final_rankings = []
        current_rank = 1
        
        for i, player_data in enumerate(players_with_scores):
            # Check for ties with previous player
            if i > 0 and player_data['score'] == players_with_scores[i-1]['score']:
                # Same score as previous player - same rank
                rank = self.final_rankings[i-1]['rank']
            else:
                # Different score - new rank
                rank = current_rank
            
            self.final_rankings.append({
                'rank': rank,
                'name': player_data['name'],
                'score': player_data['score'],
                'is_winner': rank == 1
            })
            
            current_rank = i + 2  # Next unique rank position
        
        print(f"🏆 FINAL_RANKINGS: {self.final_rankings}")
    
    def _calculate_game_statistics(self) -> None:
        """Calculate game statistics for display"""
        game = self.state_machine.game
        
        # Total rounds played
        total_rounds = getattr(game, 'round_number', 1)
        
        # Game duration calculation
        game_duration_seconds = 0
        if self.game_end_time:
            # Try to get game start time from various sources
            start_time = (
                getattr(game, 'start_time', None) or
                getattr(self.state_machine, 'start_time', None) or 
                (self.game_end_time - (total_rounds * 60))  # Fallback: estimate 1 min per round
            )
            
            if start_time:
                game_duration_seconds = int(self.game_end_time - start_time)
        
        # Convert to human-readable duration
        if game_duration_seconds > 0:
            minutes = game_duration_seconds // 60
            if minutes > 0:
                game_duration = f"{minutes} min"
            else:
                game_duration = f"{game_duration_seconds} sec"
        else:
            game_duration = "Unknown"
        
        self.game_statistics = {
            'total_rounds': total_rounds,
            'game_duration': game_duration,
            'game_duration_seconds': game_duration_seconds
        }
        
        print(f"📊 GAME_STATISTICS: {self.game_statistics}")
    
    # Action Handlers
    
    async def _handle_navigate_to_lobby(self, action: GameAction) -> Dict[str, Any]:
        """Handle player request to navigate back to lobby"""
        player_name = action.player_name
        
        print(f"🏠 NAVIGATE_LOBBY: {player_name} requested navigation to lobby")
        self.logger.info(f"🏠 {player_name} navigating back to lobby from game end")
        
        # 🚀 ENTERPRISE: Broadcast navigation event for frontend
        await self.broadcast_custom_event("navigate_to_lobby", {
            "player_name": player_name,
            "timestamp": time.time()
        }, f"Player {player_name} requested lobby navigation")
        
        return {
            'status': 'navigation_requested',
            'player': player_name,
            'destination': 'lobby',
            'message': 'Navigate to lobby'
        }
    
    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during game end"""
        player = action.player_name
        self.logger.info(f"⚠️ {player} disconnected during game end phase")
        
        return {'status': 'player_disconnected', 'player': player}
    
    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during game end"""
        player = action.player_name
        self.logger.info(f"✅ {player} reconnected during game end phase")
        
        # Re-send game end data to reconnected player
        await self.update_phase_data({
            'final_rankings': self.final_rankings,
            'game_statistics': self.game_statistics,
            'winners': [player['name'] for player in self.final_rankings if player['rank'] == 1],
            'game_complete': True
        }, f"Player {player} reconnected - resending game end data")
        
        return {'status': 'player_reconnected', 'player': player}