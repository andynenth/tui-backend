# backend/services/play_history_simple.py
"""
Simple play history service that returns data in the format expected by the frontend.
Works with both active games (in memory) and completed games (from database).
"""

import logging
from typing import Dict, List, Any, Optional
from backend.models.play_history import PlayHistoryResponse, PlayerInfo, RoundHistory
from backend.engine.async_room_manager import room_manager
from backend.engine.piece import Piece

logger = logging.getLogger(__name__)


class SimplePlayHistoryService:
    """Simple service for retrieving play history that matches frontend expectations."""
    
    async def get_play_history(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get play history for a room. First tries active game, then falls back to database.
        
        Returns data in the exact format expected by the frontend:
        {
            "roomId": "ABC123",
            "players": [
                {"name": "Andy", "type": "human", "position": 0},
                {"name": "Bot 2", "type": "bot", "position": 1},
                ...
            ],
            "rounds": [
                {
                    "roundNumber": 1,
                    "starter": "Andy",
                    "declarations": [...],
                    "turns": [...],
                    "scoring": {...},
                    "winner": "Andy",
                    "timestamp": "2025-01-01T00:00:00Z"
                }
            ],
            "gameStatus": {
                "completed": true,
                "winner": "Andy",
                "finalScores": {"Andy": 50, "Bot 2": 30, ...}
            },
            "totalRounds": 1,
            "startTime": "2025-01-01T00:00:00Z",
            "endTime": "2025-01-01T01:00:00Z"
        }
        """
        try:
            # First try to get from active game
            room = await room_manager.get_room(room_id)
            if room and room.game:
                return self._build_from_active_game(room_id, room)
            
            # If no active game, try database (placeholder for now)
            # TODO: Implement database retrieval when needed
            logger.info(f"No active game found for room {room_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting play history for room {room_id}: {e}")
            return None
    
    def _build_from_active_game(self, room_id: str, room: Any) -> Dict[str, Any]:
        """Build play history from active game state."""
        game = room.game
        
        # Build players array
        players = []
        for i, player in enumerate(game.players):
            players.append({
                "name": player.name,
                "type": "human" if not player.is_ai else "bot",
                "position": i
            })
        
        # Build rounds array
        rounds = []
        
        # Add completed rounds
        for round_num in range(1, game.round_number + 1):
            round_data = self._build_round_data(game, round_num)
            if round_data:
                rounds.append(round_data)
        
        # Determine game status
        game_completed = game.game_ended
        game_winner = None
        final_scores = {}
        
        if game_completed:
            # Find winner
            max_score = -1
            for player in game.players:
                final_scores[player.name] = player.score
                if player.score > max_score:
                    max_score = player.score
                    game_winner = player.name
        
        return {
            "roomId": room_id,
            "players": players,
            "rounds": rounds,
            "gameStatus": {
                "completed": game_completed,
                "winner": game_winner,
                "finalScores": final_scores
            },
            "totalRounds": len(rounds),
            "startTime": "2025-01-01T00:00:00Z",  # TODO: Track actual start time
            "endTime": "2025-01-01T01:00:00Z" if game_completed else None
        }
    
    def _build_round_data(self, game: Any, round_num: int) -> Optional[Dict[str, Any]]:
        """Build data for a specific round."""
        # For current round that's not complete, we can still show partial data
        if round_num == game.round_number and not game.round_ended:
            return self._build_current_round(game)
        
        # For completed rounds, we need to reconstruct from game history
        # Since we don't have full history in memory, this is limited
        # TODO: Enhance this when we have better round history tracking
        
        if round_num < game.round_number:
            # This is a completed round
            return self._build_completed_round_stub(game, round_num)
        
        return None
    
    def _build_current_round(self, game: Any) -> Dict[str, Any]:
        """Build data for the current active round."""
        # Determine starter
        starter_name = "Unknown"
        if hasattr(game, 'round_starter_index') and game.round_starter_index is not None:
            starter_name = game.players[game.round_starter_index].name
        
        # Build declarations
        declarations = []
        for player in game.players:
            hand_pieces = []
            if hasattr(player, 'hand'):
                for piece in player.hand:
                    hand_pieces.append({
                        "type": piece.kind,
                        "point": piece.point,
                        "color": "red" if "RED" in piece.kind else "black"
                    })
            
            declarations.append({
                "player": player.name,
                "declared": player.declared_pile_count if hasattr(player, 'declared_pile_count') else 0,
                "hand": hand_pieces,
                "timestamp": "2025-01-01T00:00:00Z"
            })
        
        # Build turns (simplified for now)
        turns = self._build_turns_from_game(game)
        
        # Build scoring
        scoring = self._build_scoring(game)
        
        # Determine round winner (if round is complete)
        winner = "In Progress"
        if game.round_ended:
            # Find player with highest score this round
            # This is simplified - real implementation would track round scores
            winner = max(game.players, key=lambda p: p.score).name
        
        return {
            "roundNumber": game.round_number,
            "starter": starter_name,
            "declarations": declarations,
            "turns": turns,
            "scoring": scoring,
            "winner": winner,
            "timestamp": "2025-01-01T00:00:00Z"
        }
    
    def _build_completed_round_stub(self, game: Any, round_num: int) -> Dict[str, Any]:
        """Build stub data for a completed round."""
        # Since we don't have full history, create minimal data
        return {
            "roundNumber": round_num,
            "starter": "Unknown",
            "declarations": [],
            "turns": [],
            "scoring": {
                "players": {},
                "bonuses": []
            },
            "winner": "Unknown",
            "timestamp": "2025-01-01T00:00:00Z"
        }
    
    def _build_turns_from_game(self, game: Any) -> List[Dict[str, Any]]:
        """Build turn data from game state."""
        turns = []
        
        # Get turn history if available
        if hasattr(game, 'turn_history') and game.turn_history:
            for i, turn in enumerate(game.turn_history):
                turn_data = {
                    "turnNumber": i + 1,
                    "plays": [],
                    "winner": turn.get('winner', 'Unknown'),
                    "winnerPieces": 0,
                    "timestamp": "2025-01-01T00:00:00Z"
                }
                
                # Add plays for each player
                if 'plays' in turn:
                    for play in turn['plays']:
                        play_data = {
                            "player": play.get('player', 'Unknown'),
                            "pieces": [],
                            "isStarter": False,
                            "handBefore": [],
                            "handAfter": [],
                            "captured": 0
                        }
                        
                        # Add pieces played
                        if 'pieces' in play:
                            for piece in play['pieces']:
                                play_data["pieces"].append({
                                    "type": piece.get('kind', 'UNKNOWN'),
                                    "point": piece.get('point', 0),
                                    "color": "red" if "RED" in piece.get('kind', '') else "black"
                                })
                        
                        turn_data["plays"].append(play_data)
                
                turns.append(turn_data)
        
        return turns
    
    def _build_scoring(self, game: Any) -> Dict[str, Any]:
        """Build scoring data."""
        players_scoring = {}
        
        for player in game.players:
            # Get declared and captured counts
            declared = player.declared_pile_count if hasattr(player, 'declared_pile_count') else 0
            captured = player.captured_count if hasattr(player, 'captured_count') else 0
            
            # Calculate base score (difference)
            base_score = abs(declared - captured)
            
            # Get multiplier (simplified)
            multiplier = 1
            if declared == captured:
                multiplier = 3  # Exact match
            elif declared == 0 or declared == 8:
                multiplier = 2  # Special declaration
            
            # Calculate final score
            score = base_score * multiplier
            if declared < captured:
                score = -score  # Negative if captured more than declared
            
            players_scoring[player.name] = {
                "declared": declared,
                "captured": captured,
                "score": score,
                "multiplier": multiplier,
                "baseScore": base_score
            }
        
        return {
            "players": players_scoring,
            "bonuses": []  # No bonuses for now
        }


# Create singleton instance
play_history_simple_service = SimplePlayHistoryService()