# Parallel Test Runner for Contract Testing
"""
Runs tests against both current and refactored systems in parallel,
comparing their behavior to ensure compatibility.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from tests.contracts.golden_master import GoldenMasterRecord, GoldenMasterComparator
from tests.contracts.websocket_contracts import WebSocketContract, get_contract


@dataclass
class TestResult:
    """Result of a single test execution"""
    test_name: str
    contract: WebSocketContract
    success: bool
    current_behavior: Optional[GoldenMasterRecord]
    new_behavior: Optional[GoldenMasterRecord]
    comparison: Optional[Dict[str, Any]]
    error: Optional[str]
    execution_time_ms: float


@dataclass
class TestSuite:
    """Collection of test results"""
    name: str
    started_at: datetime
    completed_at: Optional[datetime]
    results: List[TestResult]
    
    @property
    def total_tests(self) -> int:
        return len(self.results)
    
    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def failed_tests(self) -> int:
        return sum(1 for r in self.results if not r.success)
    
    @property
    def success_rate(self) -> float:
        return (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test suite summary"""
        return {
            "name": self.name,
            "total_tests": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "success_rate": f"{self.success_rate:.1f}%",
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else None
            ),
            "failed_tests": [
                {
                    "name": r.test_name,
                    "error": r.error,
                    "comparison": r.comparison
                }
                for r in self.results if not r.success
            ]
        }


class ParallelContractRunner:
    """Runs contract tests in parallel against both systems"""
    
    def __init__(
        self,
        current_system_handler: Callable,
        new_system_handler: Optional[Callable] = None,
        comparator: Optional[GoldenMasterComparator] = None
    ):
        """
        Initialize the parallel runner
        
        Args:
            current_system_handler: Handler for current system
            new_system_handler: Handler for new system (optional)
            comparator: Comparator for behavior comparison
        """
        self.current_handler = current_system_handler
        self.new_handler = new_system_handler
        self.comparator = comparator or GoldenMasterComparator()
        
    async def run_single_test(
        self,
        contract: WebSocketContract,
        test_message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        Run a single test against both systems
        
        Args:
            contract: The WebSocket contract to test
            test_message: The test message to send
            room_state: Optional initial room state
            
        Returns:
            TestResult with comparison data
        """
        test_name = f"{contract.name}_{test_message.get('action', 'test')}"
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run on current system
            current_behavior = await self._capture_behavior(
                self.current_handler,
                test_message,
                room_state,
                "current"
            )
            
            # Run on new system if available
            new_behavior = None
            comparison = None
            
            if self.new_handler:
                new_behavior = await self._capture_behavior(
                    self.new_handler,
                    test_message,
                    room_state,
                    "new"
                )
                
                # Compare behaviors
                comparison = self.comparator.compare_behavior(
                    current_behavior,
                    new_behavior
                )
                
                success = comparison["match"]
                error = None if success else "Behavior mismatch"
            else:
                # No new system - just validate current behavior
                success = current_behavior is not None
                error = None if success else "Current system test failed"
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return TestResult(
                test_name=test_name,
                contract=contract,
                success=success,
                current_behavior=current_behavior,
                new_behavior=new_behavior,
                comparison=comparison,
                error=error,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                contract=contract,
                success=False,
                current_behavior=None,
                new_behavior=None,
                comparison=None,
                error=f"Test execution failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def run_contract_suite(
        self,
        test_cases: List[Tuple[WebSocketContract, Dict[str, Any], Optional[Dict[str, Any]]]]
    ) -> TestSuite:
        """
        Run a suite of contract tests
        
        Args:
            test_cases: List of (contract, message, room_state) tuples
            
        Returns:
            TestSuite with all results
        """
        suite = TestSuite(
            name="WebSocket Contract Tests",
            started_at=datetime.now(),
            completed_at=None,
            results=[]
        )
        
        # Run tests concurrently
        tasks = []
        for contract, message, room_state in test_cases:
            task = self.run_single_test(contract, message, room_state)
            tasks.append(task)
        
        # Wait for all tests to complete
        results = await asyncio.gather(*tasks)
        suite.results = results
        suite.completed_at = datetime.now()
        
        return suite
    
    async def _capture_behavior(
        self,
        handler: Callable,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]],
        system_name: str
    ) -> GoldenMasterRecord:
        """Capture behavior from a system handler"""
        # Mock infrastructure for capturing
        broadcasts = []
        response = None
        
        async def mock_broadcast(room_id: str, event: str, data: dict):
            broadcasts.append({
                "room_id": room_id,
                "event": event,
                "data": data
            })
        
        # Create mock WebSocket
        class MockWebSocket:
            async def send_json(self, data):
                nonlocal response
                response = data
        
        mock_ws = MockWebSocket()
        
        # Execute handler
        start_time = asyncio.get_event_loop().time()
        
        try:
            # This is simplified - adapt to your actual handler interface
            await handler(mock_ws, message, room_state, mock_broadcast)
        except Exception as e:
            response = {
                "event": "error",
                "data": {"message": str(e)}
            }
        
        end_time = asyncio.get_event_loop().time()
        
        # Create behavior record
        return GoldenMasterRecord(
            test_id=f"{system_name}_{message.get('action', 'test')}",
            message_name=message.get("action", "unknown"),
            input_message=message,
            response=response,
            broadcasts=broadcasts,
            state_changes={},  # Simplified
            timing={
                "duration_ms": (end_time - start_time) * 1000
            },
            timestamp=datetime.now().isoformat(),
            system_version=system_name
        )
    
    def save_test_results(self, suite: TestSuite, output_path: str = "test_results.json"):
        """Save test results to file"""
        results_data = {
            "summary": suite.get_summary(),
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "contract_name": r.contract.name,
                    "success": r.success,
                    "error": r.error,
                    "comparison": r.comparison,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in suite.results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
    
    def generate_compatibility_report(self, suite: TestSuite) -> str:
        """Generate a human-readable compatibility report"""
        report = []
        report.append("=" * 60)
        report.append("WebSocket Contract Compatibility Report")
        report.append("=" * 60)
        report.append("")
        
        summary = suite.get_summary()
        report.append(f"Test Suite: {summary['name']}")
        report.append(f"Total Tests: {summary['total_tests']}")
        report.append(f"Passed: {summary['passed']} ({summary['success_rate']})")
        report.append(f"Failed: {summary['failed']}")
        report.append(f"Duration: {summary['duration_seconds']:.2f}s")
        report.append("")
        
        if summary['failed'] > 0:
            report.append("Failed Tests:")
            report.append("-" * 40)
            for failed in summary['failed_tests']:
                report.append(f"\n❌ {failed['name']}")
                report.append(f"   Error: {failed['error']}")
                if failed.get('comparison') and failed['comparison'].get('differences'):
                    report.append("   Differences:")
                    for diff in failed['comparison']['differences']:
                        report.append(f"   - {diff['type']}: {diff.get('details', {}).get('error', 'Unknown')}")
            report.append("")
        
        report.append("Compatibility Assessment:")
        report.append("-" * 40)
        if summary['success_rate'] == "100.0%":
            report.append("✅ FULL COMPATIBILITY - All tests passed!")
            report.append("   The refactored system behaves identically to the current system.")
        elif float(summary['success_rate'][:-1]) >= 95:
            report.append("⚠️  HIGH COMPATIBILITY - Most tests passed")
            report.append("   Review failed tests for critical issues.")
        else:
            report.append("❌ LOW COMPATIBILITY - Significant differences detected")
            report.append("   The refactored system has behavioral differences that need addressing.")
        
        return "\n".join(report)