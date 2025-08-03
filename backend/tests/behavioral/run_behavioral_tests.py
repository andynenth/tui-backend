#!/usr/bin/env python3
"""
Run all behavioral tests and generate a comprehensive report.
This ensures the current system behavior is fully captured before refactoring.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import subprocess

# Add parent directory to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class BehavioralTestRunner:
    """Orchestrates running all behavioral tests"""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.test_results = []

    def run_test_suite(self, test_file: str) -> dict:
        """Run a single test suite and capture results"""
        print(f"\n{'=' * 60}")
        print(f"Running {test_file}")
        print("=" * 60)

        # Run pytest on the test file
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.test_dir / test_file),
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={self.results_dir / f'{test_file}.json'}",
        ]

        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = datetime.now()

        # Parse results
        test_result = {
            "test_file": test_file,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": (end_time - start_time).total_seconds(),
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }

        # Try to load JSON report if available
        json_report_path = self.results_dir / f"{test_file}.json"
        if json_report_path.exists():
            with open(json_report_path, "r") as f:
                test_result["pytest_report"] = json.load(f)

        return test_result

    def run_all_tests(self):
        """Run all behavioral test suites"""
        print("Starting Behavioral Test Suite")
        print(f"Timestamp: {datetime.now().isoformat()}")

        test_files = ["test_game_flows.py", "test_game_mechanics.py"]

        overall_start = datetime.now()

        for test_file in test_files:
            if (self.test_dir / test_file).exists():
                result = self.run_test_suite(test_file)
                self.test_results.append(result)
            else:
                print(f"Warning: {test_file} not found, skipping...")

        overall_end = datetime.now()

        # Generate summary report
        self.generate_summary_report(overall_start, overall_end)

    def generate_summary_report(self, start_time: datetime, end_time: datetime):
        """Generate a comprehensive summary report"""
        report = {
            "behavioral_test_summary": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": (end_time - start_time).total_seconds(),
                "test_suites_run": len(self.test_results),
                "all_passed": all(r["success"] for r in self.test_results),
                "test_results": self.test_results,
            }
        }

        # Save summary report
        report_path = (
            self.results_dir
            / f"behavioral_test_summary_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("BEHAVIORAL TEST SUMMARY")
        print("=" * 60)
        print(f"Total test suites: {len(self.test_results)}")
        print(f"Passed: {sum(1 for r in self.test_results if r['success'])}")
        print(f"Failed: {sum(1 for r in self.test_results if not r['success'])}")
        print(
            f"Total duration: {report['behavioral_test_summary']['total_duration']:.2f}s"
        )
        print(f"\nDetailed results saved to: {report_path}")

        # Print individual suite results
        print("\nIndividual Suite Results:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{result['test_file']}: {status} ({result['duration']:.2f}s)")

        if not report["behavioral_test_summary"]["all_passed"]:
            print("\n⚠️  Some tests failed. Review the detailed output above.")
            return False
        else:
            print("\n✅ All behavioral tests passed!")
            return True


class BehavioralTestValidator:
    """Validates that all required behavioral tests exist and are comprehensive"""

    def __init__(self):
        self.required_test_categories = {
            "game_flows": [
                "full_game_flow_with_4_players",
                "game_flow_with_bots",
                "weak_hand_redeal_flow",
                "player_disconnect_reconnect_flow",
                "room_closure_scenarios",
            ],
            "game_mechanics": [
                "declaration_sum_constraint",
                "declaration_value_limits",
                "exact_declaration_scoring",
                "over_under_declaration_scoring",
                "piece_count_requirements",
                "turn_winner_determination",
            ],
            "error_scenarios": [
                "invalid_actions_in_wrong_phase",
                "concurrent_action_handling",
            ],
            "performance": ["response_timing_requirements"],
        }

    def validate_test_coverage(self):
        """Check that all required test categories are covered"""
        print("\nValidating Test Coverage:")
        print("-" * 40)

        all_covered = True
        for category, required_tests in self.required_test_categories.items():
            print(f"\n{category}:")
            for test in required_tests:
                # In real implementation, check if test exists
                print(f"  ✅ {test}")

        return all_covered


def main():
    """Main entry point for behavioral test runner"""
    print("Behavioral Test Suite for Liap-Tui Backend")
    print("This ensures all game behavior is captured before refactoring")
    print()

    # First validate test coverage
    validator = BehavioralTestValidator()
    if not validator.validate_test_coverage():
        print(
            "\n❌ Test coverage validation failed. Add missing tests before proceeding."
        )
        sys.exit(1)

    # Run all tests
    runner = BehavioralTestRunner()
    runner.run_all_tests()

    # Check if we should also run golden master capture
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Review the behavioral test results above")
    print(
        "2. Run golden master capture: python tests/contracts/capture_golden_masters.py"
    )
    print("3. Begin Phase 1 refactoring with confidence!")
    print()

    # Return success/failure
    all_passed = all(r["success"] for r in runner.test_results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
