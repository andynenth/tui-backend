# backend/engine/state_machine/states/scoring_state.py

from typing import Dict, Any, Optional, List
from ..base_state import GameState
from ..core import GamePhase, ActionType, GameAction
from ...scoring import calculate_score


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
        return [GamePhase.PREPARATION, GamePhase.GAME_OVER]  # Next round or game end

    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.allowed_actions = {
            ActionType.GAME_STATE_UPDATE,  # For viewing scores
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT,
        }

        # Phase-specific state
        self.round_scores: Dict[str, Dict[str, Any]] = {}
        self.game_complete: bool = False
        self.winners: List[str] = []
        self.scores_calculated: bool = False
        self.display_delay_complete: bool = False

    async def _setup_phase(self) -> None:
        """Initialize scoring phase - calculate all scores"""
        try:
            # Reset delay flag for new scoring phase
            self.display_delay_complete = False
            print(f"🔄 SCORING_SETUP_DEBUG: Reset display_delay_complete = False")

            self.logger.info("Setting up Scoring Phase")

            # Calculate scores for all players
            await self._calculate_round_scores()

            # Check for game winner
            await self._check_game_winner()

            self.scores_calculated = True

            # 🚀 ENTERPRISE: Use automatic broadcasting system to update scoring UI
            print(f"🚀 SCORING_BROADCAST_DEBUG: Broadcasting scoring data:")
            print(f"   📊 Round scores: {self.round_scores}")
            print(f"   🏁 Game complete: {self.game_complete}")
            print(f"   🏆 Winners: {self.winners}")

            # Prepare total scores and scoring-specific data for frontend
            # (base_state.py automatically handles standard player data)
            game = self.state_machine.game
            total_scores = {}
            scoring_players_data = []  # Scoring-specific data only
            player_stats = {}

            if hasattr(game, "players") and game.players:
                for player in game.players:
                    total_scores[player.name] = player.score
                    scoring_players_data.append(
                        {
                            "name": player.name,
                            "is_bot": player.name.startswith(
                                "Bot"
                            ),  # Simple bot detection
                            "pile_count": getattr(
                                player, "declared", 0
                            ),  # Fix: use 'declared' not 'declared_piles'
                            "captured_piles": getattr(player, "captured_piles", 0),
                        }
                    )
                    # Include player statistics
                    player_stats[player.name] = {
                        "turns_won": getattr(player, "turns_won", 0),
                        "perfect_rounds": getattr(player, "perfect_rounds", 0)
                    }

            print(f"🚀 SCORING_BROADCAST_DEBUG: Also sending:")
            print(f"   💯 Total scores: {total_scores}")
            print(f"   👥 Scoring players data: {scoring_players_data}")

            await self.update_phase_data(
                {
                    "round_scores": self.round_scores,
                    "total_scores": total_scores,
                    "scoring_players_data": scoring_players_data,  # Scoring-specific data (base_state.py handles standard players data)
                    "player_stats": player_stats,
                    "game_complete": self.game_complete,
                    "winners": self.winners,
                    "scores_calculated": True,
                    "redeal_multiplier": getattr(game, "redeal_multiplier", 1),
                },
                f"Scoring calculated for round {getattr(self.state_machine.game, 'round_number', 1)}",
            )

            # Start display delay (7 seconds to show scoring results)
            import asyncio

            asyncio.create_task(self._start_display_delay())

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
        elif action.action_type in {
            ActionType.PLAYER_DISCONNECT,
            ActionType.PLAYER_RECONNECT,
            ActionType.TIMEOUT,
        }:
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
                result["message"] = (
                    f"Action {action.action_type} not supported in Scoring Phase"
                )

        except Exception as e:
            self.logger.error(f"Error processing action {action.action_type}: {e}")
            result["message"] = f"Error processing action: {str(e)}"

        return result

    async def check_transition_conditions(self) -> Optional[GamePhase]:
        """Check if ready to transition to next phase"""

        if not self.scores_calculated:
            return None

        # Wait for display delay to complete (give users time to see scoring)
        if not self.display_delay_complete:
            return None

        if self.game_complete:
            # Game is over, transition to GAME_OVER phase (only log once)
            if not hasattr(self, "_game_complete_logged"):
                self.logger.info(
                    "🔍 SCORING_TRANSITION_DEBUG: Game complete - transitioning to GAME_OVER"
                )
                self._game_complete_logged = True
            return GamePhase.GAME_OVER

        # Can transition to next round (only log once)
        if not hasattr(self, "_ready_to_transition_logged"):
            self.logger.info(
                "🔍 SCORING_TRANSITION_DEBUG: Ready to transition to PREPARATION"
            )
            self._ready_to_transition_logged = True
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
                "total_scores": (
                    {p.name: p.score for p in game.players}
                    if hasattr(game, "players")
                    else {}
                ),
                "game_complete": self.game_complete,
                "winners": self.winners,
                "redeal_multiplier": getattr(game, "redeal_multiplier", 1),
            },
        }

    async def _handle_player_disconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player disconnection during scoring"""
        game = self.state_machine.game
        player_name = action.payload.get("player_name")
        if not player_name:
            return {"success": False, "message": "Player name required"}

        # Find player and mark as disconnected
        if hasattr(game, "players"):
            for player in game.players:
                if player.name == player_name:
                    player.connected = False
                    self.logger.info(
                        f"Player {player_name} disconnected during Scoring Phase"
                    )
                    break

        return {
            "success": True,
            "message": f"Player {player_name} disconnected",
            "data": {"disconnected_player": player_name},
        }

    async def _handle_player_reconnect(self, action: GameAction) -> Dict[str, Any]:
        """Handle player reconnection during scoring"""
        game = self.state_machine.game
        player_name = action.payload.get("player_name")
        if not player_name:
            return {"success": False, "message": "Player name required"}

        # Find player and mark as connected
        if hasattr(game, "players"):
            for player in game.players:
                if player.name == player_name:
                    player.connected = True
                    self.logger.info(
                        f"Player {player_name} reconnected during Scoring Phase"
                    )
                    break

        return {
            "success": True,
            "message": f"Player {player_name} reconnected",
            "data": {
                "reconnected_player": player_name,
                "round_scores": self.round_scores,
                "game_complete": self.game_complete,
            },
        }

    # Core Scoring Logic

    async def _calculate_round_scores(self) -> None:
        """Calculate scores for all players this round"""
        game = self.state_machine.game
        self.round_scores = {}

        if not hasattr(game, "players"):
            self.logger.warning("Game has no players attribute")
            return

        print(
            f"🗳️ DECLARATION_DEBUG: game.player_declarations = {getattr(game, 'player_declarations', {})}"
        )

        for player in game.players:
            # Get declaration from game.player_declarations or player.declared
            declared = game.player_declarations.get(
                player.name, getattr(player, "declared", 0)
            )
            # Get actual piles from player's captured_piles (much simpler!)
            actual = getattr(player, "captured_piles", 0)

            print(
                f"📋 SCORING_FIX_DEBUG: {player.name} - declared: {declared}, actual: {actual}"
            )

            # Calculate base score using dedicated scoring module
            base_score = calculate_score(declared, actual)

            # Calculate bonus and hit_value separately for frontend display
            if declared == 0 and actual == 0:
                # Perfect zero prediction
                bonus = 3
                hit_value = 0
            elif declared > 0 and declared == actual:
                # Perfect non-zero prediction
                bonus = 5
                hit_value = declared
            else:
                # Miss - no bonus
                bonus = 0
                if declared == 0:
                    hit_value = -actual  # Penalty for breaking zero
                else:
                    hit_value = -abs(declared - actual)  # Penalty for missing target

            # Apply redeal multiplier
            multiplier = getattr(game, "redeal_multiplier", 1)
            final_score = base_score * multiplier

            # Update player's total score
            current_score = getattr(player, "score", 0)
            player.score = current_score + final_score
            
            # Increment perfect rounds counter for non-zero perfect predictions
            if declared > 0 and declared == actual:
                old_perfect_rounds = player.perfect_rounds
                player.perfect_rounds += 1
                self.logger.info(
                    f"🎯 PERFECT_ROUNDS_DEBUG: {player.name} had perfect round! perfect_rounds: {old_perfect_rounds} -> {player.perfect_rounds}"
                )

            # Store round score data
            self.round_scores[player.name] = {
                "declared": declared,
                "actual": actual,
                "base_score": base_score,
                "bonus": bonus,  # Separate bonus for frontend display
                "hit_value": hit_value,  # Separate hit value for frontend display
                "multiplier": multiplier,
                "final_score": final_score,
                "total_score": player.score,
            }

            print(f"🏆 SCORING_DEBUG: {player.name} scoring data:")
            print(f"   📋 Declared: {declared}, Actual: {actual}")
            print(
                f"   📊 Base Score: {base_score}, Multiplier: {multiplier}x, Final: {final_score}"
            )
            print(f"   💯 Total Score: {player.score}")

            self.logger.info(
                f"Player {player.name}: declared {declared}, actual {actual}, "
                f"base {base_score}, final {final_score} (×{multiplier}), "
                f"total {player.score}"
            )

    async def _check_game_winner(self) -> None:
        """Check if any player has won the game (≥50 points)"""
        game = self.state_machine.game
        WIN_THRESHOLD = 50

        if not hasattr(game, "players"):
            return

        # Find players with winning scores
        winning_players = []
        max_score = -999

        for player in game.players:
            player_score = getattr(player, "score", 0)
            if player_score >= WIN_THRESHOLD:
                if player_score > max_score:
                    max_score = player_score
                    winning_players = [player.name]
                elif player_score == max_score:
                    winning_players.append(player.name)

        if winning_players:
            self.game_complete = True
            self.winners = winning_players
            self.logger.info(
                f"Game completed! Winners: {winning_players} with {max_score} points"
            )
        else:
            self.game_complete = False
            self.winners = []

    def _prepare_next_round(self) -> None:
        """Prepare game state for next round"""
        game = self.state_machine.game

        # Increment round number
        current_round = getattr(game, "round_number", 1)
        game.round_number = current_round + 1

        # Reset round-specific data (declarations and captured_piles reset by preparation_state)
        if hasattr(game, "players"):
            for player in game.players:
                player.hand = []

        # Reset redeal multiplier for next round
        game.redeal_multiplier = 1

        # Set round starter for next round (winner of last turn becomes starter)
        if hasattr(game, "last_turn_winner") and game.last_turn_winner:
            game.round_starter = game.last_turn_winner
            game.current_player = game.last_turn_winner
            self.logger.info(
                f"🎯 Next round starter set to last turn winner: {game.last_turn_winner}"
            )
        else:
            # Fallback: if no last turn winner, keep current starter
            self.logger.warning(
                "No last turn winner found, keeping current round starter"
            )

        # Clear turn-related data
        game.turn_results = []
        game.current_turn_starter = None
        game.turn_number = 0  # Reset turn number for new round

        self.logger.info(f"Prepared for round {game.round_number}")

    async def _start_display_delay(self) -> None:
        """Give users 7 seconds to view scoring results before transitioning"""
        import asyncio

        print(f"⏰ SCORING_DELAY_DEBUG: Starting 7-second display delay...")
        await asyncio.sleep(7.0)  # 7 second delay for users to see scores
        self.display_delay_complete = True
        print(
            f"⏰ SCORING_DELAY_DEBUG: 7-second delay complete - setting display_delay_complete = True"
        )
        self.logger.info("Scoring display delay complete - ready to transition")
