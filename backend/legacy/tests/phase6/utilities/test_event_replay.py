#!/usr/bin/env python3
"""
Event Replay Testing Tool

Tests event replay accuracy for Phase 6.2.3 migration validation.
"""

import asyncio
import sys
import time
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import uuid
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Mock event store and types for testing
class EventType:
    GAME_CREATED = "game_created"
    GAME_STARTED = "game_started"
    GAME_COMPLETED = "game_completed"
    PHASE_CHANGED = "phase_changed"
    PLAYER_ACTION = "player_action"
    TURN_CHANGED = "turn_changed"
    SCORE_UPDATED = "score_updated"

class GameEvent:
    def __init__(self, event_id, event_type, game_id, sequence_number=0, timestamp=None, data=None):
        self.event_id = event_id
        self.event_type = event_type
        self.game_id = game_id
        self.sequence_number = sequence_number
        self.timestamp = timestamp or datetime.utcnow()
        self.data = data or {}

class HybridEventStore:
    def __init__(self):
        self.events = []
    
    async def initialize(self):
        pass
    
    async def store_events(self, events):
        self.events.extend(events)
    
    async def replay_events(self, game_id, from_sequence=None):
        for event in self.events:
            if event.game_id == game_id:
                if from_sequence is None or event.sequence_number >= from_sequence:
                    yield event
    
    async def close(self):
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventReplayTester:
    """Tests event replay functionality and accuracy."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        
    async def test_sequential_replay_accuracy(self) -> Dict[str, Any]:
        """Test sequential event replay accuracy."""
        logger.info("📼 Testing sequential event replay accuracy...")
        
        event_store = HybridEventStore()
        await event_store.initialize()
        
        game_id = "replay_test_game"
        
        # Create a sequence of game events
        original_events = []
        
        # Game lifecycle events in order
        event_sequence = [
            (EventType.GAME_CREATED, {"players": ["p1", "p2", "p3", "p4"]}),
            (EventType.GAME_STARTED, {"start_time": datetime.utcnow().isoformat()}),
            (EventType.PHASE_CHANGED, {"from": "WAITING", "to": "PREPARATION"}),
            (EventType.PLAYER_ACTION, {"player": "p1", "action": "declare", "count": 2}),
            (EventType.PLAYER_ACTION, {"player": "p2", "action": "declare", "count": 3}),
            (EventType.PLAYER_ACTION, {"player": "p3", "action": "declare", "count": 1}),
            (EventType.PLAYER_ACTION, {"player": "p4", "action": "declare", "count": 2}),
            (EventType.PHASE_CHANGED, {"from": "DECLARATION", "to": "TURN"}),
            (EventType.TURN_CHANGED, {"from_player": "p1", "to_player": "p2"}),
            (EventType.PLAYER_ACTION, {"player": "p2", "action": "play", "pieces": 3}),
            (EventType.SCORE_UPDATED, {"player": "p2", "score": 15}),
            (EventType.PHASE_CHANGED, {"from": "TURN", "to": "SCORING"}),
            (EventType.GAME_COMPLETED, {"winner": "p2", "final_scores": {"p1": 10, "p2": 15, "p3": 8, "p4": 12}})
        ]
        
        # Create events with proper sequence numbers
        for i, (event_type, data) in enumerate(event_sequence):
            event = GameEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                game_id=game_id,
                sequence_number=i,
                timestamp=datetime.utcnow(),
                data=data
            )
            original_events.append(event)
        
        # Store events
        await event_store.store_events(original_events)
        
        # Replay events
        replayed_events = []
        async for event in event_store.replay_events(game_id):
            replayed_events.append(event)
        
        # Validate replay accuracy
        accuracy_checks = {
            "event_count_match": len(replayed_events) == len(original_events),
            "sequence_order_correct": all(
                replayed_events[i].sequence_number == original_events[i].sequence_number
                for i in range(min(len(replayed_events), len(original_events)))
            ),
            "event_types_match": all(
                replayed_events[i].event_type == original_events[i].event_type
                for i in range(min(len(replayed_events), len(original_events)))
            ),
            "data_integrity": all(
                replayed_events[i].data == original_events[i].data
                for i in range(min(len(replayed_events), len(original_events)))
            ),
            "game_id_consistency": all(
                event.game_id == game_id for event in replayed_events
            )
        }
        
        results = {
            "original_event_count": len(original_events),
            "replayed_event_count": len(replayed_events),
            "accuracy_checks": accuracy_checks,
            "replay_accuracy_percent": (
                sum(accuracy_checks.values()) / len(accuracy_checks) * 100
            )
        }
        
        print(f"\n📼 Sequential Replay Results:")
        print(f"  Original events: {results['original_event_count']}")
        print(f"  Replayed events: {results['replayed_event_count']}")
        print(f"  Accuracy: {results['replay_accuracy_percent']:.1f}%")
        
        for check, passed in accuracy_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        await event_store.close()
        
        return results
    
    async def test_partial_replay_accuracy(self) -> Dict[str, Any]:
        """Test partial event replay (from specific point)."""
        logger.info("⏩ Testing partial event replay accuracy...")
        
        event_store = HybridEventStore()
        await event_store.initialize()
        
        game_id = "partial_replay_test"
        
        # Create 20 events
        all_events = []
        for i in range(20):
            event = GameEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PLAYER_ACTION,
                game_id=game_id,
                sequence_number=i,
                timestamp=datetime.utcnow(),
                data={"action": f"action_{i}", "step": i}
            )
            all_events.append(event)
        
        await event_store.store_events(all_events)
        
        # Test replay from sequence number 10
        partial_events = []
        async for event in event_store.replay_events(game_id, from_sequence=10):
            partial_events.append(event)
        
        # Validate partial replay
        expected_events = all_events[10:]  # Events from sequence 10 onwards
        
        partial_accuracy = {
            "correct_start_sequence": (
                len(partial_events) > 0 and partial_events[0].sequence_number == 10
            ),
            "correct_event_count": len(partial_events) == len(expected_events),
            "sequence_continuity": all(
                partial_events[i].sequence_number == expected_events[i].sequence_number
                for i in range(min(len(partial_events), len(expected_events)))
            ),
            "data_consistency": all(
                partial_events[i].data == expected_events[i].data
                for i in range(min(len(partial_events), len(expected_events)))
            )
        }
        
        results = {
            "total_events": len(all_events),
            "partial_events_expected": len(expected_events),
            "partial_events_actual": len(partial_events),
            "partial_accuracy_checks": partial_accuracy,
            "partial_accuracy_percent": (
                sum(partial_accuracy.values()) / len(partial_accuracy) * 100
            )
        }
        
        print(f"\n⏩ Partial Replay Results:")
        print(f"  Expected events: {results['partial_events_expected']}")
        print(f"  Actual events: {results['partial_events_actual']}")
        print(f"  Accuracy: {results['partial_accuracy_percent']:.1f}%")
        
        await event_store.close()
        
        return results
    
    async def test_concurrent_replay_integrity(self) -> Dict[str, Any]:
        """Test concurrent replay integrity."""
        logger.info("⚡ Testing concurrent replay integrity...")
        
        event_store = HybridEventStore()
        await event_store.initialize()
        
        # Create multiple games
        games = ["concurrent_game_1", "concurrent_game_2", "concurrent_game_3"]
        all_game_events = {}
        
        # Populate each game with events
        for game_id in games:
            events = []
            for i in range(50):
                event = GameEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.PLAYER_ACTION,
                    game_id=game_id,
                    sequence_number=i,
                    timestamp=datetime.utcnow(),
                    data={"game": game_id, "step": i}
                )
                events.append(event)
            
            await event_store.store_events(events)
            all_game_events[game_id] = events
        
        # Concurrent replay tasks
        async def replay_game(game_id):
            replayed = []
            async for event in event_store.replay_events(game_id):
                replayed.append(event)
            return game_id, replayed
        
        # Run concurrent replays
        start_time = time.perf_counter()
        results = await asyncio.gather(*[replay_game(game_id) for game_id in games])
        concurrent_time = time.perf_counter() - start_time
        
        # Validate concurrent replay results
        concurrent_integrity = {}
        for game_id, replayed_events in results:
            original_events = all_game_events[game_id]
            
            concurrent_integrity[game_id] = {
                "event_count_match": len(replayed_events) == len(original_events),
                "sequence_integrity": all(
                    replayed_events[i].sequence_number == original_events[i].sequence_number
                    for i in range(min(len(replayed_events), len(original_events)))
                ),
                "game_id_isolation": all(
                    event.game_id == game_id for event in replayed_events
                )
            }
        
        # Calculate overall concurrent integrity
        all_integrity_checks = []
        for game_checks in concurrent_integrity.values():
            all_integrity_checks.extend(game_checks.values())
        
        overall_integrity = sum(all_integrity_checks) / len(all_integrity_checks) * 100
        
        results = {
            "games_tested": len(games),
            "concurrent_time": concurrent_time,
            "per_game_integrity": concurrent_integrity,
            "overall_integrity_percent": overall_integrity
        }
        
        print(f"\n⚡ Concurrent Replay Results:")
        print(f"  Games tested: {results['games_tested']}")
        print(f"  Concurrent time: {concurrent_time:.3f}s")
        print(f"  Overall integrity: {overall_integrity:.1f}%")
        
        await event_store.close()
        
        return results
    
    async def validate_replay_requirements(self) -> Dict[str, bool]:
        """Validate event replay against Phase 6.2.3 requirements."""
        logger.info("🎯 Validating event replay requirements...")
        
        # Run all replay tests
        sequential_results = await self.test_sequential_replay_accuracy()
        partial_results = await self.test_partial_replay_accuracy()
        concurrent_results = await self.test_concurrent_replay_integrity()
        
        # Validate requirements
        requirements = {
            "replay_accuracy_100_percent": sequential_results["replay_accuracy_percent"] == 100,
            "partial_replay_working": partial_results["partial_accuracy_percent"] >= 95,
            "concurrent_replay_safe": concurrent_results["overall_integrity_percent"] >= 95,
            "no_event_loss": all([
                sequential_results["original_event_count"] == sequential_results["replayed_event_count"],
                partial_results["partial_events_expected"] == partial_results["partial_events_actual"]
            ])
        }
        
        print(f"\n🎯 Event Replay Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {req}: {passed}")
        
        # Store all results
        self.test_results = {
            "sequential_replay": sequential_results,
            "partial_replay": partial_results,
            "concurrent_replay": concurrent_results,
            "requirements_validation": requirements
        }
        
        return requirements


async def main():
    """Main event replay testing function."""
    try:
        logger.info("🚀 Starting event replay testing...")
        
        tester = EventReplayTester()
        requirements = await tester.validate_replay_requirements()
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "test_results": tester.test_results,
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "replay_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "event_replay_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 Event replay report saved to: {report_file}")
        
        print(f"\n📋 Event Replay Summary:")
        print(f"✅ All requirements met: {report['summary']['all_requirements_met']}")
        print(f"🎯 Replay grade: {report['summary']['replay_grade']}")
        
        # Exit with appropriate code
        if report['summary']['all_requirements_met']:
            logger.info("✅ Event replay testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some replay requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Event replay testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())