"""
Specialized WebSocket rate limiting for the game system.

Provides rate limiting tailored for real-time game communications.
"""

from typing import Optional, Dict, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import json

from .base import (
    IRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitAlgorithm,
    MemoryRateLimitStore
)
from .token_bucket import TokenBucketRateLimiter
from .sliding_window import SlidingWindowRateLimiter


@dataclass
class GameActionCost:
    """Defines costs for different game actions."""
    # Room operations
    create_room: int = 5
    join_room: int = 2
    leave_room: int = 1
    
    # Game actions
    start_game: int = 3
    play_piece: int = 1
    declare_pile: int = 1
    accept_redeal: int = 2
    decline_redeal: int = 2
    
    # Chat/messaging
    send_message: int = 1
    send_emoji: int = 1
    
    # Expensive operations
    request_replay: int = 10
    request_stats: int = 5


class GameWebSocketRateLimiter:
    """
    Specialized rate limiter for game WebSocket connections.
    
    Features:
    - Action-based costing
    - Player-specific limits
    - Room-level rate limiting
    - Burst protection
    """
    
    def __init__(
        self,
        player_limiter: Optional[IRateLimiter] = None,
        room_limiter: Optional[IRateLimiter] = None,
        global_limiter: Optional[IRateLimiter] = None,
        action_costs: Optional[GameActionCost] = None
    ):
        """
        Initialize game WebSocket rate limiter.
        
        Args:
            player_limiter: Per-player rate limits
            room_limiter: Per-room rate limits
            global_limiter: Global rate limits
            action_costs: Cost configuration for actions
        """
        # Default limiters if not provided
        if not player_limiter:
            player_config = RateLimitConfig(
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                capacity=60,
                refill_rate=1.0,  # 1 token per second
                burst_capacity=120
            )
            player_limiter = TokenBucketRateLimiter(player_config)
        
        if not room_limiter:
            room_config = RateLimitConfig(
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                capacity=300,
                window_size=timedelta(minutes=1)
            )
            room_limiter = SlidingWindowRateLimiter(room_config)
        
        self.player_limiter = player_limiter
        self.room_limiter = room_limiter
        self.global_limiter = global_limiter
        self.action_costs = action_costs or GameActionCost()
        
        # Track active connections
        self._connections: Dict[str, ConnectionInfo] = {}
        self._room_connections: Dict[str, Set[str]] = {}
        
        # Metrics
        self._metrics = {
            'total_actions': 0,
            'limited_actions': 0,
            'action_counts': {}
        }
    
    async def check_action(
        self,
        player_id: str,
        room_id: Optional[str],
        action_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> RateLimitResult:
        """
        Check if game action is allowed.
        
        Args:
            player_id: Player identifier
            room_id: Room identifier (if in room)
            action_type: Type of action
            data: Action data for cost calculation
            
        Returns:
            Rate limit result
        """
        # Get action cost
        cost = self._get_action_cost(action_type, data)
        
        # Track metrics
        self._metrics['total_actions'] += 1
        self._metrics['action_counts'][action_type] = \
            self._metrics['action_counts'].get(action_type, 0) + 1
        
        # Check player limit
        player_result = await self.player_limiter.check_rate_limit(
            f"player:{player_id}",
            cost
        )
        
        if not player_result.allowed:
            self._metrics['limited_actions'] += 1
            return player_result
        
        # Check room limit if applicable
        if room_id and self.room_limiter:
            room_result = await self.room_limiter.check_rate_limit(
                f"room:{room_id}",
                cost
            )
            
            if not room_result.allowed:
                self._metrics['limited_actions'] += 1
                return room_result
        
        # Check global limit if applicable
        if self.global_limiter:
            global_result = await self.global_limiter.check_rate_limit(
                "global",
                cost
            )
            
            if not global_result.allowed:
                self._metrics['limited_actions'] += 1
                return global_result
        
        # All checks passed
        return player_result
    
    async def consume_action(
        self,
        player_id: str,
        room_id: Optional[str],
        action_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Consume tokens for action if allowed.
        
        Returns:
            True if action allowed and consumed
        """
        # Check first
        result = await self.check_action(player_id, room_id, action_type, data)
        
        if not result.allowed:
            return False
        
        # Consume from all limiters
        cost = self._get_action_cost(action_type, data)
        
        await self.player_limiter.consume(f"player:{player_id}", cost)
        
        if room_id and self.room_limiter:
            await self.room_limiter.consume(f"room:{room_id}", cost)
        
        if self.global_limiter:
            await self.global_limiter.consume("global", cost)
        
        return True
    
    async def on_connect(self, player_id: str, connection_id: str) -> bool:
        """
        Handle new WebSocket connection.
        
        Returns:
            True if connection allowed
        """
        # Check connection limit
        connection_result = await self.player_limiter.check_rate_limit(
            f"connections:{player_id}",
            cost=1
        )
        
        if not connection_result.allowed:
            return False
        
        # Track connection
        self._connections[connection_id] = ConnectionInfo(
            player_id=player_id,
            connected_at=datetime.utcnow()
        )
        
        await self.player_limiter.consume(f"connections:{player_id}", 1)
        return True
    
    async def on_disconnect(self, connection_id: str) -> None:
        """Handle WebSocket disconnection."""
        if connection_id in self._connections:
            info = self._connections.pop(connection_id)
            
            # Clean up room associations
            if info.room_id:
                room_connections = self._room_connections.get(info.room_id, set())
                room_connections.discard(connection_id)
                
                if not room_connections:
                    self._room_connections.pop(info.room_id, None)
    
    async def on_join_room(self, connection_id: str, room_id: str) -> None:
        """Handle player joining room."""
        if connection_id in self._connections:
            self._connections[connection_id].room_id = room_id
            
            if room_id not in self._room_connections:
                self._room_connections[room_id] = set()
            
            self._room_connections[room_id].add(connection_id)
    
    async def on_leave_room(self, connection_id: str) -> None:
        """Handle player leaving room."""
        if connection_id in self._connections:
            info = self._connections[connection_id]
            
            if info.room_id:
                room_connections = self._room_connections.get(info.room_id, set())
                room_connections.discard(connection_id)
                
                if not room_connections:
                    self._room_connections.pop(info.room_id, None)
                
                info.room_id = None
    
    def _get_action_cost(self, action_type: str, data: Optional[Dict[str, Any]]) -> int:
        """Calculate cost for action."""
        # Base cost from configuration
        base_cost = getattr(self.action_costs, action_type, 1)
        
        # Adjust based on data
        if data:
            # Large messages cost more
            if 'message' in data:
                message_len = len(str(data['message']))
                base_cost += message_len // 100  # +1 per 100 chars
            
            # Bulk operations cost more
            if 'count' in data:
                base_cost *= min(data['count'], 10)
        
        return base_cost
    
    async def get_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Get rate limit stats for player."""
        stats = await self.player_limiter.get_stats(f"player:{player_id}")
        
        # Add connection info
        player_connections = [
            cid for cid, info in self._connections.items()
            if info.player_id == player_id
        ]
        
        stats['active_connections'] = len(player_connections)
        stats['connection_ids'] = player_connections
        
        return stats
    
    async def get_room_stats(self, room_id: str) -> Dict[str, Any]:
        """Get rate limit stats for room."""
        if not self.room_limiter:
            return {}
        
        stats = await self.room_limiter.get_stats(f"room:{room_id}")
        
        # Add connection info
        room_connections = self._room_connections.get(room_id, set())
        stats['active_connections'] = len(room_connections)
        
        return stats
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get overall metrics."""
        return {
            **self._metrics,
            'active_connections': len(self._connections),
            'active_rooms': len(self._room_connections),
            'limit_hit_rate': (
                self._metrics['limited_actions'] / self._metrics['total_actions']
                if self._metrics['total_actions'] > 0 else 0
            )
        }


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    player_id: str
    connected_at: datetime
    room_id: Optional[str] = None
    last_action: Optional[datetime] = None
    action_count: int = 0


class AdaptiveGameRateLimiter(GameWebSocketRateLimiter):
    """
    Adaptive rate limiter that adjusts based on game state.
    
    Features:
    - Higher limits during active gameplay
    - Lower limits in lobby/waiting
    - Burst allowance for game starts
    """
    
    def __init__(self, base_multiplier: float = 1.0):
        """Initialize adaptive game rate limiter."""
        # Create adaptive limiters
        player_limiter = self._create_adaptive_limiter(
            base_capacity=60,
            base_refill=1.0,
            multiplier=base_multiplier
        )
        
        room_limiter = self._create_adaptive_limiter(
            base_capacity=300,
            base_refill=5.0,
            multiplier=base_multiplier
        )
        
        super().__init__(player_limiter, room_limiter)
        
        # Track game states
        self._room_states: Dict[str, str] = {}  # room_id -> state
        self._state_multipliers = {
            'lobby': 0.5,
            'preparation': 1.0,
            'declaration': 1.5,
            'turn': 2.0,
            'scoring': 1.0
        }
    
    def _create_adaptive_limiter(
        self,
        base_capacity: int,
        base_refill: float,
        multiplier: float
    ) -> IRateLimiter:
        """Create limiter with adaptive capacity."""
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            capacity=int(base_capacity * multiplier),
            refill_rate=base_refill * multiplier,
            burst_capacity=int(base_capacity * multiplier * 2)
        )
        return TokenBucketRateLimiter(config)
    
    async def on_game_state_change(self, room_id: str, new_state: str) -> None:
        """Update rate limits based on game state."""
        self._room_states[room_id] = new_state
        
        # Adjust room limiter capacity based on state
        multiplier = self._state_multipliers.get(new_state, 1.0)
        
        # In practice, would update the limiter configuration
        # For now, track for cost adjustments
    
    def _get_action_cost(self, action_type: str, data: Optional[Dict[str, Any]]) -> int:
        """Adjust cost based on game state."""
        base_cost = super()._get_action_cost(action_type, data)
        
        # Get room state if available
        room_id = data.get('room_id') if data else None
        if room_id and room_id in self._room_states:
            state = self._room_states[room_id]
            multiplier = self._state_multipliers.get(state, 1.0)
            
            # Inverse relationship - higher multiplier means lower cost
            adjusted_cost = max(1, int(base_cost / multiplier))
            return adjusted_cost
        
        return base_cost