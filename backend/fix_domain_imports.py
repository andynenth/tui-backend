#!/usr/bin/env python3
"""Fix domain event imports in application layer."""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix room event imports
    content = re.sub(
        r'from domain\.events\.room_events import (.+)',
        r'from backend.domain.events.room_events import \1',
        content
    )
    
    # Fix game event imports
    content = re.sub(
        r'from domain\.events\.game_events import (.+)',
        r'from backend.domain.events.game_events import \1',
        content
    )
    
    # Fix base event imports
    content = re.sub(
        r'from domain\.events\.base import (.+)',
        r'from backend.domain.events.base import \1',
        content
    )
    
    # Fix connection event imports
    content = re.sub(
        r'from domain\.events\.connection_events import (.+)',
        r'from backend.domain.events.connection_events import \1',
        content
    )
    
    # Fix all_events imports
    content = re.sub(
        r'from domain\.events\.all_events import (.+)',
        r'from backend.domain.events.all_events import \1',
        content
    )
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function."""
    use_cases_dir = Path("application/use_cases")
    
    fixed_count = 0
    
    # Walk through all Python files in use_cases directory
    for root, dirs, files in os.walk(use_cases_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = Path(root) / file
                if fix_imports_in_file(filepath):
                    print(f"Fixed imports in: {filepath}")
                    fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()