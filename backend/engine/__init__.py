# backend/engine/__init__.py
"""
Package initialization - handles circular import resolution
"""

# Import order matters - define classes before cross-references
from .phase_manager import PhaseManager, GamePhase
from .bot_manager import BotManager
from .game_flow_controller import GameFlowController

# Create singleton instances
_bot_manager = BotManager()
_controllers = {}

def get_bot_manager():
    return _bot_manager

def get_game_controller(room_id: str) -> GameFlowController:
    if room_id not in _controllers:
        controller = GameFlowController(room_id)
        controller.set_bot_manager(_bot_manager)
        _controllers[room_id] = controller
    return _controllers[room_id]

# Wire dependencies
_bot_manager.set_game_controller_getter(get_game_controller)