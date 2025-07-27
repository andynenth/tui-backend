"""
Player role value object for distinguishing between human players and bots.
"""

from enum import Enum


class PlayerRole(Enum):
    """
    Represents the role/type of a player in the game.
    
    This enum distinguishes between human players and AI bots,
    which may have different behaviors and timing constraints.
    """
    
    HUMAN = "human"               # Human player
    BOT = "bot"                   # AI bot player
    
    def __str__(self) -> str:
        """Return the string representation of the player role."""
        return self.value
    
    @property
    def is_human(self) -> bool:
        """Check if this is a human player."""
        return self == PlayerRole.HUMAN
    
    @property
    def is_bot(self) -> bool:
        """Check if this is a bot player."""
        return self == PlayerRole.BOT
    
    @property
    def requires_timing(self) -> bool:
        """Check if this player type requires artificial timing delays."""
        return self == PlayerRole.BOT
    
    def get_action_delay_range(self) -> tuple[float, float]:
        """
        Get the recommended action delay range for this player type.
        
        Returns:
            Tuple of (min_delay, max_delay) in seconds
        """
        if self == PlayerRole.BOT:
            return (0.5, 1.5)  # Bots should have 0.5-1.5s delays
        else:
            return (0.0, 0.0)  # Humans have no artificial delay