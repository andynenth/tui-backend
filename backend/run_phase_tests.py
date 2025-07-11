#!/usr/bin/env python
"""
Quick test runner for phase transition validation

Run this before committing or after making phase-related changes:
    python backend/run_phase_tests.py
"""

import subprocess
import sys
from pathlib import Path

def run_phase_tests():
    """Run all phase-related tests"""
    
    print("🧪 Running Phase Transition Tests...")
    print("=" * 50)
    
    # Find test directory
    backend_dir = Path(__file__).parent
    tests_dir = backend_dir / "tests"
    
    # Define test files to run
    test_files = [
        "test_phase_transition_errors.py",
        "test_round_start_phase.py",
        "test_round_start_bot_integration.py"
    ]
    
    all_passed = True
    results = []
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running {test_file}...")
        
        # Run pytest on the file
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} - All tests passed!")
            results.append((test_file, True, "All tests passed"))
        else:
            print(f"❌ {test_file} - Tests failed!")
            print("Error output:")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            all_passed = False
            results.append((test_file, False, "Tests failed"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    for test_file, passed, message in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {test_file}: {message}")
    
    if all_passed:
        print("\n🎉 All phase transition tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues before proceeding.")
        return 1

def run_quick_validation():
    """Run just the quick validation test"""
    print("\n🚀 Running quick phase validation...")
    
    backend_dir = Path(__file__).parent
    test_file = backend_dir / "tests" / "test_phase_transition_errors.py"
    
    # Run the specific test function
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file) + "::test_phase_transitions_are_valid", "-v"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Quick validation passed!")
    else:
        print("❌ Quick validation failed!")
        print(result.stdout)
    
    return result.returncode

if __name__ == "__main__":
    # Check if we want quick mode
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        sys.exit(run_quick_validation())
    else:
        sys.exit(run_phase_tests())