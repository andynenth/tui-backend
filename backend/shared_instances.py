# backend/shared_instances.py (UPDATED)
"""
Centralized dependency management - follows IoC (Inversion of Control) pattern
This acts as a service container in your infrastructure
"""

from engine.room_manager import RoomManager

# Initialize shared instances without circular imports
shared_room_manager = RoomManager()

# Lazy initialization for components with dependencies
_shared_bot_manager = None
_game_controllers = {}

def get_bot_manager():
    """Lazy initialization pattern - only create when needed"""
    global _shared_bot_manager
    if _shared_bot_manager is None:
        from backend.engine.bot_manager import BotManager
        _shared_bot_manager = BotManager()
    return _shared_bot_manager

def get_game_controller(room_id: str):
    """Factory pattern for game controllers"""
    if room_id not in _game_controllers:
        from backend.engine.game_flow_controller import GameFlowController
        # Create controller without circular dependency
        _game_controllers[room_id] = GameFlowController(room_id)
    return _game_controllers[room_id]

# Export convenient names
shared_bot_manager = property(lambda self: get_bot_manager())