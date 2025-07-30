"""
Tests for the unit of work implementation.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.repositories import (
    InMemoryGameRepository,
    InMemoryRoomRepository,
    InMemoryPlayerStatsRepository,
)
from domain.entities import Game, Room, Player
from domain.value_objects import PlayerId, RoomId, GameId


class TestInMemoryUnitOfWork:
    """Test in-memory unit of work implementation."""

    @pytest.fixture
    def uow(self):
        """Create unit of work instance."""
        return InMemoryUnitOfWork()

    @pytest.mark.asyncio
    async def test_context_manager(self, uow):
        """Test unit of work context manager."""
        # Use as context manager
        async with uow:
            # Should have repositories available
            assert uow.games is not None
            assert uow.rooms is not None
            assert uow.player_stats is not None

            # Repositories should be the expected types
            assert isinstance(uow.games, InMemoryGameRepository)
            assert isinstance(uow.rooms, InMemoryRoomRepository)
            assert isinstance(uow.player_stats, InMemoryPlayerStatsRepository)

    @pytest.mark.asyncio
    async def test_commit_success(self, uow):
        """Test successful commit."""
        async with uow:
            # Add some data
            room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
            await uow.rooms.add(room)

            # Commit should succeed
            await uow.commit()

            # Data should be persisted
            retrieved = await uow.rooms.get_by_id(RoomId("room1"))
            assert retrieved is not None
            assert retrieved.room_code == "ABCD"

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self, uow):
        """Test automatic rollback on exception."""
        # Add data before context
        async with uow:
            room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
            await uow.rooms.add(room)
            await uow.commit()

        # Now test rollback
        try:
            async with uow:
                # Modify data
                room = await uow.rooms.get_by_id(RoomId("room1"))
                room.name = "Modified Room"
                await uow.rooms.update(room)

                # Raise exception before commit
                raise ValueError("Test exception")

        except ValueError:
            pass

        # Check that changes were rolled back
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert room.name == "Test Room"  # Original name

    @pytest.mark.asyncio
    async def test_explicit_rollback(self, uow):
        """Test explicit rollback."""
        # Add initial data
        async with uow:
            room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
            await uow.rooms.add(room)
            await uow.commit()

        # Make changes and rollback
        async with uow:
            # Modify data
            room = await uow.rooms.get_by_id(RoomId("room1"))
            room.name = "Modified Room"
            await uow.rooms.update(room)

            # Explicit rollback
            await uow.rollback()

            # Changes should be reverted even within same context
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert room.name == "Test Room"

    @pytest.mark.asyncio
    async def test_nested_transactions_not_supported(self, uow):
        """Test that nested transactions raise error."""
        async with uow:
            # Try to enter again
            with pytest.raises(RuntimeError, match="Transaction already in progress"):
                async with uow:
                    pass

    @pytest.mark.asyncio
    async def test_repository_isolation(self, uow):
        """Test that repositories are isolated between transactions."""
        # First transaction
        async with uow:
            room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
            await uow.rooms.add(room)
            await uow.commit()

        # Second transaction with modifications
        async with uow:
            # Should see committed data
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert room is not None

            # Add another room
            room2 = Room(room_id=RoomId("room2"), room_code="EFGH", name="Room 2")
            await uow.rooms.add(room2)

            # Don't commit

        # Third transaction should not see uncommitted changes
        async with uow:
            room1 = await uow.rooms.get_by_id(RoomId("room1"))
            assert room1 is not None  # Committed data visible

            room2 = await uow.rooms.get_by_id(RoomId("room2"))
            assert room2 is None  # Uncommitted data not visible

    @pytest.mark.asyncio
    async def test_snapshot_restore_mechanism(self, uow):
        """Test the snapshot/restore mechanism."""
        # Setup initial state
        async with uow:
            # Add room
            room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
            await uow.rooms.add(room)

            # Add game
            game = Game(game_id=GameId("game1"), room_id=RoomId("room1"))
            await uow.games.add(game)

            await uow.commit()

        # Test snapshot/restore
        async with uow:
            # Take snapshot (happens automatically on enter)

            # Modify data
            room = await uow.rooms.get_by_id(RoomId("room1"))
            room.name = "Modified"
            await uow.rooms.update(room)

            # Delete game
            await uow.games.delete(GameId("game1"))

            # Add new room
            new_room = Room(room_id=RoomId("room2"), room_code="WXYZ", name="New Room")
            await uow.rooms.add(new_room)

            # Rollback
            await uow.rollback()

            # Check original state restored
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert room.name == "Test Room"

            game = await uow.games.get_by_id(GameId("game1"))
            assert game is not None

            new_room = await uow.rooms.get_by_id(RoomId("room2"))
            assert new_room is None

    @pytest.mark.asyncio
    async def test_concurrent_modifications(self, uow):
        """Test handling of concurrent modifications."""
        # This is a simplified test - real implementation would need proper locking

        # Setup initial data
        async with uow:
            room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
            room.add_player(Player(player_id=PlayerId("p1"), name="Player 1"))
            await uow.rooms.add(room)
            await uow.commit()

        # Simulate concurrent modifications
        # Transaction 1 - Add player
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("room1"))
            room.add_player(Player(player_id=PlayerId("p2"), name="Player 2"))
            await uow.rooms.update(room)
            await uow.commit()

        # Transaction 2 - Add different player
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("room1"))
            # Should see changes from transaction 1
            assert len(room.players) == 2

            room.add_player(Player(player_id=PlayerId("p3"), name="Player 3"))
            await uow.rooms.update(room)
            await uow.commit()

        # Verify final state
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert len(room.players) == 3


class TestInMemoryRepositories:
    """Test in-memory repository implementations."""

    @pytest.fixture
    def storage(self):
        """Create shared storage."""
        return {"rooms": {}, "games": {}, "player_stats": {}}

    @pytest.mark.asyncio
    async def test_room_repository_operations(self, storage):
        """Test room repository CRUD operations."""
        repo = InMemoryRoomRepository(storage["rooms"])

        # Add room
        room = Room(room_id=RoomId("room1"), room_code="ABCD", name="Test Room")
        await repo.add(room)

        # Get by ID
        retrieved = await repo.get_by_id(RoomId("room1"))
        assert retrieved is not None
        assert retrieved.room_code == "ABCD"

        # Get by code
        retrieved = await repo.get_by_code("ABCD")
        assert retrieved is not None
        assert retrieved.room_id == RoomId("room1")

        # Update
        retrieved.name = "Updated Room"
        await repo.update(retrieved)

        updated = await repo.get_by_id(RoomId("room1"))
        assert updated.name == "Updated Room"

        # List all
        all_rooms = await repo.list_all()
        assert len(all_rooms) == 1

        # Delete
        await repo.delete(RoomId("room1"))
        deleted = await repo.get_by_id(RoomId("room1"))
        assert deleted is None

    @pytest.mark.asyncio
    async def test_game_repository_operations(self, storage):
        """Test game repository operations."""
        repo = InMemoryGameRepository(storage["games"])

        # Add game
        game = Game(game_id=GameId("game1"), room_id=RoomId("room1"))
        await repo.add(game)

        # Get by ID
        retrieved = await repo.get_by_id(GameId("game1"))
        assert retrieved is not None
        assert retrieved.room_id == RoomId("room1")

        # Get by room
        room_games = await repo.get_by_room(RoomId("room1"))
        assert len(room_games) == 1
        assert room_games[0].game_id == GameId("game1")

        # Get active by room
        active = await repo.get_active_by_room(RoomId("room1"))
        assert active is not None

        # Complete the game
        game.end_game()
        await repo.update(game)

        # No active game now
        active = await repo.get_active_by_room(RoomId("room1"))
        assert active is None

    @pytest.mark.asyncio
    async def test_repository_snapshot_restore(self, storage):
        """Test repository snapshot/restore functionality."""
        repo = InMemoryRoomRepository(storage["rooms"])

        # Add initial data
        room1 = Room(room_id=RoomId("r1"), room_code="ABC1", name="Room 1")
        room2 = Room(room_id=RoomId("r2"), room_code="ABC2", name="Room 2")
        await repo.add(room1)
        await repo.add(room2)

        # Take snapshot
        snapshot = repo.snapshot()

        # Modify data
        await repo.delete(RoomId("r1"))
        room2.name = "Modified Room 2"
        await repo.update(room2)
        room3 = Room(room_id=RoomId("r3"), room_code="ABC3", name="Room 3")
        await repo.add(room3)

        # Verify modifications
        assert await repo.get_by_id(RoomId("r1")) is None
        assert (await repo.get_by_id(RoomId("r2"))).name == "Modified Room 2"
        assert await repo.get_by_id(RoomId("r3")) is not None

        # Restore snapshot
        repo.restore(snapshot)

        # Verify original state
        assert await repo.get_by_id(RoomId("r1")) is not None
        assert (await repo.get_by_id(RoomId("r2"))).name == "Room 2"
        assert await repo.get_by_id(RoomId("r3")) is None
