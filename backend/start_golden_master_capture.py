#!/usr/bin/env python3
"""
Helper script to start the golden master capture process.
This ensures the environment is set up correctly before running the capture.
"""

import sys
import os
from pathlib import Path
import subprocess


def main():
    print("Golden Master Capture Preparation")
    print("=" * 50)

    # Ensure we're in backend directory
    if not Path("engine").exists() or not Path("api").exists():
        print("❌ ERROR: Must run from backend directory")
        print("   cd backend && python3 start_golden_master_capture.py")
        return False

    # Check Python path
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    # Set PYTHONPATH
    os.environ["PYTHONPATH"] = str(Path.cwd())
    print(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")

    # Check if virtual environment is active
    if not hasattr(sys, "real_prefix") and not sys.base_prefix != sys.prefix:
        print("\n⚠️  WARNING: Virtual environment not detected")
        print("   It's recommended to activate your venv:")
        print("   source venv/bin/activate")

    # Check dependencies
    print("\nChecking dependencies...")
    try:
        import pytest

        print("   ✅ pytest installed")
    except ImportError:
        print("   ❌ pytest not installed - run: pip install pytest pytest-asyncio")

    try:
        import asyncio

        print("   ✅ asyncio available")
    except ImportError:
        print("   ❌ asyncio not available")

    # Create directories if needed
    dirs = [
        "tests/contracts/golden_masters",
        "tests/contracts/golden_masters/flows",
        "tests/contracts/golden_masters/mechanics",
        "tests/contracts/golden_masters/integration",
    ]

    print("\nEnsuring directories exist...")
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {dir_path}")

    # Ready to capture
    print("\n" + "=" * 50)
    print("✅ Ready to capture golden masters!")
    print("\nYou have two options:")
    print("\n1. Run the automated capture script (recommended):")
    print("   python3 tests/contracts/capture_golden_masters.py")
    print("\n2. Use actual WebSocket server (more accurate):")
    print("   - Start your game server")
    print("   - Run: python3 capture_from_live_server.py")
    print("\nOption 1 uses simulated responses, which is fine for initial setup.")
    print("Option 2 captures from the real server, which is more accurate.")

    # Ask user
    choice = input("\nProceed with automated capture? (y/n): ").lower()

    if choice == "y":
        print("\nStarting golden master capture...")
        try:
            result = subprocess.run(
                [sys.executable, "tests/contracts/capture_golden_masters.py"],
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            if result.returncode == 0:
                print("\n✅ Golden master capture completed!")
                print("\nNext steps:")
                print("1. Review captured files: ls tests/contracts/golden_masters/")
                print(
                    "2. Run behavioral tests: python3 tests/behavioral/run_behavioral_tests.py"
                )
                print(
                    "3. Generate report: python3 tests/contracts/monitor_compatibility.py --report"
                )
            else:
                print(f"\n❌ Capture failed with return code: {result.returncode}")
        except Exception as e:
            print(f"\n❌ Error running capture: {e}")
    else:
        print("\nCapture cancelled. Run manually when ready.")

    return True


if __name__ == "__main__":
    main()
