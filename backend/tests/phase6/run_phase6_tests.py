#!/usr/bin/env python3
"""
Phase 6 Test Suite Runner

Comprehensive test runner for all Phase 6 migration tests.
Provides options to run specific migration steps or full validation suite.
"""

import asyncio
import sys
import os
import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase6TestRunner:
    """Comprehensive test runner for Phase 6 migration tests."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_test_file(self, test_path: Path, description: str) -> Tuple[bool, str]:
        """Run a single test file and return success status and output."""
        try:
            logger.info(f"Running {description}...")
            
            # Change to the test file's directory
            test_dir = test_path.parent
            test_file = test_path.name
            
            # Run the test
            result = subprocess.run(
                [sys.executable, test_file],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            self.total_tests += 1
            success = result.returncode == 0
            
            if success:
                self.passed_tests += 1
                status = "✅ PASSED"
            else:
                self.failed_tests += 1
                status = "❌ FAILED"
            
            output = f"{status} - {description}\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            logger.info(f"{status} - {description}")
            return success, output
            
        except subprocess.TimeoutExpired:
            self.total_tests += 1
            self.failed_tests += 1
            output = f"❌ TIMEOUT - {description} (exceeded 5 minutes)\n"
            logger.error(f"❌ TIMEOUT - {description}")
            return False, output
            
        except Exception as e:
            self.total_tests += 1
            self.failed_tests += 1
            output = f"❌ ERROR - {description}: {e}\n"
            logger.error(f"❌ ERROR - {description}: {e}")
            return False, output
    
    def run_pytest_file(self, test_path: Path, description: str) -> Tuple[bool, str]:
        """Run a pytest file and return success status and output."""
        try:
            logger.info(f"Running {description}...")
            
            # Change to the test file's directory
            test_dir = test_path.parent
            test_file = test_path.name
            
            # Run pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            self.total_tests += 1
            success = result.returncode == 0
            
            if success:
                self.passed_tests += 1
                status = "✅ PASSED"
            else:
                self.failed_tests += 1
                status = "❌ FAILED"
            
            output = f"{status} - {description}\n"
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            logger.info(f"{status} - {description}")
            return success, output
            
        except subprocess.TimeoutExpired:
            self.total_tests += 1
            self.failed_tests += 1
            output = f"❌ TIMEOUT - {description} (exceeded 5 minutes)\n"
            logger.error(f"❌ TIMEOUT - {description}")
            return False, output
            
        except Exception as e:
            self.total_tests += 1
            self.failed_tests += 1
            output = f"❌ ERROR - {description}: {e}\n"
            logger.error(f"❌ ERROR - {description}: {e}")
            return False, output
    
    def run_step_6_4_1(self) -> Dict[str, any]:
        """Run Phase 6.4.1: State Machine Migration tests."""
        logger.info("🏗️ Running Phase 6.4.1: State Machine Migration tests...")
        
        results = {
            "step": "6.4.1",
            "name": "State Machine Migration",
            "tests": [],
            "success": True
        }
        
        step_path = self.base_path / "migration_tools" / "step_6_4_1"
        
        # Enterprise state machine test
        test_path = step_path / "test_state_machine_enterprise.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "State Machine Enterprise Features")
            results["tests"].append({
                "name": "Enterprise Features",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Integration test
        test_path = step_path / "test_state_machine_integration.py"
        if test_path.exists():
            success, output = self.run_pytest_file(test_path, "State Machine Integration")
            results["tests"].append({
                "name": "Integration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        return results
    
    def run_step_6_4_2(self) -> Dict[str, any]:
        """Run Phase 6.4.2: Bot Management Migration tests."""
        logger.info("🤖 Running Phase 6.4.2: Bot Management Migration tests...")
        
        results = {
            "step": "6.4.2",
            "name": "Bot Management Migration",
            "tests": [],
            "success": True
        }
        
        step_path = self.base_path / "migration_tools" / "step_6_4_2"
        
        # Bot management migration test
        test_path = step_path / "test_bot_management_migration.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Bot Management Migration")
            results["tests"].append({
                "name": "Migration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Bot timing accuracy test
        test_path = step_path / "test_bot_timing_accuracy.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Bot Timing Accuracy")
            results["tests"].append({
                "name": "Timing Accuracy",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Integration test
        test_path = step_path / "test_bot_management_integration.py"
        if test_path.exists():
            success, output = self.run_pytest_file(test_path, "Bot Management Integration")
            results["tests"].append({
                "name": "Integration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        return results
    
    def run_step_6_4_3(self) -> Dict[str, any]:
        """Run Phase 6.4.3: Scoring System Migration tests."""
        logger.info("🎯 Running Phase 6.4.3: Scoring System Migration tests...")
        
        results = {
            "step": "6.4.3",
            "name": "Scoring System Migration",
            "tests": [],
            "success": True
        }
        
        step_path = self.base_path / "migration_tools" / "step_6_4_3"
        
        # Scoring system migration test
        test_path = step_path / "test_scoring_system_migration.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Scoring System Migration")
            results["tests"].append({
                "name": "Migration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Integration test
        test_path = step_path / "test_scoring_integration.py"
        if test_path.exists():
            success, output = self.run_pytest_file(test_path, "Scoring Integration")
            results["tests"].append({
                "name": "Integration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        return results
    
    def run_step_6_5_1(self) -> Dict[str, any]:
        """Run Phase 6.5.1: End-to-End Integration tests."""
        logger.info("🔗 Running Phase 6.5.1: End-to-End Integration tests...")
        
        results = {
            "step": "6.5.1",
            "name": "End-to-End Integration",
            "tests": [],
            "success": True
        }
        
        step_path = self.base_path / "migration_tools" / "step_6_5_1"
        
        # Complete integration test
        test_path = step_path / "test_complete_integration.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Complete Integration")
            results["tests"].append({
                "name": "Complete Integration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        return results
    
    def run_step_6_5_2(self) -> Dict[str, any]:
        """Run Phase 6.5.2: Load Testing and Performance tests."""
        logger.info("⚡ Running Phase 6.5.2: Load Testing and Performance tests...")
        
        results = {
            "step": "6.5.2",
            "name": "Load Testing and Performance",
            "tests": [],
            "success": True
        }
        
        step_path = self.base_path / "migration_tools" / "step_6_5_2"
        
        # Load tests
        test_path = step_path / "run_load_tests.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Load Testing")
            results["tests"].append({
                "name": "Load Testing",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Performance tests
        perf_path = step_path / "performance"
        perf_tests = [
            ("test_repository_performance.py", "Repository Performance"),
            ("test_cache_performance.py", "Cache Performance"),
            ("test_event_throughput.py", "Event Throughput")
        ]
        
        for test_file, test_name in perf_tests:
            test_path = perf_path / test_file
            if test_path.exists():
                success, output = self.run_test_file(test_path, test_name)
                results["tests"].append({
                    "name": test_name,
                    "success": success,
                    "output": output
                })
                if not success:
                    results["success"] = False
        
        return results
    
    def run_step_6_5_3(self) -> Dict[str, any]:
        """Run Phase 6.5.3: Legacy Removal and Final Validation tests."""
        logger.info("🧹 Running Phase 6.5.3: Legacy Removal and Final Validation tests...")
        
        results = {
            "step": "6.5.3",
            "name": "Legacy Removal and Final Validation",
            "tests": [],
            "success": True
        }
        
        step_path = self.base_path / "migration_tools" / "step_6_5_3"
        
        # Regression tests
        test_path = step_path / "run_regression_tests.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Regression Testing")
            results["tests"].append({
                "name": "Regression Testing",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Final performance validation
        test_path = step_path / "final_performance_validation.py"
        if test_path.exists():
            success, output = self.run_test_file(test_path, "Final Performance Validation")
            results["tests"].append({
                "name": "Final Performance Validation",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        return results
    
    def run_infrastructure_tests(self) -> Dict[str, any]:
        """Run infrastructure and monitoring tests."""
        logger.info("🏗️ Running infrastructure tests...")
        
        results = {
            "step": "infrastructure",
            "name": "Infrastructure and Monitoring",
            "tests": [],
            "success": True
        }
        
        # WebSocket integration
        test_path = self.base_path / "infrastructure" / "test_websocket_integration.py"
        if test_path.exists():
            success, output = self.run_pytest_file(test_path, "WebSocket Integration")
            results["tests"].append({
                "name": "WebSocket Integration",
                "success": success,
                "output": output
            })
            if not success:
                results["success"] = False
        
        # Monitoring tests
        monitoring_path = self.base_path / "infrastructure" / "monitoring"
        monitoring_tests = [
            ("test_migration_alerts.py", "Migration Alerts"),
            ("validate_monitoring_coverage.py", "Monitoring Coverage")
        ]
        
        for test_file, test_name in monitoring_tests:
            test_path = monitoring_path / test_file
            if test_path.exists():
                success, output = self.run_test_file(test_path, test_name)
                results["tests"].append({
                    "name": test_name,
                    "success": success,
                    "output": output
                })
                if not success:
                    results["success"] = False
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """Generate comprehensive test report."""
        report = {
            "timestamp": time.time(),
            "summary": {
                "total_steps": len(results),
                "successful_steps": len([r for r in results if r["success"]]),
                "failed_steps": len([r for r in results if not r["success"]]),
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": (self.passed_tests / max(self.total_tests, 1)) * 100,
                "overall_success": self.failed_tests == 0
            },
            "step_results": results
        }
        
        return report
    
    def run_full_suite(self) -> Dict:
        """Run the complete Phase 6 test suite."""
        logger.info("🚀 Starting Phase 6 complete test suite...")
        
        results = []
        
        # Run all migration steps
        results.append(self.run_step_6_4_1())
        results.append(self.run_step_6_4_2())
        results.append(self.run_step_6_4_3())
        results.append(self.run_step_6_5_1())
        results.append(self.run_step_6_5_2())
        results.append(self.run_step_6_5_3())
        
        # Run infrastructure tests
        results.append(self.run_infrastructure_tests())
        
        return self.generate_report(results)
    
    def run_business_logic_tests(self) -> Dict:
        """Run Phase 6.4 Business Logic Migration tests only."""
        logger.info("🏗️ Running Phase 6.4 Business Logic Migration tests...")
        
        results = []
        results.append(self.run_step_6_4_1())
        results.append(self.run_step_6_4_2())
        results.append(self.run_step_6_4_3())
        
        return self.generate_report(results)
    
    def run_integration_tests(self) -> Dict:
        """Run Phase 6.5 Integration and Finalization tests only."""
        logger.info("🔗 Running Phase 6.5 Integration and Finalization tests...")
        
        results = []
        results.append(self.run_step_6_5_1())
        results.append(self.run_step_6_5_2())
        results.append(self.run_step_6_5_3())
        
        return self.generate_report(results)


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Phase 6 Test Suite Runner")
    parser.add_argument("--step", type=str, help="Run specific step (6.4.1, 6.4.2, 6.4.3, 6.5.1, 6.5.2, 6.5.3)")
    parser.add_argument("--business-logic", action="store_true", help="Run Phase 6.4 Business Logic tests only")
    parser.add_argument("--integration", action="store_true", help="Run Phase 6.5 Integration tests only")
    parser.add_argument("--infrastructure", action="store_true", help="Run infrastructure tests only")
    parser.add_argument("--report-file", type=str, default="phase6_test_report.json", help="Report file name")
    
    args = parser.parse_args()
    
    runner = Phase6TestRunner()
    
    try:
        if args.step:
            # Run specific step
            step_methods = {
                "6.4.1": runner.run_step_6_4_1,
                "6.4.2": runner.run_step_6_4_2,
                "6.4.3": runner.run_step_6_4_3,
                "6.5.1": runner.run_step_6_5_1,
                "6.5.2": runner.run_step_6_5_2,
                "6.5.3": runner.run_step_6_5_3
            }
            
            if args.step in step_methods:
                result = step_methods[args.step]()
                report = runner.generate_report([result])
            else:
                logger.error(f"Invalid step: {args.step}")
                sys.exit(1)
                
        elif args.business_logic:
            report = runner.run_business_logic_tests()
        elif args.integration:
            report = runner.run_integration_tests()
        elif args.infrastructure:
            result = runner.run_infrastructure_tests()
            report = runner.generate_report([result])
        else:
            report = runner.run_full_suite()
        
        # Save report
        report_path = Path(__file__).parent / "reports" / args.report_file
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        summary = report["summary"]
        print(f"\\n📋 Phase 6 Test Suite Results:")
        print(f"✅ Successful steps: {summary['successful_steps']}/{summary['total_steps']}")
        print(f"🧪 Test results: {summary['passed_tests']}/{summary['total_tests']} passed")
        print(f"📊 Success rate: {summary['success_rate']:.1f}%")
        print(f"📁 Report saved: {report_path}")
        
        if summary["overall_success"]:
            print(f"🎉 All Phase 6 tests passed successfully!")
            sys.exit(0)
        else:
            print(f"❌ Some Phase 6 tests failed. Check the report for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()