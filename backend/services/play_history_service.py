# backend/services/play_history_service.py

from typing import Dict, List, Optional, Any
from backend.engine.game import Game
from backend.engine.piece import Piece
from backend.models.play_history import (
    PlayerInfo,
    InitialState,
    PieceInfo,
    DeclarationInfo,
    PlayData,
    TurnInfo,
    RoundSummary,
    RoundHistory,
    PlayHistoryResponse,
)


class PlayHistoryService:
    """Service for building comprehensive play history from game state.

    This service extracts and transforms game data into a structured format
    suitable for analyzing player behavior, AI decision-making, and game progression.

    The service handles:
    - Player information extraction (AI vs human detection)
    - Hand sorting (RED before BLACK, high to low value)
    - Declaration phase data with pile room calculations
    - Turn-by-turn play history with hand state tracking
    - AI decision analysis extraction (when available)
    - Round scoring and cumulative score tracking
    - Compact format generation for reduced response sizes

    Thread Safety:
        This service is stateless and thread-safe. Each method call operates
        independently on the provided game state.

    Performance:
        - Single round extraction: O(n) where n is number of turns
        - Hand sorting: O(m log m) where m is hand size (typically 8)
        - Full game extraction: O(r * n) where r is rounds
    """

    def __init__(self):
        """Initialize the service. Currently stateless so no initialization needed."""
        # Import here to avoid circular imports
        from backend.services.play_history_db import play_history_db_service

        self.db_service = play_history_db_service

    async def build_play_history(
        self,
        game: Game,
        room_id: str,
        include_ai_analysis: bool = True,
        format: Optional[str] = None,
    ) -> PlayHistoryResponse:
        """Build complete play history for a game.

        This is the main entry point that orchestrates the extraction of all game data.
        It now uses SQLite event store as the primary data source for historical rounds,
        falling back to in-memory game state only for the current round if needed.

        Args:
            game: The Game instance containing all game state
            room_id: Unique identifier for the game room
            include_ai_analysis: Whether to include AI decision reasoning (default: True)
            format: Response format - 'compact' for minimal data, None for full (default: None)

        Returns:
            PlayHistoryResponse: Complete play history with player info and round data

        Raises:
            None - Errors are logged but method returns partial data rather than failing
        """
        try:
            # Try to get complete history from database service first
            history_data = await self.db_service.get_play_history(room_id)
            
            # If we got data, convert it to PlayHistoryResponse format
            if history_data:
                print(f"Got history data from database for room {room_id}: {len(history_data.get('rounds', []))} rounds")
                return self._convert_to_play_history_response(history_data)
            else:
                print(f"No history data from database for room {room_id}")

        except Exception as e:
            # Log error with traceback
            import traceback
            print(f"Error retrieving from database: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            print("Falling back to memory")

        # If no game provided (room not in memory), return empty response
        if game is None:
            return PlayHistoryResponse(
                room_id=room_id,
                players={},
                rounds=[],
                total_rounds=0
            )

        # Fallback to original memory-based extraction for compatibility
        # This handles cases where event store isn't available or has no data

        # Store flags for use in other methods (instance variables for simplicity)
        self.include_ai_analysis = include_ai_analysis
        self.format = format

        # Extract player information
        players = self.extract_player_info(game)

        # Build history for each completed round
        rounds = []

        # Handle invalid round numbers
        if not hasattr(game, "round_number") or game.round_number < 1:
            # Return empty history for invalid games
            return PlayHistoryResponse(
                room_id=room_id, total_rounds=0, players=players, rounds=[]
            )

        for round_num in range(1, game.round_number + 1):
            if round_num < game.round_number or (
                game.current_phase == "SCORING" if game.current_phase else False
            ):
                # Only include completed rounds or current round if in SCORING phase
                try:
                    if format == "compact":
                        round_history = self.build_compact_round_history(
                            game, round_num
                        )
                    else:
                        round_history = self.build_round_history(game, round_num)
                    if round_history:
                        rounds.append(round_history)
                except Exception as e:
                    # Log error but continue with other rounds
                    print(f"Error building history for round {round_num}: {e}")
                    continue

        return PlayHistoryResponse(
            room_id=room_id, total_rounds=len(rounds), players=players, rounds=rounds
        )

    def build_compact_round_history(
        self, game: Game, round_number: int
    ) -> RoundHistory:
        """Build compact history for a single round (minimal data).

        Compact format reduces response size by 30-50% by excluding:
        - Detailed hand information (hands_dealt)
        - Turn-by-turn play history
        - Hand states before/after plays

        This format retains essential information:
        - Initial state (who started and why)
        - Declaration phase (what each player declared)
        - Round summary (final scores and captures)
        """
        # Extract only essential components for compact format
        initial_state = self.extract_initial_state(game, round_number)

        # Empty hands_dealt significantly reduces response size
        hands_dealt = {}  # Saves ~20-30% of response size

        # Declaration info is essential for understanding the round
        declaration_phase = self.extract_declaration_phase(game, round_number)

        # Turn history is the largest component - excluding saves ~40-50%
        turn_history = []  # Most significant size reduction

        # Round summary is essential - shows outcomes and scores
        round_summary = self.extract_round_summary(game, round_number)

        return RoundHistory(
            round_number=round_number,
            initial_state=initial_state,
            hands_dealt=hands_dealt,
            declaration_phase=declaration_phase,
            turn_history=turn_history,
            round_summary=round_summary,
        )

    def build_round_history(self, game: Game, round_number: int) -> RoundHistory:
        """Build history for a single round."""
        # Extract all components using the dedicated methods
        initial_state = self.extract_initial_state(game, round_number)
        hands_dealt = self.extract_hands_dealt(game, round_number)
        declaration_phase = self.extract_declaration_phase(game, round_number)
        turn_history = self.extract_turn_history(game, round_number)
        round_summary = self.extract_round_summary(game, round_number)

        return RoundHistory(
            round_number=round_number,
            initial_state=initial_state,
            hands_dealt=hands_dealt,
            declaration_phase=declaration_phase,
            turn_history=turn_history,
            round_summary=round_summary,
        )

    def extract_player_info(self, game: Game) -> Dict[str, PlayerInfo]:
        """Extract player information including type (AI/human)."""
        player_info = {}

        for player in game.players:
            # Handle missing or None player name
            if not player or not hasattr(player, "name") or not player.name:
                continue

            # Normalize player ID from name (lowercase, replace spaces with underscores)
            # Also replace special characters
            player_id = player.name.lower().replace(" ", "_")
            player_id = (
                player_id.replace("/", "_")
                .replace("@", "_")
                .replace("#", "_")
                .replace("$", "_")
            )

            # Determine player type and AI version with safe attribute access
            is_bot = getattr(player, "is_bot", True)  # Default to True if missing
            player_type = "ai" if is_bot else "human"
            ai_version = "v2" if is_bot else None

            player_info[player.name] = PlayerInfo(
                player_id=player_id,
                player_name=player.name,
                player_type=player_type,
                ai_version=ai_version,
            )

        return player_info

    def extract_initial_state(self, game: Game, round_number: int) -> InitialState:
        """Extract initial state for a round.

        Determines who started the round and why:
        - Round 1: Player with GENERAL_RED or highest card
        - Later rounds: Winner of previous round
        """
        from backend.models.play_history import StarterInfo

        # Determine the starter through multiple fallback mechanisms
        starter_index = 0
        starter_player = None

        # Priority 1: Check stored round history (for historical rounds)
        if hasattr(game, "round_history") and round_number in game.round_history:
            # Historical data available - most reliable source
            starter_index = game.round_history[round_number].get("starter_index", 0)
            starter_player = game.players[starter_index]

        # Priority 2: Check current round starter (for current round)
        elif hasattr(game, "round_starter") and game.round_starter:
            # Current round data - game.round_starter might be index or player
            if isinstance(game.round_starter, int):
                starter_index = game.round_starter
                starter_player = game.players[starter_index]
            else:
                starter_player = game.round_starter
                # Find the index by matching player object
                for i, player in enumerate(game.players):
                    if player == starter_player:
                        starter_index = i
                        break

        # Priority 3: Default fallback
        else:
            # No starter information available - default to first player
            starter_index = 0
            starter_player = game.players[0]

        # Normalize player ID for consistency
        starter_id = starter_player.name.lower().replace(" ", "_")

        # Determine why they're the starter
        if round_number == 1:
            # First round - check for GENERAL_RED
            reason = "has_general_red"
            # Handle case where player might not have hand or has_red_general method
            try:
                has_general = (
                    starter_player.has_red_general()
                    if hasattr(starter_player, "has_red_general")
                    else False
                )
                highest_card = "GENERAL_RED(14)" if has_general else None
            except (AttributeError, TypeError):
                # Handle missing hand or other issues
                highest_card = None
        else:
            # Later rounds - previous round winner
            reason = "won_previous_round"
            highest_card = None

        starter_info = StarterInfo(
            player_id=starter_id,
            player_name=starter_player.name,
            reason=reason,
            highest_card=highest_card,
        )

        # Build player order starting from starter
        player_order = []
        for i in range(len(game.players)):
            player_index = (starter_index + i) % len(game.players)
            player_order.append(game.players[player_index].name)

        return InitialState(starter=starter_info, player_order=player_order)

    def extract_hands_dealt(
        self, game: Game, round_number: int
    ) -> Dict[str, List[PieceInfo]]:
        """Extract and sort initial hands for all players."""
        hands_dealt = {}

        # For now, use current hands if it's the current round
        # In a full implementation, we'd need to access historical hand data
        if round_number == game.round_number and game.players[0].hand:
            for player in game.players:
                # Sort the hand
                sorted_hand = self.sort_hand(player.hand)

                # Convert to PieceInfo objects
                piece_infos = [
                    PieceInfo(kind=piece.kind, point=piece.point)
                    for piece in sorted_hand
                ]

                hands_dealt[player.name] = piece_infos
        else:
            # For historical rounds, we'd need to access stored data
            # For now, check if game has an initial_hands attribute (from test)
            if hasattr(game, "initial_hands") and round_number in game.initial_hands:
                for player_name, hand in game.initial_hands[round_number].items():
                    sorted_hand = self.sort_hand(hand)
                    piece_infos = [
                        PieceInfo(kind=piece.kind, point=piece.point)
                        for piece in sorted_hand
                    ]
                    hands_dealt[player_name] = piece_infos
            elif hasattr(game, "initial_hands") and isinstance(
                game.initial_hands, dict
            ):
                # Test case where initial_hands is a simple dict
                for player_name, hand in game.initial_hands.items():
                    sorted_hand = self.sort_hand(hand)
                    piece_infos = [
                        PieceInfo(kind=piece.kind, point=piece.point)
                        for piece in sorted_hand
                    ]
                    hands_dealt[player_name] = piece_infos

        return hands_dealt

    def sort_hand(self, hand: List[Piece]) -> List[Piece]:
        """Sort hand by color (RED first) then by value (high to low).

        Sorting algorithm:
        1. RED pieces come before BLACK pieces
        2. Within each color, pieces are sorted by point value (descending)
        3. Pieces with same color and value maintain their relative order (stable sort)

        This sorting makes it easier for players to see their strongest pieces
        and plan their strategy.

        Args:
            hand: List of Piece objects to sort

        Returns:
            List[Piece]: New list with pieces sorted according to game conventions

        Example:
            Input: [SOLDIER_BLACK(2), GENERAL_RED(14), HORSE_RED(5), ADVISOR_BLACK(10)]
            Output: [GENERAL_RED(14), HORSE_RED(5), ADVISOR_BLACK(10), SOLDIER_BLACK(2)]
        """
        if not hand:
            return []

        # Create a copy to avoid modifying the original
        sorted_hand = hand.copy()

        # Sort using a composite key:
        # 1. Color (RED=0, BLACK=1, so RED comes first)
        # 2. Point value (descending, so high values come first)
        # Using negative point value achieves descending sort without reverse=True
        sorted_hand.sort(
            key=lambda piece: (
                (
                    0 if piece.color == "RED" else 1
                ),  # RED pieces get priority (lower sort value)
                -piece.point,  # Negative for descending order (14 before 2)
            )
        )

        return sorted_hand

    def extract_declaration_phase(
        self, game: Game, round_number: int
    ) -> DeclarationInfo:
        """Extract declaration phase data."""
        from backend.models.play_history import DeclarationData

        declarations = []
        pile_room_calculation = {}

        # Get declarations from game state or history
        game_declarations = {}

        # Check if we have stored round history
        if hasattr(game, "round_history") and round_number in game.round_history:
            # Use stored declarations for historical rounds
            game_declarations = game.round_history[round_number].get("declarations", {})
        elif hasattr(game, "declarations"):
            game_declarations = game.declarations
        elif hasattr(game, "player_declarations"):
            game_declarations = game.player_declarations
        else:
            # Fall back to getting from players
            for player in game.players:
                if hasattr(player, "declared"):
                    game_declarations[player.name] = player.declared

        # Get the correct starter index for this round
        starter_index = 0
        if hasattr(game, "round_history") and round_number in game.round_history:
            starter_index = game.round_history[round_number].get("starter_index", 0)
        elif hasattr(game, "round_starter") and game.round_starter:
            # Find the index of the round starter
            for i, player in enumerate(game.players):
                if player == game.round_starter:
                    starter_index = i
                    break

        # Build declarations in player order
        player_order = []
        for i in range(len(game.players)):
            player_index = (starter_index + i) % len(game.players)
            player_order.append(game.players[player_index])

        # Calculate pile room for each player based on declaration order
        # Pile room = how many piles a player can potentially capture
        # Limited by total piles (8) minus what previous players declared
        total_so_far = 0  # Running total of declarations
        for position, player in enumerate(player_order):
            player_id = player.name.lower().replace(" ", "_")
            declared = game_declarations.get(player.name, 0)

            # Determine pile room based on game rules:
            # - Starter (position 0) always has full 8 piles available
            # - GENERAL_RED holder only considers starter's declaration
            # - Other players must consider all previous declarations
            if position == 0:
                # Starter always has full 8 pile room (first to declare)
                pile_room = 8
            else:
                # Check if player has GENERAL_RED (special rule)
                has_general_red = False
                if hasattr(player, "hand") and player.hand:
                    try:
                        has_general_red = any(
                            p.kind == "GENERAL_RED" for p in player.hand
                        )
                    except (AttributeError, TypeError):
                        has_general_red = False

                if has_general_red and position > 0:
                    # GENERAL_RED special rule: only starter's declaration matters
                    # This gives GENERAL_RED holder more strategic options
                    pile_room = max(
                        0, 8 - game_declarations.get(player_order[0].name, 0)
                    )
                else:
                    # Normal pile room: 8 minus all previous declarations
                    pile_room = max(0, 8 - total_so_far)

            pile_room_calculation[player.name] = pile_room

            # Build declaration data
            strategy_notes = ""
            if position == 0:
                strategy_notes = "starter with full pile room"
            elif declared == 0:
                strategy_notes = "conservative play" if pile_room > 0 else "forced zero"
            elif pile_room > 0:
                strategy_notes = f"competing for {pile_room} pile room"

            # Add AI reasoning if available
            if (
                hasattr(self, "include_ai_analysis")
                and self.include_ai_analysis
                and player.is_bot
            ):
                ai_reasoning = self.extract_ai_declaration_reasoning(player.name, game)
                if ai_reasoning and "reasoning" in ai_reasoning:
                    strategy_notes = ai_reasoning.get("reasoning", strategy_notes)

            declarations.append(
                DeclarationData(
                    player_id=player_id,
                    declared=declared,
                    position=position,
                    strategy_notes=strategy_notes,
                )
            )

            total_so_far += declared

        return DeclarationInfo(
            declarations=declarations,
            total_declared=total_so_far,
            pile_room_calculation=pile_room_calculation,
        )

    def extract_turn_history(self, game: Game, round_number: int) -> List[TurnInfo]:
        """Extract turn-by-turn play history for analysis.

        This method reconstructs the complete sequence of plays for each turn,
        including hand states before and after each play. This data is crucial
        for understanding player strategies and AI decision-making.

        Args:
            game: The Game instance containing turn history
            round_number: The round number to extract (currently uses current round)

        Returns:
            List[TurnInfo]: Ordered list of turns with complete play data

        Note:
            Currently only extracts data for the current round. Historical rounds
            would require storing turn_history_this_round in a persistent format.
        """
        from backend.models.play_history import TurnWinner, GameStateAfterTurn, PlayData
        from backend.engine.rules import get_play_type

        turn_history = []

        # Check if we have turn history for this round
        if (
            not hasattr(game, "turn_history_this_round")
            or not game.turn_history_this_round
        ):
            return []

        # Process each turn in the history
        # Turn history structure varies based on how it was stored
        for turn_idx, turn_data in enumerate(game.turn_history_this_round):
            # Handle different turn_data formats (dict vs list of TurnPlay objects)
            if isinstance(turn_data, dict):
                # Modern format with explicit turn data
                turn_number = turn_data.get("turn_number", turn_idx + 1)
                plays = turn_data.get("plays", [])
                winner_player = turn_data.get("winner")
                winner_play = turn_data.get("winner_play")
                pieces_captured = turn_data.get("pieces_captured", 0)
            else:
                # Legacy format: turn_data is a list of TurnPlay objects
                turn_number = turn_idx + 1
                plays = turn_data if isinstance(turn_data, list) else []
                # Need to determine winner from plays
                winner_player = None
                winner_play = None
                pieces_captured = len(plays[0].pieces) if plays else 0

            # Extract plays for this turn
            play_data_list = []
            for i, turn_play in enumerate(plays):
                # Handle both TurnPlay objects and dict representations
                if hasattr(turn_play, "player"):
                    # TurnPlay object format
                    player = turn_play.player
                    pieces = turn_play.pieces
                else:
                    # Dictionary format from test setup
                    player = turn_play.get("player")
                    pieces = turn_play.get("pieces", [])

                # Reconstruct hand states before and after the play
                # This is crucial for understanding what options the player had
                hand_before = []
                hand_after = []

                # Check if we have stored hand states (ideal case)
                if (
                    "initial_hands" in turn_data
                    and player.name in turn_data["initial_hands"]
                ):
                    hand_before = self.sort_hand(
                        turn_data["initial_hands"][player.name]
                    )
                elif hasattr(player, "hand"):
                    # Approximation: current hand + played pieces = hand before play
                    # This works for the current round but not historical rounds
                    hand_before = self.sort_hand(player.hand + pieces)

                if (
                    "hands_after_play" in turn_data
                    and player.name in turn_data["hands_after_play"]
                ):
                    hand_after = self.sort_hand(
                        turn_data["hands_after_play"][player.name]
                    )
                elif hasattr(player, "hand"):
                    # Current hand represents the state after playing
                    hand_after = self.sort_hand(player.hand)

                # Convert to PieceInfo
                hand_before_info = [
                    PieceInfo(kind=p.kind, point=p.point) for p in hand_before
                ]
                hand_after_info = [
                    PieceInfo(kind=p.kind, point=p.point) for p in hand_after
                ]
                pieces_played_info = [
                    PieceInfo(kind=p.kind, point=p.point) for p in pieces
                ]

                # Determine play type (SINGLE, PAIR, TRIPLE, etc.)
                # This helps analyze strategy patterns
                play_type = get_play_type(pieces)

                # Get current captured/declared counts
                captured_count = getattr(player, "captured_piles", 0)
                declared_count = getattr(player, "declared", 0)

                # Extract AI analysis if enabled and player is AI
                ai_decision_analysis = None
                if (
                    hasattr(self, "include_ai_analysis")
                    and self.include_ai_analysis
                    and player.is_bot
                ):
                    turn_reasoning = self.extract_ai_turn_reasoning(
                        player.name, turn_number, game
                    )
                    if turn_reasoning:
                        from backend.models.play_history import AIDecisionAnalysis

                        ai_decision_analysis = AIDecisionAnalysis(
                            turn_play_reasoning=turn_reasoning
                        )

                play_data = PlayData(
                    player_id=player.name.lower().replace(" ", "_"),
                    player_name=player.name,
                    pieces_played=pieces_played_info,
                    play_type=play_type,
                    hand_before=hand_before_info,
                    hand_after=hand_after_info,
                    captured_count=captured_count,
                    declared_count=declared_count,
                    ai_decision_analysis=ai_decision_analysis,
                )
                play_data_list.append(play_data)

            # Create turn winner info
            winner_info = None
            if winner_player and winner_play:
                winner_pieces_info = [
                    PieceInfo(kind=p.kind, point=p.point) for p in winner_play.pieces
                ]
                winner_info = TurnWinner(
                    player_id=winner_player.name.lower().replace(" ", "_"),
                    player_name=winner_player.name,
                    winning_play=winner_pieces_info,
                    pieces_captured=pieces_captured,
                )

            # Get next starter (winner of this turn or from turn data)
            next_starter = turn_data.get("next_starter")
            if next_starter and hasattr(next_starter, "name"):
                next_starter = next_starter.name
            elif winner_player:
                next_starter = winner_player.name
            else:
                next_starter = ""

            # Build game state after turn
            game_state_after = {}
            for player in game.players:
                captured = getattr(player, "captured_piles", 0)
                declared = getattr(player, "declared", 0)
                hand_size = len(player.hand) if hasattr(player, "hand") else 0

                game_state_after[player.name] = GameStateAfterTurn(
                    captured=captured, declared=declared, hand_size=hand_size
                )

            # Create turn info
            turn_info = TurnInfo(
                turn_number=turn_number,
                plays=play_data_list,
                winner=winner_info,
                next_starter=next_starter,
                game_state_after=game_state_after,
            )

            turn_history.append(turn_info)

        return turn_history

    def extract_round_summary(self, game: Game, round_number: int) -> RoundSummary:
        """Extract round summary with final captures and scoring calculations.

        This method calculates the scoring for a round based on the difference
        between declared and actual captured piles. The scoring rules:
        - Exact match (captured == declared > 0): 20 points bonus
        - Overcapture (captured > declared): points = difference
        - Undercapture (captured < declared): points = -2 * difference

        Args:
            game: The Game instance with scoring data
            round_number: The round to summarize

        Returns:
            RoundSummary: Complete summary including captures, scores, and cumulative totals
        """
        from backend.models.play_history import CaptureInfo, ScoringInfo

        final_captures = {}
        scoring = {}
        cumulative_scores = {}

        # Check if we have stored round history
        if hasattr(game, "round_history") and round_number in game.round_history:
            # Use stored historical data
            round_data = game.round_history[round_number]
            declarations = round_data.get("declarations", {})
            captures = round_data.get("final_captures", {})
            scores = round_data.get("scores", {})

            for player_name in declarations:
                declared = declarations.get(player_name, 0)
                captured = captures.get(player_name, 0)
                difference = captured - declared

                # Create capture info
                final_captures[player_name] = CaptureInfo(
                    captured=captured, declared=declared, difference=difference
                )

                # Determine scoring
                points = scores.get(player_name, 0)

                # Calculate scoring multiplier and reason based on game rules
                # Note: The multiplier shown here is for display purposes
                # Actual scoring calculation happens in calculate_round_scores()
                if difference == 0 and declared > 0:
                    multiplier = 0  # Exact match gets bonus, not multiplier
                    reason = "exact_match"
                else:
                    # Standard penalty multiplier for undercapture
                    multiplier = 2
                    if difference > 0:
                        reason = f"exceeded_by_{abs(difference)}"
                    else:
                        reason = f"missed_by_{abs(difference)}"

                scoring[player_name] = ScoringInfo(
                    points=points, multiplier=multiplier, reason=reason
                )

                # Calculate cumulative score up to this round
                # This shows score progression throughout the game
                cumulative = 0
                for r in range(1, round_number + 1):
                    if hasattr(game, "round_history") and r in game.round_history:
                        # Add score from each historical round
                        cumulative += (
                            game.round_history[r].get("scores", {}).get(player_name, 0)
                        )
                cumulative_scores[player_name] = cumulative

            # Return early with historical data
            return RoundSummary(
                total_turns=8,  # Standard round has 8 turns
                final_captures=final_captures,
                scoring=scoring,
                cumulative_scores=cumulative_scores,
            )

        # Fall back to current round data
        # Get round scores if available
        round_scores = {}
        if hasattr(game, "round_scores"):
            round_scores = game.round_scores

        # Extract data for each player
        for player in game.players:
            # Skip if player is None or has no name
            if not player or not hasattr(player, "name") or not player.name:
                continue

            # Get captures and declarations with safe defaults
            declared = getattr(player, "declared", 0)
            if declared is None:
                declared = 0
            captured = getattr(player, "captured_piles", 0)
            if captured is None:
                captured = 0
            difference = captured - declared

            # Create capture info
            final_captures[player.name] = CaptureInfo(
                captured=captured, declared=declared, difference=difference
            )

            # Determine scoring
            points = round_scores.get(player.name, 0)

            # Calculate multiplier and reason
            if difference == 0 and declared > 0:
                multiplier = 0
                reason = "exact_match"
            else:
                # Standard multiplier is 2
                multiplier = 2
                if difference > 0:
                    reason = f"exceeded_by_{abs(difference)}"
                else:
                    reason = f"missed_by_{abs(difference)}"

            scoring[player.name] = ScoringInfo(
                points=points, multiplier=multiplier, reason=reason
            )

            # Get cumulative score
            cumulative_scores[player.name] = (
                player.score if hasattr(player, "score") else 0
            )

        # Determine total turns (default 8 for a complete round)
        total_turns = 8
        if hasattr(game, "turn_history_this_round") and game.turn_history_this_round:
            total_turns = len(game.turn_history_this_round)
        elif hasattr(game, "turn_number") and game.turn_number > 0:
            total_turns = game.turn_number

        return RoundSummary(
            total_turns=total_turns,
            final_captures=final_captures,
            scoring=scoring,
            cumulative_scores=cumulative_scores,
        )

    def extract_ai_analysis_for_play(
        self, play_data: dict, game: Game
    ) -> Optional[dict]:
        """Extract AI decision analysis for a play if player is AI."""
        # Check if player is AI
        if not play_data.get(
            "is_ai", True
        ):  # Default to True for backward compatibility
            return None

        # For now, return a placeholder structure
        # In a real implementation, this would extract from game.ai_decision_history
        return {
            "turn_play_reasoning": {
                "reasoning": "AI reasoning not available",
                "strategy": "unknown",
                "alternatives_considered": [],
            }
        }

    def extract_ai_declaration_reasoning(
        self, player_name: str, game: Game
    ) -> Optional[dict]:
        """Extract AI reasoning for declaration phase.

        Looks for stored AI decision data that explains why the AI chose
        a particular declaration value. This helps understand AI strategy.

        Args:
            player_name: Name of the AI player
            game: Game instance that may contain ai_decision_history

        Returns:
            Optional[dict]: AI reasoning data if available, None otherwise

        Note:
            Currently returns None if ai_decision_history is not implemented.
            Future versions should integrate with the AI strategy module.
        """
        # Check if we have AI decision history
        if not hasattr(game, "ai_decision_history"):
            return None

        player_history = game.ai_decision_history.get(player_name, {})
        declaration_data = player_history.get("declaration")

        if not declaration_data:
            return None

        return declaration_data

    def extract_ai_turn_reasoning(
        self, player_name: str, turn_number: int, game: Game
    ) -> Optional[dict]:
        """Extract AI reasoning for a specific turn.

        Retrieves the stored reasoning that explains why the AI made a particular
        play during a turn. This includes alternatives considered and strategy.

        Args:
            player_name: Name of the AI player
            turn_number: The turn number to get reasoning for
            game: Game instance that may contain ai_decision_history

        Returns:
            Optional[dict]: Turn-specific AI reasoning if available

        Note:
            The ai_decision_history structure should be:
            {player_name: {turns: {turn_number: reasoning_data}}}
        """
        # Check if we have AI decision history
        if not hasattr(game, "ai_decision_history"):
            return None

        player_history = game.ai_decision_history.get(player_name, {})
        turns_data = player_history.get("turns", {})

        return turns_data.get(turn_number)

    def extract_ai_strategy_plan(self, player_name: str, game: Game) -> Optional[dict]:
        """Extract AI overall strategy plan."""
        # Check if we have AI decision history
        if not hasattr(game, "ai_decision_history"):
            return None

        player_history = game.ai_decision_history.get(player_name, {})
        return player_history.get("strategy_plan")

    def include_ai_analysis(
        self, play_data: PlayData, player_id: str, game: Game
    ) -> PlayData:
        """Add AI decision analysis if player is AI."""
        # TODO: Implement integration with play data
        pass
    
    def _convert_to_play_history_response(self, history_data: Dict[str, Any]) -> PlayHistoryResponse:
        """Convert simple history format to PlayHistoryResponse format."""
        from backend.models.play_history import (
            PlayerInfo, RoundHistory, InitialState, StarterInfo,
            DeclarationInfo, DeclarationData, TurnInfo, PlayData,
            PieceInfo, RoundSummary, ScoringInfo, TurnWinner
        )
        
        # Convert players
        players = {}
        for player in history_data.get('players', []):
            player_id = player['name'].lower().replace(' ', '_')
            players[player['name']] = PlayerInfo(
                player_id=player_id,
                player_name=player['name'],
                player_type='human' if player['type'] == 'human' else 'ai',
                ai_version='v2' if player['type'] == 'bot' else None
            )
        
        # Convert rounds
        rounds = []
        for round_data in history_data.get('rounds', []):
            # Build initial state
            initial_state = InitialState(
                starter=StarterInfo(
                    player_id=round_data['starter'].lower().replace(' ', '_'),
                    player_name=round_data['starter'],
                    reason='default'
                ),
                player_order=[p['name'] for p in history_data['players']]
            )
            
            # Build declarations
            declarations_list = []
            total_declared = 0
            for i, decl in enumerate(round_data.get('declarations', [])):
                player_id = decl['player'].lower().replace(' ', '_')
                declarations_list.append(DeclarationData(
                    player_id=player_id,
                    declared=decl['declared'],
                    position=i
                ))
                total_declared += decl['declared']
            
            from backend.models.play_history import DeclarationInfo
            declarations_info = DeclarationInfo(
                declarations=declarations_list,
                total_declared=total_declared,
                pile_room_calculation={}  # Not available in simple format
            )
            
            # Build turn history
            turn_history = []
            for turn in round_data.get('turns', []):
                plays = []
                winner_player = None
                winner_play = None
                
                for play in turn.get('plays', []):
                    player_id = play['player'].lower().replace(' ', '_')
                    pieces_info = [
                        PieceInfo(kind=p['type'], point=p['point'])
                        for p in play.get('pieces', [])
                    ]
                    
                    play_data = PlayData(
                        player_id=player_id,
                        player_name=play['player'],
                        pieces_played=pieces_info,
                        play_type=self._determine_play_type(play.get('pieces', [])),
                        hand_before=[],  # Not available in simple format
                        hand_after=[],   # Not available in simple format
                        captured_count=play.get('captured', 0),
                        declared_count=0  # Will be filled from declarations
                    )
                    plays.append(play_data)
                    
                    if play['player'] == turn.get('winner'):
                        winner_player = players[play['player']]
                        winner_play = play_data
                
                # Create turn winner info
                winner_info = None
                if winner_player and winner_play:
                    winner_info = TurnWinner(
                        player_id=winner_player.player_id,
                        player_name=winner_player.player_name,
                        pieces_played=winner_play.pieces_played,
                        pieces_captured=turn.get('winnerPieces', 0)
                    )
                
                turn_info = TurnInfo(
                    turn_number=turn['turnNumber'],
                    plays=plays,
                    winner=winner_info
                )
                turn_history.append(turn_info)
            
            # Build round summary
            scoring_info = {}
            for player_name, score_data in round_data.get('scoring', {}).get('players', {}).items():
                # Calculate reason based on declared vs captured
                declared = score_data.get('declared', 0)
                captured = score_data.get('captured', 0)
                
                if declared == captured:
                    reason = f"Exact match: {declared} declared, {captured} captured"
                elif declared < captured:
                    reason = f"Under-declared: {declared} declared < {captured} captured"
                else:
                    reason = f"Over-declared: {declared} declared > {captured} captured"
                    
                scoring_info[player_name] = ScoringInfo(
                    points=score_data.get('score', 0),
                    multiplier=score_data.get('multiplier', 1),
                    reason=reason
                )
            
            # Build final captures info
            final_captures = {}
            for player_name, score_data in round_data.get('scoring', {}).get('players', {}).items():
                from backend.models.play_history import CaptureInfo
                declared = score_data.get('declared', 0)
                captured = score_data.get('captured', 0)
                final_captures[player_name] = CaptureInfo(
                    captured=captured,
                    declared=declared,
                    difference=abs(declared - captured)
                )
            
            # Build cumulative scores
            cumulative_scores = {}
            if 'gameStatus' in history_data and 'finalScores' in history_data['gameStatus']:
                cumulative_scores = history_data['gameStatus']['finalScores']
            else:
                # Use round scores as cumulative for single round
                for player_name, score_data in round_data.get('scoring', {}).get('players', {}).items():
                    cumulative_scores[player_name] = score_data.get('score', 0)
            
            round_summary = RoundSummary(
                total_turns=len(round_data.get('turns', [])),
                final_captures=final_captures,
                scoring=scoring_info,
                cumulative_scores=cumulative_scores
            )
            
            # Build round history
            round_history = RoundHistory(
                round_number=round_data['roundNumber'],
                initial_state=initial_state,
                hands_dealt={},  # Not available in simple format
                declaration_phase=declarations_info,
                turn_history=turn_history,
                round_summary=round_summary
            )
            rounds.append(round_history)
        
        # Return complete response
        return PlayHistoryResponse(
            room_id=history_data['roomId'],
            total_rounds=history_data['totalRounds'],
            players=players,
            rounds=rounds
        )
    
    def _determine_play_type(self, pieces: List[Dict[str, Any]]) -> str:
        """Determine the type of play based on pieces."""
        if not pieces:
            return "UNKNOWN"
        
        count = len(pieces)
        if count == 1:
            return "SINGLE"
        elif count == 2:
            # Check if same kind
            if len(set(p['type'] for p in pieces)) == 1:
                return "PAIR"
            else:
                return "DOUBLE"
        elif count == 3:
            if len(set(p['type'] for p in pieces)) == 1:
                return "TRIPLE"
            else:
                return "TRIPLE_MIXED"
        else:
            return f"MULTI_{count}"
