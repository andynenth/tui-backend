"""
Property mapper to handle attribute mismatches between domain entities and use case expectations.

This mapper provides a systematic way to handle the 216 attribute mismatches
between what the domain entities have and what the use cases expect.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class PropertyMapper:
    """Maps between domain entities and use case expectations."""
    
    @staticmethod
    def map_room_for_use_case(room) -> Dict[str, Any]:
        """
        Convert domain Room to what use cases expect.
        
        Domain Room has: room_id, host_name, slots, game, status, max_slots
        Use cases expect: id, code, name, host_id, current_game, settings, created_at, player_count
        """
        return {
            # Direct mappings
            'room_id': room.room_id,
            'status': room.status,
            'slots': room.slots,
            'max_slots': room.max_slots,
            
            # Renamed mappings
            'id': room.room_id,
            'code': room.room_id,
            'name': f"{room.host_name}'s Room",
            'host_id': f"{room.room_id}_p0",  # Host is always first player
            'current_game': room.game,
            
            # Generated/default values
            'created_at': datetime.utcnow(),
            'player_count': len([s for s in room.slots if s is not None]),
            'settings': {
                'max_players': room.max_slots,
                'is_private': False,  # Default
                'allow_bots': True,   # Default
                'win_condition_type': 'score',  # Default
                'win_condition_value': 50  # Default
            }
        }
    
    @staticmethod
    def map_player_for_use_case(player, room_id: str, slot_index: int) -> Dict[str, Any]:
        """
        Convert domain Player to what use cases expect.
        
        Domain Player has: name, is_bot, hand, score, declared_piles, captured_piles, stats
        Use cases expect: id, player_id, games_played, games_won, is_connected, avatar_color
        """
        return {
            # Direct mappings
            'name': player.name,
            'is_bot': player.is_bot,
            'hand': player.hand,
            'score': player.score,
            'declared_piles': player.declared_piles,
            'captured_piles': player.captured_piles,
            
            # Generated IDs
            'id': f"{room_id}_p{slot_index}",
            'player_id': f"{room_id}_p{slot_index}",
            
            # Default/generated values
            'games_played': getattr(player, 'games_played', 0),
            'games_won': getattr(player, 'games_won', 0),
            'is_connected': getattr(player, 'is_connected', True),
            'avatar_color': getattr(player, 'avatar_color', None),
            'seat_position': slot_index
        }
    
    @staticmethod
    def map_game_for_use_case(game) -> Dict[str, Any]:
        """
        Convert domain Game to what use cases expect.
        
        Domain Game has: game_id, room_id, players, round_number, turn_number, phase, deck, table_piles
        Use cases expect: id, current_player_id, winner_id
        """
        return {
            # Direct mappings
            'game_id': game.game_id,
            'room_id': game.room_id,
            'players': game.players,
            'round_number': game.round_number,
            'turn_number': game.turn_number,
            'phase': game.phase,
            'deck': game.deck,
            'table_piles': game.table_piles,
            
            # Renamed mappings
            'id': game.game_id,
            
            # Calculated values
            'current_player_id': PropertyMapper._calculate_current_player_id(game),
            'winner_id': PropertyMapper._calculate_winner_id(game)
        }
    
    @staticmethod
    def _calculate_current_player_id(game) -> Optional[str]:
        """Calculate current player ID from game state."""
        # This would need to be implemented based on game logic
        # For now, return None as a safe default
        return None
    
    @staticmethod
    def _calculate_winner_id(game) -> Optional[str]:
        """Calculate winner ID from game state."""
        # Check if any player has reached winning score
        for i, player in enumerate(game.players):
            if player.score >= 50:  # Default win condition
                return f"{game.room_id}_p{i}"
        return None
    
    @staticmethod
    def get_safe(obj, attr: str, default=None):
        """
        Safely get attribute with fallback.
        
        This is a helper method to avoid AttributeErrors when accessing
        properties that might not exist.
        """
        return getattr(obj, attr, default)
    
    @staticmethod
    def get_room_attr(room, attr: str):
        """
        Get room attribute with proper mapping.
        
        This handles the common room attribute mismatches.
        """
        mapping = {
            'id': 'room_id',
            'code': 'room_id',
            'name': lambda r: f"{r.host_name}'s Room",
            'host_id': lambda r: f"{r.room_id}_p0",
            'current_game': 'game',
            'created_at': lambda r: datetime.utcnow(),
            'player_count': lambda r: len([s for s in r.slots if s]),
        }
        
        if attr in mapping:
            mapped = mapping[attr]
            if callable(mapped):
                return mapped(room)
            else:
                return getattr(room, mapped)
        
        # Check settings attributes
        if attr.startswith('settings.'):
            settings_attr = attr.replace('settings.', '')
            settings_defaults = {
                'max_players': room.max_slots,
                'is_private': False,
                'allow_bots': True,
                'win_condition_type': 'score',
                'win_condition_value': 50
            }
            return settings_defaults.get(settings_attr)
        
        return getattr(room, attr)
    
    @staticmethod
    def get_player_attr(player, attr: str, room_id: str = None, slot_index: int = None):
        """
        Get player attribute with proper mapping.
        
        This handles the common player attribute mismatches.
        """
        mapping = {
            'id': lambda p: f"{room_id}_p{slot_index}" if room_id and slot_index is not None else player.name,
            'player_id': lambda p: f"{room_id}_p{slot_index}" if room_id and slot_index is not None else player.name,
            'games_played': lambda p: getattr(p, 'games_played', 0),
            'games_won': lambda p: getattr(p, 'games_won', 0),
            'is_connected': lambda p: getattr(p, 'is_connected', True),
            'avatar_color': lambda p: getattr(p, 'avatar_color', None),
        }
        
        if attr in mapping:
            mapped = mapping[attr]
            if callable(mapped):
                return mapped(player)
        
        return getattr(player, attr)
    
    @staticmethod
    def generate_player_id(room_id: str, slot_index: int) -> str:
        """Generate consistent player ID from room ID and slot index."""
        return f"{room_id}_p{slot_index}"
    
    @staticmethod
    def is_host(player_name: str, room_host_name: str) -> bool:
        """Check if player is host by comparing names."""
        return player_name == room_host_name