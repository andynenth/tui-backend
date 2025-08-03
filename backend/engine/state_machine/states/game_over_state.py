# backend/engine/state_machine/states/game_over_state.py

import asyncio
import time
from typing import List, Optional

from backend.engine.win_conditions import get_winners

from ..base_state import GameState
from ..core import ActionType, GameAction, GamePhase


class GameOverState(GameState):
    """
    Handles the Game Over Phase - terminal state for game completion

    Responsibilities:
    - Calculate final rankings and game statistics
    - Prepare completion data for frontend display
    - Handle player disconnections during game over screen
    - Manage game cleanup and logging
    - NO game logic - pure data presentation state
    """

    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAYER_DISCONNECT,  # Handle players leaving
            ActionType.PLAYER_RECONNECT,  # Handle players returning
            ActionType.TIMEOUT,  # Handle auto-redirect timeout
            # NO game actions - game is finished
        }

    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.GAME_OVER

    @property
    def next_phases(self) -> List[GamePhase]:
        return []  # Terminal state - no transitions

    async def _setup_phase(self) -> None:
        """Initialize game over phase with final data"""
        game = self.state_machine.game

        # Set game end time for duration calculation
        if not game.end_time:
            game.end_time = time.time()

        # Prepare all final data for frontend
        await self.update_phase_data(
            {
                "final_rankings": self._calculate_final_rankings(),
                "game_stats": self._calculate_game_statistics(),
                "winners": [player.name for player in get_winners(game)],
            },
            "Game over phase initialized",
        )

    async def _cleanup_phase(self) -> None:
        """Clean up phase before transition (terminal state, so minimal cleanup)"""
        self.logger.info(
            f"Game over phase completed for room {self.state_machine.room_id}"
        )

    def _validate_action(self, action: GameAction) -> tuple[bool, Optional[str]]:
        """Validate if an action is allowed in game over phase"""
        # Only allow disconnect/reconnect/timeout actions
        if action.action_type not in self.allowed_actions:
            return False, f"Action {action.action_type} not allowed in game over phase"
        return True, None

    async def _process_action(self, action: GameAction) -> None:
        """Process actions during game over phase"""
        if action.action_type == ActionType.PLAYER_DISCONNECT:
            # Just log it - players can leave during game over
            self.logger.info(
                f"Player {action.player_name} disconnected during game over"
            )

        elif action.action_type == ActionType.PLAYER_RECONNECT:
            # Just log it - players can reconnect to see results
            self.logger.info(
                f"Player {action.player_name} reconnected during game over"
            )

        elif action.action_type == ActionType.TIMEOUT:
            # Frontend handles navigation - just log it
            self.logger.info("Game over timeout reached")

    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Game over is terminal state - no transitions"""
        return None  # Players navigate away via frontend button

    def _calculate_final_rankings(self):
        """Sort players by final score and assign ranks"""
        game = self.state_machine.game
        sorted_players = sorted(game.players, key=lambda p: p.score, reverse=True)

        rankings = [
            {
                "name": player.name,
                "score": player.score,
                "rank": i + 1,
                "turns_won": getattr(player, "turns_won", 0),
                "perfect_rounds": getattr(player, "perfect_rounds", 0),
            }
            for i, player in enumerate(sorted_players)
        ]

        # Debug logging
        for ranking in rankings:
            self.logger.info(
                f"Player {ranking['name']}: turns_won={ranking['turns_won']}, perfect_rounds={ranking['perfect_rounds']}"
            )

        return rankings

    def _calculate_game_statistics(self):
        """Calculate game stats for display"""
        game = self.state_machine.game

        # Handle missing timing data gracefully
        if game.start_time and game.end_time:
            duration_seconds = game.end_time - game.start_time
            duration_minutes = int(duration_seconds / 60)
            duration_str = f"{duration_minutes} min"
        else:
            duration_str = "Unknown"

        return {
            "total_rounds": game.round_number,
            "game_duration": duration_str,
            "start_time": game.start_time,
            "end_time": game.end_time,
        }
