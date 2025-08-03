# backend/tests/test_state_replay.py

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.services.event_store import EventStore
from engine.game import Game
from engine.player import Player
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase, ActionType, GameAction


@pytest.fixture
async def temp_event_store():
    """Create a temporary event store for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db = tmp.name

    # Temporarily replace the global event store
    from api.services import event_store as event_store_module

    original_store = event_store_module.event_store
    event_store_module.event_store = EventStore(db_path=temp_db)

    yield event_store_module.event_store

    # Restore original and cleanup
    event_store_module.event_store = original_store
    try:
        os.unlink(temp_db)
    except:
        pass


@pytest.fixture
def mock_players():
    """Create mock players for testing"""
    players = []
    for i, name in enumerate(["Alice", "Bob", "Charlie", "David"]):
        player = MagicMock(spec=Player)
        player.name = name
        player.is_bot = i >= 2  # Charlie and David are bots
        player.hand = []
        player.score = 0
        player.declared = 0
        player.zero_declares_in_a_row = 0
        players.append(player)
    return players


@pytest.fixture
async def game_state_machine(mock_players, temp_event_store):
    """Create a game state machine with event storage enabled"""
    # Create game
    game = MagicMock(spec=Game)
    game.players = mock_players
    game.round_number = 1
    game.turn_number = 0

    # Create broadcast callback
    broadcast_callback = AsyncMock()

    # Create state machine
    state_machine = GameStateMachine(game, broadcast_callback)
    state_machine.room_id = "test_room"  # This will initialize ActionQueue

    return state_machine, game, broadcast_callback


@pytest.mark.asyncio
async def test_full_game_replay(game_state_machine, temp_event_store):
    """Test replaying a complete game from events"""
    state_machine, game, broadcast_callback = game_state_machine
    room_id = "test_room"

    # Start the game
    await state_machine.start(GamePhase.PREPARATION)

    # Verify initial phase change was stored
    events = await temp_event_store.get_room_events(room_id)
    phase_events = [e for e in events if e.event_type == "phase_change"]
    assert len(phase_events) >= 1
    assert phase_events[0].payload["new_phase"] == "preparation"

    # Simulate moving through phases
    state_machine.current_phase = GamePhase.DECLARATION
    await state_machine._store_phase_change_event(
        GamePhase.PREPARATION, GamePhase.DECLARATION
    )

    # Simulate player declarations
    for player in game.players[:2]:  # Only human players declare
        await state_machine.store_game_event(
            "player_declared", {"player_name": player.name, "value": 2}, player.name
        )

    # Move to turn phase
    state_machine.current_phase = GamePhase.TURN
    await state_machine._store_phase_change_event(GamePhase.DECLARATION, GamePhase.TURN)

    # Simulate a turn
    await state_machine.store_game_event(
        "pieces_played", {"player_name": "Alice", "pieces": ["R5", "R6"]}, "Alice"
    )

    await state_machine.store_game_event(
        "turn_complete", {"winner": "Alice", "turn_number": 1}
    )

    # Now replay the game
    replayed_state = await temp_event_store.replay_room_state(room_id)

    # Verify the replayed state
    assert replayed_state["room_id"] == room_id
    assert replayed_state["phase"] == "turn"
    assert replayed_state["events_processed"] > 0

    # Verify declarations were captured
    if "declarations" in replayed_state["game_state"]:
        assert replayed_state["game_state"]["declarations"]["Alice"] == 2
        assert replayed_state["game_state"]["declarations"]["Bob"] == 2

    # Export history for analysis
    history = await temp_event_store.export_room_history(room_id)
    assert history["total_events"] > 0
    assert "phase_change" in history["event_types"]
    assert "player_declared" in history["event_types"]


@pytest.mark.asyncio
async def test_phase_data_persistence(game_state_machine, temp_event_store):
    """Test that phase data updates are persisted"""
    state_machine, game, _ = game_state_machine
    room_id = "test_room"

    # Start game and move to turn phase
    await state_machine.start(GamePhase.TURN)

    # Access turn state and update phase data
    turn_state = state_machine.states[GamePhase.TURN]
    await turn_state.update_phase_data(
        {
            "current_player": "Alice",
            "turn_number": 1,
            "required_piece_count": 3,
            "turn_order": ["Alice", "Bob", "Charlie", "David"],
        },
        "Turn started with Alice",
    )

    # Get phase data update events
    events = await temp_event_store.get_events_by_type(room_id, "phase_data_update")
    assert len(events) > 0

    # Find the turn update
    turn_updates = [e for e in events if e.payload.get("phase") == "turn"]
    assert len(turn_updates) > 0

    latest_update = turn_updates[-1]
    assert latest_update.payload["updates"]["current_player"] == "Alice"
    assert latest_update.payload["updates"]["required_piece_count"] == 3
    assert latest_update.payload["reason"] == "Turn started with Alice"


@pytest.mark.asyncio
async def test_action_processing_persistence(game_state_machine, temp_event_store):
    """Test that processed actions are persisted"""
    state_machine, game, _ = game_state_machine
    room_id = "test_room"

    # Create and queue some actions
    actions = [
        GameAction(
            player_name="Alice", action_type=ActionType.DECLARE, payload={"value": 3}
        ),
        GameAction(
            player_name="Bob", action_type=ActionType.DECLARE, payload={"value": 2}
        ),
    ]

    # Add actions to queue
    for action in actions:
        await state_machine.action_queue.add_action(action)

    # Process actions
    processed = await state_machine.action_queue.process_actions()
    assert len(processed) == 2

    # Verify actions were stored
    action_events = await temp_event_store.get_events_by_type(
        room_id, "action_processed"
    )
    assert len(action_events) == 2

    # Verify action details
    assert action_events[0].payload["player_name"] == "Alice"
    assert action_events[0].payload["action_type"] == "DECLARE"
    assert action_events[1].payload["player_name"] == "Bob"


@pytest.mark.asyncio
async def test_replay_with_complex_state(game_state_machine, temp_event_store):
    """Test replaying complex game state with multiple rounds"""
    state_machine, game, _ = game_state_machine
    room_id = "test_room"

    # Simulate multiple rounds
    for round_num in range(1, 4):
        game.round_number = round_num

        # Store round start
        await state_machine.store_game_event(
            "round_started", {"round_number": round_num}
        )

        # Simulate some turns
        for turn in range(1, 3):
            await state_machine.store_game_event(
                "turn_complete",
                {"turn_number": turn, "winner": game.players[turn % 4].name},
            )

        # Store round scoring
        scores = {p.name: 10 * round_num for p in game.players}
        await state_machine.store_game_event(
            "round_scoring", {"round_number": round_num, "scores": scores}
        )

    # Replay the state
    replayed = await temp_event_store.replay_room_state(room_id)

    # Verify multiple rounds were captured
    assert replayed["round_number"] == 3

    # Verify scores accumulated correctly
    for player_name in ["Alice", "Bob", "Charlie", "David"]:
        if player_name in replayed["players"]:
            # Each player should have 10 + 20 + 30 = 60 points
            assert replayed["players"][player_name]["score"] == 60


@pytest.mark.asyncio
async def test_event_sequence_integrity(game_state_machine, temp_event_store):
    """Test that event sequences maintain integrity"""
    state_machine, _, _ = game_state_machine
    room_id = "test_room"

    # Store many events rapidly
    event_count = 50
    for i in range(event_count):
        await state_machine.store_game_event(
            f"test_event_{i % 5}", {"index": i, "data": f"test_data_{i}"}
        )

    # Validate sequence integrity
    validation = await temp_event_store.validate_event_sequence(room_id)
    assert validation["valid"] == True
    assert validation["total_events"] >= event_count
    assert len(validation["gaps"]) == 0


@pytest.mark.asyncio
async def test_concurrent_state_updates(game_state_machine, temp_event_store):
    """Test concurrent state updates maintain consistency"""
    state_machine, _, _ = game_state_machine
    room_id = "test_room"

    # Start in turn phase
    await state_machine.start(GamePhase.TURN)
    turn_state = state_machine.states[GamePhase.TURN]

    # Concurrent updates
    async def update_batch(batch_id):
        for i in range(10):
            await turn_state.update_phase_data(
                {
                    f"update_{batch_id}_{i}": f"value_{i}",
                    "last_update": f"batch_{batch_id}",
                },
                f"Batch {batch_id} update {i}",
            )
            await asyncio.sleep(0.01)  # Small delay to interleave

    # Run concurrent updates
    await asyncio.gather(update_batch(1), update_batch(2), update_batch(3))

    # Verify all updates were captured
    update_events = await temp_event_store.get_events_by_type(
        room_id, "phase_data_update"
    )
    assert len(update_events) >= 30  # 3 batches x 10 updates

    # Replay and verify final state
    replayed = await temp_event_store.replay_room_state(room_id)
    turn_data = replayed["phase_data"].get("turn", {})

    # Should have updates from all batches
    for batch in [1, 2, 3]:
        for i in range(10):
            key = f"update_{batch}_{i}"
            assert key in turn_data
            assert turn_data[key] == f"value_{i}"


@pytest.mark.asyncio
async def test_game_completion_replay(game_state_machine, temp_event_store):
    """Test replaying a completed game"""
    state_machine, game, _ = game_state_machine
    room_id = "test_room"

    # Simulate a complete game
    await state_machine.start(GamePhase.PREPARATION)

    # Play through some rounds
    for round_num in range(1, 6):
        game.round_number = round_num

        # Simulate round
        await state_machine.store_game_event(
            "round_complete",
            {
                "round_number": round_num,
                "scores": {"Alice": 15, "Bob": 10, "Charlie": 5, "David": -5},
            },
        )

    # End game
    await state_machine.store_game_event(
        "game_complete",
        {
            "final_scores": {"Alice": 75, "Bob": 50, "Charlie": 25, "David": -25},
            "winner": "Alice",
            "total_rounds": 5,
        },
    )

    # Replay the completed game
    replayed = await temp_event_store.replay_room_state(room_id)

    # Verify game completion
    assert replayed["status"] == "complete"
    assert replayed["winner"] == "Alice"
    assert replayed["final_scores"]["Alice"] == 75

    # Export and verify history
    history = await temp_event_store.export_room_history(room_id)
    assert "game_complete" in history["event_types"]
    assert history["reconstructed_state"]["status"] == "complete"
