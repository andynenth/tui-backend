#!/usr/bin/env python3
"""
Run all AI Debug Mode tests
"""

import sys
import subprocess
from pathlib import Path

# Test categories
EDGE_CASE_TESTS = [
    "tests/ai_debug/edge_cases/test_all_zero_declarations.py",
    "tests/ai_debug/edge_cases/test_weak_hand_redeals.py",
    "tests/ai_debug/edge_cases/test_perfect_rounds.py",
]

REGRESSION_TESTS = [
    "tests/ai_debug/regression/test_zero_declaration_bug.py",
]


def run_test(test_path):
    """Run a single test and return success status"""
    print(f"\nRunning {test_path}...")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Print last 20 lines of output
        output_lines = result.stdout.split('\n')
        for line in output_lines[-20:]:
            if line.strip():
                print(line)
                
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"✗ Test timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"✗ Error running test: {e}")
        return False


def main():
    print("="*60)
    print("AI DEBUG MODE - FULL TEST SUITE")
    print("="*60)
    
    all_tests = []
    
    # Run edge case tests
    print("\n\n🔍 EDGE CASE TESTS")
    print("="*60)
    
    edge_case_results = []
    for test in EDGE_CASE_TESTS:
        passed = run_test(test)
        edge_case_results.append((test, passed))
        all_tests.append((test, passed))
        
    # Run regression tests
    print("\n\n🐛 REGRESSION TESTS")
    print("="*60)
    
    regression_results = []
    for test in REGRESSION_TESTS:
        passed = run_test(test)
        regression_results.append((test, passed))
        all_tests.append((test, passed))
        
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUITE SUMMARY")
    print("="*60)
    
    # Edge case summary
    edge_passed = sum(1 for _, passed in edge_case_results if passed)
    print(f"\nEdge Cases: {edge_passed}/{len(edge_case_results)} passed")
    for test, passed in edge_case_results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {Path(test).name}: {status}")
        
    # Regression summary
    regression_passed = sum(1 for _, passed in regression_results if passed)
    print(f"\nRegression Tests: {regression_passed}/{len(regression_results)} passed")
    for test, passed in regression_results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {Path(test).name}: {status}")
        
    # Overall summary
    total_passed = sum(1 for _, passed in all_tests if passed)
    total_tests = len(all_tests)
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✅ ALL TESTS PASSED! AI Debug Mode is working correctly.")
        return 0
    else:
        failed_count = total_tests - total_passed
        print(f"\n❌ {failed_count} TESTS FAILED!")
        print("\nFailed tests indicate bugs that need to be fixed:")
        for test, passed in all_tests:
            if not passed:
                print(f"  - {Path(test).name}")
        return 1


if __name__ == "__main__":
    exit(main())