# backend/api/services/GameService.py

from typing import Dict, Any, Optional, List
from backend.shared_instances import shared_room_manager
from ..events.GameEvents import GameEvent, GameEventType, game_event_bus
import logging

class GameService:
    """
    Service wrapper รอบ engine/game.py
    เพิ่ม event-driven capabilities และ validation
    """
    
    def __init__(self):
        self.room_manager = shared_room_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_game(self, room_id: str):
        """Get game instance for room"""
        room = self.room_manager.get_room(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")
        if not room.game:
            raise ValueError(f"Game not started in room {room_id}")
        return room.game
    
    # =================================
    # WEAK HANDS / REDEAL METHODS
    # =================================
    
    def get_weak_hand_players(self, room_id: str, include_details: bool = False) -> List:
        """Get players with weak hands"""
        game = self.get_game(room_id)
        return game.get_weak_hand_players(include_details=include_details)
    
    def has_weak_hand_players(self, room_id: str) -> bool:
        """Check if any players have weak hands"""
        game = self.get_game(room_id)
        return game.has_weak_hand_players()
    
    async def execute_redeal(self, room_id: str, player_name: str) -> Dict[str, Any]:
        """Execute redeal for player and publish event"""
        game = self.get_game(room_id)
        
        try:
            result = game.execute_redeal_for_player(player_name)
            
            # Publish internal event
            event = GameEvent(
                event_type=GameEventType.PLAYER_REDEALT,
                room_id=room_id,
                player_id=player_name,
                data=result
            )
            await game_event_bus.publish(event)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute redeal for {player_name} in room {room_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    # =================================
    # DECLARATION METHODS
    # =================================
    
    def get_declaration_eligible_players(self, room_id: str, include_details: bool = False) -> List:
        """Get players who haven't declared yet"""
        game = self.get_game(room_id)
        return game.get_declaration_eligible_players(include_details=include_details)
    
    def validate_declaration(self, room_id: str, player_name: str, declaration: int) -> Dict[str, Any]:
        """Validate player declaration"""
        game = self.get_game(room_id)
        return game.validate_player_declaration(player_name, declaration)
    
    async def record_declaration(self, room_id: str, player_name: str, declaration: int) -> Dict[str, Any]:
        """Record player declaration and publish event"""
        game = self.get_game(room_id)
        
        try:
            result = game.record_player_declaration(player_name, declaration)
            
            if result['success']:
                # Publish internal event
                event = GameEvent(
                    event_type=GameEventType.DECLARATION_MADE,
                    room_id=room_id,
                    player_id=player_name,
                    data=result
                )
                await game_event_bus.publish(event)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to record declaration for {player_name} in room {room_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def all_players_declared(self, room_id: str) -> bool:
        """Check if all players have declared"""
        game = self.get_game(room_id)
        return game.all_players_declared()
    
    # =================================
    # TURN METHODS
    # =================================
    
    def get_turn_eligible_players(self, room_id: str, include_details: bool = False) -> List:
        """Get players who can play current turn"""
        game = self.get_game(room_id)
        return game.get_turn_eligible_players(include_details=include_details)
    
    def validate_turn_play(self, room_id: str, player_name: str, piece_indexes: List[int]) -> Dict[str, Any]:
        """Validate turn play"""
        game = self.get_game(room_id)
        return game.validate_turn_play(player_name, piece_indexes)
    
    async def execute_turn_play(self, room_id: str, player_name: str, piece_indexes: List[int]) -> Dict[str, Any]:
        """Execute turn play and publish events"""
        game = self.get_game(room_id)
        
        try:
            result = game.execute_turn_play(player_name, piece_indexes)
            
            if result['success']:
                # Publish internal event
                event = GameEvent(
                    event_type=GameEventType.TURN_PLAYED,
                    room_id=room_id,
                    player_id=player_name,
                    data=result
                )
                await game_event_bus.publish(event)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute turn play for {player_name} in room {room_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    # =================================
    # GAME STATE METHODS
    # =================================
    
    def get_game_phase_info(self, room_id: str) -> Dict[str, Any]:
        """Get current game phase information"""
        game = self.get_game(room_id)
        return game.get_game_phase_info()
    
    def set_game_phase(self, room_id: str, phase_name: str) -> None:
        """Set current game phase"""
        game = self.get_game(room_id)
        game.set_current_phase(phase_name)
    
    def get_game_state_snapshot(self, room_id: str) -> Dict[str, Any]:
        """Get complete game state snapshot"""
        game = self.get_game(room_id)
        
        base_info = game.get_game_phase_info()
        
        # Add more detailed info
        base_info.update({
            'players': [
                {
                    'name': p.name,
                    'score': p.score,
                    'declared': p.declared,
                    'is_bot': p.is_bot,
                    'hand_size': len(p.hand)
                }
                for p in game.players
            ],
            'weak_hand_players': game.get_weak_hand_players(include_details=False),
            'declaration_eligible': [p.name for p in game.get_declaration_eligible_players()],
            'turn_eligible': [p.name for p in game.get_turn_eligible_players()]
        })
        
        return base_info
    
    # =================================
    # ROOM MANAGEMENT
    # =================================
    
    def room_exists(self, room_id: str) -> bool:
        """Check if room exists"""
        return self.room_manager.get_room(room_id) is not None
    
    def game_exists(self, room_id: str) -> bool:
        """Check if game exists in room"""
        try:
            self.get_game(room_id)
            return True
        except ValueError:
            return False