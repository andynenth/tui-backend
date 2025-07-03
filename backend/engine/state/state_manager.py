# backend/engine/state/state_manager.py

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from collections import deque

from .state_snapshot import StateSnapshot


class StateManager:
    """
    Manages versioned game state with automatic broadcasting.
    
    This is the backend counterpart to the frontend's UnifiedGameStore.
    It tracks all state changes with version numbers and checksums.
    """
    
    def __init__(self, game_id: str, room_id: str, max_history: int = 100):
        self.game_id = game_id
        self.room_id = room_id
        self.max_history = max_history
        
        # Version tracking
        self.current_version = 0
        self.current_snapshot: Optional[StateSnapshot] = None
        
        # History tracking (for debugging and potential rollback)
        self.snapshot_history: deque[StateSnapshot] = deque(maxlen=max_history)
        
        # Subscribers for state changes
        self.subscribers: List[Callable[[StateSnapshot], None]] = []
        
        # Lock for concurrent access
        self._lock = asyncio.Lock()
    
    async def create_snapshot(
        self,
        phase: str,
        phase_data: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        round_number: int,
        turn_number: int,
        reason: str = ""
    ) -> StateSnapshot:
        """
        Create a new state snapshot with incremented version.
        
        This is the main method for updating game state.
        All state changes should go through this method.
        """
        async with self._lock:
            # Increment version
            self.current_version += 1
            
            # Create snapshot
            snapshot = StateSnapshot(
                version=self.current_version,
                timestamp=time.time(),
                game_id=self.game_id,
                room_id=self.room_id,
                phase=phase,
                phase_data=phase_data.copy(),  # Defensive copy
                players=self._deep_copy_players(players),
                round_number=round_number,
                turn_number=turn_number,
                reason=reason
            )
            
            # Validate checksum
            if not snapshot.validate_checksum():
                raise ValueError("Snapshot checksum validation failed")
            
            # Update current state
            self.current_snapshot = snapshot
            
            # Add to history
            self.snapshot_history.append(snapshot)
            
            # Notify subscribers
            await self._notify_subscribers(snapshot)
            
            # Broadcast to clients
            await self._broadcast_snapshot(snapshot)
            
            return snapshot
    
    def get_current_snapshot(self) -> Optional[StateSnapshot]:
        """Get the current state snapshot"""
        return self.current_snapshot
    
    def get_snapshot_by_version(self, version: int) -> Optional[StateSnapshot]:
        """Get a specific snapshot by version number"""
        for snapshot in self.snapshot_history:
            if snapshot.version == version:
                return snapshot
        return None
    
    def get_version_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent version history for debugging.
        
        Returns simplified representation of recent snapshots.
        """
        history = []
        for snapshot in list(self.snapshot_history)[-limit:]:
            history.append({
                'version': snapshot.version,
                'timestamp': snapshot.timestamp,
                'phase': snapshot.phase,
                'reason': snapshot.reason,
                'checksum': snapshot.checksum
            })
        return history
    
    def subscribe(self, callback: Callable[[StateSnapshot], None]) -> Callable[[], None]:
        """
        Subscribe to state changes.
        
        Returns an unsubscribe function.
        """
        self.subscribers.append(callback)
        
        def unsubscribe():
            if callback in self.subscribers:
                self.subscribers.remove(callback)
        
        return unsubscribe
    
    async def _notify_subscribers(self, snapshot: StateSnapshot) -> None:
        """Notify all subscribers of state change"""
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(snapshot)
                else:
                    subscriber(snapshot)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
    
    async def _broadcast_snapshot(self, snapshot: StateSnapshot) -> None:
        """
        Broadcast state snapshot to all clients.
        
        This will be hooked into the existing broadcast system.
        """
        try:
            # Import here to avoid circular imports
            from backend.socket_manager import broadcast
            
            # Prepare data for broadcast
            broadcast_data = {
                'phase': snapshot.phase,
                'phase_data': snapshot.phase_data,
                'players': snapshot.players,
                'round': snapshot.round_number,
                'turn': snapshot.turn_number,
                'version': snapshot.version,
                'checksum': snapshot.checksum,
                'server_timestamp': snapshot.timestamp
            }
            
            # Use existing broadcast system
            await broadcast(
                self.room_id,
                'phase_change',
                broadcast_data
            )
            
        except ImportError:
            # During testing or if broadcast not available
            print(f"Would broadcast snapshot v{snapshot.version} to room {self.room_id}")
    
    def _deep_copy_players(self, players: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create a deep copy of player data"""
        return {
            player_name: player_data.copy()
            for player_name, player_data in players.items()
        }
    
    def validate_client_version(self, client_version: int) -> bool:
        """
        Check if client version is current.
        
        Used to detect when clients are out of sync.
        """
        return client_version == self.current_version
    
    def get_state_diff(self, from_version: int) -> List[StateSnapshot]:
        """
        Get all snapshots since a given version.
        
        Used for catching up clients that missed updates.
        """
        return [
            snapshot for snapshot in self.snapshot_history
            if snapshot.version > from_version
        ]