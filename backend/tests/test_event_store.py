# backend/tests/test_event_store.py

import asyncio
import os
import tempfile
import time
from datetime import datetime, timedelta

import pytest

from api.services.event_store import EventStore, GameEvent


@pytest.fixture
def event_store():
    """Create a temporary event store for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db = tmp.name

    store = EventStore(db_path=temp_db)
    yield store

    # Cleanup
    try:
        os.unlink(temp_db)
    except:
        pass


@pytest.mark.asyncio
async def test_store_and_retrieve_event(event_store):
    """Test basic event storage and retrieval"""
    # Store an event
    event = await event_store.store_event(
        room_id="test_room",
        event_type="test_event",
        payload={"test": "data", "value": 42},
        player_id="player1",
    )

    # Verify event properties
    assert event.room_id == "test_room"
    assert event.event_type == "test_event"
    assert event.payload == {"test": "data", "value": 42}
    assert event.player_id == "player1"
    assert event.sequence >= 0
    assert isinstance(event.timestamp, float)

    # Retrieve events
    events = await event_store.get_room_events("test_room")
    assert len(events) == 1
    assert events[0].event_type == "test_event"


@pytest.mark.asyncio
async def test_get_events_since_sequence(event_store):
    """Test retrieving events after a specific sequence"""
    # Store multiple events
    for i in range(5):
        await event_store.store_event(
            room_id="test_room", event_type=f"event_{i}", payload={"index": i}
        )

    # Get all events
    all_events = await event_store.get_room_events("test_room")
    assert len(all_events) == 5

    # Get events since sequence 2
    recent_events = await event_store.get_events_since(
        "test_room", all_events[2].sequence
    )
    assert len(recent_events) == 2
    assert recent_events[0].payload["index"] == 3
    assert recent_events[1].payload["index"] == 4


@pytest.mark.asyncio
async def test_get_events_by_type(event_store):
    """Test filtering events by type"""
    # Store different types of events
    await event_store.store_event("room1", "phase_change", {"phase": "declaration"})
    await event_store.store_event("room1", "player_action", {"action": "play"})
    await event_store.store_event("room1", "phase_change", {"phase": "turn"})
    await event_store.store_event("room1", "player_action", {"action": "declare"})

    # Get only phase_change events
    phase_events = await event_store.get_events_by_type("room1", "phase_change")
    assert len(phase_events) == 2
    assert all(e.event_type == "phase_change" for e in phase_events)

    # Get only player_action events
    action_events = await event_store.get_events_by_type("room1", "player_action")
    assert len(action_events) == 2
    assert all(e.event_type == "player_action" for e in action_events)


@pytest.mark.asyncio
async def test_replay_room_state(event_store):
    """Test state reconstruction from events"""
    room_id = "game_room"

    # Simulate a game sequence
    await event_store.store_event(room_id, "game_started", {"initial_state": {}})
    await event_store.store_event(
        room_id,
        "player_joined",
        {"player_name": "Alice", "player_data": {"is_bot": False}},
    )
    await event_store.store_event(
        room_id,
        "player_joined",
        {"player_name": "Bob", "player_data": {"is_bot": False}},
    )
    await event_store.store_event(
        room_id, "phase_change", {"old_phase": None, "new_phase": "declaration"}
    )
    await event_store.store_event(
        room_id, "player_declared", {"player_name": "Alice", "value": 3}
    )
    await event_store.store_event(
        room_id, "player_declared", {"player_name": "Bob", "value": 2}
    )

    # Replay state
    state = await event_store.replay_room_state(room_id)

    # Verify reconstructed state
    assert state["room_id"] == room_id
    assert state["phase"] == "declaration"
    assert "Alice" in state["players"]
    assert "Bob" in state["players"]
    assert state["game_state"]["declarations"]["Alice"] == 3
    assert state["game_state"]["declarations"]["Bob"] == 2
    assert state["events_processed"] == 6


@pytest.mark.asyncio
async def test_phase_data_update_events(event_store):
    """Test phase data update event handling"""
    room_id = "test_room"

    # Store phase data update
    await event_store.store_event(
        room_id,
        "phase_data_update",
        {
            "phase": "turn",
            "updates": {
                "current_player": "Alice",
                "turn_number": 1,
                "required_piece_count": 3,
            },
            "reason": "Turn started",
            "sequence": 1,
        },
    )

    # Replay and verify
    state = await event_store.replay_room_state(room_id)
    assert state["phase_data"]["turn"]["current_player"] == "Alice"
    assert state["phase_data"]["turn"]["turn_number"] == 1
    assert state["phase_data"]["turn"]["required_piece_count"] == 3
    assert state["last_update_reason"] == "Turn started"


@pytest.mark.asyncio
async def test_action_processed_events(event_store):
    """Test action tracking"""
    room_id = "test_room"

    # Store player actions
    await event_store.store_event(
        room_id,
        "action_processed",
        {
            "sequence_id": 1,
            "action_type": "DECLARE",
            "player_name": "Alice",
            "payload": {"value": 3},
        },
    )

    await event_store.store_event(
        room_id,
        "action_processed",
        {
            "sequence_id": 2,
            "action_type": "PLAY_PIECES",
            "player_name": "Bob",
            "payload": {"pieces": ["R5", "R6", "R7"]},
        },
    )

    # Replay and verify
    state = await event_store.replay_room_state(room_id)
    assert len(state["actions"]) == 2
    assert state["actions"][0]["action_type"] == "DECLARE"
    assert state["actions"][1]["player_name"] == "Bob"


@pytest.mark.asyncio
async def test_turn_and_scoring_events(event_store):
    """Test turn completion and scoring events"""
    room_id = "test_room"

    # Initialize game
    await event_store.store_event(room_id, "game_started", {"initial_state": {}})

    # Add players
    for player in ["Alice", "Bob", "Charlie", "David"]:
        await event_store.store_event(
            room_id, "player_joined", {"player_name": player, "player_data": {}}
        )

    # Play some turns
    await event_store.store_event(
        room_id, "pieces_played", {"player_name": "Alice", "pieces": ["R5", "R6"]}
    )

    await event_store.store_event(
        room_id, "turn_complete", {"winner": "Alice", "turn_number": 1}
    )

    # Round scoring
    await event_store.store_event(
        room_id,
        "round_scoring",
        {
            "round_number": 1,
            "scores": {"Alice": 10, "Bob": -5, "Charlie": 0, "David": 5},
        },
    )

    # Replay and verify
    state = await event_store.replay_room_state(room_id)
    assert state["turn_number"] == 1
    assert state["last_turn_winner"] == "Alice"
    assert state["round_number"] == 1
    assert state["players"]["Alice"]["score"] == 10
    assert state["players"]["Bob"]["score"] == -5


@pytest.mark.asyncio
async def test_game_complete_event(event_store):
    """Test game completion event"""
    room_id = "test_room"

    await event_store.store_event(
        room_id,
        "game_complete",
        {
            "final_scores": {"Alice": 55, "Bob": 45, "Charlie": 30, "David": 25},
            "winner": "Alice",
        },
    )

    state = await event_store.replay_room_state(room_id)
    assert state["status"] == "complete"
    assert state["winner"] == "Alice"
    assert state["final_scores"]["Alice"] == 55


@pytest.mark.asyncio
async def test_cleanup_old_events(event_store):
    """Test cleaning up old events"""
    room_id = "test_room"

    # Store some events
    for i in range(5):
        await event_store.store_event(
            room_id=room_id, event_type="test_event", payload={"index": i}
        )

    # Verify all events exist
    events = await event_store.get_room_events(room_id)
    assert len(events) == 5

    # Clean up events older than 0 hours (should delete all)
    deleted = await event_store.cleanup_old_events(0)
    assert deleted == 5

    # Verify events are gone
    events = await event_store.get_room_events(room_id)
    assert len(events) == 0


@pytest.mark.asyncio
async def test_validate_event_sequence(event_store):
    """Test event sequence validation"""
    room_id = "test_room"

    # Store events with sequential sequences
    for i in range(5):
        await event_store.store_event(
            room_id=room_id, event_type="test_event", payload={"index": i}
        )

    # Validate sequence
    validation = await event_store.validate_event_sequence(room_id)
    assert validation["valid"] == True
    assert validation["total_events"] == 5
    assert len(validation["gaps"]) == 0


@pytest.mark.asyncio
async def test_export_room_history(event_store):
    """Test room history export"""
    room_id = "test_room"

    # Create a game with various events
    await event_store.store_event(room_id, "game_started", {})
    await event_store.store_event(room_id, "phase_change", {"new_phase": "declaration"})
    await event_store.store_event(
        room_id, "player_declared", {"player_name": "Alice", "value": 3}
    )
    await event_store.store_event(room_id, "phase_change", {"new_phase": "turn"})

    # Export history
    history = await event_store.export_room_history(room_id)

    # Verify export structure
    assert history["room_id"] == room_id
    assert history["total_events"] == 4
    assert "game_started" in history["event_types"]
    assert "phase_change" in history["event_types"]
    assert "player_declared" in history["event_types"]
    assert len(history["timeline"]) == 4
    assert "reconstructed_state" in history
    assert "events_by_type" in history


@pytest.mark.asyncio
async def test_event_stats(event_store):
    """Test event statistics"""
    # Store events in multiple rooms
    for room in ["room1", "room2", "room3"]:
        for i in range(3):
            await event_store.store_event(
                room_id=room, event_type=f"type_{i % 2}", payload={}
            )

    # Get stats
    stats = await event_store.get_event_stats()

    # Verify stats
    assert stats["total_events"] == 9
    assert stats["rooms_with_events"] == 3
    assert len(stats["room_stats"]) == 3
    assert all(count == 3 for count in stats["room_stats"].values())
    assert "type_0" in stats["event_type_stats"]
    assert "type_1" in stats["event_type_stats"]


@pytest.mark.asyncio
async def test_health_check(event_store):
    """Test health check"""
    health = await event_store.health_check()

    assert health["status"] == "healthy"
    assert health["database_accessible"] == True
    assert "total_events" in health
    assert "current_sequence" in health
    assert "last_check" in health


@pytest.mark.asyncio
async def test_concurrent_event_storage(event_store):
    """Test concurrent event storage maintains sequence integrity"""
    room_id = "concurrent_test"

    # Store many events concurrently
    async def store_event_batch(batch_id):
        for i in range(10):
            await event_store.store_event(
                room_id=room_id,
                event_type="concurrent_event",
                payload={"batch": batch_id, "index": i},
            )

    # Run batches concurrently
    await asyncio.gather(
        store_event_batch(1), store_event_batch(2), store_event_batch(3)
    )

    # Verify all events stored
    events = await event_store.get_room_events(room_id)
    assert len(events) == 30

    # Verify sequence integrity
    validation = await event_store.validate_event_sequence(room_id)
    assert validation["valid"] == True

    # Verify sequences are unique
    sequences = [e.sequence for e in events]
    assert len(sequences) == len(set(sequences))
