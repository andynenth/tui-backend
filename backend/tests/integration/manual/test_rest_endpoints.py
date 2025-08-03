#!/usr/bin/env python3
"""
Test script for remaining REST endpoints in Liap Tui backend.
Tests all admin, health, debug, and recovery endpoints.

Usage:
    python test_rest_endpoints.py
    python test_rest_endpoints.py --base-url http://localhost:5050
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, Optional
import requests
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class RestEndpointTester:
    """Test all remaining REST endpoints"""

    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.passed = 0
        self.failed = 0
        self.results = []

    def print_header(self, text: str):
        """Print a section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

    def print_test(self, name: str, endpoint: str):
        """Print test information"""
        print(f"{Colors.OKBLUE}Testing: {name}{Colors.ENDC}")
        print(f"Endpoint: {endpoint}")

    def print_success(self, message: str = "PASSED"):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}\n")
        self.passed += 1

    def print_failure(self, message: str):
        """Print failure message"""
        print(f"{Colors.FAIL}✗ FAILED: {message}{Colors.ENDC}\n")
        self.failed += 1

    def print_response(self, response: requests.Response, show_body: bool = True):
        """Print response details"""
        print(f"Status Code: {response.status_code}")
        if show_body:
            try:
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"Response: {response.text[:200]}...")
            except:
                print(f"Response: {response.text[:200]}...")

    def test_endpoint(
        self,
        name: str,
        method: str,
        path: str,
        expected_status: int = 200,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        validate_response: Optional[callable] = None,
        show_response: bool = True,
    ) -> bool:
        """Test a single endpoint"""

        url = f"{self.api_url}{path}"
        self.print_test(name, f"{method} {path}")

        try:
            if method == "GET":
                response = requests.get(url, params=params)
            elif method == "POST":
                response = requests.post(url, json=json_data, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")

            self.print_response(response, show_body=show_response)

            # Handle expected_status as either int or list
            expected_statuses = (
                [expected_status]
                if isinstance(expected_status, int)
                else expected_status
            )
            if response.status_code not in expected_statuses:
                self.print_failure(
                    f"Expected status {expected_statuses}, got {response.status_code}"
                )
                return False

            if validate_response and response.status_code == 200:
                try:
                    data = (
                        response.json()
                        if response.headers.get("content-type", "").startswith(
                            "application/json"
                        )
                        else response.text
                    )
                    validation_result = validate_response(data)
                    if validation_result is True:
                        self.print_success()
                        return True
                    else:
                        self.print_failure(
                            f"Response validation failed: {validation_result}"
                        )
                        return False
                except Exception as e:
                    self.print_failure(f"Response validation error: {str(e)}")
                    return False

            self.print_success()
            return True

        except requests.exceptions.ConnectionError:
            self.print_failure(
                f"Connection refused. Is the server running on {self.base_url}?"
            )
            return False
        except Exception as e:
            self.print_failure(f"Error: {str(e)}")
            return False

    def validate_health_response(self, data: Dict) -> Any:
        """Validate health check response"""
        required_fields = ["status", "timestamp", "service"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"

        if data["status"] not in ["healthy", "warning", "critical", "unknown"]:
            return f"Invalid status: {data['status']}"

        return True

    def validate_detailed_health(self, data: Dict) -> Any:
        """Validate detailed health response"""
        # Check required fields from DetailedHealthCheck model
        required_fields = [
            "status",
            "timestamp",
            "version",
            "uptime_seconds",
            "components",
            "memory_usage_mb",
            "active_rooms",
            "active_connections",
        ]

        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"

        # Validate status is a valid enum value
        if data["status"] not in ["healthy", "unhealthy", "degraded"]:
            return f"Invalid status: {data['status']}"

        # Print component status
        if "components" in data:
            print("  Component Status:")
            for component, status in data["components"].items():
                print(f"    - {component}: {status}")

        return True

    def validate_metrics(self, data: str) -> Any:
        """Validate Prometheus metrics response"""
        lines = data.strip().split("\n")
        if len(lines) < 5:
            return "Too few metrics returned"

        # Check for key metrics
        expected_metrics = [
            "liap_health_status",
            "liap_uptime_seconds",
            "liap_rooms_total",
        ]

        found_metrics = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                metric_name = parts[0]
                found_metrics.append(metric_name)

        for expected in expected_metrics:
            if expected not in found_metrics:
                return f"Missing expected metric: {expected}"

        print(f"  Found {len(lines)} metrics")
        return True

    def run_health_tests(self):
        """Test health monitoring endpoints"""
        self.print_header("Health Monitoring Endpoints")

        # Basic health check
        self.test_endpoint(
            "Basic Health Check",
            "GET",
            "/health",
            validate_response=self.validate_health_response,
        )

        # Detailed health check
        self.test_endpoint(
            "Detailed Health Check",
            "GET",
            "/health/detailed",
            validate_response=self.validate_detailed_health,
        )

        # Prometheus metrics
        self.test_endpoint(
            "Prometheus Metrics",
            "GET",
            "/health/metrics",
            validate_response=self.validate_metrics,
            show_response=False,  # Metrics can be long
        )

    def run_debug_tests(self):
        """Test debug endpoints"""
        self.print_header("Debug and Admin Endpoints")

        # Room stats - all rooms
        self.test_endpoint(
            "Room Statistics (All Rooms)",
            "GET",
            "/debug/room-stats",
            validate_response=lambda d: "stats" in d and "timestamp" in d,
        )

        # Room stats - specific room (might not exist)
        self.test_endpoint(
            "Room Statistics (Specific Room)",
            "GET",
            "/debug/room-stats",
            params={"room_id": "TEST123"},
            validate_response=lambda d: "stats" in d,
        )

    def run_event_store_tests(self):
        """Test event store endpoints"""
        self.print_header("Event Store Management")

        # Event store stats
        result = self.test_endpoint(
            "Event Store Statistics",
            "GET",
            "/event-store/stats",
            expected_status=200,  # Should be 200 if available
            validate_response=lambda d: "success" in d,
        )

        if result:
            # Room events
            self.test_endpoint(
                "Room Events",
                "GET",
                "/rooms/TEST123/events",
                expected_status=200,
                params={"limit": 5},
                validate_response=lambda d: "success" in d,
            )

            # Event cleanup
            self.test_endpoint(
                "Event Store Cleanup",
                "POST",
                "/event-store/cleanup",
                expected_status=200,
                params={"older_than_hours": 72},
                validate_response=lambda d: "success" in d,
            )

    def run_recovery_tests(self):
        """Test recovery system endpoints"""
        self.print_header("Recovery System")

        # Recovery status
        self.test_endpoint(
            "Recovery System Status",
            "GET",
            "/recovery/status",
            validate_response=lambda d: "recovery_system" in d,
        )

        # Trigger recovery (with safe procedure)
        self.test_endpoint(
            "Trigger Recovery Procedure",
            "POST",
            "/recovery/trigger/test_procedure",
            json_data={"context": {"dry_run": True}},
            expected_status=[200, 500],  # Might fail if procedure doesn't exist
        )

    def run_system_tests(self):
        """Test system statistics endpoint"""
        self.print_header("System Statistics")

        self.test_endpoint(
            "Comprehensive System Stats",
            "GET",
            "/system/stats",
            validate_response=lambda d: all(
                k in d for k in ["health", "websocket", "rooms"]
            ),
        )

    def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"\n{Colors.BOLD}REST API Endpoint Test Suite{Colors.ENDC}")
        print(f"Testing against: {self.api_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Check if server is running
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            print(f"{Colors.OKGREEN}✓ Server is running{Colors.ENDC}")
        except:
            print(
                f"{Colors.FAIL}✗ Cannot connect to server at {self.base_url}{Colors.ENDC}"
            )
            print("Please ensure the server is running with: ./start.sh")
            return False

        # Run test categories
        try:
            self.run_health_tests()
            self.run_debug_tests()
            self.run_event_store_tests()
            self.run_recovery_tests()
            self.run_system_tests()
        except Exception as e:
            print(f"\n{Colors.FAIL}Test suite error: {str(e)}{Colors.ENDC}")

        # Print summary
        self.print_header("Test Summary")
        total = self.passed + self.failed
        print(f"Total Tests: {total}")
        print(f"{Colors.OKGREEN}Passed: {self.passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.failed}{Colors.ENDC}")

        if self.failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}All tests passed! 🎉{Colors.ENDC}")
        else:
            print(
                f"\n{Colors.WARNING}Some tests failed. Check the output above for details.{Colors.ENDC}"
            )

        return self.failed == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test REST endpoints for Liap Tui backend"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:5050",
        help="Base URL of the server (default: http://localhost:5050)",
    )
    parser.add_argument(
        "--category",
        choices=["health", "debug", "events", "recovery", "system", "all"],
        default="all",
        help="Test only specific category of endpoints",
    )

    args = parser.parse_args()

    tester = RestEndpointTester(args.base_url)

    success = True
    if args.category == "all":
        success = tester.run_all_tests()
    elif args.category == "health":
        tester.run_health_tests()
        success = tester.failed == 0
    elif args.category == "debug":
        tester.run_debug_tests()
        success = tester.failed == 0
    elif args.category == "events":
        tester.run_event_store_tests()
        success = tester.failed == 0
    elif args.category == "recovery":
        tester.run_recovery_tests()
        success = tester.failed == 0
    elif args.category == "system":
        tester.run_system_tests()
        success = tester.failed == 0

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
