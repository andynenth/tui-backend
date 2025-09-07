# backend/engine/state_machine/states/scoring_state.py

from typing import Any, Dict, List, Optional

from ...scoring import calculate_final_score
from ..base_state import GameState
from ..core import ActionType, GameAction, GamePhase


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

            self.logger.info("Setting up Scoring Phase")

            # Calculate scores for all players
            await self._calculate_round_scores()

            # Check for game winner
            await self._check_game_winner()

            self.scores_calculated = True

            # 🚀 ENTERPRISE: Use automatic broadcasting system to update scoring UI

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
                        "perfect_rounds": getattr(player, "perfect_rounds", 0),
                    }

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
                result[
                    "message"
                ] = f"Action {action.action_type} not supported in Scoring Phase"

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
                self.logger.info("🔍 Game complete - transitioning to GAME_OVER")
                self._game_complete_logged = True
            return GamePhase.GAME_OVER

        # Can transition to next round (only log once)
        if not hasattr(self, "_ready_to_transition_logged"):
            self.logger.info("🔍 Ready to transition to PREPARATION")
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

        for player in game.players:
            # Get declaration from game.player_declarations or player.declared
            declared = game.player_declarations.get(
                player.name, getattr(player, "declared", 0)
            )
            # Get actual piles from player's captured_piles (much simpler!)
            actual = getattr(player, "captured_piles", 0)

            # Use the new centralized scoring function
            multiplier = getattr(game, "redeal_multiplier", 1)
            score_result = calculate_final_score(declared, actual, multiplier)

            # Extract values from result
            final_score = score_result["final_score"]
            bonus = score_result["bonus"]
            hit_value = score_result["hit_value"]
            base_points = score_result["base_points"]
            is_perfect = score_result["is_perfect"]

            # Update player's total score
            current_score = getattr(player, "score", 0)
            player.score = current_score + final_score

            # Increment perfect rounds counter for non-zero perfect predictions
            if declared > 0 and is_perfect:
                old_perfect_rounds = player.perfect_rounds
                player.perfect_rounds += 1
                self.logger.info(
                    f"🎯 {player.name} had perfect round! perfect_rounds: {old_perfect_rounds} -> {player.perfect_rounds}"
                )

            # Calculate base_score for display (what it would be without multiplier)
            # This maintains backward compatibility with frontend expectations
            if declared == 0 and actual == 0:
                base_score = 3
            elif declared > 0 and declared == actual:
                base_score = declared + 5
            else:
                base_score = base_points  # Already negative for penalties

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

            self.logger.info(
                f"Player {player.name}: declared {declared}, actual {actual}, "
                f"base {base_score}, final {final_score} (×{multiplier}), "
                f"total {player.score}"
            )

        # 🚀 V2 OPTIMIZATION: Fire round_completed event after scoring
        await self._fire_round_completed_event()

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

        await asyncio.sleep(7.0)  # 7 second delay for users to see scores
        self.display_delay_complete = True
        self.logger.info("Scoring display delay complete - ready to transition")

    async def _fire_round_completed_event(self) -> None:
        """🚀 V2 OPTIMIZATION: Fire round_completed event with comprehensive round data"""
        game = self.state_machine.game

        # Get initial hands data from game if stored during preparation phase
        initial_hands = {}
        if hasattr(game, "round_initial_hands"):
            initial_hands = game.round_initial_hands
        else:
            # Fallback: reconstruct from current player hands (less accurate)
            self.logger.warning("round_initial_hands not found, using fallback")
            if hasattr(game, "players"):
                for player in game.players:
                    initial_hands[player.name] = []  # Empty since we can't reconstruct

        # Gather all round data for the event
        round_data = {
            "round_number": getattr(game, "round_number", 1),
            "starter_player": getattr(game, "round_starter", ""),
            "starter_reason": getattr(game, "starter_reason", "default"),
            "initial_hands": initial_hands,
            "declarations": getattr(game, "player_declarations", {}),
            "turn_sequence": [],  # Captured from turn_results below
            "scores": self.round_scores,
            "total_scores": (
                {p.name: p.score for p in game.players}
                if hasattr(game, "players")
                else {}
            ),
        }

        # Add turn sequence if available (from turn_results)
        if hasattr(game, "turn_results") and game.turn_results:
            self.logger.info(
                f"📝 Building turn_sequence from {len(game.turn_results)} turns"
            )
            turn_sequence = []

            for i, turn in enumerate(game.turn_results):
                # Debug log
                self.logger.info(f"Turn {i}: {turn}")

                # Build plays dict from turn data
                plays_dict = {}
                for play in turn.get("plays", []):
                    player_name = play.get("player")
                    if player_name:
                        # Convert Piece objects to dictionaries
                        pieces_data = []
                        for piece in play.get("pieces", []):
                            if hasattr(piece, "kind") and hasattr(piece, "point"):
                                # It's a Piece object
                                pieces_data.append(
                                    {"kind": piece.kind, "point": piece.point}
                                )
                            elif isinstance(piece, dict):
                                # Already a dict
                                pieces_data.append(piece)
                            else:
                                # Unknown format, try to convert to string
                                pieces_data.append(str(piece))

                        plays_dict[player_name] = {
                            "pieces": pieces_data,
                            "is_starter": i == 0
                            and play
                            == turn.get("plays", [])[0],  # First player of first turn
                            "play_type": play.get("play_type", "unknown"),
                            "play_value": play.get("play_value", 0),
                        }

                turn_entry = {
                    "turn_number": turn.get("turn_number", i + 1),
                    "starter": turn.get("plays", [{}])[0].get("player", "")
                    if turn.get("plays")
                    else "",
                    "plays": plays_dict,
                    "winner": turn.get("winner", ""),
                    "piles_won": turn.get("piles_won", 0),
                }
                turn_sequence.append(turn_entry)

            round_data["turn_sequence"] = turn_sequence
            self.logger.info(f"✅ Built turn_sequence with {len(turn_sequence)} turns")

        # Add debug logging
        self.logger.info(
            f"🔥 SCORING_STATE: About to store round_completed event for room {self.state_machine.room_id}"
        )
        self.logger.info(
            f"🔥 SCORING_STATE: Round data has {len(round_data.get('turn_sequence', []))} turns"
        )

        await self.state_machine.store_game_event(
            "round_completed",
            round_data,
        )

        self.logger.info(
            f"🚀 V2 EVENT: round_completed event fired for room {self.state_machine.room_id}, round {game.round_number}"
        )
        self.logger.info(f"🔥 SCORING_STATE: round_completed event stored successfully")
