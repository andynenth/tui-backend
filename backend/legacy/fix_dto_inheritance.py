#!/usr/bin/env python3
"""
Fix dataclass inheritance issues in DTOs.

This script removes inheritance from Request/Response base classes
and adds the base fields directly to avoid dataclass field ordering issues.
"""

import os
import re
from pathlib import Path

def fix_dto_file(filepath):
    """Fix a single DTO file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Track if we made changes
    changed = False
    
    # Fix Request classes
    request_pattern = r'@dataclass\s*\nclass\s+(\w+Request)\(Request\):'
    for match in re.finditer(request_pattern, content):
        print(f"Found Request class: {match.group(1)} in {filepath}")
        changed = True
    
    # Fix Response classes  
    response_pattern = r'@dataclass\s*\nclass\s+(\w+Response)\(Response\):'
    for match in re.finditer(response_pattern, content):
        print(f"Found Response class: {match.group(1)} in {filepath}")
        changed = True
    
    if changed:
        print(f"  -> Would need to fix {filepath}")
    
    return changed

def main():
    """Main function."""
    dto_dir = Path("application/dto")
    
    if not dto_dir.exists():
        print(f"Directory {dto_dir} does not exist!")
        return
    
    # Find all Python files in dto directory
    dto_files = list(dto_dir.glob("*.py"))
    
    total_files = 0
    files_to_fix = []
    
    for filepath in dto_files:
        if filepath.name == "__init__.py" or filepath.name == "base.py":
            continue
            
        if fix_dto_file(filepath):
            files_to_fix.append(filepath)
            total_files += 1
    
    print(f"\nSummary:")
    print(f"Total files that need fixing: {total_files}")
    print(f"Files: {[f.name for f in files_to_fix]}")

if __name__ == "__main__":
    main()