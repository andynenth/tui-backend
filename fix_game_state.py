#!/usr/bin/env python3
"""
Fix game state issues
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.api.dependencies import get_room_manager
from backend.engine.state_machine.core import GameAction, ActionType

async def fix_game_active_flag(room_id: str):
    """Fix game active flag if it's incorrectly set to False"""
    room_manager = get_room_manager()
    
    if room_id not in room_manager.rooms:
        print(f"Room {room_id} not found")
        return
    
    room = room_manager.rooms[room_id]
    game = room.game
    
    print(f"Current game.active: {game.active}")
    print(f"Current game.ended: {game.ended}")
    
    # Check if game should be active
    if not game.ended and not game.active:
        print("⚠️  Game is not ended but marked as inactive. Fixing...")
        game.active = True
        print("✅ Set game.active = True")
    
    # Check phase
    if hasattr(game, 'current_phase'):
        print(f"Current phase in game object: {game.current_phase}")
    
    # Check state machine
    if room.state_machine:
        current_phase = room.state_machine.current_phase
        print(f"Current phase in state machine: {current_phase}")
        
        if room.state_machine.is_running:
            print("✅ State machine is running")
        else:
            print("❌ State machine is NOT running")

async def trigger_bot_check(room_id: str):
    """Manually trigger bot manager to check the room"""
    from backend.engine.bot_manager import BotManager
    
    bot_manager = BotManager()
    
    # Send a phase_change event to trigger bot processing
    await bot_manager.handle_game_event(
        room_id,
        "phase_change",
        {
            "old_phase": "turn",
            "new_phase": "turn",
            "phase_data": {
                "current_player": "Alexanderium"
            }
        }
    )
    print("✅ Triggered bot manager check")

if __name__ == "__main__":
    import asyncio
    
    room_id = sys.argv[1] if len(sys.argv) > 1 else "1A8F34"
    
    print(f"\n=== Fixing Room {room_id} ===\n")
    
    # Run the fix
    asyncio.run(fix_game_active_flag(room_id))