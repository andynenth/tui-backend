"""
Tests for the hybrid event store and event sourcing infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

from infrastructure.event_store import (
    Event,
    EventType,
    EventStream,
    HybridEventStore,
    DomainEvent,
    EventSourcedAggregate,
    EventSourcedRepository,
    Projection,
    ProjectionManager,
    GameCreatedEvent,
    GameStartedEvent,
    PlayerActionEvent,
    PhaseChangedEvent
)


# Test fixtures

@pytest.fixture
async def event_store():
    """Create a test event store."""
    store = HybridEventStore(
        memory_capacity=1000,
        archive_completed_games=True,
        archive_after_hours=1,
        enable_snapshots=True,
        snapshot_frequency=10
    )
    await store.start()
    yield store
    await store.stop()


# Test domain aggregate

class TestGameAggregate(EventSourcedAggregate):
    """Test game aggregate for event sourcing tests."""
    
    aggregate_type = "game"
    
    def __init__(self, aggregate_id: Optional[str] = None):
        super().__init__(aggregate_id)
        self.room_id = None
        self.players = []
        self.is_started = False
        self.current_phase = None
        self.is_completed = False
    
    def _register_event_handlers(self) -> None:
        """Register event handlers."""
        self._event_handlers[EventType.GAME_CREATED] = self._on_game_created
        self._event_handlers[EventType.GAME_STARTED] = self._on_game_started
        self._event_handlers[EventType.PHASE_CHANGED] = self._on_phase_changed
        self._event_handlers[EventType.GAME_COMPLETED] = self._on_game_completed
    
    def _on_game_created(self, event: Event) -> None:
        """Handle game created event."""
        self.room_id = event.data['room_id']
        self.players = event.data['players']
    
    def _on_game_started(self, event: Event) -> None:
        """Handle game started event."""
        self.is_started = True
    
    def _on_phase_changed(self, event: Event) -> None:
        """Handle phase changed event."""
        self.current_phase = event.data['to_phase']
    
    def _on_game_completed(self, event: Event) -> None:
        """Handle game completed event."""
        self.is_completed = True
    
    # Commands
    
    def create(self, room_id: str, players: List[str]) -> None:
        """Create a new game."""
        if self.room_id is not None:
            raise ValueError("Game already created")
        
        self.raise_event(GameCreatedEvent(
            room_id=room_id,
            players=players,
            config={'max_rounds': 20}
        ))
    
    def start(self, player_id: str) -> None:
        """Start the game."""
        if not self.room_id:
            raise ValueError("Game not created")
        if self.is_started:
            raise ValueError("Game already started")
        
        self.raise_event(GameStartedEvent(started_by=player_id))
    
    def change_phase(self, to_phase: str) -> None:
        """Change game phase."""
        if not self.is_started:
            raise ValueError("Game not started")
        
        self.raise_event(PhaseChangedEvent(
            from_phase=self.current_phase or "NONE",
            to_phase=to_phase,
            phase_data={}
        ))
    
    def complete(self) -> None:
        """Complete the game."""
        if not self.is_started:
            raise ValueError("Game not started")
        
        event = DomainEvent({'reason': 'normal_completion'})
        event.event_type = EventType.GAME_COMPLETED
        self.raise_event(event)


# Test projection

class GameStatsProjection(Projection):
    """Projection that tracks game statistics."""
    
    def __init__(self):
        super().__init__("game_stats")
        self.total_games = 0
        self.active_games = 0
        self.completed_games = 0
        self.games_by_phase = {}
        self.player_game_count = {}
    
    def _register_handlers(self) -> None:
        """Register event handlers."""
        self.register_handler(EventType.GAME_CREATED, self._on_game_created)
        self.register_handler(EventType.GAME_STARTED, self._on_game_started)
        self.register_handler(EventType.PHASE_CHANGED, self._on_phase_changed)
        self.register_handler(EventType.GAME_COMPLETED, self._on_game_completed)
    
    async def _on_game_created(self, event: Event) -> None:
        """Handle game created."""
        self.total_games += 1
        
        for player in event.data['players']:
            self.player_game_count[player] = self.player_game_count.get(player, 0) + 1
    
    async def _on_game_started(self, event: Event) -> None:
        """Handle game started."""
        self.active_games += 1
    
    async def _on_phase_changed(self, event: Event) -> None:
        """Handle phase change."""
        to_phase = event.data['to_phase']
        self.games_by_phase[to_phase] = self.games_by_phase.get(to_phase, 0) + 1
    
    async def _on_game_completed(self, event: Event) -> None:
        """Handle game completed."""
        self.active_games -= 1
        self.completed_games += 1
    
    async def clear(self) -> None:
        """Clear projection state."""
        self.total_games = 0
        self.active_games = 0
        self.completed_games = 0
        self.games_by_phase = {}
        self.player_game_count = {}


# Tests for HybridEventStore

class TestHybridEventStore:
    """Test the hybrid event store implementation."""
    
    @pytest.mark.asyncio
    async def test_append_and_retrieve_events(self, event_store):
        """Test basic event append and retrieval."""
        # Create test events
        game_id = str(uuid.uuid4())
        
        event1 = Event(
            id=str(uuid.uuid4()),
            type=EventType.GAME_CREATED,
            aggregate_id=game_id,
            aggregate_type="game",
            data={'room_id': 'room1', 'players': ['p1', 'p2']},
            metadata={},
            timestamp=datetime.utcnow(),
            sequence_number=0
        )
        
        event2 = Event(
            id=str(uuid.uuid4()),
            type=EventType.GAME_STARTED,
            aggregate_id=game_id,
            aggregate_type="game",
            data={'started_by': 'p1'},
            metadata={},
            timestamp=datetime.utcnow(),
            sequence_number=0
        )
        
        # Append events
        await event_store.append_events([event1, event2])
        
        # Retrieve events
        events = await event_store.get_events(game_id)
        assert len(events) == 2
        assert events[0].type == EventType.GAME_CREATED
        assert events[1].type == EventType.GAME_STARTED
        
        # Check sequence numbers were assigned
        assert events[0].sequence_number == 1
        assert events[1].sequence_number == 2
    
    @pytest.mark.asyncio
    async def test_get_stream(self, event_store):
        """Test retrieving complete event stream."""
        game_id = str(uuid.uuid4())
        
        # Create and append events
        events = []
        for i in range(5):
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.PLAYER_ACTION,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'action': f'action_{i}'},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            )
            events.append(event)
        
        await event_store.append_events(events)
        
        # Get stream
        stream = await event_store.get_stream(game_id)
        assert stream is not None
        assert stream.aggregate_id == game_id
        assert stream.aggregate_type == "game"
        assert len(stream.events) == 5
        assert stream.version == 5
    
    @pytest.mark.asyncio
    async def test_version_filtering(self, event_store):
        """Test retrieving events with version filtering."""
        game_id = str(uuid.uuid4())
        
        # Create 10 events
        events = []
        for i in range(10):
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.PLAYER_ACTION,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'action': f'action_{i}'},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            )
            events.append(event)
        
        await event_store.append_events(events)
        
        # Get events from version 3 to 7
        filtered_events = await event_store.get_events(game_id, from_version=3, to_version=7)
        assert len(filtered_events) == 5
        assert filtered_events[0].sequence_number == 3
        assert filtered_events[-1].sequence_number == 7
    
    @pytest.mark.asyncio
    async def test_event_subscriptions(self, event_store):
        """Test event subscription mechanism."""
        received_events = []
        
        # Subscribe to game created events
        async def handler(event: Event):
            received_events.append(event)
        
        event_store.subscribe(EventType.GAME_CREATED, handler)
        
        # Append event
        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.GAME_CREATED,
            aggregate_id=str(uuid.uuid4()),
            aggregate_type="game",
            data={'room_id': 'room1'},
            metadata={},
            timestamp=datetime.utcnow(),
            sequence_number=0
        )
        
        await event_store.append_event(event)
        
        # Allow async handler to complete
        await asyncio.sleep(0.1)
        
        # Check handler was called
        assert len(received_events) == 1
        assert received_events[0].type == EventType.GAME_CREATED
    
    @pytest.mark.asyncio
    async def test_completed_game_archival(self, event_store):
        """Test that completed games are marked for archival."""
        game_id = str(uuid.uuid4())
        
        # Create game events including completion
        events = [
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_CREATED,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'room_id': 'room1'},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            ),
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_COMPLETED,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'winner': 'p1'},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            )
        ]
        
        await event_store.append_events(events)
        
        # Check stream is marked as completed
        stream = await event_store.get_stream(game_id)
        assert stream.is_completed is True
    
    @pytest.mark.asyncio
    async def test_get_all_events_by_type(self, event_store):
        """Test retrieving all events of a specific type."""
        # Create events of different types
        for i in range(3):
            await event_store.append_event(Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_CREATED,
                aggregate_id=str(uuid.uuid4()),
                aggregate_type="game",
                data={},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            ))
        
        for i in range(2):
            await event_store.append_event(Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_STARTED,
                aggregate_id=str(uuid.uuid4()),
                aggregate_type="game",
                data={},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            ))
        
        # Get only GAME_CREATED events
        created_events = await event_store.get_all_events(event_type=EventType.GAME_CREATED)
        assert len(created_events) == 3
        assert all(e.type == EventType.GAME_CREATED for e in created_events)
        
        # Get only GAME_STARTED events
        started_events = await event_store.get_all_events(event_type=EventType.GAME_STARTED)
        assert len(started_events) == 2
        assert all(e.type == EventType.GAME_STARTED for e in started_events)


# Tests for Event Sourcing

class TestEventSourcing:
    """Test event sourcing abstractions."""
    
    @pytest.mark.asyncio
    async def test_aggregate_creation_and_events(self):
        """Test creating aggregate and raising events."""
        game = TestGameAggregate()
        
        # Create game
        game.create(room_id="room1", players=["p1", "p2", "p3", "p4"])
        
        # Check state
        assert game.room_id == "room1"
        assert game.players == ["p1", "p2", "p3", "p4"]
        assert game.version == 1
        
        # Check uncommitted events
        uncommitted = game.get_uncommitted_events()
        assert len(uncommitted) == 1
        assert isinstance(uncommitted[0], GameCreatedEvent)
    
    @pytest.mark.asyncio
    async def test_aggregate_command_sequence(self):
        """Test executing multiple commands on aggregate."""
        game = TestGameAggregate()
        
        # Execute commands
        game.create(room_id="room1", players=["p1", "p2", "p3", "p4"])
        game.start("p1")
        game.change_phase("PREPARATION")
        game.change_phase("DECLARATION")
        
        # Check state
        assert game.is_started is True
        assert game.current_phase == "DECLARATION"
        assert game.version == 4
        
        # Check uncommitted events
        uncommitted = game.get_uncommitted_events()
        assert len(uncommitted) == 4
    
    @pytest.mark.asyncio
    async def test_rebuild_aggregate_from_events(self):
        """Test rebuilding aggregate from event history."""
        # Create events
        game_id = str(uuid.uuid4())
        events = [
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_CREATED,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'room_id': 'room1', 'players': ['p1', 'p2']},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=1
            ),
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_STARTED,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'started_by': 'p1'},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=2
            ),
            Event(
                id=str(uuid.uuid4()),
                type=EventType.PHASE_CHANGED,
                aggregate_id=game_id,
                aggregate_type="game",
                data={'from_phase': 'NONE', 'to_phase': 'PREPARATION'},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=3
            )
        ]
        
        # Rebuild aggregate
        game = TestGameAggregate.from_events(events)
        
        # Check state
        assert game.id == game_id
        assert game.room_id == "room1"
        assert game.players == ["p1", "p2"]
        assert game.is_started is True
        assert game.current_phase == "PREPARATION"
        assert game.version == 3
        assert len(game.get_uncommitted_events()) == 0
    
    @pytest.mark.asyncio
    async def test_event_sourced_repository(self, event_store):
        """Test saving and loading aggregates through repository."""
        repo = EventSourcedRepository(event_store, TestGameAggregate)
        
        # Create and save aggregate
        game = TestGameAggregate()
        game.create(room_id="room1", players=["p1", "p2", "p3", "p4"])
        game.start("p1")
        
        await repo.save(game)
        
        # Check events are committed
        assert len(game.get_uncommitted_events()) == 0
        
        # Load aggregate
        loaded_game = await repo.get(game.id)
        assert loaded_game is not None
        assert loaded_game.id == game.id
        assert loaded_game.room_id == "room1"
        assert loaded_game.is_started is True
        assert loaded_game.version == 2


# Tests for Projections

class TestProjections:
    """Test projection functionality."""
    
    @pytest.mark.asyncio
    async def test_projection_handles_events(self):
        """Test that projections handle events correctly."""
        projection = GameStatsProjection()
        
        # Create test events
        events = [
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_CREATED,
                aggregate_id="game1",
                aggregate_type="game",
                data={'players': ['p1', 'p2']},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=1
            ),
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_STARTED,
                aggregate_id="game1",
                aggregate_type="game",
                data={},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=2
            ),
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_COMPLETED,
                aggregate_id="game1",
                aggregate_type="game",
                data={},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=3
            )
        ]
        
        # Process events
        for event in events:
            await projection.handle_event(event)
        
        # Check projection state
        assert projection.total_games == 1
        assert projection.active_games == 0
        assert projection.completed_games == 1
        assert projection.player_game_count['p1'] == 1
        assert projection.player_game_count['p2'] == 1
        assert projection.get_last_processed_sequence() == 3
    
    @pytest.mark.asyncio
    async def test_projection_rebuild(self):
        """Test rebuilding projection from event history."""
        projection = GameStatsProjection()
        
        # Set some initial state
        projection.total_games = 100
        projection.active_games = 50
        
        # Create events
        events = [
            Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_CREATED,
                aggregate_id=f"game{i}",
                aggregate_type="game",
                data={'players': ['p1', 'p2']},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=i+1
            )
            for i in range(5)
        ]
        
        # Rebuild projection
        await projection.rebuild_from_events(events)
        
        # Check state was cleared and rebuilt
        assert projection.total_games == 5
        assert projection.active_games == 0
        assert projection.player_game_count['p1'] == 5
    
    @pytest.mark.asyncio
    async def test_projection_manager(self, event_store):
        """Test projection manager functionality."""
        manager = ProjectionManager(event_store)
        
        # Register projection
        stats_projection = GameStatsProjection()
        manager.register_projection(stats_projection)
        
        # Add some events to store
        for i in range(3):
            event = Event(
                id=str(uuid.uuid4()),
                type=EventType.GAME_CREATED,
                aggregate_id=f"game{i}",
                aggregate_type="game",
                data={'players': [f'p{i}', f'p{i+1}']},
                metadata={},
                timestamp=datetime.utcnow(),
                sequence_number=0
            )
            await event_store.append_event(event)
        
        # Rebuild projections
        await manager.rebuild_all()
        
        # Check projection was updated
        assert stats_projection.total_games == 3
        assert len(stats_projection.player_game_count) == 4  # p0, p1, p2, p3