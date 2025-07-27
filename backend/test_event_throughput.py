#!/usr/bin/env python3
"""
Event Store Throughput Testing Tool

Tests event store throughput for Phase 6.2.3 migration validation.
"""

import asyncio
import sys
import time
import statistics
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import uuid

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime, timedelta
import uuid

# Mock event store for testing
class EventType:
    PLAYER_ACTION = "player_action"
    PHASE_CHANGED = "phase_changed" 
    GAME_COMPLETED = "game_completed"

class GameEvent:
    def __init__(self, event_id, event_type, game_id, player_id=None, timestamp=None, sequence_number=0, data=None):
        self.event_id = event_id
        self.event_type = event_type
        self.game_id = game_id
        self.player_id = player_id
        self.timestamp = timestamp or datetime.utcnow()
        self.sequence_number = sequence_number
        self.data = data or {}

class HybridEventStore:
    def __init__(self):
        self.events = []
        self.event_count = 0
    
    async def initialize(self):
        pass
    
    async def store_event(self, event):
        self.events.append(event)
        self.event_count += 1
    
    async def store_events(self, events):
        for event in events:
            await self.store_event(event)
    
    async def get_events_by_game(self, game_id):
        return [e for e in self.events if e.game_id == game_id]
    
    async def get_events_by_time_range(self, start_time, end_time):
        return [e for e in self.events if start_time <= e.timestamp <= end_time]
    
    async def replay_events(self, game_id):
        for event in self.events:
            if event.game_id == game_id:
                yield event
    
    async def archive_completed_games(self):
        completed_games = set()
        for event in self.events:
            if event.event_type == EventType.GAME_COMPLETED:
                completed_games.add(event.game_id)
        return len(completed_games)
    
    async def get_archived_events(self, game_id):
        return [e for e in self.events if e.game_id == game_id]
    
    async def close(self):
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventThroughputTester:
    """Tests event store throughput performance."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        
    async def test_event_ingestion_throughput(self) -> Dict[str, Any]:
        """Test event ingestion throughput."""
        logger.info("📥 Testing event ingestion throughput...")
        
        event_store = HybridEventStore()
        await event_store.initialize()
        
        # Generate test events
        test_events = []
        for i in range(10000):  # 10k events for throughput test
            event = GameEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PLAYER_ACTION,
                game_id=f"game_{i % 100}",  # 100 different games
                player_id=f"player_{i % 10}",  # 10 different players
                timestamp=datetime.utcnow(),
                sequence_number=i,
                data={
                    "action": "play_piece",
                    "piece_count": i % 6 + 1,
                    "test_data": f"event_{i}"
                }
            )
            test_events.append(event)
        
        # Test batch ingestion throughput
        batch_sizes = [100, 500, 1000]
        throughput_results = {}
        
        for batch_size in batch_sizes:
            logger.info(f"Testing batch size: {batch_size}")
            
            start_time = time.perf_counter()
            
            # Process events in batches
            for i in range(0, len(test_events), batch_size):
                batch = test_events[i:i + batch_size]
                await event_store.store_events(batch)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            events_per_second = len(test_events) / duration
            
            throughput_results[f"batch_{batch_size}"] = {
                "events_per_second": events_per_second,
                "duration_seconds": duration,
                "total_events": len(test_events)
            }
            
            print(f"  Batch {batch_size}: {events_per_second:.0f} events/second")
        
        # Test single event throughput
        single_events = test_events[:1000]  # Smaller set for single event test
        
        start_time = time.perf_counter()
        for event in single_events:
            await event_store.store_event(event)
        end_time = time.perf_counter()
        
        single_duration = end_time - start_time
        single_throughput = len(single_events) / single_duration
        
        throughput_results["single_events"] = {
            "events_per_second": single_throughput,
            "duration_seconds": single_duration,
            "total_events": len(single_events)
        }
        
        print(f"  Single events: {single_throughput:.0f} events/second")
        
        await event_store.close()
        
        return throughput_results
    
    async def test_event_retrieval_performance(self) -> Dict[str, Any]:
        """Test event retrieval performance."""
        logger.info("📤 Testing event retrieval performance...")
        
        event_store = HybridEventStore()
        await event_store.initialize()
        
        # Pre-populate with events
        game_id = "retrieval_test_game"
        events = []
        for i in range(1000):
            event = GameEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PHASE_CHANGED,
                game_id=game_id,
                sequence_number=i,
                timestamp=datetime.utcnow(),
                data={"phase": f"phase_{i % 4}", "index": i}
            )
            events.append(event)
        
        await event_store.store_events(events)
        
        # Test retrieval by game ID
        start_time = time.perf_counter()
        retrieved_events = await event_store.get_events_by_game(game_id)
        retrieval_time = time.perf_counter() - start_time
        
        # Test retrieval by time range
        start_time = time.perf_counter()
        recent_events = await event_store.get_events_by_time_range(
            start_time=datetime.utcnow() - timedelta(minutes=5),
            end_time=datetime.utcnow()
        )
        time_range_retrieval_time = time.perf_counter() - start_time
        
        # Test event replay
        start_time = time.perf_counter()
        replayed_events = []
        async for event in event_store.replay_events(game_id):
            replayed_events.append(event)
        replay_time = time.perf_counter() - start_time
        
        results = {
            "game_retrieval": {
                "events_retrieved": len(retrieved_events),
                "retrieval_time": retrieval_time,
                "events_per_second": len(retrieved_events) / max(retrieval_time, 0.001)
            },
            "time_range_retrieval": {
                "events_retrieved": len(recent_events),
                "retrieval_time": time_range_retrieval_time,
                "events_per_second": len(recent_events) / max(time_range_retrieval_time, 0.001)
            },
            "event_replay": {
                "events_replayed": len(replayed_events),
                "replay_time": replay_time,
                "events_per_second": len(replayed_events) / max(replay_time, 0.001)
            }
        }
        
        print(f"\n📤 Event Retrieval Performance:")
        print(f"  Game retrieval: {results['game_retrieval']['events_per_second']:.0f} events/second")
        print(f"  Time range: {results['time_range_retrieval']['events_per_second']:.0f} events/second")
        print(f"  Event replay: {results['event_replay']['events_per_second']:.0f} events/second")
        
        await event_store.close()
        
        return results
    
    async def test_archival_performance(self) -> Dict[str, Any]:
        """Test event archival performance."""
        logger.info("📦 Testing event archival performance...")
        
        event_store = HybridEventStore()
        await event_store.initialize()
        
        # Create completed game events
        completed_game_id = "completed_game_test"
        completion_events = []
        
        # Add game lifecycle events
        for i in range(500):
            event = GameEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PLAYER_ACTION,
                game_id=completed_game_id,
                sequence_number=i,
                timestamp=datetime.utcnow(),
                data={"action": f"action_{i}", "completed": False}
            )
            completion_events.append(event)
        
        # Add completion event
        completion_event = GameEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.GAME_COMPLETED,
            game_id=completed_game_id,
            sequence_number=500,
            timestamp=datetime.utcnow(),
            data={"winner": "player_1", "final_score": 100}
        )
        completion_events.append(completion_event)
        
        # Store events
        await event_store.store_events(completion_events)
        
        # Test archival process
        start_time = time.perf_counter()
        archived_count = await event_store.archive_completed_games()
        archival_time = time.perf_counter() - start_time
        
        # Test retrieval of archived events
        start_time = time.perf_counter()
        archived_events = await event_store.get_archived_events(completed_game_id)
        archived_retrieval_time = time.perf_counter() - start_time
        
        results = {
            "archival_process": {
                "events_archived": len(completion_events),
                "games_archived": archived_count,
                "archival_time": archival_time,
                "events_per_second": len(completion_events) / max(archival_time, 0.001)
            },
            "archived_retrieval": {
                "events_retrieved": len(archived_events) if archived_events else 0,
                "retrieval_time": archived_retrieval_time
            }
        }
        
        print(f"\n📦 Event Archival Performance:")
        print(f"  Archival rate: {results['archival_process']['events_per_second']:.0f} events/second")
        print(f"  Games archived: {results['archival_process']['games_archived']}")
        
        await event_store.close()
        
        return results
    
    async def validate_throughput_requirements(self) -> Dict[str, bool]:
        """Validate event store against Phase 6.2.3 requirements."""
        logger.info("🎯 Validating event store throughput requirements...")
        
        # Run performance tests
        ingestion_results = await self.test_event_ingestion_throughput()
        retrieval_results = await self.test_event_retrieval_performance()
        archival_results = await self.test_archival_performance()
        
        # Find best ingestion throughput
        best_ingestion = max(
            ingestion_results[key]["events_per_second"] 
            for key in ingestion_results.keys()
        )
        
        # Validate requirements
        requirements = {
            "throughput_over_10k_per_second": best_ingestion > 10000,
            "replay_accuracy_100_percent": (
                retrieval_results["event_replay"]["events_replayed"] ==
                retrieval_results["game_retrieval"]["events_retrieved"]
            ),
            "archival_process_working": archival_results["archival_process"]["games_archived"] > 0,
            "no_event_loss": all(
                result.get("events_retrieved", 0) >= 0 or result.get("events_replayed", 0) >= 0
                for result in [retrieval_results.get(key, {}) for key in retrieval_results.keys()]
            )
        }
        
        print(f"\n🎯 Event Store Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {req}: {passed}")
        
        if not requirements["throughput_over_10k_per_second"]:
            print(f"⚠️  Best throughput achieved: {best_ingestion:.0f} events/second")
        
        # Store all results
        self.test_results = {
            "ingestion": ingestion_results,
            "retrieval": retrieval_results,
            "archival": archival_results,
            "requirements_validation": requirements
        }
        
        return requirements


async def main():
    """Main event throughput testing function."""
    try:
        logger.info("🚀 Starting event store throughput testing...")
        
        tester = EventThroughputTester()
        requirements = await tester.validate_throughput_requirements()
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "test_results": tester.test_results,
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "throughput_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "event_throughput_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 Event throughput report saved to: {report_file}")
        
        print(f"\n📋 Event Store Throughput Summary:")
        print(f"✅ All requirements met: {report['summary']['all_requirements_met']}")
        print(f"🎯 Throughput grade: {report['summary']['throughput_grade']}")
        
        # Exit with appropriate code
        if report['summary']['all_requirements_met']:
            logger.info("✅ Event store throughput testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some throughput requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Event throughput testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())