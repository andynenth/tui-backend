#!/usr/bin/env python3
"""
Move legacy files to quarantine directory for Phase 7.2
"""

import json
import os
import shutil
from pathlib import Path


def move_to_quarantine(source_path: str, preserve_structure: bool = True) -> bool:
    """Move a file to the legacy quarantine directory"""
    
    if not os.path.exists(source_path):
        print(f"  ⚠️  File not found: {source_path}")
        return False
    
    # Determine destination path
    if preserve_structure:
        dest_path = os.path.join('legacy', source_path)
    else:
        dest_path = os.path.join('legacy', os.path.basename(source_path))
    
    # Create destination directory
    dest_dir = os.path.dirname(dest_path)
    os.makedirs(dest_dir, exist_ok=True)
    
    try:
        # Move the file
        shutil.move(source_path, dest_path)
        print(f"  ✅ Moved: {source_path} -> {dest_path}")
        return True
    except Exception as e:
        print(f"  ❌ Error moving {source_path}: {e}")
        return False


def update_import_guard(file_path: str):
    """Add import guard to help detect legacy usage"""
    
    guard_file = f"{file_path}.guard.py"
    guard_content = f'''"""
Import guard for quarantined file: {file_path}
This file has been moved to legacy/ directory.
"""

import warnings

warnings.warn(
    f"Attempting to import quarantined legacy file: {file_path}\\n"
    f"This file has been moved to legacy/{file_path}\\n"
    f"Use clean architecture components instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from quarantine location (temporary for transition)
try:
    from legacy.{file_path.replace('/', '.').replace('.py', '')} import *
except ImportError:
    raise ImportError(
        f"Legacy file {file_path} has been quarantined. "
        f"Please use clean architecture replacements."
    )
'''
    
    # Write guard file in original location
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(guard_file, 'w') as f:
        f.write(guard_content)


def main():
    """Main quarantine process"""
    
    print("=== Phase 7.2.1: Moving Legacy Files to Quarantine ===\n")
    
    # Load the architecture analysis
    with open('phase7_architecture_analysis.json', 'r') as f:
        arch_analysis = json.load(f)
    
    # Get legacy files
    legacy_files = arch_analysis['summary']['files_by_type']['legacy']
    
    # Priority files to move first (core legacy components)
    priority_files = [
        'socket_manager.py',
        'shared_instances.py',
        'engine/room_manager.py',
        'engine/async_room_manager.py',
        'engine/game.py',
        'engine/bot_manager.py',
        'engine/scoring.py',
        'engine/player.py',
        'engine/piece.py',
        'engine/room.py',
        'engine/async_room.py',
        'engine/async_game.py',
        'engine/rules.py',
        'engine/ai.py',
        'engine/win_conditions.py'
    ]
    
    # Move priority files first
    print("=== Moving Priority Legacy Files ===")
    moved_count = 0
    
    for file_path in priority_files:
        if file_path in legacy_files:
            if move_to_quarantine(file_path):
                moved_count += 1
                # Don't create import guards yet - that could break things
    
    print(f"\n✅ Moved {moved_count} priority files to quarantine")
    
    # For now, we'll only move the core legacy files
    # Moving all 192 files at once could be risky
    
    print("\n=== Quarantine Status ===")
    print(f"- Moved: {moved_count} core legacy files")
    print(f"- Remaining: {len(legacy_files) - moved_count} legacy files")
    print(f"- Next step: Update imports and validate system")
    
    # Save quarantine status
    quarantine_status = {
        "phase": "7.2.1",
        "date": "2025-07-27",
        "moved_files": priority_files[:moved_count],
        "total_legacy_files": len(legacy_files),
        "status": "partial_quarantine"
    }
    
    with open('legacy/quarantine_status.json', 'w') as f:
        json.dump(quarantine_status, f, indent=2)
    
    print("\n⚠️  IMPORTANT: System validation required before proceeding!")
    print("Run validation tests to ensure system still functions correctly.")


if __name__ == '__main__':
    main()