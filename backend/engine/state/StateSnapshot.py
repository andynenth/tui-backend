"""Versioned state representation for game synchronization."""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional


class StateSnapshot:
    """Represents complete game state at a point in time with versioning."""
    
    def __init__(
        self,
        version: int,
        game_id: str,
        phase: str,
        phase_data: Dict[str, Any],
        players: Dict[str, Any],
        round_number: int,
        turn_number: int,
        timestamp: Optional[datetime] = None
    ):
        """Initialize a state snapshot.
        
        Args:
            version: Monotonic version number for this snapshot
            game_id: Unique game identifier
            phase: Current game phase (PREPARATION, DECLARATION, TURN, SCORING)
            phase_data: Phase-specific state data
            players: Player states including scores, pieces, etc.
            round_number: Current round number
            turn_number: Current turn number within the round
            timestamp: When this snapshot was created (defaults to now)
        """
        self.version = version
        self.game_id = game_id
        self.phase = phase
        self.phase_data = phase_data
        self.players = players
        self.round_number = round_number
        self.turn_number = turn_number
        self.timestamp = timestamp or datetime.now()
        self._checksum: Optional[str] = None
    
    @property
    def checksum(self) -> str:
        """Calculate checksum for state validation."""
        if self._checksum is None:
            # Create deterministic JSON representation
            state_dict = {
                "version": self.version,
                "game_id": self.game_id,
                "phase": self.phase,
                "phase_data": self.phase_data,
                "players": self.players,
                "round_number": self.round_number,
                "turn_number": self.turn_number
            }
            state_json = json.dumps(state_dict, sort_keys=True)
            self._checksum = hashlib.sha256(state_json.encode()).hexdigest()[:8]
        return self._checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "game_id": self.game_id,
            "phase": self.phase,
            "phase_data": self.phase_data,
            "players": self.players,
            "round_number": self.round_number,
            "turn_number": self.turn_number,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StateSnapshot(v{self.version}, game={self.game_id}, "
            f"phase={self.phase}, checksum={self.checksum})"
        )