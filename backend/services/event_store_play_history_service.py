"""
Event Store Play History Service
Extracts play history from SQLite event store for complete game history
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import logging

from backend.models.play_history import (
    PlayerInfo, InitialState, PieceInfo, DeclarationInfo,
    PlayData, TurnInfo, RoundSummary, RoundHistory, PlayHistoryResponse,
    StarterInfo, DeclarationData, TurnWinner, GameStateAfterTurn,
    CaptureInfo, ScoringInfo, AIDecisionAnalysis
)
from backend.api.services.event_store import GameEvent, event_store
from backend.engine.piece import Piece

logger = logging.getLogger(__name__)


def get_play_type_from_dicts(pieces: List[Dict[str, Any]]) -> str:
    """Determine play type from piece dictionaries"""
    if not pieces:
        return "UNKNOWN"

    count = len(pieces)
    if count == 1:
        return "SINGLE"
    elif count == 2:
        # Check if same kind
        if pieces[0]["kind"] == pieces[1]["kind"]:
            return "PAIR"
        else:
            return "DOUBLE"
    elif count == 3:
        # Check if all same kind
        if all(p["kind"] == pieces[0]["kind"] for p in pieces):
            # Check if all soldiers
            if "SOLDIER" in pieces[0]["kind"]:
                return "THREE_OF_A_KIND"
            else:
                return "TRIPLE"
        else:
            return "TRIPLE"
    elif count == 4:
        return "QUADRUPLE"
    elif count == 5:
        return "QUINTUPLE"
    elif count == 6:
        return "SEXTUPLE"
    else:
        return "MULTIPLE"


class EventStorePlayHistoryService:
    """Extract play history from SQLite event store"""

    def __init__(self):
        # Use the same path calculation as EventStore to ensure we use the same database
        from pathlib import Path
        current_dir = Path(__file__).resolve()
        # backend/services/event_store_play_history_service.py -> project_root
        project_root = current_dir.parent.parent.parent
        self.db_path = str(project_root / "game_events.db")
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def build_play_history_from_events(
        self,
        room_id: str,
        include_ai_analysis: bool = True,
        format: Optional[str] = None
    ) -> PlayHistoryResponse:
        """
        Build complete play history from event store

        Args:
            room_id: The room identifier
            include_ai_analysis: Whether to include AI analysis
            format: Response format (None or "compact")

        Returns:
            PlayHistoryResponse with complete game history
        """
        # Check cache first
        cache_key = f"{room_id}:{format}:{include_ai_analysis}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.info(f"Cache hit for room {room_id}")
                return cached_data

        logger.info(f"Building play history from events for room {room_id}")

        # Get all events for the room
        events = await event_store.get_room_events(room_id)

        if not events:
            return PlayHistoryResponse(
                room_id=room_id,
                total_rounds=0,
                players={},
                rounds=[]
            )

        # Extract player information
        players = self._extract_players_from_events(events)

        # Find round boundaries
        round_boundaries = self._find_round_boundaries(events)

        # Extract data for each round
        rounds = []
        for round_num, (start_idx, end_idx) in enumerate(round_boundaries, 1):
            round_events = events[start_idx:end_idx+1]

            if format == "compact":
                round_history = self._build_compact_round_from_events(
                    round_events, round_num, players
                )
            else:
                round_history = self._build_round_from_events(
                    round_events, round_num, players, include_ai_analysis
                )

            if round_history:
                rounds.append(round_history)

        # Build response
        response = PlayHistoryResponse(
            room_id=room_id,
            total_rounds=len(rounds),
            players=players,
            rounds=rounds
        )

        # Cache the result
        self._cache[cache_key] = (response, time.time())

        return response

    def _extract_players_from_events(self, events: List[GameEvent]) -> Dict[str, PlayerInfo]:
        """Extract player information from events"""
        players = {}

        for event in events:
            if event.event_type == "phase_change" and event.payload.get("phase") == "preparation":
                game_players = event.payload.get("players", {})
                for player_name, player_data in game_players.items():
                    if player_name not in players:
                        player_id = player_name.lower().replace(" ", "_")
                        is_bot = player_data.get("is_bot", True)

                        players[player_name] = PlayerInfo(
                            player_id=player_id,
                            player_name=player_name,
                            player_type="ai" if is_bot else "human",
                            ai_version="v2" if is_bot else None
                        )
                break  # Only need first preparation phase

        return players

    def _find_round_boundaries(self, events: List[GameEvent]) -> List[tuple]:
        """Find the start and end event indices for each round"""
        boundaries = []
        current_round_start = 0

        for i, event in enumerate(events):
            # Round ends at scoring phase
            if event.event_type == "phase_change" and event.payload.get("phase") == "scoring":
                # Find next preparation phase or end of events
                round_end = i
                for j in range(i + 1, len(events)):
                    if events[j].event_type == "phase_change" and events[j].payload.get("phase") == "preparation":
                        boundaries.append((current_round_start, round_end))
                        current_round_start = j
                        break
                else:
                    # No more preparation phases - this is the last round
                    boundaries.append((current_round_start, len(events) - 1))
                    break

        # Handle case where game didn't reach scoring yet
        if not boundaries and events:
            boundaries.append((0, len(events) - 1))

        return boundaries

    def _build_round_from_events(
        self,
        events: List[GameEvent],
        round_num: int,
        players: Dict[str, PlayerInfo],
        include_ai_analysis: bool
    ) -> RoundHistory:
        """Build complete round history from events"""
        initial_state = self._extract_initial_state(events, round_num)
        hands_dealt = self._extract_hands_dealt(events)
        declaration_phase = self._extract_declaration_phase(events, players)
        turn_history = self._extract_turn_history(events, include_ai_analysis)
        round_summary = self._extract_round_summary(events, players)

        return RoundHistory(
            round_number=round_num,
            initial_state=initial_state,
            hands_dealt=hands_dealt,
            declaration_phase=declaration_phase,
            turn_history=turn_history,
            round_summary=round_summary
        )

    def _build_compact_round_from_events(
        self,
        events: List[GameEvent],
        round_num: int,
        players: Dict[str, PlayerInfo]
    ) -> RoundHistory:
        """Build compact round history (minimal data)"""
        initial_state = self._extract_initial_state(events, round_num)
        declaration_phase = self._extract_declaration_phase(events, players)
        round_summary = self._extract_round_summary(events, players)

        return RoundHistory(
            round_number=round_num,
            initial_state=initial_state,
            hands_dealt={},  # Empty for compact
            declaration_phase=declaration_phase,
            turn_history=[],  # Empty for compact
            round_summary=round_summary
        )

    def _extract_initial_state(self, events: List[GameEvent], round_num: int) -> InitialState:
        """Extract initial state from events"""
        starter = None
        starter_reason = "default"
        player_order = []

        # Look for hands_dealt event
        for event in events:
            if event.event_type == "hands_dealt":
                data = event.payload
                starter = data.get("starter")
                starter_reason = data.get("starter_reason", "default")

                # Ensure starter_reason is never None
                if starter_reason is None:
                    starter_reason = "default"

                # Extract player order from hands data
                if data.get("hands"):
                    player_order = list(data["hands"].keys())
                    # Rotate to start with starter
                    if starter and starter in player_order:
                        starter_idx = player_order.index(starter)
                        player_order = player_order[starter_idx:] + player_order[:starter_idx]
                break

        # Fallback: extract from phase_change events or declarations
        if not starter:
            for event in events:
                if event.event_type == "phase_change":
                    game_context = event.payload.get("game_context", {})
                    if game_context.get("current_player"):
                        starter = game_context["current_player"]
                        break

        # Extract player order from declaration phase if not found
        if not player_order:
            declaration_order = []
            for event in events:
                # Look for phase_data_update events that contain player declarations
                if event.event_type == "phase_data_update":
                    phase_data = event.payload.get("updates", {})
                    if "declarations" in phase_data:
                        declarations = phase_data["declarations"]
                        for player_name in declarations:
                            if player_name and player_name not in declaration_order:
                                declaration_order.append(player_name)

            if declaration_order and starter:
                # Rotate to start with starter
                if starter in declaration_order:
                    starter_idx = declaration_order.index(starter)
                    player_order = declaration_order[starter_idx:] + declaration_order[:starter_idx]
                else:
                    player_order = declaration_order
            elif declaration_order:
                player_order = declaration_order

        # Final fallback: extract from phase_change events with player data
        if not player_order:
            for event in events:
                if event.event_type == "phase_change":
                    players_data = event.payload.get("players", {})
                    if players_data:
                        player_order = list(players_data.keys())
                        break

        # Create starter info
        starter_info = StarterInfo(
            player_id=starter.lower().replace(" ", "_") if starter else "unknown",
            player_name=starter or "Unknown",
            reason=starter_reason,
            highest_card="GENERAL_RED(14)" if starter_reason == "has_general_red" else None
        )

        return InitialState(
            starter=starter_info,
            player_order=player_order
        )

    def _extract_hands_dealt(self, events: List[GameEvent]) -> Dict[str, List[PieceInfo]]:
        """Extract initial hands from events"""
        hands = {}

        # Look for hands_dealt event
        for event in events:
            if event.event_type == "hands_dealt":
                hands_data = event.payload.get("hands", {})
                for player_name, hand in hands_data.items():
                    # Sort hand by color (RED first) then by value (high to low)
                    sorted_hand = sorted(
                        hand,
                        key=lambda p: (
                            0 if "RED" in p["kind"] else 1,
                            -p["point"]
                        )
                    )
                    hands[player_name] = [
                        PieceInfo(kind=p["kind"], point=p["point"])
                        for p in sorted_hand
                    ]
                break

        return hands

    def _extract_declaration_phase(
        self,
        events: List[GameEvent],
        players: Dict[str, PlayerInfo]
    ) -> DeclarationInfo:
        """Extract declaration phase data from events"""
        declarations = []
        pile_room_calculation = {}
        total_declared = 0

        # Extract declarations from phase_data_update events
        declaration_map = {}
        for event in events:
            if event.event_type == "phase_data_update":
                phase_data = event.payload.get("updates", {})
                if "declarations" in phase_data:
                    event_declarations = phase_data["declarations"]
                    for player_name, declared_value in event_declarations.items():
                        declaration_map[player_name] = declared_value

        # Build declarations in player order
        player_order = list(players.keys())
        running_total = 0

        for position, player_name in enumerate(player_order):
            declared = declaration_map.get(player_name, 0)

            # Simple pile room calculation
            if position == 0:
                pile_room = 8
            else:
                pile_room = max(0, 8 - running_total)

            pile_room_calculation[player_name] = pile_room

            # Strategy notes
            strategy_notes = ""
            if position == 0:
                strategy_notes = "starter with full pile room"
            elif declared == 0:
                strategy_notes = "conservative play" if pile_room > 0 else "forced zero"
            else:
                strategy_notes = f"competing for {pile_room} pile room"

            declarations.append(DeclarationData(
                player_id=player_name.lower().replace(" ", "_"),
                declared=declared,
                position=position,
                strategy_notes=strategy_notes
            ))

            running_total += declared
            total_declared += declared

        return DeclarationInfo(
            declarations=declarations,
            total_declared=total_declared,
            pile_room_calculation=pile_room_calculation
        )

    def _extract_turn_history(
        self,
        events: List[GameEvent],
        include_ai_analysis: bool
    ) -> List[TurnInfo]:
        """Extract turn-by-turn play history from events"""
        turns = []
        current_turn_plays = []
        turn_number = 1
        turn_declarations = {}  # Store declared counts

        # First, extract initial hands from hands_dealt event
        player_hands = {}  # Current hand for each player
        initial_hands = {}  # Store initial hands for reference

        for event in events:
            if event.event_type == "hands_dealt":
                hands_data = event.payload.get("hands", {})
                for player_name, pieces in hands_data.items():
                    # Convert to PieceInfo objects for easier comparison
                    hand_pieces = [
                        {"kind": p["kind"], "point": p["point"]} for p in pieces
                    ]
                    player_hands[player_name] = hand_pieces.copy()
                    initial_hands[player_name] = hand_pieces.copy()
                break

        # Extract declarations from phase_data_update events
        for event in events:
            if event.event_type == "phase_data_update":
                phase_data = event.payload.get("updates", {})
                if "declarations" in phase_data:
                    event_declarations = phase_data["declarations"]
                    for player_name, declared_value in event_declarations.items():
                        turn_declarations[player_name] = declared_value

        # Track game state
        player_pieces_played = {}  # Track total pieces played per player
        player_captured = {}  # Track captured piles per player

        # Initialize player states
        for player_name in turn_declarations:
            player_pieces_played[player_name] = 0
            player_captured[player_name] = 0

        # Helper to update captured counts from phase_change events
        def update_captured_from_event(event):
            if event.event_type == "phase_change":
                players_data = event.payload.get("players", {})
                for player_name, player_info in players_data.items():
                    if isinstance(player_info, dict) and "captured_piles" in player_info:
                        player_captured[player_name] = player_info["captured_piles"]

        for i, event in enumerate(events):
            # Update captured counts from phase_change events
            update_captured_from_event(event)

            if event.event_type == "phase_data_update":
                # Check for turn_plays data in phase updates
                phase_data = event.payload.get("updates", {})
                if "turn_plays" in phase_data:
                    turn_plays = phase_data["turn_plays"]

                    # Process any new plays in this update
                    for player_name, play_data in turn_plays.items():
                        # Skip if we've already processed this play
                        if any(p.player_name == player_name for p in current_turn_plays):
                            continue

                        pieces_raw = play_data.get("pieces", [])
                        
                        # Convert piece strings to dictionaries
                        pieces = []
                        for piece_str in pieces_raw:
                            # Parse strings like "ADVISOR_BLACK(11)" or "GENERAL_RED(14)"
                            if isinstance(piece_str, str) and "(" in piece_str and ")" in piece_str:
                                kind = piece_str[:piece_str.index("(")]
                                point = int(piece_str[piece_str.index("(")+1:piece_str.index(")")])
                                pieces.append({"kind": kind, "point": point})
                            elif isinstance(piece_str, dict):
                                # Already a dictionary
                                pieces.append(piece_str)
                            else:
                                # Unknown format, skip
                                continue

                        # Track pieces played
                        if player_name in player_pieces_played:
                            player_pieces_played[player_name] += len(pieces)

                        # Calculate hand_before (current hand)
                        hand_before = []
                        if player_name in player_hands:
                            hand_before = [
                                PieceInfo(kind=p["kind"], point=p["point"])
                                for p in player_hands[player_name]
                            ]

                        # Remove played pieces from player's hand
                        hand_after_data = player_hands.get(player_name, []).copy()
                        for played_piece in pieces:
                            # Find and remove the played piece from hand
                            for j, hand_piece in enumerate(hand_after_data):
                                if (hand_piece["kind"] == played_piece["kind"] and
                                    hand_piece["point"] == played_piece["point"]):
                                    hand_after_data.pop(j)
                                    break

                        # Update player's current hand
                        if player_name in player_hands:
                            player_hands[player_name] = hand_after_data

                        # Convert hand_after to PieceInfo objects
                        hand_after = [
                            PieceInfo(kind=p["kind"], point=p["point"])
                            for p in hand_after_data
                        ]

                        play_data_obj = PlayData(
                            player_id=player_name.lower().replace(" ", "_"),
                            player_name=player_name,
                            pieces_played=[
                                PieceInfo(kind=p["kind"], point=p["point"])
                                for p in pieces
                            ],
                            play_type=get_play_type_from_dicts(pieces) if pieces else "UNKNOWN",
                            hand_before=hand_before,
                            hand_after=hand_after,
                            captured_count=player_captured.get(player_name, 0),
                            declared_count=turn_declarations.get(player_name, 0),
                            ai_decision_analysis=None
                        )
                        current_turn_plays.append(play_data_obj)

                # Also check if turn completed in same event
                if phase_data.get("turn_complete") and current_turn_plays:
                    current_turn_num = phase_data.get("current_turn_number", turn_number)

                    # Look ahead for winner event
                    winner_info = None
                    next_starter = ""

                    # Search for the winner event that follows this turn completion
                    for j in range(i + 1, min(i + 10, len(events))):
                        next_event = events[j]
                        if (next_event.event_type == "phase_data_update" and
                            next_event.payload.get("updates", {}).get("winner")):
                            winner_data = next_event.payload.get("updates", {})
                            winner_name = winner_data.get("winner")
                            piles_won = winner_data.get("piles_won", 1)
                            next_starter = winner_data.get("next_turn_starter", winner_name)

                            # Also look for updated captured counts in following events
                            for k in range(j, min(j + 5, len(events))):
                                update_captured_from_event(events[k])

                            # Find winner's play
                            winner_play = next(
                                (p for p in current_turn_plays if p.player_name == winner_name),
                                None
                            )
                            if winner_play:
                                winner_info = TurnWinner(
                                    player_id=winner_name.lower().replace(" ", "_"),
                                    player_name=winner_name,
                                    winning_play=winner_play.pieces_played,
                                    pieces_captured=piles_won
                                )
                            break

                    # Calculate game state after turn
                    game_state_after = {}
                    for player_name in turn_declarations:
                        game_state_after[player_name] = GameStateAfterTurn(
                            captured=player_captured.get(player_name, 0),
                            declared=turn_declarations.get(player_name, 0),
                            hand_size=8 - player_pieces_played.get(player_name, 0)
                        )

                    turn = TurnInfo(
                        turn_number=current_turn_num,
                        plays=current_turn_plays,
                        winner=winner_info,
                        next_starter=next_starter,
                        game_state_after=game_state_after
                    )
                    turns.append(turn)

                    # Reset for next turn
                    current_turn_plays = []
                    turn_number += 1

        return turns

    def _extract_round_summary(
        self,
        events: List[GameEvent],
        players: Dict[str, PlayerInfo]
    ) -> RoundSummary:
        """Extract round summary from events"""
        final_captures = {}
        scoring = {}
        cumulative_scores = {}
        total_turns = 8  # Default

        # Look for scoring phase data
        for event in reversed(events):  # Start from end
            if event.event_type == "phase_change" and event.payload.get("phase") == "scoring":
                phase_data = event.payload.get("phase_data", {})

                # Extract captures and scores
                round_scores = phase_data.get("round_scores", {})
                total_scores = phase_data.get("total_scores", {})

                # Also check players data for captured_piles
                players_data = event.payload.get("players", {})

                for player_name in players:
                    # Get score data from round_scores
                    score_data = round_scores.get(player_name, {})
                    if isinstance(score_data, dict):
                        declared = score_data.get("declared", 0)
                        captured = score_data.get("actual", 0)
                        score = score_data.get("final_score", 0)
                    else:
                        # Fallback to player data
                        player_info = players_data.get(player_name, {})
                        declared = player_info.get("declared", 0)
                        captured = player_info.get("captured_piles", 0)
                        score = player_info.get("score", 0)

                    total_score = total_scores.get(player_name, score)

                    difference = captured - declared

                    final_captures[player_name] = CaptureInfo(
                        captured=captured,
                        declared=declared,
                        difference=difference
                    )

                    # Determine scoring reason
                    if difference == 0 and declared > 0:
                        reason = "exact_match"
                        multiplier = 0
                    elif difference > 0:
                        reason = f"exceeded_by_{abs(difference)}"
                        multiplier = 1
                    else:
                        reason = f"missed_by_{abs(difference)}"
                        multiplier = 2

                    scoring[player_name] = ScoringInfo(
                        points=score,
                        multiplier=multiplier,
                        reason=reason
                    )

                    cumulative_scores[player_name] = total_score

                break

        return RoundSummary(
            total_turns=total_turns,
            final_captures=final_captures,
            scoring=scoring,
            cumulative_scores=cumulative_scores
        )
