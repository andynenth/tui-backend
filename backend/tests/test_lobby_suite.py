"""
Test suite runner for all lobby-related tests.

This module provides a convenient way to run all lobby tests
and verify the real-time update functionality.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def run_lobby_tests():
    """Run all lobby-related tests."""
    print("Running Lobby Real-time Updates Test Suite")
    print("=" * 60)

    # Define test modules
    test_modules = [
        "tests/application/test_lobby_realtime_updates.py",
        "tests/application/websocket/test_lobby_dispatcher.py",
        "tests/integration/test_lobby_websocket_integration.py",
    ]

    # Run each test module
    total_passed = 0
    total_failed = 0

    for module in test_modules:
        print(f"\nRunning tests in {module}...")
        print("-" * 40)

        # Run pytest for this module
        result = pytest.main(["-v", "--tb=short", module])

        if result == 0:
            print(f"✅ All tests passed in {module}")
            total_passed += 1
        else:
            print(f"❌ Some tests failed in {module}")
            total_failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("LOBBY TEST SUITE SUMMARY")
    print(f"Total test modules run: {len(test_modules)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print("=" * 60)

    return total_failed == 0


if __name__ == "__main__":
    success = run_lobby_tests()
    sys.exit(0 if success else 1)
