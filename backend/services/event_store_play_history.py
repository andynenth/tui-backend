"""
Event Store Play History Extractor
Reconstructs play history from SQLite event store
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoundData:
    """Stores data for a single round"""

    round_number: int
    start_sequence: int
    end_sequence: int
    declarations: Dict[str, int]
    plays: List[Dict[str, Any]]
    final_scores: Dict[str, int]
    starter: Optional[str] = None


class EventStorePlayHistoryExtractor:
    """Extract play history from SQLite event store"""

    def __init__(self, db_path: str = "game_events.db"):
        self.db_path = db_path

    def extract_game_history(self, room_id: str) -> Dict[str, Any]:
        """Extract complete game history from event store"""

        # Find round boundaries (scoring phases)
        round_boundaries = self._find_round_boundaries(room_id)

        # Extract data for each round
        rounds = []
        for i, (start_seq, end_seq) in enumerate(round_boundaries):
            round_data = self._extract_round_data(room_id, i + 1, start_seq, end_seq)
            if round_data:
                rounds.append(round_data)

        # Get current round if in progress
        current_round = self._extract_current_round(room_id, round_boundaries)
        if current_round:
            rounds.append(current_round)

        return {"room_id": room_id, "total_rounds": len(rounds), "rounds": rounds}

    def _find_round_boundaries(self, room_id: str) -> List[tuple]:
        """Find sequence boundaries for each round"""
        with sqlite3.connect(self.db_path) as conn:
            # Find scoring phases
            cursor = conn.execute(
                """
                SELECT sequence 
                FROM game_events 
                WHERE room_id = ? 
                AND event_type = 'phase_change'
                AND json_extract(payload, '$.phase') = 'scoring'
                ORDER BY sequence
            """,
                (room_id,),
            )

            scoring_sequences = [row[0] for row in cursor.fetchall()]

            # Find preparation phases (round starts)
            cursor = conn.execute(
                """
                SELECT sequence 
                FROM game_events 
                WHERE room_id = ? 
                AND event_type = 'phase_change'
                AND json_extract(payload, '$.phase') = 'preparation'
                ORDER BY sequence
            """,
                (room_id,),
            )

            prep_sequences = [row[0] for row in cursor.fetchall()]

            # Build round boundaries
            boundaries = []
            for i, scoring_seq in enumerate(scoring_sequences):
                # Find the preparation phase that started this round
                start_seq = max(
                    [p for p in prep_sequences if p < scoring_seq], default=0
                )
                boundaries.append((start_seq, scoring_seq))

            return boundaries

    def _extract_round_data(
        self, room_id: str, round_num: int, start_seq: int, end_seq: int
    ) -> Optional[Dict[str, Any]]:
        """Extract all data for a specific round"""
        with sqlite3.connect(self.db_path) as conn:
            # Get all events for this round
            cursor = conn.execute(
                """
                SELECT sequence, event_type, payload, player_id, created_at
                FROM game_events
                WHERE room_id = ?
                AND sequence BETWEEN ? AND ?
                ORDER BY sequence
            """,
                (room_id, start_seq, end_seq),
            )

            events = cursor.fetchall()

            # Process events
            declarations = {}
            plays = []
            final_scores = {}
            initial_hands = {}
            turn_history = []
            current_turn_plays = []

            for seq, event_type, payload_str, player_id, created_at in events:
                payload = json.loads(payload_str)

                if event_type == "action_processed":
                    action_type = payload.get("action_type")
                    player_name = payload.get("player_name")

                    if action_type == "declare":
                        value = payload.get("payload", {}).get("value", 0)
                        declarations[player_name] = value

                    elif action_type == "play_pieces" or action_type == "play":
                        pieces = payload.get("payload", {}).get("pieces", [])
                        plays.append(
                            {"player": player_name, "pieces": pieces, "sequence": seq}
                        )
                        current_turn_plays.append(
                            {"player": player_name, "pieces": pieces}
                        )

                elif event_type == "phase_change":
                    phase = payload.get("phase")

                    # Extract initial hands from preparation phase
                    if phase == "preparation":
                        players = payload.get("players", {})
                        for player_name, player_info in players.items():
                            if player_info.get("hand_size", 0) > 0:
                                # Store that this player has cards (we don't have the actual cards in events)
                                initial_hands[player_name] = player_info.get(
                                    "hand_size", 8
                                )

                    # Extract final scores from scoring phase
                    elif phase == "scoring":
                        players = payload.get("players", {})
                        for player_name, player_info in players.items():
                            final_scores[player_name] = player_info.get("score", 0)

                    # Track turn changes
                    elif phase == "turn" and current_turn_plays:
                        turn_history.append(current_turn_plays)
                        current_turn_plays = []

            return {
                "round_number": round_num,
                "declarations": declarations,
                "plays": plays,
                "turn_history": turn_history,
                "final_scores": final_scores,
                "initial_hands": initial_hands,
                "event_count": len(events),
            }

    def _extract_current_round(
        self, room_id: str, completed_boundaries: List[tuple]
    ) -> Optional[Dict[str, Any]]:
        """Extract data for the current round in progress"""
        with sqlite3.connect(self.db_path) as conn:
            # Find the last sequence from completed rounds
            last_completed_seq = max(
                [end for _, end in completed_boundaries], default=0
            )

            # Get current round number
            cursor = conn.execute(
                """
                SELECT MAX(sequence), payload
                FROM game_events
                WHERE room_id = ?
                AND event_type = 'phase_change'
                AND sequence > ?
            """,
                (room_id, last_completed_seq),
            )

            row = cursor.fetchone()
            if not row or not row[1]:
                return None

            # Check if we're past preparation phase
            current_events = conn.execute(
                """
                SELECT COUNT(*)
                FROM game_events
                WHERE room_id = ?
                AND sequence > ?
                AND event_type = 'action_processed'
            """,
                (room_id, last_completed_seq),
            ).fetchone()[0]

            if current_events > 0:
                # Extract current round data
                round_num = len(completed_boundaries) + 1
                return self._extract_round_data(
                    room_id, round_num, last_completed_seq + 1, 999999
                )

        return None


# Test function
if __name__ == "__main__":
    extractor = EventStorePlayHistoryExtractor()
    history = extractor.extract_game_history("258B79")
    print(json.dumps(history, indent=2))
