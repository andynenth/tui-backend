#!/usr/bin/env python3
"""Run all AI regression tests"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_test(test_file):
    """Run a single test file and return result"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file.name}")
    print(f"{'='*60}")

    try:
        # Run test in subprocess to capture output
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Test timed out!")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Run all regression tests"""
    print("AI REGRESSION TEST SUITE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Find all test files
    test_dir = Path(__file__).parent
    test_files = sorted(test_dir.glob("test_*.py"))

    if not test_files:
        print("No test files found!")
        return 1

    print(f"Found {len(test_files)} test files:")
    for tf in test_files:
        print(f"  - {tf.name}")

    # Run each test
    results = {}
    for test_file in test_files:
        success = run_test(test_file)
        results[test_file.name] = success

    # Summary
    print("\n" + "="*60)
    print("REGRESSION TEST SUMMARY")
    print("="*60)

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Return non-zero if any test failed
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
