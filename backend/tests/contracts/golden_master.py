# Golden Master Testing Tool
"""
Captures and stores the current system's behavior as "golden masters" - 
reference outputs that the refactored system must match exactly.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
from dataclasses import dataclass, asdict
import time


@dataclass
class GoldenMasterRecord:
    """A single golden master test record"""

    test_id: str
    message_name: str
    input_message: Dict[str, Any]
    response: Optional[Dict[str, Any]]
    broadcasts: List[Dict[str, Any]]
    state_changes: Dict[str, Any]
    timing: Dict[str, float]
    timestamp: str
    system_version: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoldenMasterRecord":
        """Create from dictionary"""
        return cls(**data)


class GoldenMasterCapture:
    """Captures golden master test data from the current system"""

    def __init__(self, storage_path: str = "tests/contracts/golden_masters"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.system_version = "1.0.0"  # Current system version

    async def capture_message_behavior(
        self,
        websocket_handler,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
    ) -> GoldenMasterRecord:
        """
        Capture the behavior of the current system for a given message

        Args:
            websocket_handler: The current WebSocket handler
            message: The input message to test
            room_state: Optional initial room state

        Returns:
            GoldenMasterRecord with captured behavior
        """
        # Generate test ID
        test_id = self._generate_test_id(message)

        # Capture broadcasts
        broadcasts = []
        original_broadcast = None

        async def capture_broadcast(room_id: str, event: str, data: dict):
            """Intercept broadcasts during test"""
            broadcasts.append(
                {
                    "room_id": room_id,
                    "event": event,
                    "data": data,
                    "timestamp": time.time(),
                }
            )
            if original_broadcast:
                await original_broadcast(room_id, event, data)

        # Mock broadcast function
        if hasattr(websocket_handler, "broadcast"):
            original_broadcast = websocket_handler.broadcast
            websocket_handler.broadcast = capture_broadcast

        # Capture timing
        start_time = time.time()

        # Execute the message
        response = None
        try:
            response = await websocket_handler.handle_message(message, room_state)
        except Exception as e:
            response = {
                "event": "error",
                "data": {"message": str(e), "type": "exception"},
            }

        end_time = time.time()

        # Restore original broadcast
        if original_broadcast:
            websocket_handler.broadcast = original_broadcast

        # Capture state changes (simplified - expand based on your needs)
        state_changes = {"room_state_after": room_state if room_state else {}}

        # Create golden master record
        record = GoldenMasterRecord(
            test_id=test_id,
            message_name=message.get("action", message.get("event", "unknown")),
            input_message=message,
            response=response,
            broadcasts=broadcasts,
            state_changes=state_changes,
            timing={
                "start": start_time,
                "end": end_time,
                "duration_ms": (end_time - start_time) * 1000,
            },
            timestamp=datetime.now().isoformat(),
            system_version=self.system_version,
        )

        return record

    def save_golden_master(self, record: GoldenMasterRecord) -> str:
        """Save a golden master record to disk"""
        filename = f"{record.message_name}_{record.test_id}.json"
        filepath = self.storage_path / filename

        with open(filepath, "w") as f:
            json.dump(record.to_dict(), f, indent=2, default=str)

        return str(filepath)

    def load_golden_master(
        self, message_name: str, test_id: str
    ) -> Optional[GoldenMasterRecord]:
        """Load a golden master record from disk"""
        filename = f"{message_name}_{test_id}.json"
        filepath = self.storage_path / filename

        if not filepath.exists():
            return None

        with open(filepath, "r") as f:
            data = json.load(f)

        return GoldenMasterRecord.from_dict(data)

    def list_golden_masters(self) -> List[Dict[str, str]]:
        """List all available golden masters"""
        masters = []
        for filepath in self.storage_path.glob("*.json"):
            with open(filepath, "r") as f:
                data = json.load(f)
            masters.append(
                {
                    "filename": filepath.name,
                    "message_name": data.get("message_name"),
                    "test_id": data.get("test_id"),
                    "timestamp": data.get("timestamp"),
                }
            )
        return masters

    def _generate_test_id(self, message: Dict[str, Any]) -> str:
        """Generate a unique test ID for a message"""
        # Create a hash of the message content for consistent IDs
        message_str = json.dumps(message, sort_keys=True)
        return hashlib.md5(message_str.encode()).hexdigest()[:8]


class GoldenMasterComparator:
    """Compares system behavior against golden masters"""

    def __init__(self, ignore_fields: Optional[List[str]] = None):
        self.ignore_fields = ignore_fields or ["timestamp", "server_time", "room_id"]

    def compare_behavior(
        self, golden_master: GoldenMasterRecord, actual_behavior: GoldenMasterRecord
    ) -> Dict[str, Any]:
        """
        Compare actual behavior against golden master

        Returns:
            Dictionary with comparison results
        """
        comparison = {"match": True, "differences": [], "timing_analysis": {}}

        # Compare responses
        response_diff = self._compare_responses(
            golden_master.response, actual_behavior.response
        )
        if response_diff:
            comparison["match"] = False
            comparison["differences"].append(
                {"type": "response", "details": response_diff}
            )

        # Compare broadcasts
        broadcast_diff = self._compare_broadcasts(
            golden_master.broadcasts, actual_behavior.broadcasts
        )
        if broadcast_diff:
            comparison["match"] = False
            comparison["differences"].append(
                {"type": "broadcasts", "details": broadcast_diff}
            )

        # Compare timing
        timing_analysis = self._analyze_timing(
            golden_master.timing, actual_behavior.timing
        )
        comparison["timing_analysis"] = timing_analysis

        return comparison

    def _compare_responses(
        self, expected: Optional[Dict[str, Any]], actual: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Compare two response objects"""
        if expected is None and actual is None:
            return None

        if expected is None or actual is None:
            return {
                "error": "One response is None",
                "expected": expected,
                "actual": actual,
            }

        # Deep comparison ignoring specified fields
        return self._deep_compare(expected, actual)

    def _compare_broadcasts(
        self, expected: List[Dict[str, Any]], actual: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Compare broadcast sequences"""
        if len(expected) != len(actual):
            return {
                "error": "Different number of broadcasts",
                "expected_count": len(expected),
                "actual_count": len(actual),
            }

        for i, (exp_broadcast, act_broadcast) in enumerate(zip(expected, actual)):
            diff = self._deep_compare(exp_broadcast, act_broadcast)
            if diff:
                return {
                    "error": f"Broadcast {i} differs",
                    "index": i,
                    "difference": diff,
                }

        return None

    def _deep_compare(
        self, expected: Any, actual: Any, path: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Deep comparison of objects, ignoring specified fields"""
        # Check if current path should be ignored
        field_name = path.split(".")[-1] if path else ""
        if field_name in self.ignore_fields:
            return None

        if type(expected) != type(actual):
            return {
                "path": path,
                "expected_type": type(expected).__name__,
                "actual_type": type(actual).__name__,
                "expected": expected,
                "actual": actual,
            }

        if isinstance(expected, dict):
            # Compare dictionaries
            all_keys = set(expected.keys()) | set(actual.keys())
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key
                if key not in expected:
                    return {
                        "path": new_path,
                        "error": "Missing in expected",
                        "actual": actual[key],
                    }
                if key not in actual:
                    return {
                        "path": new_path,
                        "error": "Missing in actual",
                        "expected": expected[key],
                    }
                diff = self._deep_compare(expected[key], actual[key], new_path)
                if diff:
                    return diff

        elif isinstance(expected, list):
            # Compare lists
            if len(expected) != len(actual):
                return {
                    "path": path,
                    "error": "Different list lengths",
                    "expected_length": len(expected),
                    "actual_length": len(actual),
                }
            for i, (exp_item, act_item) in enumerate(zip(expected, actual)):
                new_path = f"{path}[{i}]"
                diff = self._deep_compare(exp_item, act_item, new_path)
                if diff:
                    return diff

        else:
            # Compare primitive values
            if expected != actual:
                return {"path": path, "expected": expected, "actual": actual}

        return None

    def _analyze_timing(
        self, expected_timing: Dict[str, float], actual_timing: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze timing differences"""
        expected_duration = expected_timing.get("duration_ms", 0)
        actual_duration = actual_timing.get("duration_ms", 0)

        return {
            "expected_duration_ms": expected_duration,
            "actual_duration_ms": actual_duration,
            "difference_ms": actual_duration - expected_duration,
            "performance_ratio": (
                actual_duration / expected_duration if expected_duration > 0 else 0
            ),
            "within_threshold": abs(actual_duration - expected_duration)
            < 100,  # 100ms threshold
        }
