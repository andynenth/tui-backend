#!/usr/bin/env python3
"""
Validate that the contract testing infrastructure is properly set up.
Run this before attempting to capture golden masters.
"""

import sys
import os
from pathlib import Path
import importlib.util

def check_module(module_name, file_path):
    """Check if a Python module can be imported"""
    try:
        if file_path.exists():
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "OK"
        else:
            return False, f"File not found: {file_path}"
    except Exception as e:
        return False, f"Import error: {str(e)}"

def main():
    """Run validation checks"""
    print("Contract Testing Infrastructure Validation")
    print("=" * 50)
    
    # Check we're in the right directory
    if not Path("engine").exists() or not Path("api").exists():
        print("❌ ERROR: Must run from backend directory")
        print("   cd backend && python validate_test_setup.py")
        return False
    
    all_good = True
    
    # Check directory structure
    print("\n1. Checking directory structure...")
    dirs_to_check = [
        "tests/contracts",
        "tests/contracts/golden_masters",
        "tests/behavioral",
        "tests/behavioral/results",
        "shadow_mode_data"
    ]
    
    for dir_path in dirs_to_check:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} - Creating...")
            path.mkdir(parents=True, exist_ok=True)
    
    # Check contract testing modules
    print("\n2. Checking contract testing modules...")
    modules_to_check = [
        ("websocket_contracts", Path("tests/contracts/websocket_contracts.py")),
        ("golden_master", Path("tests/contracts/golden_master.py")),
        ("parallel_runner", Path("tests/contracts/parallel_runner.py")),
        ("capture_golden_masters", Path("tests/contracts/capture_golden_masters.py")),
    ]
    
    for module_name, file_path in modules_to_check:
        success, message = check_module(module_name, file_path)
        if success:
            print(f"   ✅ {module_name}")
        else:
            print(f"   ❌ {module_name}: {message}")
            all_good = False
    
    # Check behavioral testing modules
    print("\n3. Checking behavioral testing modules...")
    behavioral_modules = [
        ("test_game_flows", Path("tests/behavioral/test_game_flows.py")),
        ("test_game_mechanics", Path("tests/behavioral/test_game_mechanics.py")),
        ("test_integration", Path("tests/behavioral/test_integration.py")),
    ]
    
    for module_name, file_path in behavioral_modules:
        success, message = check_module(module_name, file_path)
        if success:
            print(f"   ✅ {module_name}")
        else:
            print(f"   ❌ {module_name}: {message}")
            all_good = False
    
    # Check shadow mode modules
    print("\n4. Checking shadow mode modules...")
    shadow_modules = [
        ("shadow_mode", Path("api/shadow_mode.py")),
        ("shadow_mode_manager", Path("api/shadow_mode_manager.py")),
        ("shadow_mode_integration", Path("api/shadow_mode_integration.py")),
    ]
    
    for module_name, file_path in shadow_modules:
        success, message = check_module(module_name, file_path)
        if success:
            print(f"   ✅ {module_name}")
        else:
            print(f"   ❌ {module_name}: {message}")
            all_good = False
    
    # Check contract count
    print("\n5. Validating contract definitions...")
    try:
        from tests.contracts.websocket_contracts import get_all_contracts
        contracts = get_all_contracts()
        print(f"   ✅ Found {len(contracts)} WebSocket contracts")
        if len(contracts) != 21:
            print(f"   ⚠️  Expected 21 contracts, found {len(contracts)}")
    except Exception as e:
        print(f"   ❌ Failed to load contracts: {e}")
        all_good = False
    
    # Check for existing golden masters
    print("\n6. Checking for existing golden masters...")
    golden_masters_dir = Path("tests/contracts/golden_masters")
    if golden_masters_dir.exists():
        masters = list(golden_masters_dir.glob("*.json"))
        if masters:
            print(f"   ⚠️  Found {len(masters)} existing golden masters")
            print("      These will be overwritten when you run capture_golden_masters.py")
        else:
            print("   ✅ No golden masters yet (expected for first run)")
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All checks passed! Ready to capture golden masters.")
        print("\nNext steps:")
        print("1. Run: python tests/contracts/capture_golden_masters.py")
        print("2. Run: python tests/behavioral/run_behavioral_tests.py")
        print("3. Check: python tests/contracts/monitor_compatibility.py --report")
        return True
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)