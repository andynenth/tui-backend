# infrastructure/auth/simple_auth_adapter.py
"""
Simple authentication implementation for the AuthenticationService interface.
"""

import logging
from typing import Optional, Dict, Any, Set
from datetime import datetime, timedelta
import secrets
import hashlib

from application.interfaces.authentication_service import (
    AuthenticationService,
    PlayerIdentity,
    AuthToken
)

logger = logging.getLogger(__name__)


class SimpleAuthAdapter(AuthenticationService):
    """
    Simple implementation of AuthenticationService.
    
    This provides basic authentication without external dependencies.
    In production, this would integrate with a real auth system.
    """
    
    def __init__(self):
        # In-memory storage (in production, use a database)
        self._tokens: Dict[str, AuthToken] = {}
        self._player_identities: Dict[str, PlayerIdentity] = {}
        self._revoked_tokens: Set[str] = set()
        
        # Simple permissions (in production, use proper RBAC)
        self._permissions = {
            "create_room": ["authenticated", "guest"],
            "join_room": ["authenticated", "guest"],
            "start_game": ["authenticated", "guest"],
            "admin": ["authenticated"]
        }
    
    async def authenticate_player(
        self,
        player_name: str,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Optional[PlayerIdentity]:
        """
        Authenticate a player.
        
        For this simple implementation, we just create identities
        based on player name. In production, this would verify
        credentials against a user database.
        
        Args:
            player_name: The player's name
            credentials: Optional credentials (ignored in simple impl)
            
        Returns:
            PlayerIdentity if authentication successful
        """
        # Generate a deterministic player ID from name
        player_id = self._generate_player_id(player_name)
        
        # Check if we already have this identity
        if player_id in self._player_identities:
            return self._player_identities[player_id]
        
        # Create new identity
        identity = PlayerIdentity(
            player_id=player_id,
            player_name=player_name,
            is_authenticated=bool(credentials),
            is_guest=not bool(credentials),
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "auth_method": "credentials" if credentials else "guest"
            }
        )
        
        # Store identity
        self._player_identities[player_id] = identity
        
        logger.info(f"Authenticated player {player_name} as {player_id}")
        
        return identity
    
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
        # Generate guest ID
        player_id = f"guest_{self._generate_player_id(player_name)}"
        
        # Create guest identity
        identity = PlayerIdentity(
            player_id=player_id,
            player_name=player_name,
            is_authenticated=False,
            is_guest=True,
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "auth_method": "guest"
            }
        )
        
        # Store identity
        self._player_identities[player_id] = identity
        
        logger.info(f"Created guest player {player_name} as {player_id}")
        
        return identity
    
    async def validate_token(
        self,
        token: str
    ) -> Optional[PlayerIdentity]:
        """
        Validate an authentication token.
        
        Args:
            token: The token to validate
            
        Returns:
            PlayerIdentity if token is valid
        """
        # Check if token is revoked
        if token in self._revoked_tokens:
            return None
        
        # Look up token
        auth_token = self._tokens.get(token)
        if not auth_token:
            return None
        
        # Check if token is still valid
        if not auth_token.is_valid:
            return None
        
        # Check expiration
        if auth_token.expires_at and auth_token.expires_at < datetime.utcnow():
            auth_token.is_valid = False
            return None
        
        # Get associated identity
        return self._player_identities.get(auth_token.player_id)
    
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
        # Generate secure random token
        token_value = secrets.token_urlsafe(32)
        
        # Set expiration (24 hours for authenticated, 4 hours for guests)
        if player_identity.is_guest:
            expires_at = datetime.utcnow() + timedelta(hours=4)
        else:
            expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create token
        auth_token = AuthToken(
            token=token_value,
            player_id=player_identity.player_id,
            expires_at=expires_at,
            is_valid=True
        )
        
        # Store token
        self._tokens[token_value] = auth_token
        
        logger.info(f"Generated token for player {player_identity.player_id}")
        
        return auth_token
    
    async def revoke_token(
        self,
        token: str
    ) -> None:
        """
        Revoke an authentication token.
        
        Args:
            token: The token to revoke
        """
        self._revoked_tokens.add(token)
        
        # Also mark as invalid if it exists
        if token in self._tokens:
            self._tokens[token].is_valid = False
        
        logger.info(f"Revoked token {token[:8]}...")
    
    async def can_join_room(
        self,
        player_identity: PlayerIdentity,
        room_id: str
    ) -> bool:
        """
        Check if a player can join a specific room.
        
        For this simple implementation, all players can join any room.
        In production, this would check room permissions, bans, etc.
        
        Args:
            player_identity: The player's identity
            room_id: The room to check
            
        Returns:
            True if the player can join the room
        """
        # Simple implementation: everyone can join
        # In production: check room settings, ban lists, etc.
        return True
    
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
            action: The action to check
            resource: Optional resource identifier
            
        Returns:
            True if the player can perform the action
        """
        # Get allowed roles for this action
        allowed_roles = self._permissions.get(action, [])
        
        # Check player's role
        if player_identity.is_guest and "guest" in allowed_roles:
            return True
        
        if player_identity.is_authenticated and "authenticated" in allowed_roles:
            return True
        
        # Check specific permissions in metadata
        player_permissions = player_identity.metadata.get("permissions", [])
        if action in player_permissions:
            return True
        
        # Default deny
        return False
    
    def _generate_player_id(self, player_name: str) -> str:
        """Generate a deterministic player ID from name."""
        # Use SHA256 to generate a consistent ID from name
        # In production, use proper UUID generation
        hash_input = f"player_{player_name}_{player_name.lower()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        now = datetime.utcnow()
        expired_tokens = []
        
        for token, auth_token in self._tokens.items():
            if auth_token.expires_at and auth_token.expires_at < now:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self._tokens[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        
        return len(expired_tokens)