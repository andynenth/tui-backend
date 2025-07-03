# backend/engine/state/state_snapshot.py

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class StateSnapshot:
    """
    Immutable snapshot of game state at a specific version.
    
    This represents the complete game state at a point in time,
    with version tracking and checksum validation.
    """
    
    # Version and metadata
    version: int
    timestamp: float
    game_id: str
    room_id: str
    
    # Game state
    phase: str
    phase_data: Dict[str, Any]
    players: Dict[str, Dict[str, Any]]  # player_name -> player data
    round_number: int
    turn_number: int
    
    # Change metadata
    reason: str = ""  # Human-readable reason for this state change
    
    # Computed fields
    checksum: str = field(init=False)
    
    def __post_init__(self):
        """Calculate checksum after initialization"""
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """
        Calculate SHA256 checksum of the state data.
        
        This ensures state integrity and allows detection of any corruption.
        """
        # Create deterministic JSON representation
        state_dict = {
            'version': self.version,
            'game_id': self.game_id,
            'phase': self.phase,
            'phase_data': self._serialize_data(self.phase_data),
            'players': self._serialize_data(self.players),
            'round_number': self.round_number,
            'turn_number': self.turn_number
        }
        
        # Sort keys for deterministic output
        state_json = json.dumps(state_dict, sort_keys=True)
        
        # Calculate SHA256 hash
        return hashlib.sha256(state_json.encode()).hexdigest()[:16]  # Use first 16 chars
    
    def _serialize_data(self, data: Any) -> Any:
        """
        Convert data to JSON-serializable format.
        
        Handles common game objects that might not be directly serializable.
        """
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif hasattr(data, '__dict__'):
            # Convert objects to dict representation
            return self._serialize_data(data.__dict__)
        elif hasattr(data, 'value'):
            # Handle enums
            return data.value
        else:
            # Primitive types
            return data
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert snapshot to dictionary for JSON serialization.
        
        This is used when sending state to frontend via WebSocket.
        """
        return {
            'version': self.version,
            'timestamp': self.timestamp,
            'checksum': self.checksum,
            'game_id': self.game_id,
            'room_id': self.room_id,
            'phase': self.phase,
            'phase_data': self._serialize_data(self.phase_data),
            'players': self._serialize_data(self.players),
            'round_number': self.round_number,
            'turn_number': self.turn_number,
            'reason': self.reason
        }
    
    def validate_checksum(self) -> bool:
        """Validate that the checksum matches the current state"""
        return self.checksum == self._calculate_checksum()
    
    def get_player_data(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific player"""
        return self.players.get(player_name)
    
    def get_phase_data_value(self, key: str, default: Any = None) -> Any:
        """Get a specific value from phase data"""
        return self.phase_data.get(key, default)