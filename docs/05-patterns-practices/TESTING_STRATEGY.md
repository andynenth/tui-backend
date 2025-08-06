# Testing Strategy - Comprehensive Testing Architecture

## Table of Contents
1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Testing Pyramid](#testing-pyramid)
4. [Backend Testing](#backend-testing)
5. [Frontend Testing](#frontend-testing)
6. [WebSocket Testing](#websocket-testing)
7. [Integration Testing](#integration-testing)
8. [End-to-End Testing](#end-to-end-testing)
9. [Performance Testing](#performance-testing)
10. [Testing Tools & Infrastructure](#testing-tools--infrastructure)

## Overview

This document outlines the comprehensive testing strategy for Liap Tui, covering all layers from unit tests to end-to-end testing, with special focus on real-time multiplayer game testing challenges.

### Testing Goals

1. **Confidence**: Ensure game logic correctness
2. **Reliability**: Prevent regressions
3. **Performance**: Maintain responsiveness
4. **Documentation**: Tests as living documentation
5. **Development Speed**: Fast feedback loops

## Testing Philosophy

### Core Principles

1. **Test Behavior, Not Implementation**
   ```python
   # ❌ Bad - Testing implementation
   def test_internal_state():
       game._phase_data['current_player'] = 'Alice'
       assert game._current_player_index == 0
   
   # ✅ Good - Testing behavior
   def test_player_turn():
       game.start_new_round()
       assert game.get_current_player() == 'Alice'
   ```

2. **Arrange-Act-Assert Pattern**
   ```python
   def test_play_validation():
       # Arrange
       game = create_game_with_players(['Alice', 'Bob', 'Carol', 'David'])
       game.start_new_round()
       
       # Act
       result = game.play_pieces('Alice', ['p1', 'p2'])
       
       # Assert
       assert result.success
       assert len(result.pieces_played) == 2
   ```

3. **Test Isolation**
   ```python
   # Each test should be independent
   @pytest.fixture
   def fresh_game():
       game = Game(['Alice', 'Bob', 'Carol', 'David'])
       game.start_new_round()
       yield game
       # Cleanup if needed
   ```

## Testing Pyramid

### Test Distribution

```mermaid
graph TB
    subgraph "Testing Pyramid"
        E2E[E2E Tests<br/>10%]
        Integration[Integration Tests<br/>20%]
        Unit[Unit Tests<br/>70%]
    end
    
    subgraph "Characteristics"
        E2E_C[Slow, Expensive<br/>Full User Flows]
        Int_C[Medium Speed<br/>Component Integration]
        Unit_C[Fast, Cheap<br/>Individual Functions]
    end
    
    E2E --> E2E_C
    Integration --> Int_C
    Unit --> Unit_C
    
    style E2E fill:#ff9999
    style Integration fill:#ffcc99
    style Unit fill:#99ff99
```

### Test Categories

| Type | Purpose | Speed | Scope | Example |
|------|---------|-------|-------|---------|
| Unit | Single function/class | <100ms | Isolated | `test_piece_validation()` |
| Integration | Component interaction | <1s | Multiple units | `test_game_state_transitions()` |
| E2E | Full user journey | <10s | Entire system | `test_complete_game_flow()` |
| Performance | Speed/load testing | Varies | System-wide | `test_1000_concurrent_players()` |

## Backend Testing

### Unit Tests

```python
# tests/unit/test_game_rules.py
import pytest
from backend.engine.rules import Rules
from backend.engine.piece import Piece, Rank, Color
from backend.engine.play import PlayType

class TestGameRules:
    """Test game rules validation."""
    
    @pytest.fixture
    def rules(self):
        return Rules()
    
    @pytest.fixture
    def sample_pieces(self):
        return [
            Piece("p1", Rank.GENERAL, Color.RED, 10),
            Piece("p2", Rank.GENERAL, Color.BLACK, 10),
            Piece("p3", Rank.ADVISOR, Color.RED, 10),
            Piece("p4", Rank.ADVISOR, Color.RED, 10)
        ]
    
    def test_valid_pair_play(self, rules, sample_pieces):
        """Test valid pair play."""
        pieces = [sample_pieces[2], sample_pieces[3]]  # Two advisors
        
        is_valid, error, play = rules.is_valid_play(pieces)
        
        assert is_valid
        assert error is None
        assert play.play_type == PlayType.PAIR
    
    def test_invalid_mixed_rank_play(self, rules, sample_pieces):
        """Test invalid play with mixed ranks."""
        pieces = [sample_pieces[0], sample_pieces[2]]  # General + Advisor
        
        is_valid, error, play = rules.is_valid_play(pieces)
        
        assert not is_valid
        assert "Invalid piece combination" in error
        assert play is None
    
    @pytest.mark.parametrize("piece_count,required,expected", [
        (2, 2, True),   # Exact match
        (3, 2, False),  # Too many
        (1, 2, False),  # Too few
        (0, None, True) # Pass allowed
    ])
    def test_piece_count_validation(
        self, rules, sample_pieces, piece_count, required, expected
    ):
        """Test piece count requirements."""
        pieces = sample_pieces[:piece_count]
        
        is_valid, _, _ = rules.is_valid_play(pieces, required)
        
        assert is_valid == expected
    
    def test_mixed_color_play_validation(self, rules):
        """Test mixed color play rules."""
        pieces = [
            Piece("p1", Rank.GENERAL, Color.RED, 10),
            Piece("p2", Rank.GENERAL, Color.BLACK, 10),
            Piece("p3", Rank.ADVISOR, Color.RED, 10)
        ]
        
        is_valid, _, play = rules.is_valid_play(pieces)
        
        assert is_valid
        assert play.play_type == PlayType.MIXED_COLOR
```

### State Machine Tests

```python
# tests/unit/test_state_machine.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.engine.state_machine import (
    GameStateMachine, GamePhase, PreparationState, DeclarationState
)

class TestStateMachine:
    """Test game state machine transitions."""
    
    @pytest.fixture
    def mock_context(self):
        context = MagicMock()
        context.room_id = "test-room"
        context.game = MagicMock()
        context.room_manager = AsyncMock()
        return context
    
    @pytest.mark.asyncio
    async def test_preparation_to_declaration_transition(self, mock_context):
        """Test transition from preparation to declaration phase."""
        # Setup
        state_machine = GameStateMachine(mock_context)
        prep_state = PreparationState(mock_context)
        state_machine.current_state = prep_state
        
        # No weak hands scenario
        mock_context.game.check_weak_hands.return_value = []
        
        # Act
        await state_machine.transition_to_phase(GamePhase.DECLARATION)
        
        # Assert
        assert isinstance(state_machine.current_state, DeclarationState)
        assert state_machine.current_state.phase == GamePhase.DECLARATION
        
        # Verify broadcast called
        mock_context.room_manager.broadcast.assert_called()
        call_args = mock_context.room_manager.broadcast.call_args
        assert call_args[0][1] == "phase_change"
        assert call_args[0][2]["phase"] == "DECLARATION"
    
    @pytest.mark.asyncio
    async def test_weak_hand_redeal_flow(self, mock_context):
        """Test weak hand redeal decision flow."""
        prep_state = PreparationState(mock_context)
        
        # Setup weak hand scenario
        mock_context.game.players = [
            MagicMock(name="Alice", has_weak_hand=True),
            MagicMock(name="Bob", has_weak_hand=True),
            MagicMock(name="Carol", has_weak_hand=False),
            MagicMock(name="David", has_weak_hand=False)
        ]
        
        # Alice accepts redeal
        action = GameAction(
            action_type=ActionType.ACCEPT_REDEAL,
            player_name="Alice",
            data={}
        )
        
        result = await prep_state.handle_action(action)
        
        assert result.success
        assert "Alice" in prep_state.weak_hand_decisions
        assert prep_state.weak_hand_decisions["Alice"] == True
        
        # Bob declines
        action.action_type = ActionType.DECLINE_REDEAL
        action.player_name = "Bob"
        
        result = await prep_state.handle_action(action)
        
        # Should trigger redeal since at least one accepted
        mock_context.game.handle_weak_hand_decision.assert_called()
```

### Mock Testing

```python
# tests/unit/test_with_mocks.py
from unittest.mock import patch, AsyncMock
import pytest

class TestWithMocks:
    """Test using mocks for external dependencies."""
    
    @pytest.mark.asyncio
    @patch('backend.api.room_manager.broadcast')
    async def test_broadcast_on_player_join(self, mock_broadcast):
        """Test that joining triggers broadcast."""
        mock_broadcast.return_value = None
        
        # Join room
        room_manager = RoomManager()
        await room_manager.add_player_to_room("room1", "Alice")
        
        # Verify broadcast called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args[0]
        assert call_args[0] == "room1"
        assert call_args[1] == "player_joined"
        assert call_args[2]["player_name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_game_with_mock_websocket(self):
        """Test game flow with mock WebSocket."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        
        # Process game action
        await handle_play_action(
            mock_ws,
            {"player_name": "Alice", "piece_ids": ["p1", "p2"]}
        )
        
        # Verify response sent
        mock_ws.send_json.assert_called()
        response = mock_ws.send_json.call_args[0][0]
        assert response["event"] == "play_accepted"
```

## Frontend Testing

### Component Tests

```typescript
// tests/components/PieceCard.test.tsx
import { render, fireEvent, screen } from '@testing-library/react';
import { PieceCard } from '@/components/game/PieceCard';
import { Piece } from '@/types/game';

describe('PieceCard Component', () => {
    const mockPiece: Piece = {
        id: 'p1',
        rank: 'GENERAL',
        color: 'RED',
        point: 10
    };
    
    const mockOnClick = jest.fn();
    
    beforeEach(() => {
        mockOnClick.mockClear();
    });
    
    test('renders piece information correctly', () => {
        render(<PieceCard piece={mockPiece} />);
        
        expect(screen.getByText('帥')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
    });
    
    test('handles click when selectable', () => {
        render(
            <PieceCard 
                piece={mockPiece}
                selectable={true}
                onClick={mockOnClick}
            />
        );
        
        fireEvent.click(screen.getByRole('button'));
        
        expect(mockOnClick).toHaveBeenCalledWith('p1');
    });
    
    test('shows selected state', () => {
        const { container } = render(
            <PieceCard piece={mockPiece} selected={true} />
        );
        
        expect(container.firstChild).toHaveClass('selected');
    });
    
    test('disables interaction when not selectable', () => {
        render(
            <PieceCard 
                piece={mockPiece}
                selectable={false}
                onClick={mockOnClick}
            />
        );
        
        const button = screen.getByRole('button');
        expect(button).toHaveAttribute('tabindex', '-1');
        
        fireEvent.click(button);
        expect(mockOnClick).not.toHaveBeenCalled();
    });
});
```

### Hook Tests

```typescript
// tests/hooks/useGame.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useGame } from '@/hooks/useGame';
import { GameProvider } from '@/contexts/GameContext';
import { NetworkService } from '@/services/NetworkService';

// Mock NetworkService
jest.mock('@/services/NetworkService');

describe('useGame Hook', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
        <GameProvider>{children}</GameProvider>
    );
    
    beforeEach(() => {
        (NetworkService.getInstance as jest.Mock).mockReturnValue({
            send: jest.fn(),
            addEventListener: jest.fn(),
            removeEventListener: jest.fn()
        });
    });
    
    test('initializes with default state', () => {
        const { result } = renderHook(() => useGame(), { wrapper });
        
        expect(result.current.gameState).toEqual({
            phase: 'NOT_STARTED',
            players: [],
            currentPlayer: null
        });
    });
    
    test('handles phase change events', async () => {
        const { result } = renderHook(() => useGame(), { wrapper });
        
        // Simulate phase change event
        act(() => {
            result.current.handlePhaseChange({
                phase: 'DECLARATION',
                phase_data: { declarations: {} },
                game_state: { round_number: 1 }
            });
        });
        
        expect(result.current.gameState.phase).toBe('DECLARATION');
        expect(result.current.gameState.round_number).toBe(1);
    });
    
    test('sends game actions', async () => {
        const mockSend = jest.fn();
        (NetworkService.getInstance as jest.Mock).mockReturnValue({
            send: mockSend,
            addEventListener: jest.fn(),
            removeEventListener: jest.fn()
        });
        
        const { result } = renderHook(() => useGame(), { wrapper });
        
        await act(async () => {
            await result.current.playPieces(['p1', 'p2']);
        });
        
        expect(mockSend).toHaveBeenCalledWith(
            expect.any(String), // room_id
            'play',
            expect.objectContaining({
                piece_ids: ['p1', 'p2']
            })
        );
    });
});
```

### Snapshot Tests

```typescript
// tests/components/GameBoard.test.tsx
import { render } from '@testing-library/react';
import { GameBoard } from '@/components/game/GameBoard';

describe('GameBoard Snapshots', () => {
    test('matches snapshot for empty board', () => {
        const { container } = render(
            <GameBoard 
                currentPlays={{}}
                pileCount={0}
            />
        );
        
        expect(container).toMatchSnapshot();
    });
    
    test('matches snapshot with plays', () => {
        const currentPlays = {
            Alice: {
                pieces: [
                    { id: 'p1', rank: 'GENERAL', color: 'RED', point: 10 },
                    { id: 'p2', rank: 'GENERAL', color: 'BLACK', point: 10 }
                ],
                play_type: 'PAIR'
            }
        };
        
        const { container } = render(
            <GameBoard 
                currentPlays={currentPlays}
                pileCount={2}
                lastWinner="Alice"
            />
        );
        
        expect(container).toMatchSnapshot();
    });
});
```

## WebSocket Testing

### WebSocket Test Client

```python
# tests/websocket/test_client.py
import asyncio
import json
from typing import List, Dict, Optional
import websockets

class TestWebSocketClient:
    """Test client for WebSocket testing."""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.received_messages: List[Dict] = []
        self.message_handlers = {}
    
    async def connect(self):
        """Connect to WebSocket server."""
        self.websocket = await websockets.connect(self.url)
        asyncio.create_task(self._receive_messages())
    
    async def _receive_messages(self):
        """Receive messages in background."""
        async for message in self.websocket:
            data = json.loads(message)
            self.received_messages.append(data)
            
            # Call handlers
            event = data.get('event')
            if event in self.message_handlers:
                await self.message_handlers[event](data)
    
    async def send(self, event: str, data: Dict):
        """Send message to server."""
        message = json.dumps({
            'event': event,
            'data': data
        })
        await self.websocket.send(message)
    
    async def wait_for_event(
        self, 
        event: str, 
        timeout: float = 5.0
    ) -> Optional[Dict]:
        """Wait for specific event."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            for msg in reversed(self.received_messages):
                if msg.get('event') == event:
                    return msg
            await asyncio.sleep(0.1)
        
        return None
    
    def on(self, event: str, handler):
        """Register event handler."""
        self.message_handlers[event] = handler
    
    async def close(self):
        """Close connection."""
        if self.websocket:
            await self.websocket.close()
```

### WebSocket Integration Tests

```python
# tests/integration/test_websocket_flow.py
import pytest
import asyncio
from tests.websocket.test_client import TestWebSocketClient

class TestWebSocketGameFlow:
    """Test complete game flow over WebSocket."""
    
    @pytest.mark.asyncio
    async def test_room_creation_and_joining(self, test_server):
        """Test room creation and player joining."""
        # Create clients
        alice = TestWebSocketClient(f"{test_server}/ws/lobby")
        bob = TestWebSocketClient(f"{test_server}/ws/lobby")
        
        await alice.connect()
        await bob.connect()
        
        try:
            # Alice creates room
            await alice.send('create_room', {
                'room_name': 'Test Room',
                'player_name': 'Alice'
            })
            
            # Wait for room created response
            response = await alice.wait_for_event('room_created')
            assert response is not None
            room_id = response['data']['room_id']
            
            # Bob joins room
            bob_room = TestWebSocketClient(f"{test_server}/ws/{room_id}")
            await bob_room.connect()
            
            await bob_room.send('join_room', {
                'player_name': 'Bob'
            })
            
            # Wait for player joined event
            joined_event = await alice.wait_for_event('player_joined')
            assert joined_event['data']['player_name'] == 'Bob'
            
        finally:
            await alice.close()
            await bob.close()
    
    @pytest.mark.asyncio
    async def test_complete_game_round(self, test_server, four_players):
        """Test a complete game round with 4 players."""
        clients = await self._connect_four_players(test_server)
        
        try:
            # Start game
            await clients[0].send('start_game', {
                'player_name': 'Alice'
            })
            
            # Wait for preparation phase
            phase_change = await clients[0].wait_for_event('phase_change')
            assert phase_change['data']['phase'] == 'PREPARATION'
            
            # Handle weak hands if any
            await self._handle_weak_hands(clients, phase_change)
            
            # Declaration phase
            await self._make_declarations(clients)
            
            # Turn phase
            await self._play_turns(clients)
            
            # Verify scoring phase
            scoring = await clients[0].wait_for_event('phase_change')
            assert scoring['data']['phase'] == 'SCORING'
            
            # Verify scores calculated
            assert 'scores' in scoring['data']['phase_data']
            
        finally:
            for client in clients:
                await client.close()
    
    async def _handle_weak_hands(self, clients, phase_data):
        """Handle weak hand decisions if needed."""
        weak_hands = phase_data['data']['phase_data'].get('weak_hands', [])
        
        for i, client in enumerate(clients):
            player_name = ['Alice', 'Bob', 'Carol', 'David'][i]
            if player_name in weak_hands:
                # Decline redeal for testing
                await client.send('decline_redeal', {
                    'player_name': player_name
                })
```

## Integration Testing

### Database Integration Tests

```python
# tests/integration/test_database.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import Player, Game, Room

@pytest.mark.asyncio
async def test_game_persistence(async_session: AsyncSession):
    """Test game state persistence."""
    # Create room and game
    room = Room(
        room_code="TEST123",
        name="Test Room",
        created_by=None
    )
    async_session.add(room)
    
    game = Game(
        room_id=room.id,
        current_phase="DECLARATION",
        phase_data={
            "declarations": {
                "Alice": 2,
                "Bob": 3
            }
        }
    )
    async_session.add(game)
    await async_session.commit()
    
    # Retrieve and verify
    saved_game = await async_session.get(Game, game.id)
    assert saved_game.current_phase == "DECLARATION"
    assert saved_game.phase_data["declarations"]["Alice"] == 2
```

### API Integration Tests

```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient
import pytest

class TestAPIIntegration:
    """Test API endpoints integration."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_room_stats_endpoint(self, client: TestClient, setup_rooms):
        """Test room statistics endpoint."""
        response = client.get("/api/debug/room-stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_rooms" in data
        assert "active_games" in data
        assert "connected_players" in data
```

## End-to-End Testing

### Playwright Tests

```typescript
// tests/e2e/game-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Game Flow E2E', () => {
    test('complete game from start to finish', async ({ page, context }) => {
        // Open 4 browser contexts for 4 players
        const pages = await Promise.all([
            context.newPage(),
            context.newPage(),
            context.newPage(),
            context.newPage()
        ]);
        
        const players = ['Alice', 'Bob', 'Carol', 'David'];
        
        // All players go to lobby
        await Promise.all(
            pages.map(p => p.goto('http://localhost:3000'))
        );
        
        // Alice creates room
        await pages[0].fill('[data-testid="player-name"]', 'Alice');
        await pages[0].fill('[data-testid="room-name"]', 'Test Room');
        await pages[0].click('[data-testid="create-room"]');
        
        // Wait for room creation
        await pages[0].waitForSelector('[data-testid="room-code"]');
        const roomCode = await pages[0].textContent('[data-testid="room-code"]');
        
        // Other players join
        for (let i = 1; i < 4; i++) {
            await pages[i].fill('[data-testid="player-name"]', players[i]);
            await pages[i].fill('[data-testid="room-code"]', roomCode!);
            await pages[i].click('[data-testid="join-room"]');
            
            // Wait for lobby
            await pages[i].waitForSelector('[data-testid="player-list"]');
        }
        
        // Start game
        await pages[0].click('[data-testid="start-game"]');
        
        // All players should see preparation phase
        await Promise.all(
            pages.map(p => p.waitForSelector('[data-testid="phase-preparation"]'))
        );
        
        // Make declarations
        for (let i = 0; i < 4; i++) {
            await pages[i].click(`[data-testid="declare-${i}"]`);
            await pages[i].click('[data-testid="submit-declaration"]');
        }
        
        // Play a turn
        await pages[0].waitForSelector('[data-testid="my-turn-indicator"]');
        await pages[0].click('[data-testid="piece-0"]');
        await pages[0].click('[data-testid="piece-1"]');
        await pages[0].click('[data-testid="play-pieces"]');
        
        // Continue game...
    });
    
    test('handles disconnection and reconnection', async ({ page }) => {
        // Join game
        await page.goto('http://localhost:3000');
        await page.fill('[data-testid="player-name"]', 'Alice');
        // ... join room
        
        // Disconnect network
        await page.context().setOffline(true);
        
        // Should show disconnected state
        await page.waitForSelector('[data-testid="connection-lost"]');
        
        // Reconnect
        await page.context().setOffline(false);
        
        // Should reconnect automatically
        await page.waitForSelector('[data-testid="connection-restored"]');
        
        // Game state should be preserved
        const gamePhase = await page.textContent('[data-testid="game-phase"]');
        expect(gamePhase).toBeTruthy();
    });
});
```

### Visual Regression Tests

```typescript
// tests/visual/game-states.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
    test('game board layouts', async ({ page }) => {
        await page.goto('http://localhost:3000/test/visual');
        
        // Set up test state
        await page.evaluate(() => {
            window.setTestGameState({
                phase: 'TURN',
                players: ['Alice', 'Bob', 'Carol', 'David'],
                current_player: 'Alice'
            });
        });
        
        // Take screenshots
        await expect(page).toHaveScreenshot('game-board-empty.png');
        
        // Add some plays
        await page.evaluate(() => {
            window.addTestPlay('Alice', ['p1', 'p2']);
        });
        
        await expect(page).toHaveScreenshot('game-board-with-play.png');
    });
    
    test('responsive layouts', async ({ page }) => {
        const viewports = [
            { width: 375, height: 667, name: 'iphone' },
            { width: 768, height: 1024, name: 'ipad' },
            { width: 1920, height: 1080, name: 'desktop' }
        ];
        
        for (const viewport of viewports) {
            await page.setViewportSize(viewport);
            await page.goto('http://localhost:3000/game/test');
            
            await expect(page).toHaveScreenshot(`game-${viewport.name}.png`);
        }
    });
});
```

## Performance Testing

### Load Testing

```python
# tests/performance/load_test.py
import asyncio
import time
from statistics import mean, stdev
from tests.websocket.test_client import TestWebSocketClient

class LoadTester:
    """Load test the game server."""
    
    async def test_concurrent_games(
        self,
        num_games: int = 10,
        players_per_game: int = 4
    ):
        """Test multiple concurrent games."""
        results = {
            'connection_times': [],
            'game_start_times': [],
            'turn_times': [],
            'errors': []
        }
        
        games = []
        
        # Start games concurrently
        start_time = time.time()
        
        for game_id in range(num_games):
            game = await self._start_game(
                game_id, 
                players_per_game,
                results
            )
            games.append(game)
        
        # Play some turns
        await asyncio.gather(*[
            self._play_game_turns(game, results)
            for game in games
        ])
        
        total_time = time.time() - start_time
        
        # Generate report
        self._generate_report(results, total_time)
    
    async def _start_game(self, game_id: int, num_players: int, results: dict):
        """Start a single game."""
        players = []
        
        # Connect players
        for i in range(num_players):
            player = TestWebSocketClient(
                f"ws://localhost:8000/ws/game-{game_id}"
            )
            
            connect_start = time.time()
            await player.connect()
            results['connection_times'].append(time.time() - connect_start)
            
            players.append(player)
        
        # Start game
        start_time = time.time()
        await players[0].send('start_game', {
            'player_name': f'Player-{game_id}-0'
        })
        
        # Wait for game start
        await players[0].wait_for_event('phase_change')
        results['game_start_times'].append(time.time() - start_time)
        
        return players
    
    def _generate_report(self, results: dict, total_time: float):
        """Generate performance report."""
        print("\n=== Load Test Results ===")
        print(f"Total test time: {total_time:.2f}s")
        
        if results['connection_times']:
            print(f"\nConnection times:")
            print(f"  Mean: {mean(results['connection_times']):.3f}s")
            print(f"  StdDev: {stdev(results['connection_times']):.3f}s")
            print(f"  Max: {max(results['connection_times']):.3f}s")
        
        if results['errors']:
            print(f"\nErrors: {len(results['errors'])}")
            for error in results['errors'][:5]:
                print(f"  - {error}")
```

### Performance Benchmarks

```python
# tests/performance/benchmarks.py
import pytest
import time
from backend.engine.game import Game

class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""
    
    @pytest.mark.benchmark
    def test_game_initialization_performance(self, benchmark):
        """Benchmark game initialization."""
        def init_game():
            game = Game(['Alice', 'Bob', 'Carol', 'David'])
            game.start_new_round()
            return game
        
        result = benchmark(init_game)
        assert result.round_number == 1
    
    @pytest.mark.benchmark
    def test_play_validation_performance(self, benchmark):
        """Benchmark play validation."""
        game = Game(['Alice', 'Bob', 'Carol', 'David'])
        game.start_new_round()
        
        # Get some pieces
        pieces = game.players[0].hand[:2]
        piece_ids = [p.id for p in pieces]
        
        def validate_play():
            return game.rules.is_valid_play(pieces)
        
        result = benchmark(validate_play)
        assert result[0] is True  # is_valid
    
    @pytest.mark.benchmark
    def test_state_serialization_performance(self, benchmark):
        """Benchmark state serialization."""
        game = Game(['Alice', 'Bob', 'Carol', 'David'])
        game.start_new_round()
        
        def serialize_state():
            return game.to_dict()
        
        result = benchmark(serialize_state)
        assert 'players' in result
        assert 'phase' in result
```

## Testing Tools & Infrastructure

### Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.testclient import TestClient

# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/liap_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    engine = create_async_engine(TEST_DATABASE_URL)
    
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
    
    await engine.dispose()

@pytest.fixture
def test_client() -> TestClient:
    """Create test client."""
    from backend.api.main import app
    return TestClient(app)

@pytest.fixture
def mock_game():
    """Create a mock game for testing."""
    game = Game(['Alice', 'Bob', 'Carol', 'David'])
    game.start_new_round()
    
    # Set up some test state
    game.players[0].hand = [
        Piece("p1", Rank.GENERAL, Color.RED, 10),
        Piece("p2", Rank.GENERAL, Color.BLACK, 10),
        # ... more pieces
    ]
    
    return game
```

### Test Utilities

```python
# tests/utils.py
from typing import List, Dict
import json

class TestHelpers:
    """Common test utilities."""
    
    @staticmethod
    def create_test_pieces(count: int) -> List[Piece]:
        """Create test pieces."""
        pieces = []
        ranks = list(Rank)
        colors = list(Color)
        
        for i in range(count):
            piece = Piece(
                id=f"p{i}",
                rank=ranks[i % len(ranks)],
                color=colors[i % len(colors)],
                point=(i % 10) + 1
            )
            pieces.append(piece)
        
        return pieces
    
    @staticmethod
    async def setup_game_state(
        game: Game,
        phase: GamePhase,
        **kwargs
    ):
        """Set up game in specific state."""
        game.phase = phase
        
        if phase == GamePhase.DECLARATION:
            # Set up for declaration phase
            for i, player in enumerate(game.players):
                if i < kwargs.get('declarations_made', 0):
                    player.declared = i
        
        elif phase == GamePhase.TURN:
            # Set up for turn phase
            game.current_player_index = kwargs.get('current_player', 0)
            game.turn_number = kwargs.get('turn_number', 1)
    
    @staticmethod
    def assert_websocket_message(
        message: Dict,
        event: str,
        **data_checks
    ):
        """Assert WebSocket message format."""
        assert message['event'] == event
        
        for key, expected in data_checks.items():
            assert key in message['data']
            assert message['data'][key] == expected
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: liap_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          pytest tests/ \
            --cov=backend \
            --cov-report=xml \
            --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm run test -- --coverage
      
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright install
          npm run test:e2e
```

### Test Coverage Requirements

```ini
# .coveragerc
[run]
source = backend
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml

# Coverage thresholds
# fail_under = 80
```

## Summary

The testing strategy ensures:

1. **Comprehensive Coverage**: All layers tested thoroughly
2. **Fast Feedback**: Unit tests run in milliseconds
3. **Confidence**: Integration and E2E tests verify behavior
4. **Documentation**: Tests serve as living documentation
5. **Performance**: Benchmarks prevent regressions
6. **Reliability**: Automated CI/CD catches issues early

This creates a robust testing framework that supports rapid development while maintaining quality.