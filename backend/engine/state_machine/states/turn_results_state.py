# backend/engine/state_machine/states/turn_results_state.py

from typing import Dict, Any, Optional, List
from ..core import GamePhase, ActionType, GameAction
from ..base_state import GameState
import asyncio


class TurnResultsState(GameState):
    """
    Turn Results Phase State

    Handles:
    - Display turn completion results to all players
    - Automatic progression after display period (7 seconds)
    - Transition to next turn or scoring phase based on game state
    """

    @property
    def phase_name(self) -> GamePhase:
        return GamePhase.TURN_RESULTS

    @property
    def next_phases(self) -> List[GamePhase]:
        return [GamePhase.TURN, GamePhase.SCORING]

    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
        }

        # Phase-specific state for turn results
        self.display_duration: float = 7.0  # 7 second display period
        self.turn_winner: Optional[str] = None
        self.winning_play: Optional[dict] = None
        self.turn_plays: Dict[str, Any] = {}  # Store turn plays for display
        self.auto_transition_task: Optional[asyncio.Task] = None
        self.transition_target: Optional[GamePhase] = None

    async def _setup_phase(self) -> None:
        """Initialize turn results phase with display data"""
        self.logger.info("🏆 Turn results phase starting - displaying turn outcome")

        # Get turn result data from previous turn state
        await self._load_turn_results()

        # Start auto-transition timer
        await self._start_auto_transition()

    async def _load_turn_results(self) -> None:
        """Load turn result data from game state"""
        try:
            game = self.state_machine.game
            if not game:
                self.logger.warning("No game instance available for turn results")
                return

            # Get turn results from current phase data or game state
            phase_data = getattr(self.state_machine, "phase_data", {})

            self.turn_winner = phase_data.get("turn_winner") or phase_data.get("winner")
            self.winning_play = phase_data.get("winning_play")
            self.turn_plays = phase_data.get("turn_plays", {})

            # Determine next phase based on game state
            all_hands_empty = self._check_all_hands_empty()
            self.transition_target = (
                GamePhase.SCORING if all_hands_empty else GamePhase.TURN
            )

            # Update turn winner's statistics
            if self.turn_winner:
                winner_player = next(
                    (p for p in game.players if p.name == self.turn_winner), None
                )
                if winner_player:
                    winner_player.turns_won += 1
                    self.logger.info(
                        f"Player {self.turn_winner} now has {winner_player.turns_won} turns won"
                    )

            # Prepare player statistics for broadcast
            player_stats = {
                p.name: {"turns_won": p.turns_won, "perfect_rounds": p.perfect_rounds}
                for p in game.players
            }

            # Get accumulated pile counts
            pile_counts = getattr(game, "pile_counts", {})

            # 🚀 ENTERPRISE: Update phase data with turn results display
            await self.update_phase_data(
                {
                    "turn_winner": self.turn_winner,
                    "winning_play": self.winning_play,
                    "turn_plays": self.turn_plays,  # Include turn plays for display
                    "display_duration": self.display_duration,
                    "next_phase": self.transition_target.value,
                    "auto_transition": True,
                    "player_stats": player_stats,
                    "pile_counts": pile_counts.copy(),  # Include accumulated pile counts
                },
                f"Displaying turn results - winner: {self.turn_winner}",
            )

        except Exception as e:
            self.logger.error(f"Failed to load turn results: {e}", exc_info=True)

    def _check_all_hands_empty(self) -> bool:
        """Check if all player hands are empty (end of round)"""
        try:
            game = self.state_machine.game
            if hasattr(game, "players") and game.players:
                return all(len(player.hand) == 0 for player in game.players)
        except Exception as e:
            self.logger.error(f"Error checking hand status: {e}")

        return False

    async def _start_auto_transition(self) -> None:
        """Start automatic transition timer"""
        try:
            # Cancel any existing transition task
            if self.auto_transition_task and not self.auto_transition_task.done():
                self.auto_transition_task.cancel()

            # Create new auto-transition task
            self.auto_transition_task = asyncio.create_task(
                self._auto_transition_after_delay()
            )

        except Exception as e:
            self.logger.error(f"Failed to start auto transition: {e}", exc_info=True)

    async def _auto_transition_after_delay(self) -> None:
        """Handle automatic transition after display period"""
        try:
            # Wait for display duration
            await asyncio.sleep(self.display_duration)

            # 🚀 ENTERPRISE: Update phase data for transition
            await self.update_phase_data(
                {
                    "auto_transition_triggered": True,
                    "transitioning_to": (
                        self.transition_target.value
                        if self.transition_target
                        else "unknown"
                    ),
                },
                f"Auto-transition triggered after {self.display_duration}s display",
            )

            # The transition will be handled by check_transition_conditions()

        except asyncio.CancelledError:
            self.logger.info("Auto-transition cancelled")
        except Exception as e:
            self.logger.error(f"Error in auto-transition: {e}", exc_info=True)

    async def handle_action(self, action: GameAction) -> bool:
        """Handle turn results phase actions (minimal - mostly display only)"""
        try:
            if action.action_type == ActionType.PLAYER_DISCONNECT:
                # Handle disconnection but don't interrupt display
                self.logger.info(
                    f"Player {action.player_name} disconnected during turn results display"
                )
                return True
            elif action.action_type == ActionType.PLAYER_RECONNECT:
                # Handle reconnection and send current results
                self.logger.info(
                    f"Player {action.player_name} reconnected during turn results display"
                )
                return True
            else:
                self.logger.warning(
                    f"Unhandled action in turn results phase: {action.action_type}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Error handling action {action.action_type}: {e}", exc_info=True
            )
            return False

    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition after display period"""
        # Transition when auto-transition task completes
        if self.auto_transition_task and self.auto_transition_task.done():
            if self.transition_target:
                self.logger.info(
                    f"🏆 Turn results complete - transitioning to {self.transition_target}"
                )
                return self.transition_target

        return None

    async def _cleanup_phase(self) -> None:
        """Clean up turn results phase before transition"""
        self.logger.info("🏆 Cleaning up turn results phase")

        # Cancel auto-transition task if still running
        if self.auto_transition_task and not self.auto_transition_task.done():
            self.auto_transition_task.cancel()

        # Clear turn results state
        self.turn_winner = None
        self.winning_play = None
        self.transition_target = None

    async def _validate_action(self, action: GameAction) -> bool:
        """Validate action is appropriate for turn results phase"""
        # Turn results is mostly display-only, so very limited actions allowed
        if action.action_type in [
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
        ]:
            return True

        return False

    async def _process_action(self, action: GameAction) -> Dict[str, Any]:
        """Process validated action and return result"""
        if action.action_type == ActionType.PLAYER_DISCONNECT:
            self.logger.info(
                f"Player {action.player_name} disconnected during turn results display"
            )
            return {
                "success": True,
                "action": "player_disconnected",
                "phase": "turn_results",
            }
        elif action.action_type == ActionType.PLAYER_RECONNECT:
            self.logger.info(
                f"Player {action.player_name} reconnected during turn results display"
            )
            # Could send current turn results to reconnecting player
            return {
                "success": True,
                "action": "player_reconnected",
                "phase": "turn_results",
            }

        return {"success": False, "error": "unhandled_action"}
