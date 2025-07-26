"""
Connection status value object.

Represents the possible states of a player's connection.
"""

from enum import Enum


class ConnectionStatus(Enum):
    """
    Connection status for a player.
    
    This value object represents the different states a player's
    connection can be in during their game session.
    """
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    
    def is_active(self) -> bool:
        """Check if status represents an active connection."""
        return self == ConnectionStatus.CONNECTED
    
    def allows_bot_activation(self) -> bool:
        """Check if status allows bot activation."""
        return self == ConnectionStatus.DISCONNECTED