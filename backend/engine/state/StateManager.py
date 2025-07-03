"""State management coordinator for backend-frontend synchronization."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from .StateSnapshot import StateSnapshot
from ..state_machine.core import GamePhase

logger = logging.getLogger(__name__)


class StateManager:
    """Coordinates game state with versioning and broadcasts versioned snapshots.
    
    This integrates with the existing enterprise architecture automatic broadcasting system
    to provide versioned state snapshots for frontend synchronization.
    """
    
    def __init__(self, game_id: str, room_id: str):
        """Initialize state manager.
        
        Args:
            game_id: Unique game identifier
            room_id: Room ID for WebSocket broadcasting
        """
        self.game_id = game_id
        self.room_id = room_id
        self._version = 0
        self._snapshots: List[StateSnapshot] = []
        self._max_snapshots = 100  # Keep last 100 snapshots for history
        self._subscribers: List[Callable] = []
        self._lock = asyncio.Lock()
        
        # Cache for current state components
        self._current_phase: Optional[str] = None
        self._current_phase_data: Dict[str, Any] = {}
        self._current_players: Dict[str, Any] = {}
        self._current_round = 1
        self._current_turn = 0
    
    async def create_snapshot(
        self,
        phase: str,
        phase_data: Dict[str, Any],
        players: Dict[str, Any],
        round_number: int,
        turn_number: int,
        reason: str = "State update"
    ) -> StateSnapshot:
        """Create a new state snapshot and broadcast it.
        
        Args:
            phase: Current game phase
            phase_data: Phase-specific state data
            players: Player states
            round_number: Current round
            turn_number: Current turn
            reason: Human-readable reason for this state change
            
        Returns:
            The created StateSnapshot
        """
        async with self._lock:
            # Increment version
            self._version += 1
            
            # Create snapshot
            snapshot = StateSnapshot(
                version=self._version,
                game_id=self.game_id,
                phase=phase,
                phase_data=phase_data,
                players=players,
                round_number=round_number,
                turn_number=turn_number
            )
            
            # Store snapshot
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots.pop(0)
            
            # Update cached state
            self._current_phase = phase
            self._current_phase_data = phase_data
            self._current_players = players
            self._current_round = round_number
            self._current_turn = turn_number
            
            # Log state change
            logger.info(
                f"State v{self._version} created: {reason} "
                f"(phase={phase}, checksum={snapshot.checksum})"
            )
            
            # Broadcast state update using enterprise architecture
            await self._broadcast_snapshot(snapshot, reason)
            
            # Notify subscribers
            for subscriber in self._subscribers:
                try:
                    await subscriber(snapshot)
                except Exception as e:
                    logger.error(f"Subscriber error: {e}")
            
            return snapshot
    
    async def _broadcast_snapshot(self, snapshot: StateSnapshot, reason: str):
        """Broadcast state snapshot to all clients.
        
        This uses the enterprise architecture broadcast_custom_event for consistency.
        
        Args:
            snapshot: The state snapshot to broadcast
            reason: Human-readable reason for the update
        """
        try:
            # Import broadcast function
            try:
                from backend.socket_manager import broadcast
            except ImportError:
                # Handle different import paths
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from socket_manager import broadcast
            
            await broadcast(
                self.room_id,
                "state_update",
                {
                    "snapshot": snapshot.to_dict(),
                    "reason": reason,
                    "event_type": "state_update"
                }
            )
        except Exception as e:
            logger.error(f"Failed to broadcast state update: {e}")
    
    def get_current_snapshot(self) -> Optional[StateSnapshot]:
        """Get the most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None
    
    def get_snapshot_by_version(self, version: int) -> Optional[StateSnapshot]:
        """Get a specific snapshot by version number."""
        for snapshot in self._snapshots:
            if snapshot.version == version:
                return snapshot
        return None
    
    def get_version_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent version history.
        
        Args:
            limit: Maximum number of versions to return
            
        Returns:
            List of version info dictionaries
        """
        history = []
        for snapshot in self._snapshots[-limit:]:
            history.append({
                "version": snapshot.version,
                "phase": snapshot.phase,
                "timestamp": snapshot.timestamp.isoformat(),
                "checksum": snapshot.checksum
            })
        return history
    
    async def sync_from_game_state(
        self,
        game_state: Any,
        reason: str = "Game state sync"
    ) -> StateSnapshot:
        """Create snapshot from game engine state.
        
        This method extracts data from the game state machine and creates
        a versioned snapshot, integrating with the enterprise architecture.
        
        Args:
            game_state: Current game state from engine
            reason: Reason for the sync
            
        Returns:
            The created StateSnapshot
        """
        # Extract state from game engine
        phase = game_state.phase.value if hasattr(game_state.phase, 'value') else str(game_state.phase)
        phase_data = game_state.phase_data.copy() if hasattr(game_state, 'phase_data') else {}
        
        # Extract player data with JSON-safe conversion
        players = {}
        if hasattr(game_state, 'game') and hasattr(game_state.game, 'players'):
            for player_id, player in game_state.game.players.items():
                players[player_id] = {
                    "name": player.name,
                    "score": player.score,
                    "pieces_count": len(player.pieces) if hasattr(player, 'pieces') else 0,
                    "is_active": getattr(player, 'is_active', True),
                    "declared_piles": getattr(player, 'declared_piles', None),
                    "actual_piles": getattr(player, 'actual_piles', None)
                }
        
        # Get round and turn info
        round_number = game_state.game.current_round if hasattr(game_state.game, 'current_round') else 1
        turn_number = game_state.game.turn_number if hasattr(game_state.game, 'turn_number') else 0
        
        return await self.create_snapshot(
            phase=phase,
            phase_data=phase_data,
            players=players,
            round_number=round_number,
            turn_number=turn_number,
            reason=reason
        )
    
    async def integrate_with_state_machine(self, state_machine: Any):
        """Integrate StateManager with the game state machine.
        
        This subscribes to the enterprise architecture's automatic broadcasting
        to create versioned snapshots whenever state changes occur.
        
        Args:
            state_machine: The game state machine instance
        """
        # Store reference to state machine
        self.state_machine = state_machine
        
        # Hook into the enterprise architecture's update_phase_data
        original_update = state_machine.current_state.update_phase_data
        
        async def wrapped_update(updates: Dict[str, Any], reason: str = "", broadcast: bool = True):
            # Call original update
            await original_update(updates, reason, broadcast)
            
            # Create versioned snapshot if broadcasting is enabled
            if broadcast:
                await self.sync_from_game_state(state_machine.current_state, reason)
        
        # Replace method with wrapped version
        state_machine.current_state.update_phase_data = wrapped_update
        
        logger.info(f"StateManager integrated with state machine for game {self.game_id}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to state updates.
        
        Args:
            callback: Async function to call on state updates
        """
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from state updates."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    @property
    def current_version(self) -> int:
        """Get current version number."""
        return self._version
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StateManager(game={self.game_id}, version={self._version}, "
            f"phase={self._current_phase}, snapshots={len(self._snapshots)})"
        )