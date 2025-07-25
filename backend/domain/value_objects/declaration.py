"""
Declaration value object - represents a player's pile count declaration.

This is an immutable value object that encapsulates declaration logic.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Declaration:
    """
    Immutable value object representing a player's declaration.
    
    A declaration is the number of piles a player claims they will capture
    in the upcoming round. Valid values are 0-8.
    """
    player_name: str
    pile_count: int
    is_forced: bool = False  # True if player was forced to declare non-zero
    
    def __post_init__(self):
        """Validate declaration on creation."""
        if not isinstance(self.pile_count, int):
            raise ValueError(f"Pile count must be an integer, got {type(self.pile_count)}")
        
        if self.pile_count < 0 or self.pile_count > 8:
            raise ValueError(f"Pile count must be between 0 and 8, got {self.pile_count}")
        
        if not self.player_name:
            raise ValueError("Player name cannot be empty")
    
    @classmethod
    def create(
        cls,
        player_name: str,
        pile_count: int,
        is_forced: bool = False
    ) -> "Declaration":
        """
        Factory method to create a declaration.
        
        Args:
            player_name: Name of the declaring player
            pile_count: Number of piles declared (0-8)
            is_forced: Whether player was forced to declare non-zero
            
        Returns:
            Declaration instance
            
        Raises:
            ValueError: If declaration is invalid
        """
        return cls(
            player_name=player_name,
            pile_count=pile_count,
            is_forced=is_forced
        )
    
    @property
    def is_zero(self) -> bool:
        """Check if this is a zero declaration."""
        return self.pile_count == 0
    
    @property
    def is_maximum(self) -> bool:
        """Check if this is the maximum declaration (8)."""
        return self.pile_count == 8
    
    def matches_actual(self, actual_piles: int) -> bool:
        """
        Check if declaration matches actual piles captured.
        
        Args:
            actual_piles: Number of piles actually captured
            
        Returns:
            True if declaration matches actual
        """
        return self.pile_count == actual_piles
    
    def get_difference(self, actual_piles: int) -> int:
        """
        Get the difference between declared and actual.
        
        Args:
            actual_piles: Number of piles actually captured
            
        Returns:
            Difference (can be negative)
        """
        return actual_piles - self.pile_count
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "player_name": self.player_name,
            "pile_count": self.pile_count,
            "is_forced": self.is_forced
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Declaration":
        """Create from dictionary."""
        return cls(
            player_name=data["player_name"],
            pile_count=data["pile_count"],
            is_forced=data.get("is_forced", False)
        )
    
    def __str__(self) -> str:
        """String representation."""
        forced_str = " (forced)" if self.is_forced else ""
        return f"{self.player_name} declares {self.pile_count}{forced_str}"


@dataclass(frozen=True)
class DeclarationSet:
    """
    Immutable value object representing all declarations for a round.
    
    Ensures that the total of all declarations does not equal 8.
    """
    declarations: tuple[Declaration, ...]
    
    def __post_init__(self):
        """Validate declaration set."""
        if len(self.declarations) == 0:
            raise ValueError("Declaration set cannot be empty")
        
        # Check for duplicates
        player_names = [d.player_name for d in self.declarations]
        if len(player_names) != len(set(player_names)):
            raise ValueError("Duplicate player declarations found")
        
        # Validate total is not 8
        total = self.get_total()
        if total == 8:
            raise ValueError(f"Total declarations cannot equal 8, got {total}")
    
    @classmethod
    def create(cls, declarations: list[Declaration]) -> "DeclarationSet":
        """
        Factory method to create a declaration set.
        
        Args:
            declarations: List of declarations
            
        Returns:
            DeclarationSet instance
            
        Raises:
            ValueError: If declarations are invalid
        """
        return cls(declarations=tuple(declarations))
    
    def get_total(self) -> int:
        """Get total of all declarations."""
        return sum(d.pile_count for d in self.declarations)
    
    def get_declaration_for(self, player_name: str) -> Optional[Declaration]:
        """Get declaration for specific player."""
        for declaration in self.declarations:
            if declaration.player_name == player_name:
                return declaration
        return None
    
    def has_all_players(self, player_names: list[str]) -> bool:
        """Check if all players have declared."""
        declared_names = {d.player_name for d in self.declarations}
        return all(name in declared_names for name in player_names)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "declarations": [d.to_dict() for d in self.declarations],
            "total": self.get_total()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DeclarationSet":
        """Create from dictionary."""
        declarations = [
            Declaration.from_dict(d) for d in data["declarations"]
        ]
        return cls.create(declarations)