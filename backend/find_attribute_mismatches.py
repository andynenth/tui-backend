#!/usr/bin/env python3
"""
Script to find all attribute mismatches in use cases.
This helps identify all places that need fixing.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Patterns to search for incorrect attributes
INCORRECT_PATTERNS = {
    # Room attributes
    r'room\.id(?![a-zA-Z_])': 'room.room_id',
    r'room\.current_game': 'room.game',
    r'room\.host_id': 'room.host_name',
    r'room\.settings\.': 'room.<direct_property>',
    r'room\.code': 'room.room_id',
    r'room\.name': 'f"{room.host_name}\'s Room"',
    r'room\.created_at': 'datetime.utcnow()',
    
    # Player/slot attributes
    r'player\.id(?![a-zA-Z_])': 'player.name or generate ID',
    r'slot\.id(?![a-zA-Z_])': 'slot.name or generate ID',
    r'player\.player_id': 'player.name',
    r'player\.games_played': 'getattr(player, "games_played", 0)',
    r'player\.games_won': 'getattr(player, "games_won", 0)',
    
    # Game attributes
    r'game\.id(?![a-zA-Z_])': 'game.game_id',
    r'game\.current_player_id': 'calculate from game state',
    r'game\.winner_id': 'calculate from game state',
}


def find_mismatches(directory: str) -> List[Tuple[str, int, str, str]]:
    """Find all attribute mismatches in Python files."""
    mismatches = []
    
    for root, dirs, files in os.walk(directory):
        # Skip test directories
        if 'test' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, suggestion in INCORRECT_PATTERNS.items():
                            if re.search(pattern, line):
                                # Skip comments
                                if line.strip().startswith('#'):
                                    continue
                                    
                                mismatches.append((
                                    filepath,
                                    line_num,
                                    line.strip(),
                                    suggestion
                                ))
                
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return mismatches


def main():
    """Find and report all attribute mismatches."""
    print("🔍 Searching for attribute mismatches in use cases...\n")
    
    # Search in use cases directory
    use_cases_dir = "application/use_cases"
    mismatches = find_mismatches(use_cases_dir)
    
    if not mismatches:
        print("✅ No attribute mismatches found!")
        return
    
    # Group by file
    files_with_issues = {}
    for filepath, line_num, line, suggestion in mismatches:
        if filepath not in files_with_issues:
            files_with_issues[filepath] = []
        files_with_issues[filepath].append((line_num, line, suggestion))
    
    # Report findings
    print(f"❌ Found {len(mismatches)} attribute mismatches in {len(files_with_issues)} files:\n")
    
    for filepath, issues in files_with_issues.items():
        rel_path = filepath.replace('application/use_cases/', '')
        print(f"📄 {rel_path}")
        
        for line_num, line, suggestion in issues:
            print(f"   Line {line_num}: {line}")
            print(f"   ➡️  Suggestion: Use {suggestion}")
            print()
    
    # Summary
    print("\n📊 Summary:")
    print(f"   - Total mismatches: {len(mismatches)}")
    print(f"   - Files affected: {len(files_with_issues)}")
    print("\n💡 Use DOMAIN_MODEL_REFERENCE.md for correct attribute names")


if __name__ == "__main__":
    main()