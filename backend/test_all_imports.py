#!/usr/bin/env python3
"""
Quick script to test all critical imports and identify issues.
Run this to diagnose import problems in the adapter system.
"""

import sys
import traceback
from typing import Dict, List, Tuple


def test_import(module_path: str) -> Tuple[bool, str]:
    """
    Test if a module can be imported.
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        __import__(module_path)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    """Run import tests and report results."""
    print("=" * 80)
    print("IMPORT VALIDATION TEST")
    print("=" * 80)
    print()
    
    # Define test categories
    tests = {
        "Core Adapters": [
            "api.adapters.room_adapters",
            "api.adapters.game_adapters",
            "api.adapters.connection_adapters",
            "api.adapters.integrated_adapter_system",
        ],
        
        "Infrastructure": [
            "infrastructure.adapters.legacy_repository_bridge",
            "infrastructure.adapters.clean_architecture_adapter",
        ],
        
        "Room Use Cases": [
            "application.use_cases.room_management.create_room",
            "application.use_cases.room_management.join_room",
            "application.use_cases.room_management.leave_room",
        ],
        
        "Game Use Cases (Problematic)": [
            "application.use_cases.game.play",
            "application.use_cases.game.request_redeal",
            "application.use_cases.game.declare",
            "application.use_cases.game.start_game",
        ],
        
        "Domain Events": [
            "domain.events.game_events",
            "domain.events.player_events",
            "domain.events.room_events",
            "domain.events.all_events",
        ],
    }
    
    all_passed = True
    problem_imports = []
    
    # Run tests by category
    for category, modules in tests.items():
        print(f"{category}:")
        print("-" * len(category))
        
        for module in modules:
            success, error = test_import(module)
            
            if success:
                print(f"  ✓ {module}")
            else:
                print(f"  ✗ {module}")
                print(f"    Error: {error}")
                all_passed = False
                problem_imports.append((module, error))
        
        print()
    
    # Detailed analysis of failures
    if problem_imports:
        print("=" * 80)
        print("DETAILED ERROR ANALYSIS")
        print("=" * 80)
        print()
        
        # Group by error type
        error_patterns = {
            "PlayerPlayedPieces": [],
            "RedealVoteStarted": [],
            "Other": []
        }
        
        for module, error in problem_imports:
            if "PlayerPlayedPieces" in error:
                error_patterns["PlayerPlayedPieces"].append((module, error))
            elif "RedealVoteStarted" in error:
                error_patterns["RedealVoteStarted"].append((module, error))
            else:
                error_patterns["Other"].append((module, error))
        
        # Report by error type
        if error_patterns["PlayerPlayedPieces"]:
            print("❌ PlayerPlayedPieces Import Error:")
            print("  The event 'PlayerPlayedPieces' does not exist.")
            print("  It should be 'PiecesPlayed' from domain.events.game_events")
            print("  Affected modules:")
            for module, _ in error_patterns["PlayerPlayedPieces"]:
                print(f"    - {module}")
            print()
        
        if error_patterns["RedealVoteStarted"]:
            print("❌ RedealVoteStarted Import Error:")
            print("  The event 'RedealVoteStarted' does not exist.")
            print("  This import should be removed or the event should be created.")
            print("  Affected modules:")
            for module, _ in error_patterns["RedealVoteStarted"]:
                print(f"    - {module}")
            print()
        
        if error_patterns["Other"]:
            print("❌ Other Import Errors:")
            for module, error in error_patterns["Other"]:
                print(f"  {module}:")
                print(f"    {error}")
            print()
        
        # Import chain analysis
        print("=" * 80)
        print("IMPORT CHAIN ANALYSIS")
        print("=" * 80)
        print()
        print("When creating a room, this is the import chain that fails:")
        print()
        print("1. room_adapters.py imports legacy_repository_bridge")
        print("2. legacy_repository_bridge imports infrastructure/adapters/__init__.py")
        print("3. __init__.py imports clean_architecture_adapter.py")
        print("4. clean_architecture_adapter imports ALL use cases")
        print("5. Some use cases have broken imports → FAILURE")
        print()
        print("This is why room creation fails even though it has nothing to do")
        print("with playing pieces or redeals!")
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_modules = sum(len(modules) for modules in tests.values())
    failed_count = len(problem_imports)
    
    print(f"Total modules tested: {total_modules}")
    print(f"Successful imports: {total_modules - failed_count}")
    print(f"Failed imports: {failed_count}")
    print()
    
    if all_passed:
        print("✅ All imports successful!")
        return 0
    else:
        print("❌ Import validation failed!")
        print()
        print("To fix room creation, you need to fix these imports:")
        print("1. Fix the 'PlayerPlayedPieces' → 'PiecesPlayed' import")
        print("2. Remove or fix the 'RedealVoteStarted' import")
        return 1


if __name__ == "__main__":
    sys.exit(main())