# backend/api/websocket/handlers.py

import logging
from datetime import datetime
from typing import Optional

# Import will be done inside functions to avoid circular imports
# from backend.socket_manager import broadcast
from backend.engine.state_machine.core import GamePhase
from api.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)


class DisconnectHandler:
    """Enhanced disconnect handler with phase awareness"""
    
    @staticmethod
    async def handle_phase_aware_disconnect(
        room_id: str, 
        websocket_id: str,
        room,
        player_name: str
    ) -> dict:
        """
        Handle player disconnection with awareness of current game phase
        
        Returns:
            dict: Result of disconnect handling with phase-specific actions
        """
        result = {
            "success": False,
            "phase": None,
            "actions_taken": [],
            "bot_activated": False
        }
        
        try:
            # Get current game phase
            current_phase = None
            if room and room.game_state_machine:
                current_phase = room.game_state_machine.get_current_phase()
                result["phase"] = current_phase.value if current_phase else "NO_GAME"
            
            # Get player from the game
            player = None
            if room and room.game:
                player = next(
                    (p for p in room.game.players if p.name == player_name),
                    None
                )
            
            if not player:
                logger.warning(f"Player {player_name} not found in game")
                return result
            
            # Phase-specific handling
            if current_phase == GamePhase.PREPARATION:
                await DisconnectHandler._handle_preparation_disconnect(
                    room, player, player_name, result
                )
            elif current_phase == GamePhase.DECLARATION:
                await DisconnectHandler._handle_declaration_disconnect(
                    room, player, player_name, result
                )
            elif current_phase == GamePhase.TURN:
                await DisconnectHandler._handle_turn_disconnect(
                    room, player, player_name, result
                )
            elif current_phase == GamePhase.SCORING:
                await DisconnectHandler._handle_scoring_disconnect(
                    room, player, player_name, result
                )
            else:
                # Default handling for other phases
                await DisconnectHandler._handle_default_disconnect(
                    room, player, player_name, result
                )
            
            # Common disconnect actions for all phases
            if not player.is_bot:
                # Store original bot state
                player.original_is_bot = player.is_bot
                player.is_connected = False
                player.disconnect_time = datetime.now()
                
                # Convert to bot
                player.is_bot = True
                result["bot_activated"] = True
                result["actions_taken"].append("bot_activated")
                
                logger.info(
                    f"Player {player_name} disconnected during {result['phase']}. "
                    f"Bot activated."
                )
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error in phase-aware disconnect handling: {e}")
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def _handle_preparation_disconnect(room, player, player_name: str, result: dict):
        """Handle disconnect during PREPARATION phase"""
        # Check if player was in the middle of weak hand voting
        phase_data = room.game_state_machine.get_phase_data()
        weak_hand_votes = phase_data.get("weak_hand_votes", {})
        
        if player_name in weak_hand_votes and weak_hand_votes[player_name] is None:
            # Player hasn't voted yet - bot will handle it
            result["actions_taken"].append("pending_weak_hand_vote")
            logger.info(f"{player_name} disconnected with pending weak hand vote")
    
    @staticmethod
    async def _handle_declaration_disconnect(room, player, player_name: str, result: dict):
        """Handle disconnect during DECLARATION phase"""
        phase_data = room.game_state_machine.get_phase_data()
        declarations = phase_data.get("declarations", {})
        
        if player_name not in declarations:
            # Player hasn't declared yet - bot will handle it
            result["actions_taken"].append("pending_declaration")
            logger.info(f"{player_name} disconnected with pending declaration")
    
    @staticmethod
    async def _handle_turn_disconnect(room, player, player_name: str, result: dict):
        """Handle disconnect during TURN phase"""
        phase_data = room.game_state_machine.get_phase_data()
        current_player = phase_data.get("current_player")
        
        if current_player == player_name:
            # It's this player's turn - bot will take over immediately
            result["actions_taken"].append("active_turn_handoff")
            logger.info(f"{player_name} disconnected during their turn")
        else:
            # Not their turn yet
            result["actions_taken"].append("waiting_for_turn")
    
    @staticmethod
    async def _handle_scoring_disconnect(room, player, player_name: str, result: dict):
        """Handle disconnect during SCORING phase"""
        # During scoring, players are mostly passive
        # Bot doesn't need to do anything special
        result["actions_taken"].append("scoring_phase_passive")
        logger.info(f"{player_name} disconnected during scoring")
    
    @staticmethod
    async def _handle_default_disconnect(room, player, player_name: str, result: dict):
        """Default disconnect handling for other phases"""
        result["actions_taken"].append("default_handling")
        logger.info(f"{player_name} disconnected during {result['phase']}")


class ReconnectionHandler:
    """Enhanced reconnection handler with state synchronization"""
    
    @staticmethod
    async def handle_player_reconnection(
        room_id: str,
        player_name: str,
        websocket_id: str,
        room,
        websocket
    ) -> dict:
        """
        Handle player reconnection with full state synchronization
        
        Returns:
            dict: Result of reconnection handling with sync status
        """
        result = {
            "success": False,
            "state_synced": False,
            "bot_deactivated": False,
            "phase": None
        }
        
        try:
            # Register the reconnection
            await connection_manager.register_player(room_id, player_name, websocket_id)
            
            # Get player from the game
            player = None
            if room and room.game:
                player = next(
                    (p for p in room.game.players if p.name == player_name),
                    None
                )
            
            if not player:
                logger.warning(f"Player {player_name} not found for reconnection")
                return result
            
            # Check if this was a disconnected human player
            if player.is_bot and not player.original_is_bot:
                # Restore human control
                player.is_bot = False
                player.is_connected = True
                player.disconnect_time = None
                result["bot_deactivated"] = True
                
                logger.info(f"Player {player_name} reconnected. Human control restored.")
            
            # Get current game state for synchronization
            if room.game_state_machine:
                current_phase = room.game_state_machine.get_current_phase()
                result["phase"] = current_phase.value if current_phase else None
                
                # Send full game state to reconnected player
                await ReconnectionHandler._send_full_game_state(
                    websocket, room, player_name
                )
                result["state_synced"] = True
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error in reconnection handling: {e}")
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def _send_full_game_state(websocket, room, player_name: str):
        """Send complete game state to reconnected player"""
        try:
            # Get current phase data
            phase_data = room.game_state_machine.get_phase_data()
            current_phase = room.game_state_machine.get_current_phase()
            allowed_actions = [
                action.value for action in room.game_state_machine.get_allowed_actions()
            ]
            
            # Build player data
            players_data = {}
            if room.game and hasattr(room.game, "players"):
                for player in room.game.players:
                    player_hand = []
                    if hasattr(player, "hand") and player.hand:
                        player_hand = [str(piece) for piece in player.hand]
                    
                    players_data[player.name] = {
                        "hand": player_hand,
                        "hand_size": len(player_hand),
                        "declared": getattr(player, "declared", 0),
                        "score": getattr(player, "score", 0),
                        "is_bot": getattr(player, "is_bot", False),
                        "is_connected": getattr(player, "is_connected", True),
                        "captured_piles": getattr(player, "captured_piles", 0)
                    }
            
            # Get round number
            current_round = getattr(room.game, "round_number", 1) if room.game else 1
            
            # Send comprehensive state update
            await websocket.send_json({
                "event": "full_state_sync",
                "data": {
                    "phase": current_phase.value if current_phase else None,
                    "allowed_actions": allowed_actions,
                    "phase_data": phase_data,
                    "players": players_data,
                    "round": current_round,
                    "reconnected_player": player_name,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            logger.info(f"Full state sync sent to reconnected player {player_name}")
            
        except Exception as e:
            logger.error(f"Error sending full game state: {e}")


class ConnectionCleanupHandler:
    """Handle connection cleanup and resource management"""
    
    @staticmethod
    async def cleanup_expired_connections():
        """
        Clean up expired connections (for future use with limited reconnection time)
        Currently not needed with unlimited reconnection
        """
        # This method is kept for potential future use
        # With unlimited reconnection, we don't expire connections
        pass
    
    @staticmethod
    async def cleanup_game_ended_connections(room_id: str):
        """Clean up all connections when a game ends"""
        try:
            # Remove all player connections for this room
            if hasattr(connection_manager, 'connections') and room_id in connection_manager.connections:
                del connection_manager.connections[room_id]
                logger.info(f"Cleaned up all connections for ended game in room {room_id}")
        except Exception as e:
            logger.error(f"Error cleaning up game connections: {e}")