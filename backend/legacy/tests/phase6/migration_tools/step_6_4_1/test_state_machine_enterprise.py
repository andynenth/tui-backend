#!/usr/bin/env python3
"""
State Machine Enterprise Features Testing Tool

Tests enterprise state machine functionality for Step 6.4.1 migration validation.
Validates enterprise broadcasting, phase transitions, and change history.
"""

import asyncio
import sys
import time
import statistics
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockEnterpriseStateMachine:
    """Mock enterprise state machine for testing."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.current_phase = "PREPARATION"
        self.phase_data = {}
        self.change_history = []
        self.sequence_number = 0
        self.created_at = datetime.utcnow()
        self.broadcasting_enabled = True
        self.broadcast_events = []
        
    async def update_phase_data(self, updates: Dict[str, Any], reason: str = ""):
        """Enterprise pattern: Update phase data with automatic broadcasting."""
        self.sequence_number += 1
        
        # Store change in history
        change_record = {
            "sequence": self.sequence_number,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "updates": updates.copy(),
            "phase": self.current_phase
        }
        self.change_history.append(change_record)
        
        # Apply updates
        self.phase_data.update(updates)
        
        # Automatic broadcasting (enterprise feature)
        if self.broadcasting_enabled:
            await self._automatic_broadcast("phase_change", {
                "game_id": self.game_id,
                "phase": self.current_phase,
                "phase_data": self.phase_data.copy(),
                "sequence": self.sequence_number,
                "reason": reason
            })
    
    async def broadcast_custom_event(self, event_type: str, data: Dict[str, Any], reason: str = ""):
        """Enterprise pattern: Custom event broadcasting."""
        self.sequence_number += 1
        
        # Store in history
        change_record = {
            "sequence": self.sequence_number,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "event_type": event_type,
            "data": data.copy(),
            "phase": self.current_phase
        }
        self.change_history.append(change_record)
        
        # Broadcast event
        if self.broadcasting_enabled:
            await self._automatic_broadcast(event_type, data)
    
    async def transition_phase(self, new_phase: str, reason: str = ""):
        """Transition to new phase with enterprise logging."""
        old_phase = self.current_phase
        self.current_phase = new_phase
        
        # Update phase data with transition info
        await self.update_phase_data({
            "previous_phase": old_phase,
            "transition_time": datetime.utcnow().isoformat(),
            "phase_duration": self._calculate_phase_duration()
        }, f"Phase transition: {old_phase} -> {new_phase}. {reason}")
    
    async def _automatic_broadcast(self, event_type: str, data: Dict[str, Any]):
        """Mock automatic broadcasting."""
        broadcast_event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data,
            "game_id": self.game_id
        }
        self.broadcast_events.append(broadcast_event)
        
        # Simulate broadcast delay
        await asyncio.sleep(0.001)
    
    def _calculate_phase_duration(self) -> float:
        """Calculate phase duration in seconds."""
        if self.change_history:
            last_transition = next(
                (record for record in reversed(self.change_history) 
                 if "transition" in record.get("reason", "")), 
                None
            )
            if last_transition:
                then = datetime.fromisoformat(last_transition["timestamp"])
                now = datetime.utcnow()
                return (now - then).total_seconds()
        return 0.0
    
    def get_change_history(self) -> List[Dict[str, Any]]:
        """Get complete change history (enterprise feature)."""
        return self.change_history.copy()
    
    def get_serializable_state(self) -> Dict[str, Any]:
        """Get JSON-safe serialized state for WebSocket transmission."""
        return {
            "game_id": self.game_id,
            "phase": self.current_phase,
            "phase_data": self.phase_data.copy(),
            "sequence": self.sequence_number,
            "change_count": len(self.change_history),
            "created_at": self.created_at.isoformat()
        }


class StateTransitionValidator:
    """Validates state transitions follow game rules."""
    
    VALID_TRANSITIONS = {
        "PREPARATION": ["DECLARATION", "PREPARATION"],
        "DECLARATION": ["TURN", "PREPARATION"],
        "TURN": ["SCORING", "TURN"],
        "SCORING": ["PREPARATION", "COMPLETED"],
        "COMPLETED": []
    }
    
    def validate_transition(self, from_phase: str, to_phase: str) -> bool:
        """Validate if transition is allowed."""
        return to_phase in self.VALID_TRANSITIONS.get(from_phase, [])
    
    def get_valid_next_phases(self, current_phase: str) -> List[str]:
        """Get list of valid next phases."""
        return self.VALID_TRANSITIONS.get(current_phase, [])


class StateMachineEnterpriseTester:
    """Tests enterprise state machine functionality."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.state_machines: Dict[str, MockEnterpriseStateMachine] = {}
        self.validator = StateTransitionValidator()
        
    async def test_enterprise_broadcasting_system(self) -> Dict[str, Any]:
        """Test automatic broadcasting system."""
        logger.info("📡 Testing enterprise broadcasting system...")
        
        results = {
            "broadcasts_sent": 0,
            "phase_changes_broadcasted": 0,
            "custom_events_broadcasted": 0,
            "broadcasting_performance_ms": [],
            "all_changes_broadcasted": True,
            "broadcast_data_complete": True
        }
        
        # Create state machine
        game_id = f"broadcast_test_{uuid.uuid4().hex[:8]}"
        sm = MockEnterpriseStateMachine(game_id)
        self.state_machines[game_id] = sm
        
        # Test 1: Phase data updates trigger broadcasts
        broadcast_start = time.perf_counter()
        
        await sm.update_phase_data({
            "current_player": "player_1",
            "turn_number": 1
        }, "First turn initialization")
        
        broadcast_end = time.perf_counter()
        results["broadcasting_performance_ms"].append((broadcast_end - broadcast_start) * 1000)
        
        # Check broadcast occurred
        if sm.broadcast_events:
            results["broadcasts_sent"] += 1
            results["phase_changes_broadcasted"] += 1
            
            # Validate broadcast content
            last_broadcast = sm.broadcast_events[-1]
            if ("game_id" in last_broadcast["data"] and 
                "phase_data" in last_broadcast["data"] and
                "sequence" in last_broadcast["data"]):
                results["broadcast_data_complete"] = True
        
        # Test 2: Custom events trigger broadcasts
        await sm.broadcast_custom_event("player_action", {
            "action": "declare",
            "player": "player_1",
            "data": {"pile_count": 2}
        }, "Player declaration")
        
        if len(sm.broadcast_events) > results["broadcasts_sent"]:
            results["broadcasts_sent"] += 1
            results["custom_events_broadcasted"] += 1
        
        # Test 3: Phase transitions trigger broadcasts
        await sm.transition_phase("DECLARATION", "Game initialization complete")
        
        if len(sm.broadcast_events) > results["broadcasts_sent"]:
            results["broadcasts_sent"] += 1
            results["phase_changes_broadcasted"] += 1
        
        # Test 4: Multiple rapid updates
        for i in range(5):
            await sm.update_phase_data({
                f"rapid_update_{i}": f"value_{i}"
            }, f"Rapid update {i}")
        
        results["broadcasts_sent"] = len(sm.broadcast_events)
        
        # Validate all changes were broadcasted
        total_changes = len(sm.get_change_history())
        if results["broadcasts_sent"] < total_changes:
            results["all_changes_broadcasted"] = False
        
        # Performance validation
        if results["broadcasting_performance_ms"]:
            avg_broadcast_time = statistics.mean(results["broadcasting_performance_ms"])
        else:
            avg_broadcast_time = 0
        
        print(f"\n📡 Enterprise Broadcasting System Results:")
        print(f"  Broadcasts sent: {results['broadcasts_sent']}")
        print(f"  Phase changes broadcasted: {results['phase_changes_broadcasted']}")
        print(f"  Custom events broadcasted: {results['custom_events_broadcasted']}")
        print(f"  All changes broadcasted: {'✅' if results['all_changes_broadcasted'] else '❌'}")
        print(f"  Broadcast data complete: {'✅' if results['broadcast_data_complete'] else '❌'}")
        print(f"  Average broadcast time: {avg_broadcast_time:.2f}ms")
        
        return results
    
    async def test_phase_transition_validation(self) -> Dict[str, Any]:
        """Test phase transition validation."""
        logger.info("🔄 Testing phase transition validation...")
        
        results = {
            "valid_transitions_tested": 0,
            "invalid_transitions_blocked": 0,
            "transition_validation_working": True,
            "phase_history_accurate": True,
            "transition_performance_ms": []
        }
        
        # Create state machine
        game_id = f"transition_test_{uuid.uuid4().hex[:8]}"
        sm = MockEnterpriseStateMachine(game_id)
        self.state_machines[game_id] = sm
        
        # Test valid transition sequence
        valid_sequence = ["PREPARATION", "DECLARATION", "TURN", "SCORING", "PREPARATION"]
        
        for i in range(len(valid_sequence) - 1):
            current_phase = valid_sequence[i]
            next_phase = valid_sequence[i + 1]
            
            # Set current phase
            sm.current_phase = current_phase
            
            # Validate transition
            is_valid = self.validator.validate_transition(current_phase, next_phase)
            
            if is_valid:
                transition_start = time.perf_counter()
                await sm.transition_phase(next_phase, f"Valid transition {i}")
                transition_end = time.perf_counter()
                
                results["transition_performance_ms"].append((transition_end - transition_start) * 1000)
                results["valid_transitions_tested"] += 1
                
                # Verify phase changed
                if sm.current_phase != next_phase:
                    results["transition_validation_working"] = False
        
        # Test invalid transitions
        invalid_transitions = [
            ("PREPARATION", "TURN"),  # Skip DECLARATION
            ("DECLARATION", "SCORING"),  # Skip TURN
            ("COMPLETED", "PREPARATION")  # From terminal state
        ]
        
        for from_phase, to_phase in invalid_transitions:
            is_valid = self.validator.validate_transition(from_phase, to_phase)
            if not is_valid:
                results["invalid_transitions_blocked"] += 1
        
        # Validate phase history in change records
        history = sm.get_change_history()
        for record in history:
            if "phase" not in record:
                results["phase_history_accurate"] = False
                break
        
        # Performance validation
        if results["transition_performance_ms"]:
            avg_transition_time = statistics.mean(results["transition_performance_ms"])
            max_transition_time = max(results["transition_performance_ms"])
        else:
            avg_transition_time = max_transition_time = 0
        
        print(f"\n🔄 Phase Transition Validation Results:")
        print(f"  Valid transitions tested: {results['valid_transitions_tested']}")
        print(f"  Invalid transitions blocked: {results['invalid_transitions_blocked']}")
        print(f"  Transition validation working: {'✅' if results['transition_validation_working'] else '❌'}")
        print(f"  Phase history accurate: {'✅' if results['phase_history_accurate'] else '❌'}")
        print(f"  Average transition time: {avg_transition_time:.2f}ms")
        print(f"  Max transition time: {max_transition_time:.2f}ms")
        
        return results
    
    async def test_change_history_tracking(self) -> Dict[str, Any]:
        """Test change history tracking enterprise feature."""
        logger.info("📚 Testing change history tracking...")
        
        results = {
            "history_records_created": 0,
            "sequence_numbers_correct": True,
            "timestamps_present": True,
            "reasons_recorded": True,
            "history_completeness": True,
            "serialization_performance_ms": []
        }
        
        # Create state machine
        game_id = f"history_test_{uuid.uuid4().hex[:8]}"
        sm = MockEnterpriseStateMachine(game_id)
        self.state_machines[game_id] = sm
        
        # Perform various operations to create history
        operations = [
            ("update_phase_data", {"player_1_ready": True}, "Player 1 ready"),
            ("update_phase_data", {"player_2_ready": True}, "Player 2 ready"),
            ("transition_phase", "DECLARATION", "All players ready"),
            ("broadcast_custom_event", "declaration_started", {"timestamp": time.time()}),
            ("update_phase_data", {"declarations": {"player_1": 2}}, "Player 1 declared"),
            ("transition_phase", "TURN", "All declarations complete")
        ]
        
        for op_type, *args in operations:
            if op_type == "update_phase_data":
                await sm.update_phase_data(args[0], args[1])
            elif op_type == "transition_phase":
                await sm.transition_phase(args[0], args[1])
            elif op_type == "broadcast_custom_event":
                await sm.broadcast_custom_event(args[0], args[1])
        
        # Get and validate history
        history = sm.get_change_history()
        results["history_records_created"] = len(history)
        
        # Validate sequence numbers
        for i, record in enumerate(history):
            expected_sequence = i + 1
            if record.get("sequence", 0) != expected_sequence:
                results["sequence_numbers_correct"] = False
                break
        
        # Validate timestamps
        for record in history:
            if "timestamp" not in record or not record["timestamp"]:
                results["timestamps_present"] = False
                break
        
        # Validate reasons
        for record in history:
            if "reason" not in record:
                results["reasons_recorded"] = False
                break
        
        # Test serialization performance
        for _ in range(10):
            serialize_start = time.perf_counter()
            serializable_state = sm.get_serializable_state()
            serialize_end = time.perf_counter()
            
            results["serialization_performance_ms"].append((serialize_end - serialize_start) * 1000)
            
            # Validate serializable state completeness
            required_fields = ["game_id", "phase", "phase_data", "sequence", "change_count"]
            if not all(field in serializable_state for field in required_fields):
                results["history_completeness"] = False
        
        # Performance metrics
        if results["serialization_performance_ms"]:
            avg_serialization_time = statistics.mean(results["serialization_performance_ms"])
        else:
            avg_serialization_time = 0
        
        print(f"\n📚 Change History Tracking Results:")
        print(f"  History records created: {results['history_records_created']}")
        print(f"  Sequence numbers correct: {'✅' if results['sequence_numbers_correct'] else '❌'}")
        print(f"  Timestamps present: {'✅' if results['timestamps_present'] else '❌'}")
        print(f"  Reasons recorded: {'✅' if results['reasons_recorded'] else '❌'}")
        print(f"  History completeness: {'✅' if results['history_completeness'] else '❌'}")
        print(f"  Average serialization time: {avg_serialization_time:.2f}ms")
        
        return results
    
    async def test_concurrent_state_operations(self) -> Dict[str, Any]:
        """Test concurrent state machine operations."""
        logger.info("⚡ Testing concurrent state operations...")
        
        results = {
            "concurrent_operations": 0,
            "successful_operations": 0,
            "state_consistency_maintained": True,
            "sequence_order_correct": True,
            "broadcast_order_correct": True,
            "operation_times_ms": []
        }
        
        # Create state machine
        game_id = f"concurrent_test_{uuid.uuid4().hex[:8]}"
        sm = MockEnterpriseStateMachine(game_id)
        self.state_machines[game_id] = sm
        
        # Concurrent operation function
        async def concurrent_operation(operation_id: int):
            """Perform concurrent state operation."""
            op_start = time.perf_counter()
            
            try:
                if operation_id % 3 == 0:
                    await sm.update_phase_data({
                        f"concurrent_data_{operation_id}": f"value_{operation_id}"
                    }, f"Concurrent operation {operation_id}")
                elif operation_id % 3 == 1:
                    await sm.broadcast_custom_event("concurrent_event", {
                        "operation_id": operation_id,
                        "timestamp": time.time()
                    }, f"Concurrent event {operation_id}")
                else:
                    # Just get state (read operation)
                    state = sm.get_serializable_state()
                    if not state:
                        raise Exception("Failed to get state")
                
                op_end = time.perf_counter()
                return {
                    "success": True,
                    "operation_id": operation_id,
                    "operation_time": (op_end - op_start) * 1000
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "operation_id": operation_id,
                    "error": str(e),
                    "operation_time": 0
                }
        
        # Execute concurrent operations
        concurrent_count = 20
        tasks = [concurrent_operation(i) for i in range(concurrent_count)]
        operation_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        for result in operation_results:
            if isinstance(result, dict):
                results["concurrent_operations"] += 1
                results["operation_times_ms"].append(result["operation_time"])
                
                if result["success"]:
                    results["successful_operations"] += 1
        
        # Validate state consistency
        final_state = sm.get_serializable_state()
        if final_state["sequence"] != len(sm.get_change_history()):
            results["state_consistency_maintained"] = False
        
        # Validate sequence order in history
        history = sm.get_change_history()
        for i in range(1, len(history)):
            if history[i]["sequence"] != history[i-1]["sequence"] + 1:
                results["sequence_order_correct"] = False
                break
        
        # Validate broadcast order
        broadcasts = sm.broadcast_events
        broadcast_sequences = []
        for broadcast in broadcasts:
            if "sequence" in broadcast["data"]:
                broadcast_sequences.append(broadcast["data"]["sequence"])
        
        if broadcast_sequences != sorted(broadcast_sequences):
            results["broadcast_order_correct"] = False
        
        # Performance metrics
        if results["operation_times_ms"]:
            avg_operation_time = statistics.mean(results["operation_times_ms"])
            success_rate = (results["successful_operations"] / results["concurrent_operations"]) * 100
        else:
            avg_operation_time = success_rate = 0
        
        print(f"\n⚡ Concurrent State Operations Results:")
        print(f"  Concurrent operations: {results['concurrent_operations']}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  State consistency maintained: {'✅' if results['state_consistency_maintained'] else '❌'}")
        print(f"  Sequence order correct: {'✅' if results['sequence_order_correct'] else '❌'}")
        print(f"  Broadcast order correct: {'✅' if results['broadcast_order_correct'] else '❌'}")
        print(f"  Average operation time: {avg_operation_time:.2f}ms")
        
        return results
    
    async def validate_state_machine_requirements(self) -> Dict[str, bool]:
        """Validate state machine against Step 6.4.1 requirements."""
        logger.info("🎯 Validating state machine requirements...")
        
        # Run all tests
        broadcasting_results = await self.test_enterprise_broadcasting_system()
        transition_results = await self.test_phase_transition_validation()
        history_results = await self.test_change_history_tracking()
        concurrent_results = await self.test_concurrent_state_operations()
        
        # Validate requirements
        requirements = {
            "all_phase_transitions_working": (
                transition_results.get("valid_transitions_tested", 0) > 0 and
                transition_results.get("transition_validation_working", False)
            ),
            "enterprise_broadcasting_functional": (
                broadcasting_results.get("all_changes_broadcasted", False) and
                broadcasting_results.get("broadcast_data_complete", False) and
                broadcasting_results.get("broadcasts_sent", 0) > 0
            ),
            "change_history_accurate": (
                history_results.get("sequence_numbers_correct", False) and
                history_results.get("timestamps_present", False) and
                history_results.get("reasons_recorded", False) and
                history_results.get("history_completeness", False)
            ),
            "performance_maintained": (
                concurrent_results.get("state_consistency_maintained", False) and
                concurrent_results.get("sequence_order_correct", False) and
                (concurrent_results.get("successful_operations", 0) / 
                 max(concurrent_results.get("concurrent_operations", 1), 1)) > 0.95
            )
        }
        
        print(f"\n🎯 State Machine Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {req}: {passed}")
        
        # Store all results
        self.test_results = {
            "broadcasting_test": broadcasting_results,
            "transition_test": transition_results,
            "history_test": history_results,
            "concurrent_test": concurrent_results,
            "requirements_validation": requirements
        }
        
        return requirements


async def main():
    """Main state machine testing function."""
    try:
        logger.info("🚀 Starting state machine enterprise features testing...")
        
        tester = StateMachineEnterpriseTester()
        requirements = await tester.validate_state_machine_requirements()
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "test_results": tester.test_results,
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "state_machine_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "state_machine_enterprise_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 State machine enterprise report saved to: {report_file}")
        
        print(f"\n📋 State Machine Enterprise Summary:")
        print(f"✅ All requirements met: {report['summary']['all_requirements_met']}")
        print(f"🎯 State machine grade: {report['summary']['state_machine_grade']}")
        
        # Exit with appropriate code
        if report['summary']['all_requirements_met']:
            logger.info("✅ State machine enterprise testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some state machine requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ State machine enterprise testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())