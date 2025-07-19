# backend/api/websocket/state_sync.py

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.engine.state_machine.core import GamePhase
from backend.engine.piece import Piece

logger = logging.getLogger(__name__)


class GameStateSync:
    """Enhanced game state synchronization for reconnecting players"""
    
    @staticmethod
    async def get_full_game_state(room, player_name: str) -> Dict[str, Any]:
        """
        Get comprehensive game state for a reconnecting player
        
        Returns:
            dict: Complete game state including all necessary data
        """
        try:
            if not room or not room.game:
                return {"error": "No active game"}
            
            game = room.game
            state_machine = room.game_state_machine
            
            # Get current phase info
            current_phase = state_machine.get_current_phase() if state_machine else None
            phase_data = state_machine.get_phase_data() if state_machine else {}
            allowed_actions = []
            
            if state_machine:
                allowed_actions = [
                    action.value for action in state_machine.get_allowed_actions()
                ]
            
            # Build comprehensive player data
            players_data = GameStateSync._build_players_data(game, player_name)
            
            # Get game history and recent events
            recent_events = GameStateSync._get_recent_events(game, player_name)
            
            # Get phase-specific data
            phase_specific = GameStateSync._get_phase_specific_data(
                current_phase, phase_data, game, player_name
            )
            
            # Build complete state
            state = {
                "event": "full_state_sync",
                "data": {
                    # Basic info
                    "room_id": room.room_id,
                    "round": getattr(game, "round_number", 1),
                    "phase": current_phase.value if current_phase else None,
                    "allowed_actions": allowed_actions,
                    "reconnected_player": player_name,
                    "timestamp": datetime.now().isoformat(),
                    
                    # Player data
                    "players": players_data,
                    
                    # Phase data
                    "phase_data": phase_data,
                    "phase_specific": phase_specific,
                    
                    # Game state
                    "game_state": {
                        "total_rounds": getattr(game, "total_rounds", 20),
                        "winning_score": getattr(game, "winning_score", 50),
                        "current_turn": phase_data.get("current_player"),
                        "turn_number": getattr(game, "turn_number", 0),
                        "last_winner": getattr(game, "last_winner", None),
                    },
                    
                    # Recent events for context
                    "recent_events": recent_events,
                    
                    # Reconnection info
                    "reconnection_info": {
                        "message": "Welcome back! Your AI was playing for you.",
                        "missed_turns": GameStateSync._calculate_missed_turns(
                            game, player_name
                        ),
                    }
                }
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error building full game state: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _build_players_data(game, reconnecting_player: str) -> Dict[str, Any]:
        """Build comprehensive player data"""
        players_data = {}
        
        for player in game.players:
            # Get hand data (only full hand for reconnecting player)
            if player.name == reconnecting_player:
                hand_data = [
                    {
                        "rank": piece.rank,
                        "suit": piece.suit,
                        "display": str(piece),
                        "value": piece.value
                    }
                    for piece in (player.hand or [])
                ]
            else:
                # Other players just get hand size
                hand_data = None
            
            players_data[player.name] = {
                # Basic info
                "name": player.name,
                "is_bot": getattr(player, "is_bot", False),
                "is_connected": getattr(player, "is_connected", True),
                "position": getattr(player, "position", 0),
                
                # Game stats
                "score": getattr(player, "score", 0),
                "hand_size": len(player.hand) if player.hand else 0,
                "hand": hand_data,  # Full hand only for reconnecting player
                "declared": getattr(player, "declared", 0),
                "captured_piles": getattr(player, "captured_piles", 0),
                
                # Status
                "is_ready": getattr(player, "is_ready", True),
                "has_weak_hand": getattr(player, "has_weak_hand", False),
                "passed": getattr(player, "passed", False),
            }
        
        return players_data
    
    @staticmethod
    def _get_phase_specific_data(phase: GamePhase, phase_data: dict, game, player_name: str) -> Dict[str, Any]:
        """Get data specific to current phase"""
        if not phase:
            return {}
        
        if phase == GamePhase.PREPARATION:
            return {
                "weak_hand_votes": phase_data.get("weak_hand_votes", {}),
                "weak_hand_players": phase_data.get("weak_hand_players", []),
                "votes_needed": phase_data.get("votes_needed", 0),
            }
        
        elif phase == GamePhase.DECLARATION:
            return {
                "declarations": phase_data.get("declarations", {}),
                "declaration_order": phase_data.get("declaration_order", []),
                "total_declared": sum(phase_data.get("declarations", {}).values()),
                "valid_options": GameStateSync._get_valid_declaration_options(
                    game, player_name, phase_data
                ),
            }
        
        elif phase == GamePhase.TURN:
            return {
                "current_player": phase_data.get("current_player"),
                "current_pile": phase_data.get("current_pile", []),
                "turn_winner": phase_data.get("turn_winner"),
                "required_piece_count": phase_data.get("required_piece_count"),
                "players_passed": phase_data.get("players_passed", []),
                "pile_number": phase_data.get("pile_number", 1),
            }
        
        elif phase == GamePhase.SCORING:
            return {
                "round_scores": phase_data.get("round_scores", {}),
                "score_details": phase_data.get("score_details", {}),
                "round_winner": phase_data.get("round_winner"),
                "game_over": phase_data.get("game_over", False),
                "final_winner": phase_data.get("final_winner"),
            }
        
        return {}
    
    @staticmethod
    def _get_valid_declaration_options(game, player_name: str, phase_data: dict) -> List[int]:
        """Calculate valid declaration options for a player"""
        declarations = phase_data.get("declarations", {})
        
        # If player already declared, return empty
        if player_name in declarations:
            return []
        
        # Calculate remaining options
        total_declared = sum(declarations.values())
        remaining_players = 4 - len(declarations)
        
        if remaining_players == 1:
            # Last player must make total != 8
            required = 8 - total_declared
            return [i for i in range(9) if i != required]
        else:
            # Other players can declare 0-8
            return list(range(9))
    
    @staticmethod
    def _get_recent_events(game, player_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent game events for context"""
        events = []
        
        # This would ideally come from an event log
        # For now, return empty list
        # In a full implementation, you'd track events like:
        # - Player disconnections/reconnections
        # - Turn winners
        # - Declarations made
        # - Score changes
        
        return events
    
    @staticmethod
    def _calculate_missed_turns(game, player_name: str) -> int:
        """Calculate how many turns the player missed"""
        # This would need to track when player disconnected
        # For now, return 0
        return 0
    
    @staticmethod
    async def get_reconnection_summary(game, player_name: str, disconnect_time: datetime) -> Dict[str, Any]:
        """
        Get a summary of what happened while player was disconnected
        
        Returns:
            dict: Summary of missed events
        """
        summary = {
            "event": "reconnection_summary",
            "data": {
                "player_name": player_name,
                "disconnect_duration": (datetime.now() - disconnect_time).total_seconds(),
                "missed_events": [],
                "current_state": {
                    "phase": None,
                    "round": getattr(game, "round_number", 1),
                    "your_score": 0,
                    "your_position": 0,
                }
            }
        }
        
        # Get player's current state
        player = next((p for p in game.players if p.name == player_name), None)
        if player:
            scores = [(p.name, p.score) for p in game.players]
            scores.sort(key=lambda x: x[1], reverse=True)
            position = next(i for i, (name, _) in enumerate(scores, 1) if name == player_name)
            
            summary["data"]["current_state"]["your_score"] = player.score
            summary["data"]["current_state"]["your_position"] = position
        
        return summary