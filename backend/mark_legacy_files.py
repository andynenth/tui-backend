#!/usr/bin/env python3
"""
Script to mark legacy files with deprecation headers for Phase 7.1
"""

import json
import os
from datetime import datetime


LEGACY_HEADER_TEMPLATE = '''"""
LEGACY_CODE: This file is scheduled for removal after Phase 6 migration
REPLACEMENT: {replacement}
REMOVAL_TARGET: Phase {removal_phase}
FEATURE_FLAG: {feature_flag}
DEPENDENCIES: {dependencies}
LAST_MODIFIED: {last_modified}
MIGRATION_STATUS: {migration_status}
"""

'''


def add_legacy_header(file_path, metadata):
    """Add legacy header to a Python file"""
    
    # Read the current file content
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  ❌ File not found: {file_path}")
        return False
    
    # Check if already has legacy header
    if "LEGACY_CODE:" in content:
        print(f"  ⏭️  Already marked: {file_path}")
        return True
    
    # Create the header
    header = LEGACY_HEADER_TEMPLATE.format(
        replacement=metadata.get('replacement', 'TBD'),
        removal_phase=metadata.get('removal_phase', '7.2'),
        feature_flag=metadata.get('feature_flag', 'N/A'),
        dependencies=', '.join(metadata.get('dependencies', [])),
        last_modified=metadata.get('last_modified', datetime.now().strftime('%Y-%m-%d')),
        migration_status=metadata.get('migration_status', 'ready_for_removal')
    )
    
    # Handle shebang lines
    if content.startswith('#!'):
        lines = content.split('\n', 1)
        new_content = lines[0] + '\n' + header + lines[1]
    else:
        new_content = header + content
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"  ✅ Marked: {file_path}")
    return True


def main():
    """Main function to mark legacy files"""
    
    print("=== Phase 7.1: Marking Legacy Files ===\n")
    
    # Load the legacy registry
    with open('legacy_registry.json', 'r') as f:
        registry = json.load(f)
    
    # Mark each legacy file
    marked_count = 0
    for file_info in registry['legacy_files']:
        file_path = file_info['path']
        # Remove 'backend/' prefix if present
        if file_path.startswith('backend/'):
            file_path = file_path[8:]
        print(f"\nProcessing: {file_path}")
        
        if os.path.exists(file_path) and add_legacy_header(file_path, file_info):
            marked_count += 1
    
    print(f"\n✅ Marked {marked_count} legacy files")
    
    # Also mark the main legacy entry points
    print("\n=== Marking Key Legacy Entry Points ===")
    
    key_files = [
        ('socket_manager.py', {
            'replacement': 'infrastructure/websocket/connection_manager.py',
            'removal_phase': '7.2',
            'feature_flag': 'USE_LEGACY_SOCKET_MANAGER',
            'dependencies': ['shared_instances.py'],
            'migration_status': 'ready_for_removal'
        }),
        ('shared_instances.py', {
            'replacement': 'infrastructure/dependencies.py',
            'removal_phase': '7.3',
            'feature_flag': 'USE_LEGACY_SHARED_INSTANCES',
            'dependencies': [],
            'migration_status': 'ready_for_removal'
        })
    ]
    
    for file_path, metadata in key_files:
        if os.path.exists(file_path):
            add_legacy_header(file_path, metadata)
    
    print("\n✅ Phase 7.1.3: Legacy file marking complete!")


if __name__ == '__main__':
    main()