"""
Phase 4.9 - Testing & Validation Script

This script runs comprehensive tests to validate the clean architecture
implementation and generates a validation report.
"""

import pytest
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import subprocess


class Phase4Validator:
    """Validates Phase 4 implementation completeness and correctness."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "phase": "Phase 4.9 - Testing & Validation",
            "components": {},
            "tests": {},
            "metrics": {},
            "issues": [],
        }

    def validate_structure(self):
        """Validate the clean architecture structure."""
        print("🔍 Validating Clean Architecture Structure...")

        components = {
            "domain_layer": {
                "entities": ["Room", "Game", "Player"],
                "value_objects": ["RoomId", "GameId", "PlayerId"],
                "events": ["RoomCreated", "GameStarted", "PlayerJoinedRoom"],
                "exceptions": ["DomainException", "ValidationException"],
            },
            "application_layer": {
                "use_cases": 22,  # Expected number of use cases
                "dtos": 6,  # Expected number of DTO modules
                "services": 4,  # Expected number of application services
                "interfaces": ["UnitOfWork", "EventPublisher", "NotificationService"],
            },
            "infrastructure_layer": {
                "repositories": ["InMemoryRoomRepository", "InMemoryGameRepository"],
                "services": ["WebSocketNotificationService", "SimpleBotService"],
                "adapters": ["CleanArchitectureAdapter"],
                "features": ["FeatureFlags", "DependencyContainer"],
            },
        }

        # Check domain layer
        domain_valid = True
        try:
            from domain import entities, value_objects, events, exceptions

            self.results["components"]["domain"] = "VALID"
        except ImportError as e:
            self.results["components"]["domain"] = f"INVALID: {e}"
            domain_valid = False

        # Check application layer
        app_valid = True
        try:
            from application import use_cases, dto, services, interfaces

            # Count use cases
            use_case_count = self._count_files(Path("application/use_cases"), "*.py")
            dto_count = len(list(Path("application/dto").glob("*.py"))) - 1
            service_count = len(list(Path("application/services").glob("*.py"))) - 1

            self.results["components"]["application"] = {
                "status": "VALID",
                "use_cases": use_case_count,
                "dtos": dto_count,
                "services": service_count,
            }
        except ImportError as e:
            self.results["components"]["application"] = f"INVALID: {e}"
            app_valid = False

        # Check infrastructure layer
        infra_valid = True
        try:
            from infrastructure import repositories, services, adapters

            self.results["components"]["infrastructure"] = "VALID"
        except ImportError as e:
            self.results["components"]["infrastructure"] = f"INVALID: {e}"
            infra_valid = False

        return domain_valid and app_valid and infra_valid

    def run_tests(self):
        """Run all test suites."""
        print("\n🧪 Running Test Suites...")

        test_suites = [
            ("Domain Tests", "tests/test_domain/"),
            ("Application Tests", "tests/test_application/"),
            (
                "Infrastructure Tests",
                "tests/test_infrastructure/test_phase4_complete.py",
            ),
            ("Integration Tests", "tests/test_infrastructure/test_integration.py"),
            ("E2E Tests", "tests/test_infrastructure/test_e2e_flow.py"),
            ("Performance Tests", "tests/test_infrastructure/test_performance.py"),
        ]

        all_passed = True

        for suite_name, test_path in test_suites:
            print(f"\n  Running {suite_name}...")

            try:
                # Run pytest with JSON output
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_path, "-q", "--tb=short"],
                    capture_output=True,
                    text=True,
                )

                passed = result.returncode == 0
                all_passed = all_passed and passed

                # Parse output
                output_lines = result.stdout.strip().split("\n")
                summary_line = output_lines[-1] if output_lines else "No output"

                self.results["tests"][suite_name] = {
                    "passed": passed,
                    "summary": summary_line,
                    "errors": result.stderr if not passed else None,
                }

                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"    {status}: {summary_line}")

            except Exception as e:
                self.results["tests"][suite_name] = {"passed": False, "error": str(e)}
                all_passed = False
                print(f"    ❌ ERROR: {e}")

        return all_passed

    def check_code_quality(self):
        """Check code quality metrics."""
        print("\n📊 Checking Code Quality...")

        # Count lines of code
        loc_counts = {
            "domain": self._count_lines(Path("domain")),
            "application": self._count_lines(Path("application")),
            "infrastructure": self._count_lines(Path("infrastructure")),
            "tests": self._count_lines(Path("tests")),
        }

        total_loc = sum(loc_counts.values())
        test_ratio = loc_counts["tests"] / (total_loc - loc_counts["tests"])

        self.results["metrics"]["lines_of_code"] = loc_counts
        self.results["metrics"]["test_ratio"] = f"{test_ratio:.2%}"

        print(f"  Total LOC: {total_loc:,}")
        print(f"  Test Ratio: {test_ratio:.2%}")

        # Check for common issues
        issues = []

        # Check for TODO comments
        todo_count = self._count_pattern(Path("."), "TODO")
        if todo_count > 0:
            issues.append(f"Found {todo_count} TODO comments")

        # Check for print statements in production code
        print_count = self._count_pattern(
            Path("."), r"^\s*print\(", exclude_dirs=["tests"]
        )
        if print_count > 0:
            issues.append(f"Found {print_count} print statements in production code")

        self.results["issues"] = issues

        if issues:
            print("\n  ⚠️  Issues found:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✅ No quality issues found")

        return len(issues) == 0

    def generate_report(self):
        """Generate validation report."""
        print("\n📄 Generating Validation Report...")

        report_path = Path("tests/reports/phase4_validation_report.json")
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"  Report saved to: {report_path}")

        # Generate summary
        print("\n" + "=" * 60)
        print("PHASE 4.9 VALIDATION SUMMARY")
        print("=" * 60)

        # Structure validation
        structure_valid = all(
            v == "VALID" or (isinstance(v, dict) and v.get("status") == "VALID")
            for v in self.results["components"].values()
        )
        print(f"\n✓ Structure Validation: {'PASSED' if structure_valid else 'FAILED'}")

        # Test results
        tests_passed = all(
            t.get("passed", False) for t in self.results["tests"].values()
        )
        print(f"✓ Test Suites: {'ALL PASSED' if tests_passed else 'SOME FAILED'}")

        # Code quality
        quality_good = len(self.results["issues"]) == 0
        print(f"✓ Code Quality: {'GOOD' if quality_good else 'ISSUES FOUND'}")

        # Overall result
        all_valid = structure_valid and tests_passed and quality_good

        print("\n" + "=" * 60)
        if all_valid:
            print("🎉 PHASE 4.9 VALIDATION: PASSED")
            print("Clean architecture implementation is complete and validated!")
        else:
            print("❌ PHASE 4.9 VALIDATION: FAILED")
            print("Please address the issues above before proceeding.")
        print("=" * 60)

        return all_valid

    def _count_files(self, path: Path, pattern: str) -> int:
        """Count files matching pattern recursively."""
        count = 0
        for file in path.rglob(pattern):
            if file.name != "__init__.py" and not file.name.startswith("test_"):
                count += 1
        return count

    def _count_lines(self, path: Path) -> int:
        """Count lines of Python code."""
        total = 0
        for file in path.rglob("*.py"):
            if not file.name.startswith("test_"):
                try:
                    total += len(file.read_text().splitlines())
                except:
                    pass
        return total

    def _count_pattern(self, path: Path, pattern: str, exclude_dirs=None) -> int:
        """Count occurrences of pattern in Python files."""
        import re

        count = 0
        exclude_dirs = exclude_dirs or []

        for file in path.rglob("*.py"):
            # Skip excluded directories
            if any(excluded in file.parts for excluded in exclude_dirs):
                continue

            try:
                content = file.read_text()
                count += len(re.findall(pattern, content, re.MULTILINE))
            except:
                pass
        return count


def main():
    """Run Phase 4.9 validation."""
    validator = Phase4Validator()

    # Run validation steps
    structure_valid = validator.validate_structure()
    tests_passed = validator.run_tests()
    quality_good = validator.check_code_quality()

    # Generate report
    all_valid = validator.generate_report()

    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
