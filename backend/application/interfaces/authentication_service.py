# application/interfaces/authentication_service.py
"""
Authentication service interface for the application layer.
This abstracts player authentication and authorization.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PlayerIdentity:
    """Value object representing a player's identity."""
    player_id: str
    player_name: str
    is_authenticated: bool = True
    is_guest: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AuthToken:
    """Value object representing an authentication token."""
    token: str
    player_id: str
    expires_at: Optional[datetime] = None
    is_valid: bool = True


class AuthenticationService(ABC):
    """
    Interface for player authentication and authorization.
    
    This abstracts the actual authentication mechanism from
    the application layer.
    """
    
    @abstractmethod
    async def authenticate_player(
        self,
        player_name: str,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Optional[PlayerIdentity]:
        """
        Authenticate a player.
        
        Args:
            player_name: The player's name
            credentials: Optional credentials (for non-guest players)
            
        Returns:
            PlayerIdentity if authentication successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_guest_player(
        self,
        player_name: str
    ) -> PlayerIdentity:
        """
        Create a guest player identity.
        
        Args:
            player_name: The guest player's name
            
        Returns:
            PlayerIdentity for the guest
        """
        pass
    
    @abstractmethod
    async def validate_token(
        self,
        token: str
    ) -> Optional[PlayerIdentity]:
        """
        Validate an authentication token.
        
        Args:
            token: The token to validate
            
        Returns:
            PlayerIdentity if token is valid, None otherwise
        """
        pass
    
    @abstractmethod
    async def generate_token(
        self,
        player_identity: PlayerIdentity
    ) -> AuthToken:
        """
        Generate an authentication token for a player.
        
        Args:
            player_identity: The player's identity
            
        Returns:
            AuthToken for the player
        """
        pass
    
    @abstractmethod
    async def revoke_token(
        self,
        token: str
    ) -> None:
        """
        Revoke an authentication token.
        
        Args:
            token: The token to revoke
        """
        pass
    
    @abstractmethod
    async def can_join_room(
        self,
        player_identity: PlayerIdentity,
        room_id: str
    ) -> bool:
        """
        Check if a player can join a specific room.
        
        Args:
            player_identity: The player's identity
            room_id: The room to check
            
        Returns:
            True if the player can join the room
        """
        pass
    
    @abstractmethod
    async def can_perform_action(
        self,
        player_identity: PlayerIdentity,
        action: str,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if a player can perform a specific action.
        
        Args:
            player_identity: The player's identity
            action: The action to check (e.g., "create_room", "start_game")
            resource: Optional resource identifier (e.g., room_id)
            
        Returns:
            True if the player can perform the action
        """
        pass