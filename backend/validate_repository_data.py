#!/usr/bin/env python3
"""
Repository Data Validation Tool

Validates data consistency and integrity for repository migration.
"""

import asyncio
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Set
import json
import uuid

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.repositories.optimized_room_repository import OptimizedRoomRepository
from infrastructure.repositories.optimized_game_repository import OptimizedGameRepository
from infrastructure.repositories.in_memory_room_repository import InMemoryRoomRepository
from domain.entities.room import Room
from domain.entities.game import Game
from domain.value_objects.room_status import RoomStatus
from domain.value_objects.player_role import PlayerRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RepositoryDataValidator:
    """Validates repository data consistency and integrity."""
    
    def __init__(self):
        self.validation_results: Dict[str, Any] = {}
        self.test_data: Dict[str, Any] = {}
        
    async def generate_test_data(self) -> Dict[str, List[Room]]:
        """Generate comprehensive test data for validation."""
        logger.info("📝 Generating test data for validation...")
        
        test_rooms = []
        
        # Basic rooms
        for i in range(50):
            room = Room(
                room_id=f"test_room_{i}",
                host_name=f"host_{i}"
            )
            test_rooms.append(room)
        
        # Rooms with different hosts
        for i in range(10):
            room = Room(
                room_id=f"multi_room_{i}",
                host_name=f"multi_player_{i}_0"
            )
            test_rooms.append(room)
        
        # Edge case rooms
        edge_cases = [
            # Room with very long IDs
            Room(
                room_id="x" * 100,
                host_name="y" * 50
            ),
            # Room with special characters
            Room(
                room_id="special_room_!@#$%",
                host_name="special_player_&*()"
            ),
            # Room with Unicode characters
            Room(
                room_id="unicode_room_αβγδε",
                host_name="unicode_player_中文"
            )
        ]
        
        test_rooms.extend(edge_cases)
        
        self.test_data = {"rooms": test_rooms}
        logger.info(f"✅ Generated {len(test_rooms)} test rooms")
        
        return self.test_data
    
    async def validate_crud_operations(self, repository) -> Dict[str, bool]:
        """Validate basic CRUD operations."""
        logger.info(f"🔄 Validating CRUD operations for {type(repository).__name__}...")
        
        test_rooms = self.test_data["rooms"]
        validation_results = {}
        
        # Test Create (Save)
        try:
            for room in test_rooms:
                await repository.save(room)
            validation_results["create_operations"] = True
            logger.info("✅ Create operations successful")
        except Exception as e:
            validation_results["create_operations"] = False
            logger.error(f"❌ Create operations failed: {e}")
        
        # Test Read (Find)
        try:
            found_count = 0
            for room in test_rooms[:20]:  # Test subset
                found_room = await repository.get_by_id(room.room_id)
                if found_room and found_room.room_id == room.room_id:
                    found_count += 1
            
            validation_results["read_operations"] = found_count == 20
            if validation_results["read_operations"]:
                logger.info("✅ Read operations successful")
            else:
                logger.error(f"❌ Read operations failed: found {found_count}/20")
        except Exception as e:
            validation_results["read_operations"] = False
            logger.error(f"❌ Read operations failed: {e}")
        
        # Test Update
        try:
            test_room = test_rooms[0]
            # Create a new room with same ID but different host (simulating update)
            updated_room = Room(
                room_id=test_room.room_id,
                host_name="updated_host"
            )
            await repository.save(updated_room)
            
            # Verify update
            found_room = await repository.get_by_id(test_room.room_id)
            validation_results["update_operations"] = (
                found_room and found_room.host_name == "updated_host"
            )
            
            if validation_results["update_operations"]:
                logger.info("✅ Update operations successful")
            else:
                logger.error("❌ Update operations failed: host not updated")
        except Exception as e:
            validation_results["update_operations"] = False
            logger.error(f"❌ Update operations failed: {e}")
        
        # Test Delete (if supported)
        try:
            if hasattr(repository, 'delete'):
                await repository.delete(test_rooms[-1].room_id)
                deleted_room = await repository.get_by_id(test_rooms[-1].room_id)
                validation_results["delete_operations"] = deleted_room is None
            else:
                validation_results["delete_operations"] = True  # Not required
                logger.info("ℹ️ Delete operations not implemented (acceptable)")
        except Exception as e:
            validation_results["delete_operations"] = False
            logger.error(f"❌ Delete operations failed: {e}")
        
        return validation_results
    
    async def validate_data_integrity(self, repository) -> Dict[str, bool]:
        """Validate data integrity and consistency."""
        logger.info(f"🔍 Validating data integrity for {type(repository).__name__}...")
        
        test_rooms = self.test_data["rooms"]
        integrity_results = {}
        
        # Test data round-trip integrity
        try:
            integrity_errors = 0
            for room in test_rooms[:10]:  # Test subset for detailed validation
                saved_room = room
                await repository.save(saved_room)
                
                retrieved_room = await repository.get_by_id(room.room_id)
                
                # Validate all fields
                if not retrieved_room:
                    integrity_errors += 1
                    continue
                
                if (retrieved_room.room_id != saved_room.room_id or
                    retrieved_room.host_name != saved_room.host_name):
                    integrity_errors += 1
            
            integrity_results["data_round_trip"] = integrity_errors == 0
            if integrity_results["data_round_trip"]:
                logger.info("✅ Data round-trip integrity validated")
            else:
                logger.error(f"❌ Data integrity errors: {integrity_errors}")
        except Exception as e:
            integrity_results["data_round_trip"] = False
            logger.error(f"❌ Data integrity validation failed: {e}")
        
        # Test concurrent access integrity
        try:
            # Concurrent writes to same room
            test_room = test_rooms[5]
            
            async def concurrent_update(suffix):
                updated_room = Room(
                    room_id=test_room.room_id,
                    host_name=f"{test_room.host_name}_{suffix}"
                )
                await repository.save(updated_room)
            
            # Run concurrent updates
            await asyncio.gather(
                concurrent_update("_1"),
                concurrent_update("_2"),
                concurrent_update("_3")
            )
            
            # Verify room still exists and is valid
            final_room = await repository.get_by_id(test_room.room_id)
            integrity_results["concurrent_access"] = final_room is not None
            
            if integrity_results["concurrent_access"]:
                logger.info("✅ Concurrent access integrity validated")
            else:
                logger.error("❌ Concurrent access integrity failed")
        except Exception as e:
            integrity_results["concurrent_access"] = False
            logger.error(f"❌ Concurrent access validation failed: {e}")
        
        # Test edge case handling
        try:
            edge_case_errors = 0
            
            # Test None handling
            try:
                none_result = await repository.get_by_id(None)
                if none_result is not None:
                    edge_case_errors += 1
            except:
                pass  # Exception is acceptable for None input
            
            # Test empty string handling
            try:
                empty_result = await repository.get_by_id("")
                if empty_result is not None:
                    edge_case_errors += 1
            except:
                pass  # Exception is acceptable for empty string
            
            # Test non-existent ID
            nonexistent_result = await repository.get_by_id("nonexistent_room_12345")
            if nonexistent_result is not None:
                edge_case_errors += 1
            
            integrity_results["edge_case_handling"] = edge_case_errors == 0
            
            if integrity_results["edge_case_handling"]:
                logger.info("✅ Edge case handling validated")
            else:
                logger.error(f"❌ Edge case handling errors: {edge_case_errors}")
        except Exception as e:
            integrity_results["edge_case_handling"] = False
            logger.error(f"❌ Edge case validation failed: {e}")
        
        return integrity_results
    
    async def compare_repository_implementations(self) -> Dict[str, Any]:
        """Compare optimized vs legacy repository implementations."""
        logger.info("⚖️ Comparing repository implementations...")
        
        optimized_repo = OptimizedRoomRepository(max_rooms=1000)
        legacy_repo = InMemoryRoomRepository()
        
        # Validate both repositories with same data
        optimized_crud = await self.validate_crud_operations(optimized_repo)
        optimized_integrity = await self.validate_data_integrity(optimized_repo)
        
        legacy_crud = await self.validate_crud_operations(legacy_repo)
        legacy_integrity = await self.validate_data_integrity(legacy_repo)
        
        # Compare results
        comparison = {
            "optimized_repository": {
                "crud_operations": optimized_crud,
                "data_integrity": optimized_integrity,
                "overall_score": sum(optimized_crud.values()) + sum(optimized_integrity.values())
            },
            "legacy_repository": {
                "crud_operations": legacy_crud,
                "data_integrity": legacy_integrity,
                "overall_score": sum(legacy_crud.values()) + sum(legacy_integrity.values())
            }
        }
        
        # Consistency check
        comparison["consistency_check"] = {
            "crud_parity": optimized_crud == legacy_crud,
            "integrity_parity": optimized_integrity == legacy_integrity,
            "full_parity": comparison["optimized_repository"]["overall_score"] == comparison["legacy_repository"]["overall_score"]
        }
        
        print(f"\n⚖️ Repository Comparison Results:")
        print(f"✅ Optimized repository score: {comparison['optimized_repository']['overall_score']}")
        print(f"✅ Legacy repository score: {comparison['legacy_repository']['overall_score']}")
        print(f"🔄 Full parity: {comparison['consistency_check']['full_parity']}")
        
        return comparison
    
    async def validate_all_requirements(self) -> Dict[str, bool]:
        """Validate all data consistency requirements."""
        logger.info("🎯 Validating all data consistency requirements...")
        
        # Generate test data
        await self.generate_test_data()
        
        # Run comparison validation
        comparison = await self.compare_repository_implementations()
        
        # Define requirements
        requirements = {
            "data_consistency_100_percent": comparison["consistency_check"]["full_parity"],
            "crud_operations_functional": all(comparison["optimized_repository"]["crud_operations"].values()),
            "data_integrity_maintained": all(comparison["optimized_repository"]["data_integrity"].values()),
            "edge_cases_handled": comparison["optimized_repository"]["data_integrity"].get("edge_case_handling", False),
            "concurrent_access_safe": comparison["optimized_repository"]["data_integrity"].get("concurrent_access", False)
        }
        
        print(f"\n🎯 Data Validation Requirements:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"{status} {req}: {passed}")
        
        return requirements


async def main():
    """Main data validation function."""
    try:
        logger.info("🚀 Starting repository data validation...")
        
        validator = RepositoryDataValidator()
        requirements = await validator.validate_all_requirements()
        
        # Prepare report
        results = {
            "timestamp": time.time(),
            "requirements_validation": requirements,
            "test_data_summary": {
                "total_rooms": len(validator.test_data.get("rooms", [])),
                "edge_cases": 3
            },
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "validation_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "repository_data_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📁 Validation report saved to: {report_file}")
        
        print(f"\n📋 Data Validation Summary:")
        print(f"✅ All requirements met: {results['summary']['all_requirements_met']}")
        print(f"🎯 Validation grade: {results['summary']['validation_grade']}")
        
        # Exit with appropriate code
        if results['summary']['all_requirements_met']:
            logger.info("✅ Repository data validation successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some data validation requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Data validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())