# backend/services/play_history_db.py
"""
Play history service that reads from the V2 database schema.
"""

import json
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PlayHistoryDatabaseService:
    """Service for retrieving play history from the V2 database schema."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        if db_path is None:
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            self.db_path = str(project_root / "game_events.db")
        else:
            self.db_path = db_path
        
        logger.info(f"PlayHistoryDatabaseService initialized with db: {self.db_path}")
    
    async def get_play_history(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get play history for a room from the database.
        
        Returns data in the format expected by the frontend.
        """
        try:
            logger.info(f"Getting play history for room {room_id} from database at {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            
            # First check if room exists
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM game_summaries WHERE room_id = ?",
                (room_id,)
            )
            summary = cursor.fetchone()
            
            if not summary:
                logger.info(f"No game summary found for room {room_id}")
                conn.close()
                return None
            
            logger.info(f"Found game summary for room {room_id}: {dict(summary)}")
            
            # Get round snapshots
            cursor.execute(
                """
                SELECT * FROM round_snapshots 
                WHERE room_id = ? 
                ORDER BY round_number
                """,
                (room_id,)
            )
            round_snapshots = cursor.fetchall()
            
            # Build the response
            result = self._build_response(room_id, summary, round_snapshots)
            
            conn.close()
            logger.info(f"Returning play history for room {room_id} with {len(round_snapshots)} rounds")
            return result
            
        except Exception as e:
            logger.error(f"Error getting play history for room {room_id}: {e}")
            return None
    
    def _build_response(self, room_id: str, summary: sqlite3.Row, round_snapshots: List[sqlite3.Row]) -> Dict[str, Any]:
        """Build the response in the format expected by frontend transformer."""
        
        # Parse players from summary (using correct column name)
        players_data = json.loads(summary['player_names']) if summary['player_names'] else []
        players = []
        
        for i, player_data in enumerate(players_data):
            # Handle different player data formats
            if isinstance(player_data, dict):
                player_name = player_data.get('name', f'Player {i+1}')
                player_type = 'bot' if player_data.get('is_ai', False) else 'human'
            else:
                # Simple string format
                player_name = str(player_data)
                player_type = 'bot' if player_name.startswith('Bot') else 'human'
            
            # Include position field for frontend validation
            players.append({
                "name": player_name,
                "type": player_type,
                "position": i
            })
        
        # Build rounds from snapshots
        rounds = []
        for snapshot in round_snapshots:
            round_data = self._build_round(snapshot, players)
            if round_data:
                rounds.append(round_data)
        
        # Get final scores from last round
        final_scores = {}
        winner = None
        if round_snapshots:
            last_round = round_snapshots[-1]
            cumulative_scores = json.loads(last_round['cumulative_scores']) if last_round['cumulative_scores'] else {}
            final_scores = cumulative_scores
            
            # Determine winner based on highest score
            if final_scores:
                max_score = max(final_scores.values())
                for player_name, score in final_scores.items():
                    if score == max_score:
                        winner = player_name
                        break
        
        # Return in snake_case format for transformer
        return {
            "room_id": room_id,
            "total_rounds": len(round_snapshots),
            "start_time": datetime.fromtimestamp(summary['started_at']).isoformat() if summary['started_at'] else datetime.now().isoformat(),
            "end_time": datetime.fromtimestamp(summary['completed_at']).isoformat() if summary['completed_at'] else None,
            "players": players,
            "rounds": rounds,
            "game_status": {
                "completed": bool(summary['completed_at']),
                "winner": winner,
                "final_scores": final_scores
            }
        }
    
    def _build_round(self, snapshot: sqlite3.Row, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build round data from snapshot in frontend format."""
        
        # Parse JSON fields
        initial_hands = json.loads(snapshot['initial_hands']) if snapshot['initial_hands'] else {}
        declarations_data = json.loads(snapshot['declarations']) if snapshot['declarations'] else {}
        turn_sequence = json.loads(snapshot['turn_sequence']) if snapshot['turn_sequence'] else []
        round_scores = json.loads(snapshot['round_scores']) if snapshot['round_scores'] else {}
        cumulative_scores = json.loads(snapshot['cumulative_scores']) if snapshot['cumulative_scores'] else {}
        
        # Build declarations array
        declarations = []
        for player_name, declared_value in declarations_data.items():
            hand = initial_hands.get(player_name, [])
            
            # Convert hand pieces to frontend format
            hand_pieces = []
            for piece in hand:
                if isinstance(piece, dict):
                    hand_pieces.append({
                        "type": piece.get('kind', 'UNKNOWN'),
                        "point": piece.get('point', 0),
                        "color": "red" if "RED" in piece.get('kind', '') else "black"
                    })
            
            declarations.append({
                "player": player_name,
                "player_name": player_name,  # Transformer expects player_name
                "player_id": player_name.lower().replace(' ', '_'),
                "declared": declared_value,
                "hand": hand_pieces,
                "timestamp": datetime.now().isoformat()  # Add timestamp for validation
            })
        
        # Build turns array
        # Track hands across turns
        player_hands = {}
        for player_name, hand in initial_hands.items():
            player_hands[player_name] = hand.copy() if hand else []
        
        turns = []
        for turn_data in turn_sequence:
            turn = self._build_turn(turn_data, player_hands)
            if turn:
                turns.append(turn)
        
        # Build scoring in frontend format
        scoring = {
            "players": {},
            "bonuses": []
        }
        
        # Also build final_captures
        final_captures = {}
        
        for player_name in [p['name'] for p in players]:
            player_round_score = round_scores.get(player_name, {})
            
            if isinstance(player_round_score, dict):
                declared = player_round_score.get('declared', declarations_data.get(player_name, 0))
                actual = player_round_score.get('actual', 0)
                multiplier = player_round_score.get('multiplier', 1)
                final_score = player_round_score.get('final_score', 0)
                bonus = player_round_score.get('bonus', 0)
            else:
                # Simple score format
                declared = declarations_data.get(player_name, 0)
                actual = 0  # Not available in simple format
                multiplier = 1
                final_score = player_round_score if isinstance(player_round_score, (int, float)) else 0
                bonus = 0
            
            # Store actual captures
            final_captures[player_name] = actual
            
            # Calculate base score (for display)
            base_score = player_round_score.get('base_score', abs(declared - actual)) if isinstance(player_round_score, dict) else abs(declared - actual)
            
            scoring["players"][player_name] = {
                "declared": declared,
                "captured": actual,
                "score": final_score,
                "multiplier": multiplier,
                "baseScore": base_score
            }
            
            # Add bonus events
            if bonus > 0:
                bonus_type = ""
                if declared == 0 and actual == 0:
                    bonus_type = "ZERO_DECLARATION"
                elif declared > 0 and declared == actual:
                    bonus_type = "PERFECT_PREDICTION"
                
                if bonus_type:
                    scoring["bonuses"].append({
                        "type": bonus_type,
                        "player": player_name,
                        "value": bonus,
                        "description": f"{player_name} achieved {bonus_type.replace('_', ' ').lower()}"
                    })
        
        # Determine round winner
        winner = snapshot['starter_player']  # Default to starter
        if round_scores:
            # Find player with highest score this round
            max_score = -999
            for player_name, score_data in round_scores.items():
                if isinstance(score_data, dict):
                    score = score_data.get('score', 0)
                else:
                    score = score_data
                
                if score > max_score:
                    max_score = score
                    winner = player_name
        
        # Build hands_dealt from initial_hands
        hands_dealt = {}
        for player_name, hand in initial_hands.items():
            # Convert hand pieces to frontend format
            hand_pieces = []
            for piece in hand:
                if isinstance(piece, dict):
                    hand_pieces.append({
                        "type": piece.get('kind', 'UNKNOWN'),
                        "point": piece.get('point', 0),
                        "color": "red" if "RED" in piece.get('kind', '') else "black"
                    })
            hands_dealt[player_name] = hand_pieces
        
        # Return in the format expected by the transformer
        return {
            "round_number": snapshot['round_number'],
            "initial_state": {
                "starter": {
                    "player_name": snapshot['starter_player'] or "Unknown"
                }
            },
            "timestamp": snapshot['created_at'] or datetime.now().isoformat(),
            "turn_history": turns,  # Transformer expects turn_history
            "declaration_phase": {
                "declarations": declarations  # Nested under declaration_phase
            },
            "hands_dealt": hands_dealt,  # Same data as in declarations
            "round_summary": {
                "winner": winner,
                "scoring": scoring,  # Nested under round_summary
                "final_captures": final_captures,
                "cumulative_scores": cumulative_scores
            }
        }
    
    def _build_turn(self, turn_data: Dict[str, Any], player_hands: Dict[str, List[Any]]) -> Optional[Dict[str, Any]]:
        """Build turn data from turn sequence entry in frontend format.
        
        Args:
            turn_data: Turn data from database
            player_hands: Mutable dict tracking current hands for each player
        """
        if not isinstance(turn_data, dict):
            return None
        
        turn_number = turn_data.get('turn_number', 0)
        plays_data = turn_data.get('plays', {})
        winner = turn_data.get('winner', 'Unknown')
        
        # Build plays array
        plays = []
        winner_pieces = 0
        
        for player_name, play_info in plays_data.items():
            if isinstance(play_info, dict):
                pieces = play_info.get('pieces', [])
                is_starter = play_info.get('is_starter', False)
            else:
                # Simple format
                pieces = []
                is_starter = False
            
            # Get player's current hand
            hand_before = player_hands.get(player_name, []).copy()
            
            # Convert pieces to frontend format
            pieces_list = []
            for piece in pieces:
                if isinstance(piece, dict):
                    pieces_list.append({
                        "type": piece.get('kind', 'UNKNOWN'),
                        "point": piece.get('point', 0),
                        "color": "red" if "RED" in piece.get('kind', '') else "black"
                    })
            
            # Calculate hand after by removing played pieces
            hand_after = hand_before.copy()
            for played_piece in pieces:
                # Find and remove the piece from hand_after
                for i, hand_piece in enumerate(hand_after):
                    if isinstance(hand_piece, dict) and isinstance(played_piece, dict):
                        if hand_piece.get('kind') == played_piece.get('kind') and hand_piece.get('point') == played_piece.get('point'):
                            hand_after.pop(i)
                            break
            
            # Update player's hand for next turn
            player_hands[player_name] = hand_after
            
            # Convert hands to frontend format
            hand_before_formatted = []
            for piece in hand_before:
                if isinstance(piece, dict):
                    hand_before_formatted.append({
                        "type": piece.get('kind', 'UNKNOWN'),
                        "point": piece.get('point', 0),
                        "color": "red" if "RED" in piece.get('kind', '') else "black"
                    })
            
            hand_after_formatted = []
            for piece in hand_after:
                if isinstance(piece, dict):
                    hand_after_formatted.append({
                        "type": piece.get('kind', 'UNKNOWN'),
                        "point": piece.get('point', 0),
                        "color": "red" if "RED" in piece.get('kind', '') else "black"
                    })
            
            # Count winner pieces
            if player_name == winner:
                winner_pieces = len(pieces_list)
            
            plays.append({
                "player": player_name,
                "pieces": pieces_list,
                "isStarter": is_starter,
                "handBefore": hand_before_formatted,
                "handAfter": hand_after_formatted,
                "captured": len(pieces_list) if player_name == winner else 0
            })
        
        return {
            "turnNumber": turn_number,
            "plays": plays,
            "winner": winner,
            "winnerPieces": winner_pieces,
            "timestamp": datetime.now().isoformat()  # Add timestamp for validation
        }


# Create singleton instance
play_history_db_service = PlayHistoryDatabaseService()