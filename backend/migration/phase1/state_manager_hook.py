"""
State Manager Hook for Enterprise Architecture Integration

This module shows how to inject StateManager into the existing enterprise
architecture without modifying the base state machine code.
"""

import time
from typing import Dict, Any, Optional
from backend.engine.state.state_manager import StateManager


class StateManagerHook:
    """
    Hooks StateManager into the existing enterprise architecture's
    update_phase_data() method to add versioning and checksums.
    """
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self._hooked = False
        
    def inject_into_state(self, game_state) -> None:
        """
        Inject StateManager into a GameState instance.
        This wraps the _auto_broadcast_phase_change method to include versioning.
        """
        if self._hooked:
            return
            
        # Store original method
        original_broadcast = game_state._auto_broadcast_phase_change
        
        # Create wrapped version
        async def versioned_broadcast(reason: str) -> None:
            """Enhanced broadcast that includes version and checksum"""
            
            # First, create a state snapshot
            phase = game_state.phase_name.value
            phase_data = game_state.phase_data.copy()
            
            # Get game data
            game = game_state.state_machine.game
            players_data = {}
            if hasattr(game, 'players'):
                for player in game.players:
                    player_name = getattr(player, 'name', str(player))
                    players_data[player_name] = {
                        'score': getattr(player, 'score', 0),
                        'pieces_count': len(getattr(player, 'hand', [])),
                        'declared': getattr(player, 'declared', 0),
                        'piles_won': getattr(player, 'piles_won', 0)
                    }
            
            # Create versioned snapshot
            snapshot = await self.state_manager.create_snapshot(
                phase=phase,
                phase_data=phase_data,
                players=players_data,
                round_number=getattr(game, 'round_number', 1),
                turn_number=getattr(game, 'turn_number', 0),
                reason=reason
            )
            
            # Now call original broadcast
            await original_broadcast(reason)
            
            # The broadcast above sent the phase_change event
            # Now we need to ensure version/checksum are included
            # We'll do this by intercepting the broadcast call itself
            
        # Replace method
        game_state._auto_broadcast_phase_change = versioned_broadcast
        self._hooked = True
        
    def inject_into_broadcast(self, broadcast_func):
        """
        Wraps the broadcast function to include version and checksum
        in all phase_change events.
        """
        async def versioned_broadcast_func(room_id: str, event: str, data: dict):
            """Enhanced broadcast that adds version/checksum to phase_change events"""
            
            # If this is a phase_change event, add version info
            if event == "phase_change" and self.state_manager:
                current_snapshot = self.state_manager.current_snapshot
                if current_snapshot:
                    data['version'] = current_snapshot.version
                    data['checksum'] = current_snapshot.checksum
                    data['server_timestamp'] = current_snapshot.timestamp
            
            # Call original broadcast
            return await broadcast_func(room_id, event, data)
            
        return versioned_broadcast_func


def setup_state_manager_integration(game_state_machine, room_id: str) -> StateManager:
    """
    Set up StateManager integration with an existing game state machine.
    
    Args:
        game_state_machine: The existing GameStateMachine instance
        room_id: The room ID for this game
        
    Returns:
        StateManager: The configured state manager instance
    """
    # Create StateManager
    game_id = f"game_{room_id}_{int(time.time())}"
    state_manager = StateManager(game_id=game_id, room_id=room_id)
    
    # Create hook
    hook = StateManagerHook(state_manager)
    
    # Inject into current state
    if hasattr(game_state_machine, 'current_state') and game_state_machine.current_state:
        hook.inject_into_state(game_state_machine.current_state)
    
    # Store reference in state machine for later access
    game_state_machine._state_manager = state_manager
    game_state_machine._state_manager_hook = hook
    
    # Hook into state machine's broadcast method instead of transition
    original_broadcast = game_state_machine.broadcast_event
    
    async def hooked_broadcast(event: str, data: dict):
        """Broadcast that creates state snapshots for phase changes"""
        # Create snapshot for phase changes
        if event == "phase_change":
            await state_manager.create_snapshot(
                data.get('phase', game_state_machine.get_current_phase()),
                data.get('phase_data', game_state_machine.get_phase_data()),
                f"Phase change broadcast: {event}"
            )
        
        # Call original broadcast
        return await original_broadcast(event, data)
    
    game_state_machine.broadcast_event = hooked_broadcast
    
    return state_manager


# Example usage in room initialization:
"""
# In room.py or where game is initialized:

from backend.migration.phase1.state_manager_hook import setup_state_manager_integration

class Room:
    async def start_game(self):
        # ... existing game initialization ...
        
        # Add StateManager integration
        self.state_manager = setup_state_manager_integration(
            self.game_state_machine,
            self.room_id
        )
        
        # Now all state changes will be versioned!
"""


# For modifying the broadcast function globally:
"""
# In socket_manager.py or at app startup:

from backend.migration.phase1.state_manager_hook import StateManagerHook

# Assuming you have access to state managers by room_id
state_managers = {}  # room_id -> StateManager

# Wrap the broadcast function
original_broadcast = broadcast

async def versioned_broadcast(room_id: str, event: str, data: dict):
    if event == "phase_change" and room_id in state_managers:
        state_manager = state_managers[room_id]
        if state_manager.current_snapshot:
            data['version'] = state_manager.current_snapshot.version
            data['checksum'] = state_manager.current_snapshot.checksum
            
    return await original_broadcast(room_id, event, data)

# Replace globally
broadcast = versioned_broadcast
"""