#!/usr/bin/env python3
"""
Script to fix common attribute mismatches in use case files.
"""

import re
import os

# Replacements for room attributes
ROOM_REPLACEMENTS = [
    (r'room\.id(?![a-zA-Z_])', 'room.room_id'),
    (r'room\.code(?![a-zA-Z_])', 'room.room_id'),
    (r'room\.name(?![a-zA-Z_])', 'f"{room.host_name}\'s Room"'),
    (r'room\.host_id(?![a-zA-Z_])', 'PropertyMapper.get_room_attr(room, "host_id")'),
    (r'room\.current_game(?![a-zA-Z_])', 'room.game'),
    (r'room\.created_at(?![a-zA-Z_])', 'datetime.utcnow()'),
    (r'room\.settings\.is_private(?![a-zA-Z_])', 'PropertyMapper.get_room_attr(room, "settings.is_private")'),
    (r'room\.settings\.max_players(?![a-zA-Z_])', 'room.max_slots'),
    (r'room\.settings\.allow_bots(?![a-zA-Z_])', 'PropertyMapper.get_room_attr(room, "settings.allow_bots")'),
    (r'room\.settings\.win_condition_type(?![a-zA-Z_])', 'PropertyMapper.get_room_attr(room, "settings.win_condition_type")'),
    (r'room\.settings\.win_condition_value(?![a-zA-Z_])', 'PropertyMapper.get_room_attr(room, "settings.win_condition_value")'),
    (r'room\.settings\.(?![a-zA-Z_])', 'PropertyMapper.get_room_attr(room, "settings.")'),
]

# Replacements for player/slot attributes
PLAYER_REPLACEMENTS = [
    (r'slot\.id(?![a-zA-Z_])', 'PropertyMapper.generate_player_id(room.room_id, i)'),
    (r'player\.id(?![a-zA-Z_])', 'PropertyMapper.get_player_attr(player, "id", room.room_id, i)'),
    (r'player\.player_id(?![a-zA-Z_])', 'PropertyMapper.get_player_attr(player, "player_id", room.room_id, i)'),
    (r'slot\.games_played(?![a-zA-Z_])', 'PropertyMapper.get_safe(slot, "games_played", 0)'),
    (r'slot\.games_won(?![a-zA-Z_])', 'PropertyMapper.get_safe(slot, "games_won", 0)'),
    (r'player\.games_played(?![a-zA-Z_])', 'PropertyMapper.get_safe(player, "games_played", 0)'),
    (r'player\.games_won(?![a-zA-Z_])', 'PropertyMapper.get_safe(player, "games_won", 0)'),
]

# Replacements for game attributes
GAME_REPLACEMENTS = [
    (r'game\.id(?![a-zA-Z_])', 'game.game_id'),
    (r'game\.current_player_id(?![a-zA-Z_])', 'PropertyMapper.get_safe(game, "current_player_id")'),
    (r'game\.winner_id(?![a-zA-Z_])', 'PropertyMapper.get_safe(game, "winner_id")'),
]

# Check comparisons
COMPARISON_REPLACEMENTS = [
    (r'slot\.id == room\.host_id', 'PropertyMapper.is_host(slot.name, room.host_name)'),
    (r'slot and slot\.id == room\.host_id', 'slot and PropertyMapper.is_host(slot.name, room.host_name)'),
    (r'player\.id == room\.host_id', 'PropertyMapper.is_host(player.name, room.host_name)'),
]

def add_import_if_missing(content, file_path):
    """Add PropertyMapper import if missing."""
    if 'from application.utils import PropertyMapper' not in content:
        # Find the last import line
        import_lines = []
        lines = content.split('\n')
        last_import_idx = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_idx = i
        
        # Insert after last import
        lines.insert(last_import_idx + 1, 'from application.utils import PropertyMapper')
        content = '\n'.join(lines)
    
    # Also add datetime import if using datetime.utcnow()
    if 'datetime.utcnow()' in content and 'from datetime import datetime' not in content:
        lines = content.split('\n')
        last_import_idx = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_idx = i
        
        lines.insert(last_import_idx + 1, 'from datetime import datetime')
        content = '\n'.join(lines)
    
    return content

def fix_use_case_file(file_path):
    """Fix attribute mismatches in a use case file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Apply replacements
    for old, new in ROOM_REPLACEMENTS + PLAYER_REPLACEMENTS + GAME_REPLACEMENTS + COMPARISON_REPLACEMENTS:
        content = re.sub(old, new, content)
    
    # Add imports if needed
    if content != original_content:
        content = add_import_if_missing(content, file_path)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")
        return True
    return False

# Files to fix
use_case_files = [
    # Room management
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/room_management/leave_room.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/room_management/add_bot.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/room_management/remove_player.py',
    
    # Game
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/start_game.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/declare.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/play.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/accept_redeal.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/decline_redeal.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/handle_redeal_decision.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/request_redeal.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/leave_game.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/game/mark_player_ready.py',
    
    # Lobby
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/lobby/get_room_details.py',
    
    # Connection
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/connection/sync_client_state.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/connection/mark_client_ready.py',
    '/Users/nrw/python/tui-project/liap-tui/backend/application/use_cases/connection/handle_ping.py',
]

print("🔧 Fixing use case files...")
fixed_count = 0

for file_path in use_case_files:
    if os.path.exists(file_path):
        if fix_use_case_file(file_path):
            fixed_count += 1
    else:
        print(f"❌ File not found: {file_path}")

print(f"\n✅ Fixed {fixed_count} files!")