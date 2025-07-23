# infrastructure/compatibility/legacy_adapter.py
"""
Adapter for interfacing with legacy code during migration.
"""

import logging
from typing import Dict, Any, Optional, List

from domain.entities.game import Game
from domain.entities.player import Player
from domain.entities.piece import Piece

logger = logging.getLogger(__name__)


class LegacyAdapter:
    """
    Provides compatibility between new clean architecture
    and legacy code that hasn't been migrated yet.
    """
    
    @staticmethod
    def room_to_legacy_format(room: Any) -> Dict[str, Any]:
        """
        Convert new Room domain model to legacy format.
        
        Args:
            room: New Room domain entity
            
        Returns:
            Legacy room dictionary format
        """
        return {
            "id": room.id,
            "host_name": room.host,
            "join_code": room.join_code,
            "players": [
                {
                    "name": p.name,
                    "is_bot": p.is_bot,
                    "is_ready": p.is_ready,
                    "avatar_color": getattr(p, 'avatar_color', None)
                }
                for p in room.players
            ],
            "settings": room.settings,
            "state": room.state,
            "created_at": room.created_at.isoformat() if hasattr(room, 'created_at') else None,
            # Legacy specific fields
            "room_id": room.id,  # Legacy used room_id
            "max_players": room.settings.get("max_players", 4),
            "is_game_started": room.state == "in_game"
        }
    
    @staticmethod
    def game_to_legacy_format(game: Game) -> Dict[str, Any]:
        """
        Convert new Game domain model to legacy format.
        
        Args:
            game: New Game domain entity
            
        Returns:
            Legacy game dictionary format
        """
        return {
            "id": game.id,
            "players": [
                {
                    "name": p.name,
                    "is_bot": p.is_bot,
                    "pieces": len(p.pieces),
                    "won_pieces": len(p.won_pieces),
                    "declared_piles": p.declared_piles,
                    "score": game.get_total_score(p.name)
                }
                for p in game.players
            ],
            "round_number": game.round_number,
            "current_phase": game.current_phase.value,
            "turn_number": game.turn_number,
            "is_started": game.is_started,
            "is_ended": game.is_ended,
            "scores": game.scores,
            # Legacy specific fields
            "game_id": game.id,
            "state": "playing" if game.is_started and not game.is_ended else "waiting",
            "max_score": game.max_score,
            "max_rounds": game.max_rounds
        }
    
    @staticmethod
    def legacy_to_player(legacy_data: Dict[str, Any]) -> Player:
        """
        Convert legacy player data to new Player entity.
        
        Args:
            legacy_data: Legacy player dictionary
            
        Returns:
            New Player domain entity
        """
        player = Player(
            name=legacy_data.get("name") or legacy_data.get("player_name"),
            is_bot=legacy_data.get("is_bot", False),
            is_ready=legacy_data.get("is_ready", True)
        )
        
        # Handle pieces if present
        if "pieces" in legacy_data and isinstance(legacy_data["pieces"], list):
            pieces = [
                Piece(face=p["face"], points=p["points"])
                for p in legacy_data["pieces"]
                if isinstance(p, dict)
            ]
            player.receive_pieces(pieces)
        
        return player
    
    @staticmethod
    def legacy_command_to_new(command_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert legacy WebSocket command to new command format.
        
        Args:
            command_type: Legacy command type
            data: Legacy command data
            
        Returns:
            New command format
        """
        # Map legacy command types to new ones
        command_mapping = {
            "create_room": "CreateRoomCommand",
            "join_room": "JoinRoomCommand",
            "leave_room": "LeaveRoomCommand",
            "start_game": "StartGameCommand",
            "play_turn": "PlayTurnCommand",
            "declare": "DeclareCommand",
            "add_bot": "AddBotCommand",
            "remove_bot": "RemoveBotCommand",
            "kick_player": "KickPlayerCommand",
            "transfer_host": "TransferHostCommand"
        }
        
        new_command_type = command_mapping.get(command_type, command_type)
        
        # Transform data based on command type
        if command_type == "create_room":
            return {
                "type": new_command_type,
                "host_name": data.get("player_name", ""),
                "room_settings": data.get("settings", {})
            }
        
        elif command_type == "join_room":
            return {
                "type": new_command_type,
                "room_id": data.get("room_id") or data.get("join_code"),
                "player_name": data.get("player_name", "")
            }
        
        elif command_type == "play_turn":
            return {
                "type": new_command_type,
                "room_id": data.get("room_id"),
                "player_name": data.get("player_name") or data.get("player"),
                "piece_indices": data.get("piece_indices") or data.get("pieces", [])
            }
        
        elif command_type == "declare":
            return {
                "type": new_command_type,
                "room_id": data.get("room_id"),
                "player_name": data.get("player_name") or data.get("player"),
                "declared_piles": data.get("declared_piles") or data.get("declaration")
            }
        
        # Default: pass through with type mapping
        return {
            "type": new_command_type,
            **data
        }
    
    @staticmethod
    def validate_legacy_compatibility(
        old_response: Dict[str, Any],
        new_response: Dict[str, Any]
    ) -> List[str]:
        """
        Validate that new response maintains compatibility with old format.
        
        Args:
            old_response: Response from legacy system
            new_response: Response from new system
            
        Returns:
            List of compatibility issues found
        """
        issues = []
        
        # Check required fields
        if old_response.get("type") != new_response.get("type"):
            issues.append(
                f"Message type mismatch: "
                f"old={old_response.get('type')} new={new_response.get('type')}"
            )
        
        # Check critical fields based on message type
        message_type = old_response.get("type")
        
        if message_type == "room_created":
            for field in ["room_id", "join_code"]:
                if field in old_response and field not in new_response:
                    issues.append(f"Missing required field: {field}")
        
        elif message_type == "game_started":
            for field in ["room_id", "players", "phase"]:
                if field in old_response and field not in new_response:
                    issues.append(f"Missing required field: {field}")
        
        elif message_type == "turn_played":
            for field in ["player", "pieces", "success"]:
                if field in old_response and field not in new_response:
                    issues.append(f"Missing required field: {field}")
        
        return issues
    
    @staticmethod
    def migrate_game_state(legacy_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate legacy game state to new format.
        
        Useful for loading saved games or recovering from crashes.
        """
        return {
            "game_id": legacy_state.get("id") or legacy_state.get("game_id"),
            "players": [
                LegacyAdapter.legacy_to_player(p).to_dict()
                for p in legacy_state.get("players", [])
            ],
            "round_number": legacy_state.get("round_number", 1),
            "current_phase": legacy_state.get("current_phase", "WAITING"),
            "turn_number": legacy_state.get("turn_number", 0),
            "scores": legacy_state.get("scores", {}),
            "settings": {
                "max_score": legacy_state.get("max_score", 50),
                "max_rounds": legacy_state.get("max_rounds", 20)
            }
        }