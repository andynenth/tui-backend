#!/usr/bin/env python3
"""
Test runner for event system tests.

Run all event-related tests with appropriate configuration.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all event system tests."""
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent.parent
    os.chdir(backend_dir)
    
    # Set up Python path
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    print("=" * 80)
    print("Running Event System Tests")
    print("=" * 80)
    print()
    
    # Test categories
    test_suites = [
        {
            "name": "Unit Tests",
            "path": "tests/events/unit",
            "description": "Core event system functionality"
        },
        {
            "name": "Contract Tests",
            "path": "tests/events/contracts",
            "description": "Adapter compatibility verification"
        },
        {
            "name": "Shadow Mode Tests",
            "path": "tests/events/shadow",
            "description": "Shadow mode comparison functionality"
        },
        {
            "name": "Integration Tests",
            "path": "tests/events/integration",
            "description": "State machine and system integration"
        }
    ]
    
    # Run each test suite
    total_passed = 0
    total_failed = 0
    
    for suite in test_suites:
        print(f"\n{'=' * 60}")
        print(f"Running {suite['name']}")
        print(f"Description: {suite['description']}")
        print(f"Path: {suite['path']}")
        print("=" * 60)
        
        # Run pytest for this suite
        cmd = [
            sys.executable, "-m", "pytest",
            suite['path'],
            "-v",
            "--tb=short",
            "--color=yes"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Parse results (simple parsing)
        if "passed" in result.stdout:
            # Extract pass/fail counts
            import re
            match = re.search(r'(\d+) passed', result.stdout)
            if match:
                passed = int(match.group(1))
                total_passed += passed
            
            match = re.search(r'(\d+) failed', result.stdout)
            if match:
                failed = int(match.group(1))
                total_failed += failed
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print()
    
    if total_failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


def run_performance_tests():
    """Run performance tests separately."""
    print("\n" + "=" * 80)
    print("Running Performance Tests")
    print("=" * 80)
    
    backend_dir = Path(__file__).parent.parent.parent
    os.chdir(backend_dir)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/events/integration/test_event_performance.py",
        "-v", "-s",  # -s to show print statements
        "--tb=short",
        "--color=yes"
    ]
    
    subprocess.run(cmd)


def run_coverage():
    """Run tests with coverage reporting."""
    print("\n" + "=" * 80)
    print("Running Tests with Coverage")
    print("=" * 80)
    
    backend_dir = Path(__file__).parent.parent.parent
    os.chdir(backend_dir)
    
    # Run with coverage
    cmd = [
        sys.executable, "-m", "coverage", "run",
        "-m", "pytest",
        "tests/events",
        "-v"
    ]
    
    subprocess.run(cmd)
    
    # Generate coverage report
    print("\n" + "=" * 80)
    print("Coverage Report")
    print("=" * 80)
    
    subprocess.run([sys.executable, "-m", "coverage", "report", "--include=*/events/*"])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run event system tests")
    parser.add_argument(
        "--performance", "-p",
        action="store_true",
        help="Run performance tests"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests including performance"
    )
    
    args = parser.parse_args()
    
    if args.coverage:
        run_coverage()
    elif args.performance:
        run_performance_tests()
    elif args.all:
        exit_code = run_tests()
        run_performance_tests()
        sys.exit(exit_code)
    else:
        exit_code = run_tests()
        sys.exit(exit_code)