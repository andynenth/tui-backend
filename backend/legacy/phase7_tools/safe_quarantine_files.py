#!/usr/bin/env python3
"""
Identify and quarantine only safe legacy files with no active dependencies
"""

import json
import os
import shutil


def move_safe_file(file_path: str) -> bool:
    """Move a safe file to quarantine"""
    
    if not os.path.exists(file_path):
        return False
    
    dest_path = os.path.join('legacy', file_path)
    dest_dir = os.path.dirname(dest_path)
    os.makedirs(dest_dir, exist_ok=True)
    
    try:
        shutil.move(file_path, dest_path)
        print(f"  ✅ Moved: {file_path}")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Quarantine only safe files"""
    
    print("=== Phase 7.2: Safe Partial Quarantine ===\n")
    
    # Load dependency analysis
    with open('legacy_dependency_analysis.json', 'r') as f:
        dep_analysis = json.load(f)
    
    # Get files with no dependencies from Phase 7.2.1
    safe_files = dep_analysis['removal_phases']['phase_7.2.1']
    
    # Filter for only test files and utility scripts (safest to move)
    very_safe_files = [
        f for f in safe_files 
        if f.startswith('tests/') or 
           f.endswith('_test.py') or
           f in [
               'verify_adapter_only_mode_simple.py',
               'simple_ws_test.py',
               'verify_adapter_only_mode.py',
               'fix_dto_inheritance.py',
               'run_tests.py',
               'start_golden_master_capture.py',
               'extract_legacy_handlers.py',
               'fix_domain_imports.py',
               'run_phase_tests.py',
               'analyze_golden_master_mismatches.py',
               'benchmark_async.py',
               'async_migration_example.py',
               'trigger_adapter_init.py',
               'architecture_status_dashboard.py',
               'verify_adapter_files.py',
               'check_adapter_integration.py',
               'fix_dto_base_classes.py',
               'monitor_shadow_mode.py'
           ]
    ]
    
    print(f"Found {len(very_safe_files)} safe files to quarantine")
    print("(Test files and utility scripts with no dependencies)\n")
    
    moved_count = 0
    for file_path in very_safe_files[:20]:  # Move first 20 as a test
        if move_safe_file(file_path):
            moved_count += 1
    
    print(f"\n✅ Safely quarantined {moved_count} files")
    
    # Update quarantine status
    status = {
        "phase": "7.2",
        "step": "partial_safe_quarantine",
        "date": "2025-07-27",
        "moved_files": very_safe_files[:moved_count],
        "status": "partial_quarantine_safe_files_only",
        "notes": "Only moved test files and utility scripts with no dependencies"
    }
    
    with open('legacy/quarantine_status.json', 'w') as f:
        json.dump(status, f, indent=2)
    
    print("\n⚠️  Core legacy files NOT moved due to active dependencies:")
    print("  - socket_manager.py (used by infrastructure)")
    print("  - engine/*.py files (used by state machine)")
    print("  - shared_instances.py (used by socket_manager)")
    print("\nThese require adapter layer or import fixes first!")


if __name__ == '__main__':
    main()