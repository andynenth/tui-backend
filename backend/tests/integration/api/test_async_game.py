# backend/tests/test_async_game.py
"""
Tests for AsyncGame implementation.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from engine.async_game import AsyncGame
from engine.player import Player
from engine.piece import Piece
from engine.win_conditions import WinConditionType
from engine.state_machine.async_game_adapter import (
    AsyncGameAdapter,
    wrap_game_for_async,
)
from engine.game import Game


class TestAsyncGame:
    """Test suite for AsyncGame."""

    @pytest.fixture
    def mock_players(self):
        """Create mock players for testing."""
        players = []
        for i, name in enumerate(["Alice", "Bob", "Charlie", "David"]):
            player = MagicMock(spec=Player)
            player.name = name
            player.is_bot = i >= 2  # Charlie and David are bots
            player.hand = []
            player.score = 0
            player.declared = 0
            player.captured_piles = 0
            player.zero_declares_in_a_row = 0
            player.reset_for_next_round = MagicMock()
            players.append(player)
        return players

    @pytest.fixture
    async def async_game(self, mock_players):
        """Create an AsyncGame instance for testing."""
        game = AsyncGame(mock_players)
        game.start_time = 1000.0  # Mock start time
        return game

    @pytest.mark.asyncio
    async def test_async_game_initialization(self, mock_players):
        """Test AsyncGame initialization."""
        game = AsyncGame(mock_players)

        assert len(game.players) == 4
        assert game.round_number == 1
        assert game.max_score == 50
        assert game.win_condition_type == WinConditionType.FIRST_TO_REACH_50

        # Check async-specific attributes
        assert hasattr(game, "_game_lock")
        assert hasattr(game, "_deal_lock")
        assert hasattr(game, "_turn_lock")
        assert hasattr(game, "_score_lock")
        assert game._async_operations["deals"] == 0

    @pytest.mark.asyncio
    async def test_deal_pieces_async(self, async_game):
        """Test async deal_pieces method."""
        # Mock the deck
        with patch("engine.piece.Piece.build_deck") as mock_build_deck:
            mock_deck = [MagicMock(spec=Piece, point=i) for i in range(32)]
            for i, piece in enumerate(mock_deck):
                piece.__str__ = MagicMock(return_value=f"Piece{i}")
            mock_build_deck.return_value = mock_deck

            # Deal pieces
            result = await async_game.deal_pieces()

            assert result["success"] == True
            assert "players" in result
            assert len(result["players"]) == 4

            # Check each player got 8 pieces
            for player in async_game.players:
                assert len(player.hand) == 8

            # Check stats
            assert async_game._async_operations["deals"] == 1

    @pytest.mark.asyncio
    async def test_play_turn_async(self, async_game):
        """Test async play_turn method."""
        # Setup game state
        async_game.pile_counts = {p.name: 0 for p in async_game.players}

        # Give players some pieces
        for i, player in enumerate(async_game.players):
            player.hand = [
                MagicMock(spec=Piece, point=5, color="RED"),
                MagicMock(spec=Piece, point=6, color="RED"),
                MagicMock(spec=Piece, point=7, color="RED"),
            ]
            for j, piece in enumerate(player.hand):
                piece.__str__ = MagicMock(return_value=f"R{5+j}")

        # Mock is_valid_play
        with patch("engine.rules.is_valid_play", return_value=True):
            with patch("engine.rules.get_play_type", return_value="triple"):
                # Play turn
                result = await async_game.play_turn("Alice", [0, 1, 2])

                assert result["status"] == "ok"
                assert result["player"] == "Alice"
                assert result["async"] == True
                assert len(result["pieces"]) == 3
                assert async_game._async_operations["turns"] == 1

    @pytest.mark.asyncio
    async def test_calculate_scores_async(self, async_game):
        """Test async calculate_scores method."""
        # Setup game state
        async_game.pile_counts = {"Alice": 3, "Bob": 2, "Charlie": 2, "David": 1}
        async_game.redeal_multiplier = 1.5

        # Set declarations
        for i, player in enumerate(async_game.players):
            player.declared = 2

        # Calculate scores
        scores = await async_game.calculate_scores()

        assert isinstance(scores, dict)
        assert len(scores) == 4
        assert async_game._async_operations["scores"] == 1

        # Check scores were added to players
        for player in async_game.players:
            assert player.score > 0

    @pytest.mark.asyncio
    async def test_start_new_round_async(self, async_game):
        """Test async start_new_round method."""
        # Setup some state to verify reset
        async_game.round_number = 5
        async_game.redeal_multiplier = 2.0
        async_game.turn_number = 10
        async_game.player_declarations = {"Alice": 3, "Bob": 2}

        # Mock deal_pieces
        with patch.object(
            async_game, "deal_pieces", new_callable=AsyncMock
        ) as mock_deal:
            mock_deal.return_value = {"success": True}

            # Start new round
            result = await async_game.start_new_round()

            assert result["success"] == True
            assert result["round_number"] == 6
            assert async_game.round_number == 6
            assert async_game.redeal_multiplier == 1
            assert async_game.turn_number == 0
            assert len(async_game.player_declarations) == 0
            assert async_game._async_operations["rounds"] == 1

            # Check players were reset
            for player in async_game.players:
                player.reset_for_next_round.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_game_over_async(self, async_game):
        """Test async check_game_over method."""
        # Test not game over
        result = await async_game.check_game_over()
        assert result is None

        # Make game over
        async_game.players[0].score = 55
        result = await async_game.check_game_over()

        assert result is not None
        assert result["game_over"] == True
        assert "Alice" in result["winners"]
        assert result["final_scores"]["Alice"] == 55
        assert result["rounds_played"] == 1

    @pytest.mark.asyncio
    async def test_execute_redeal_async(self, async_game):
        """Test async execute_redeal_for_player method."""
        # Setup player with weak hand
        player = async_game.players[0]
        weak_hand = [MagicMock(spec=Piece, point=i) for i in range(1, 9)]
        player.hand = weak_hand

        # Mock deck generation
        with patch("random.shuffle"):
            with patch("engine.piece.Piece.build_deck") as mock_deck:
                new_hand = [MagicMock(spec=Piece, point=i) for i in range(5, 13)]
                for piece in new_hand:
                    piece.__str__ = MagicMock(return_value="TestPiece")
                mock_deck.return_value = new_hand * 4  # Enough for dealing

                # Execute redeal
                result = await async_game.execute_redeal_for_player("Alice")

                assert result["success"] == True
                assert result["player"] == "Alice"
                assert result["async"] == True
                assert async_game.redeal_multiplier == 1.5
                assert len(player.hand) == 8

    @pytest.mark.asyncio
    async def test_record_declaration_async(self, async_game):
        """Test async record_player_declaration method."""
        # Setup player
        player = async_game.players[0]
        player.declared = 0
        player.record_declaration = MagicMock()

        # Mock validation
        with patch("engine.rules.get_valid_declares", return_value=[0, 1, 2, 3]):
            # Record declaration
            result = await async_game.record_player_declaration("Alice", 2)

            assert result["success"] == True
            assert result["player"] == "Alice"
            assert result["declaration"] == 2
            assert result["async"] == True
            player.record_declaration.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, async_game):
        """Test that concurrent operations are properly synchronized."""
        # Mock deck
        with patch("engine.piece.Piece.build_deck") as mock_deck:
            mock_deck.return_value = [MagicMock(spec=Piece) for _ in range(128)]

            # Run multiple deals concurrently
            results = await asyncio.gather(
                async_game.deal_pieces(),
                async_game.deal_pieces(),
                async_game.deal_pieces(),
                return_exceptions=True,
            )

            # All should succeed (locks prevent conflicts)
            for result in results:
                assert not isinstance(result, Exception)
                assert result["success"] == True

            assert async_game._async_operations["deals"] == 3


class TestAsyncGameAdapter:
    """Test suite for AsyncGameAdapter."""

    @pytest.fixture
    def sync_game(self):
        """Create a sync Game instance."""
        players = []
        for name in ["Alice", "Bob", "Charlie", "David"]:
            player = MagicMock(spec=Player)
            player.name = name
            player.hand = []
            player.score = 0
            players.append(player)

        game = Game(players)
        game.deal_pieces = MagicMock()
        game.play_turn = MagicMock(return_value={"status": "ok"})
        game._is_game_over = MagicMock(return_value=False)
        return game

    @pytest.fixture
    async def async_game(self):
        """Create an AsyncGame instance."""
        players = []
        for name in ["Alice", "Bob", "Charlie", "David"]:
            player = MagicMock(spec=Player)
            player.name = name
            player.hand = []
            player.score = 0
            players.append(player)

        return AsyncGame(players)

    @pytest.mark.asyncio
    async def test_adapter_with_sync_game(self, sync_game):
        """Test adapter with sync Game."""
        adapter = AsyncGameAdapter(sync_game)

        assert not adapter.is_async
        assert adapter.players == sync_game.players

        # Test deal_pieces
        result = await adapter.deal_pieces()
        assert result["success"] == True
        assert result["sync"] == True
        sync_game.deal_pieces.assert_called_once()

        # Test play_turn
        turn_result = await adapter.play_turn("Alice", [0, 1, 2])
        assert turn_result["status"] == "ok"
        sync_game.play_turn.assert_called_once_with("Alice", [0, 1, 2])

    @pytest.mark.asyncio
    async def test_adapter_with_async_game(self, async_game):
        """Test adapter with AsyncGame."""
        adapter = AsyncGameAdapter(async_game)

        assert adapter.is_async
        assert adapter.players == async_game.players

        # Mock async methods
        async_game.deal_pieces = AsyncMock(
            return_value={"success": True, "async": True}
        )
        async_game.play_turn = AsyncMock(return_value={"status": "ok", "async": True})

        # Test deal_pieces
        result = await adapter.deal_pieces()
        assert result["success"] == True
        assert result["async"] == True

        # Test play_turn
        turn_result = await adapter.play_turn("Alice", [0, 1, 2])
        assert turn_result["status"] == "ok"
        assert turn_result["async"] == True

    @pytest.mark.asyncio
    async def test_wrap_game_for_async(self, sync_game, async_game):
        """Test wrap_game_for_async utility."""
        # Test with sync game
        sync_adapter = wrap_game_for_async(sync_game)
        assert isinstance(sync_adapter, AsyncGameAdapter)
        assert not sync_adapter.is_async

        # Test with async game
        async_adapter = wrap_game_for_async(async_game)
        assert isinstance(async_adapter, AsyncGameAdapter)
        assert async_adapter.is_async
