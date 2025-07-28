#!/usr/bin/env python3
"""
Memory Usage Monitoring Tool

Monitors memory usage patterns for repository migration validation.
"""

import asyncio
import sys
import time
import psutil
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.repositories.optimized_room_repository import OptimizedRoomRepository
from infrastructure.repositories.optimized_game_repository import OptimizedGameRepository
from domain.entities.room import Room
from domain.value_objects.room_status import RoomStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitors memory usage for repository migration validation."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_current_memory()
        self.samples: List[Dict[str, Any]] = []
        
    def get_current_memory(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
            "timestamp": time.time()
        }
    
    def record_sample(self, operation: str, data_count: int = 0):
        """Record a memory usage sample."""
        current_memory = self.get_current_memory()
        sample = {
            "operation": operation,
            "data_count": data_count,
            "memory": current_memory,
            "memory_delta_mb": current_memory["rss_mb"] - self.baseline_memory["rss_mb"]
        }
        self.samples.append(sample)
        return sample
    
    async def monitor_repository_lifecycle(self) -> Dict[str, Any]:
        """Monitor memory usage throughout repository lifecycle."""
        logger.info("🧠 Monitoring repository memory lifecycle...")
        
        # Record baseline
        self.record_sample("baseline")
        
        # Initialize repository
        repo = OptimizedRoomRepository(max_rooms=2000)
        self.record_sample("repository_initialized")
        
        # Gradual data loading
        for batch in range(10):
            # Add 100 rooms per batch
            for i in range(100):
                room_id = f"mem_monitor_room_{batch}_{i}"
                room = Room(
                    room_id=room_id,
                    host_name=f"player_{batch}_{i}"
                )
                await repo.save(room)
            
            # Record memory after each batch
            total_rooms = (batch + 1) * 100
            self.record_sample(f"batch_{batch}_loaded", total_rooms)
            
            # Small delay to allow GC
            await asyncio.sleep(0.1)
        
        # Memory stress test - rapid operations
        stress_start = time.time()
        for i in range(500):
            room_id = f"stress_room_{i}"
            room = Room(
                room_id=room_id,
                host_name=f"stress_player_{i}"
            )
            await repo.save(room)
            
            # Find the room (basic read operation)
            found_room = await repo.get_by_id(room_id)
            # Note: Room is immutable, so we just verify the find operation works
        
        stress_end = time.time()
        self.record_sample("stress_test_complete", 1500)
        
        # Cleanup test
        repo = None  # Release repository reference
        await asyncio.sleep(1)  # Allow GC time
        self.record_sample("repository_released")
        
        # Force garbage collection
        import gc
        gc.collect()
        await asyncio.sleep(1)
        self.record_sample("after_gc")
        
        return {
            "stress_test_duration": stress_end - stress_start,
            "samples": self.samples,
            "memory_analysis": self._analyze_memory_patterns()
        }
    
    def _analyze_memory_patterns(self) -> Dict[str, Any]:
        """Analyze memory usage patterns from samples."""
        if len(self.samples) < 2:
            return {}
        
        # Memory growth analysis
        memory_deltas = [s["memory_delta_mb"] for s in self.samples[1:]]  # Skip baseline
        
        # Find peak memory usage
        peak_sample = max(self.samples, key=lambda s: s["memory"]["rss_mb"])
        
        # Memory efficiency (data items per MB)
        efficiency_samples = [s for s in self.samples if s["data_count"] > 0]
        if efficiency_samples:
            avg_efficiency = sum(s["data_count"] / max(s["memory_delta_mb"], 0.1) 
                               for s in efficiency_samples) / len(efficiency_samples)
        else:
            avg_efficiency = 0
        
        # Memory leak detection (simple heuristic)
        final_memory = self.samples[-1]["memory_delta_mb"]
        expected_cleanup_memory = self.samples[-3]["memory_delta_mb"] * 0.1  # Should cleanup 90%
        potential_leak = final_memory > expected_cleanup_memory
        
        return {
            "peak_memory_mb": peak_sample["memory"]["rss_mb"],
            "peak_memory_delta_mb": peak_sample["memory_delta_mb"],
            "total_memory_growth_mb": max(memory_deltas) - min(memory_deltas),
            "avg_data_efficiency": avg_efficiency,
            "potential_memory_leak": potential_leak,
            "final_memory_delta_mb": final_memory
        }
    
    async def validate_memory_requirements(self) -> Dict[str, bool]:
        """Validate memory usage against requirements."""
        logger.info("🎯 Validating memory requirements...")
        
        # Run memory lifecycle monitoring
        lifecycle_results = await self.monitor_repository_lifecycle()
        analysis = lifecycle_results["memory_analysis"]
        
        # Define memory requirements
        requirements = {
            "memory_growth_under_100mb": analysis.get("total_memory_growth_mb", 200) < 100,
            "no_significant_memory_leaks": not analysis.get("potential_memory_leak", True),
            "efficient_memory_usage": analysis.get("avg_data_efficiency", 0) > 10,  # >10 items per MB
            "peak_memory_reasonable": analysis.get("peak_memory_mb", 1000) < 500  # <500MB peak
        }
        
        print(f"\n🎯 Memory Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"{status} {req}: {passed}")
        
        # Additional memory statistics
        if "peak_memory_mb" in analysis:
            print(f"\n📊 Memory Statistics:")
            print(f"  Peak memory: {analysis['peak_memory_mb']:.2f}MB")
            print(f"  Memory growth: {analysis['total_memory_growth_mb']:.2f}MB")
            print(f"  Data efficiency: {analysis['avg_data_efficiency']:.1f} items/MB")
            print(f"  Memory leak detected: {analysis['potential_memory_leak']}")
        
        return requirements
    
    def save_memory_report(self, results: Dict[str, Any], filename: str = "memory_monitoring_report.json"):
        """Save memory monitoring report to file."""
        report_file = Path(__file__).parent / filename
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"💾 Memory report saved to: {report_file}")
        return report_file


async def main():
    """Main memory monitoring function."""
    try:
        logger.info("🚀 Starting memory usage monitoring...")
        
        monitor = MemoryMonitor()
        
        # Run memory validation
        requirements = await monitor.validate_memory_requirements()
        
        # Prepare full report
        results = {
            "timestamp": time.time(),
            "baseline_memory": monitor.baseline_memory,
            "requirements_validation": requirements,
            "samples": monitor.samples,
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "memory_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        monitor.save_memory_report(results)
        
        print(f"\n📋 Memory Monitoring Summary:")
        print(f"✅ All requirements met: {results['summary']['all_requirements_met']}")
        print(f"🎯 Memory grade: {results['summary']['memory_grade']}")
        
        # Exit with appropriate code
        if results['summary']['all_requirements_met']:
            logger.info("✅ Memory monitoring successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some memory requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Memory monitoring error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())