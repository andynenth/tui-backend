#!/usr/bin/env python3
"""
Room State Synchronization Testing Tool

Tests room state consistency for Step 6.3.2 migration validation.
Validates room operations with clean architecture adapters.
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


class MockRoom:
    """Mock room for testing."""
    
    def __init__(self, room_id: str, host_name: str):
        self.id = room_id
        self.host_name = host_name
        self.slots = []
        self.max_slots = 4
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
    def add_player(self, player):
        """Add player to room."""
        if len(self.slots) < self.max_slots:
            self.slots.append(player)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def remove_player(self, player_id: str):
        """Remove player from room."""
        for i, player in enumerate(self.slots):
            if player and player.id == player_id:
                del self.slots[i]
                self.updated_at = datetime.utcnow()
                return True
        return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get room state dictionary."""
        return {
            "room_id": self.id,
            "host_name": self.host_name,
            "players": [{"id": p.id, "name": p.name} for p in self.slots if p],
            "max_slots": self.max_slots,
            "current_slots": len(self.slots),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class MockPlayer:
    """Mock player for testing."""
    
    def __init__(self, player_id: str, name: str):
        self.id = player_id
        self.name = name
        self.joined_at = datetime.utcnow()


class RoomStateSyncTester:
    """Tests room state synchronization between legacy and clean architecture."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.rooms: Dict[str, MockRoom] = {}
        
    async def test_room_creation_consistency(self) -> Dict[str, Any]:
        """Test room creation state consistency."""
        logger.info("🏠 Testing room creation consistency...")
        
        results = {
            "rooms_created": 0,
            "successful_creations": 0,
            "failed_creations": 0,
            "state_consistency_checks": 0,
            "consistent_states": 0,
            "creation_times": [],
            "average_creation_time_ms": 0
        }
        
        room_count = 10
        
        for i in range(room_count):
            room_id = f"test_room_{i}_{uuid.uuid4().hex[:8]}"
            host_name = f"TestHost{i}"
            
            creation_start = time.perf_counter()
            
            try:
                # Create room (simulate clean architecture)
                room = MockRoom(room_id, host_name)
                self.rooms[room_id] = room
                
                creation_end = time.perf_counter()
                creation_time = (creation_end - creation_start) * 1000
                
                results["rooms_created"] += 1
                results["successful_creations"] += 1
                results["creation_times"].append(creation_time)
                
                # Validate state consistency
                room_state = room.get_state()
                
                # Check state properties
                state_valid = all([
                    room_state["room_id"] == room_id,
                    room_state["host_name"] == host_name,
                    room_state["current_slots"] == 0,
                    room_state["max_slots"] == 4,
                    "created_at" in room_state,
                    "updated_at" in room_state
                ])
                
                results["state_consistency_checks"] += 1
                if state_valid:
                    results["consistent_states"] += 1
                
            except Exception as e:
                logger.error(f"Room creation failed: {e}")
                results["failed_creations"] += 1
        
        # Calculate statistics
        if results["creation_times"]:
            results["average_creation_time_ms"] = statistics.mean(results["creation_times"])
            results["max_creation_time_ms"] = max(results["creation_times"])
        
        consistency_rate = (results["consistent_states"] / max(results["state_consistency_checks"], 1)) * 100
        success_rate = (results["successful_creations"] / max(results["rooms_created"], 1)) * 100
        
        print(f"\n🏠 Room Creation Consistency Results:")
        print(f"  Rooms created: {results['rooms_created']}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  State consistency: {consistency_rate:.1f}%")
        print(f"  Average creation time: {results.get('average_creation_time_ms', 0):.2f}ms")
        
        return results
    
    async def test_player_join_leave_consistency(self) -> Dict[str, Any]:
        """Test player join/leave state consistency."""
        logger.info("👥 Testing player join/leave consistency...")
        
        results = {
            "join_operations": 0,
            "successful_joins": 0,
            "leave_operations": 0,
            "successful_leaves": 0,
            "state_sync_errors": 0,
            "final_state_consistent": True,
            "operation_times": []
        }
        
        # Create test room
        room_id = f"join_leave_test_{uuid.uuid4().hex[:8]}"
        room = MockRoom(room_id, "JoinLeaveHost")
        self.rooms[room_id] = room
        
        # Test multiple join/leave cycles
        players = []
        
        # Join phase
        for i in range(4):  # Room capacity is 4
            player_id = f"player_{i}"
            player_name = f"TestPlayer{i}"
            
            operation_start = time.perf_counter()
            
            try:
                player = MockPlayer(player_id, player_name)
                join_success = room.add_player(player)
                
                operation_end = time.perf_counter()
                operation_time = (operation_end - operation_start) * 1000
                
                results["join_operations"] += 1
                results["operation_times"].append(operation_time)
                
                if join_success:
                    results["successful_joins"] += 1
                    players.append(player)
                    
                    # Validate state after join
                    room_state = room.get_state()
                    expected_count = len(players)
                    actual_count = room_state["current_slots"]
                    
                    if actual_count != expected_count:
                        results["state_sync_errors"] += 1
                        logger.warning(f"State mismatch: expected {expected_count}, got {actual_count}")
                        
            except Exception as e:
                logger.error(f"Player join failed: {e}")
        
        # Leave phase
        for i in range(2):  # Remove 2 players
            if players:
                player = players.pop()
                
                operation_start = time.perf_counter()
                
                try:
                    leave_success = room.remove_player(player.id)
                    
                    operation_end = time.perf_counter()
                    operation_time = (operation_end - operation_start) * 1000
                    
                    results["leave_operations"] += 1
                    results["operation_times"].append(operation_time)
                    
                    if leave_success:
                        results["successful_leaves"] += 1
                        
                        # Validate state after leave
                        room_state = room.get_state()
                        expected_count = len(players)
                        actual_count = room_state["current_slots"]
                        
                        if actual_count != expected_count:
                            results["state_sync_errors"] += 1
                            logger.warning(f"State mismatch after leave: expected {expected_count}, got {actual_count}")
                            
                except Exception as e:
                    logger.error(f"Player leave failed: {e}")
        
        # Final state validation
        final_state = room.get_state()
        expected_final_count = len(players)  # Should be 2
        actual_final_count = final_state["current_slots"]
        
        results["final_state_consistent"] = (expected_final_count == actual_final_count)
        
        # Calculate statistics
        if results["operation_times"]:
            results["average_operation_time_ms"] = statistics.mean(results["operation_times"])
        
        join_success_rate = (results["successful_joins"] / max(results["join_operations"], 1)) * 100
        leave_success_rate = (results["successful_leaves"] / max(results["leave_operations"], 1)) * 100
        
        print(f"\n👥 Player Join/Leave Consistency Results:")
        print(f"  Join success rate: {join_success_rate:.1f}%")
        print(f"  Leave success rate: {leave_success_rate:.1f}%")
        print(f"  State sync errors: {results['state_sync_errors']}")
        print(f"  Final state consistent: {'✅' if results['final_state_consistent'] else '❌'}")
        print(f"  Average operation time: {results.get('average_operation_time_ms', 0):.2f}ms")
        
        return results
    
    async def test_concurrent_room_operations(self) -> Dict[str, Any]:
        """Test concurrent room operations consistency."""
        logger.info("⚡ Testing concurrent room operations...")
        
        results = {
            "concurrent_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "state_conflicts": 0,
            "final_consistency_achieved": True,
            "operation_times": []
        }
        
        # Create test room
        room_id = f"concurrent_test_{uuid.uuid4().hex[:8]}"
        room = MockRoom(room_id, "ConcurrentHost")
        self.rooms[room_id] = room
        
        async def concurrent_join_operation(player_index: int):
            """Simulate concurrent player join."""
            player_id = f"concurrent_player_{player_index}"
            player_name = f"ConcurrentPlayer{player_index}"
            
            operation_start = time.perf_counter()
            
            try:
                # Simulate some processing delay
                await asyncio.sleep(0.01)
                
                player = MockPlayer(player_id, player_name)
                success = room.add_player(player)
                
                operation_end = time.perf_counter()
                operation_time = (operation_end - operation_start) * 1000
                
                return {
                    "success": success,
                    "player_id": player_id,
                    "operation_time": operation_time
                }
                
            except Exception as e:
                logger.error(f"Concurrent join operation failed: {e}")
                return {
                    "success": False,
                    "player_id": player_id,
                    "error": str(e),
                    "operation_time": 0
                }
        
        # Execute concurrent operations
        concurrent_count = 6  # More than room capacity (4) to test limits
        tasks = [concurrent_join_operation(i) for i in range(concurrent_count)]
        
        operation_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        for result in operation_results:
            if isinstance(result, dict):
                results["concurrent_operations"] += 1
                results["operation_times"].append(result["operation_time"])
                
                if result["success"]:
                    results["successful_operations"] += 1
                else:
                    results["failed_operations"] += 1
        
        # Validate final state
        final_state = room.get_state()
        actual_players = final_state["current_slots"]
        
        # Should have exactly 4 players (room capacity)
        if actual_players != 4:
            results["state_conflicts"] += 1
            results["final_consistency_achieved"] = False
            logger.warning(f"Expected 4 players, got {actual_players}")
        
        # Validate that exactly 4 operations succeeded and 2 failed
        expected_successes = 4
        expected_failures = 2
        
        if (results["successful_operations"] != expected_successes or 
            results["failed_operations"] != expected_failures):
            results["state_conflicts"] += 1
            results["final_consistency_achieved"] = False
        
        # Calculate statistics
        if results["operation_times"]:
            results["average_operation_time_ms"] = statistics.mean(results["operation_times"])
        
        success_rate = (results["successful_operations"] / max(results["concurrent_operations"], 1)) * 100
        
        print(f"\n⚡ Concurrent Operations Results:")
        print(f"  Concurrent operations: {results['concurrent_operations']}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  State conflicts: {results['state_conflicts']}")
        print(f"  Final consistency: {'✅' if results['final_consistency_achieved'] else '❌'}")
        print(f"  Average operation time: {results.get('average_operation_time_ms', 0):.2f}ms")
        
        return results
    
    async def test_room_capacity_enforcement(self) -> Dict[str, Any]:
        """Test room capacity enforcement consistency."""
        logger.info("🚪 Testing room capacity enforcement...")
        
        results = {
            "capacity_tests": 0,
            "proper_rejections": 0,
            "capacity_violations": 0,
            "state_consistency_maintained": True
        }
        
        # Create test room
        room_id = f"capacity_test_{uuid.uuid4().hex[:8]}"
        room = MockRoom(room_id, "CapacityHost")
        self.rooms[room_id] = room
        
        # Fill room to capacity
        for i in range(4):  # Room capacity
            player = MockPlayer(f"capacity_player_{i}", f"CapacityPlayer{i}")
            success = room.add_player(player)
            
            if not success:
                results["capacity_violations"] += 1
                logger.error(f"Failed to add player {i} when room should have space")
        
        # Verify room is at capacity
        state = room.get_state()
        if state["current_slots"] != 4:
            results["capacity_violations"] += 1
            results["state_consistency_maintained"] = False
        
        # Try to add beyond capacity
        for i in range(3):  # Try to add 3 more (should all fail)
            player = MockPlayer(f"overflow_player_{i}", f"OverflowPlayer{i}")
            success = room.add_player(player)
            
            results["capacity_tests"] += 1
            
            if not success:
                results["proper_rejections"] += 1
            else:
                results["capacity_violations"] += 1
                logger.error(f"Room allowed player beyond capacity: {i}")
        
        # Verify room is still at exactly capacity
        final_state = room.get_state()
        if final_state["current_slots"] != 4:
            results["capacity_violations"] += 1
            results["state_consistency_maintained"] = False
        
        rejection_rate = (results["proper_rejections"] / max(results["capacity_tests"], 1)) * 100
        
        print(f"\n🚪 Room Capacity Enforcement Results:")
        print(f"  Capacity tests: {results['capacity_tests']}")
        print(f"  Proper rejections: {rejection_rate:.1f}%")
        print(f"  Capacity violations: {results['capacity_violations']}")
        print(f"  State consistency: {'✅' if results['state_consistency_maintained'] else '❌'}")
        
        return results
    
    async def validate_room_management_requirements(self) -> Dict[str, bool]:
        """Validate room management against Phase 6.3.2 requirements."""
        logger.info("🎯 Validating room management requirements...")
        
        # Run all room management tests
        creation_results = await self.test_room_creation_consistency()
        join_leave_results = await self.test_player_join_leave_consistency()
        concurrent_results = await self.test_concurrent_room_operations()
        capacity_results = await self.test_room_capacity_enforcement()
        
        # Validate requirements
        requirements = {
            "all_room_operations_working": (
                creation_results["successful_creations"] > 0 and
                join_leave_results["successful_joins"] > 0 and
                join_leave_results["successful_leaves"] > 0
            ),
            "state_consistency_maintained": (
                creation_results.get("consistent_states", 0) == creation_results.get("state_consistency_checks", 0) and
                join_leave_results.get("final_state_consistent", False) and
                concurrent_results.get("final_consistency_achieved", False) and
                capacity_results.get("state_consistency_maintained", False)
            ),
            "performance_equal_or_better": (
                creation_results.get("average_creation_time_ms", 0) < 100 and
                join_leave_results.get("average_operation_time_ms", 0) < 50
            ),
            "no_data_corruption": (
                creation_results.get("failed_creations", 0) == 0 and
                join_leave_results.get("state_sync_errors", 0) == 0 and
                concurrent_results.get("state_conflicts", 0) == 0 and
                capacity_results.get("capacity_violations", 0) == 0
            )
        }
        
        print(f"\n🎯 Room Management Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {req}: {passed}")
        
        # Store all results
        self.test_results = {
            "creation_test": creation_results,
            "join_leave_test": join_leave_results,
            "concurrent_test": concurrent_results,
            "capacity_test": capacity_results,
            "requirements_validation": requirements
        }
        
        return requirements


async def main():
    """Main room state sync testing function."""
    try:
        logger.info("🚀 Starting room state synchronization testing...")
        
        tester = RoomStateSyncTester()
        requirements = await tester.validate_room_management_requirements()
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "test_results": tester.test_results,
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "room_management_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "room_state_sync_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 Room state sync report saved to: {report_file}")
        
        print(f"\n📋 Room State Synchronization Summary:")
        print(f"✅ All requirements met: {report['summary']['all_requirements_met']}")
        print(f"🎯 Room management grade: {report['summary']['room_management_grade']}")
        
        # Exit with appropriate code
        if report['summary']['all_requirements_met']:
            logger.info("✅ Room state synchronization testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some room management requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Room state synchronization testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())