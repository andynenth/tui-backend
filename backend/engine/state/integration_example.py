"""Example of integrating StateManager with the existing game state machine."""

import logging
from typing import Optional
from .StateManager import StateManager
from ..state_machine.game_state_machine import GameStateMachine
from ..state_machine.base_state import GameState

logger = logging.getLogger(__name__)


class StateManagerIntegration:
    """Integration helper for StateManager with existing enterprise architecture."""
    
    @staticmethod
    async def integrate_state_manager(
        game_state_machine: GameStateMachine,
        game_id: str,
        room_id: str
    ) -> StateManager:
        """Integrate StateManager with an existing game state machine.
        
        This hooks into the enterprise architecture's automatic broadcasting system
        to create versioned snapshots on every state change.
        
        Args:
            game_state_machine: The game state machine to integrate with
            game_id: Unique game identifier
            room_id: Room ID for broadcasting
            
        Returns:
            The integrated StateManager instance
        """
        # Create StateManager instance
        state_manager = StateManager(game_id, room_id)
        
        # Store reference in state machine for access
        game_state_machine.state_manager = state_manager
        
        # Hook into all state changes by wrapping update_phase_data
        original_methods = {}
        
        for phase, state in game_state_machine.states.items():
            # Store original method
            original_methods[phase] = state.update_phase_data
            
            # Create wrapped version that creates snapshots
            async def create_wrapped_update(state_obj: GameState):
                original_update = original_methods[state_obj.phase_name]
                
                async def wrapped_update(updates, reason="", broadcast=True):
                    # Call original update (enterprise architecture)
                    await original_update(updates, reason, broadcast)
                    
                    # Create versioned snapshot after update
                    if broadcast and game_state_machine.is_running:
                        try:
                            # Extract current game state
                            game = game_state_machine.game
                            
                            # Build players data
                            players_data = {}
                            if hasattr(game, 'players'):
                                for player_id, player in game.players.items():
                                    players_data[player_id] = {
                                        "name": player.name,
                                        "score": getattr(player, 'score', 0),
                                        "pieces_count": len(getattr(player, 'pieces', [])),
                                        "is_active": getattr(player, 'is_active', True),
                                        "hand_size": len(getattr(player, 'hand', [])),
                                        "declared_piles": getattr(player, 'declared_piles', None),
                                        "actual_piles": getattr(player, 'actual_piles', None)
                                    }
                            
                            # Create snapshot
                            await state_manager.create_snapshot(
                                phase=state_obj.phase_name.value,
                                phase_data=state_obj.phase_data,
                                players=players_data,
                                round_number=getattr(game, 'current_round', 1),
                                turn_number=getattr(game, 'turn_number', 0),
                                reason=f"[{state_obj.phase_name.value}] {reason}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to create state snapshot: {e}")
                
                return wrapped_update
            
            # Replace method with wrapped version
            state.update_phase_data = await create_wrapped_update(state)
        
        # Also hook into broadcast_custom_event for non-phase-data events
        for phase, state in game_state_machine.states.items():
            original_broadcast = state.broadcast_custom_event
            
            async def create_wrapped_broadcast(state_obj: GameState):
                original = original_broadcast
                
                async def wrapped_broadcast(event_type, data, reason=""):
                    # Call original broadcast
                    await original(event_type, data, reason)
                    
                    # For certain events, create snapshots
                    snapshot_events = {"play", "declaration", "scoring_update", "round_complete"}
                    if event_type in snapshot_events:
                        try:
                            game = game_state_machine.game
                            
                            # Build players data
                            players_data = {}
                            if hasattr(game, 'players'):
                                for player_id, player in game.players.items():
                                    players_data[player_id] = {
                                        "name": player.name,
                                        "score": getattr(player, 'score', 0),
                                        "pieces_count": len(getattr(player, 'pieces', [])),
                                        "is_active": getattr(player, 'is_active', True)
                                    }
                            
                            # Create snapshot for important events
                            await state_manager.create_snapshot(
                                phase=state_obj.phase_name.value,
                                phase_data=state_obj.phase_data,
                                players=players_data,
                                round_number=getattr(game, 'current_round', 1),
                                turn_number=getattr(game, 'turn_number', 0),
                                reason=f"[Event: {event_type}] {reason}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to create event snapshot: {e}")
                
                return wrapped_broadcast
            
            state.broadcast_custom_event = await create_wrapped_broadcast(state)
        
        logger.info(f"StateManager integrated with game {game_id}")
        return state_manager


# Example usage in game initialization:
"""
# In your game setup code:
from backend.engine.state.integration_example import StateManagerIntegration

# After creating game and state machine
game = Game(...)
state_machine = GameStateMachine(game)

# Integrate StateManager
state_manager = await StateManagerIntegration.integrate_state_manager(
    state_machine,
    game_id="game123",
    room_id="room456"
)

# Now all state changes will automatically create versioned snapshots
# Frontend can request specific versions or get version history:
current_snapshot = state_manager.get_current_snapshot()
version_history = state_manager.get_version_history()
"""