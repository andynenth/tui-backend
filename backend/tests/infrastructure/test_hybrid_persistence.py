"""
Tests for hybrid persistence strategy.

Validates archival behavior, performance, and data integrity.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path


from infrastructure.persistence.archive import (
    ArchivalPolicy,
    ArchivalRequest,
    ArchivalTrigger,
    ArchivalPriority,
    GameArchivalStrategy,
    FileSystemArchiveBackend,
    ArchivalWorker,
    ArchiveManager,
    ArchiveQuery,
)
from infrastructure.persistence.hybrid_game_repository import HybridGameRepository
from domain.entities import Game, Player, Round


class TestArchivalStrategy:
    """Test archival strategies."""

    @pytest.mark.asyncio
    async def test_game_archival_strategy(self, tmp_path):
        """Test game-specific archival strategy."""
        # Setup
        backend = FileSystemArchiveBackend(base_path=str(tmp_path))
        strategy = GameArchivalStrategy(backend)

        # Create test game
        game = Game(id="game-123", room_id="room-456")
        game.status = "completed"
        game.created_at = datetime.utcnow() - timedelta(hours=2)
        game.completed_at = datetime.utcnow()

        player1 = Player(id="p1", name="Alice", is_bot=False)
        player2 = Player(id="p2", name="Bob", is_bot=True)
        game.players.extend([player1, player2])

        # Create archival request
        request = ArchivalRequest(
            entity_id=game.id,
            entity_type="game",
            entity=game,
            trigger=ArchivalTrigger.GAME_COMPLETED,
        )

        policy = ArchivalPolicy(
            name="test",
            entity_type="game",
            compress_after=timedelta(0),  # Immediate compression
        )

        # Archive game
        result = await strategy.archive_entity(request, policy)

        # Verify success
        assert result.success
        assert result.compressed
        assert result.archive_location
        assert result.size_bytes > 0

        # Verify file exists
        archive_path = tmp_path / result.archive_location
        assert archive_path.exists()

        # Retrieve game
        restored = await strategy.retrieve_entity(game.id, result.archive_location)

        # Verify restoration
        assert restored.id == game.id
        assert restored.room_id == game.room_id
        assert restored.status == game.status
        assert len(restored.players) == 2

    @pytest.mark.asyncio
    async def test_archival_policy_triggers(self):
        """Test different archival triggers."""
        policy = ArchivalPolicy(
            name="test",
            entity_type="game",
            triggers={ArchivalTrigger.GAME_COMPLETED, ArchivalTrigger.TIME_BASED},
            archive_after=timedelta(hours=1),
        )

        current_time = datetime.utcnow()

        # Test completed game - should archive
        completed_game = Game(id="g1", room_id="r1")
        completed_game.status = "completed"
        completed_game.created_at = current_time
        assert policy.should_archive(completed_game, current_time)

        # Test old game - should archive
        old_game = Game(id="g2", room_id="r2")
        old_game.status = "active"
        old_game.created_at = current_time - timedelta(hours=2)
        assert policy.should_archive(old_game, current_time)

        # Test recent active game - should not archive
        active_game = Game(id="g3", room_id="r3")
        active_game.status = "active"
        active_game.created_at = current_time - timedelta(minutes=30)
        assert not policy.should_archive(active_game, current_time)


class TestArchivalWorker:
    """Test background archival worker."""

    @pytest.mark.asyncio
    async def test_worker_batch_processing(self, tmp_path):
        """Test worker processes requests in batches."""
        # Setup
        backend = FileSystemArchiveBackend(base_path=str(tmp_path))
        strategy = GameArchivalStrategy(backend)

        policy = ArchivalPolicy(
            name="test", entity_type="game", batch_size=3, max_concurrent_archives=2
        )

        worker = ArchivalWorker(
            strategy=strategy,
            policies={"game": policy},
            batch_timeout=timedelta(seconds=0.5),
        )

        await worker.start()

        try:
            # Submit multiple requests
            games = []
            for i in range(5):
                game = Game(id=f"game-{i}", room_id=f"room-{i}")
                game.status = "completed"
                game.created_at = datetime.utcnow()
                games.append(game)

                request = ArchivalRequest(
                    entity_id=game.id,
                    entity_type="game",
                    entity=game,
                    trigger=ArchivalTrigger.GAME_COMPLETED,
                )

                success = await worker.submit(request)
                assert success

            # Wait for processing
            await asyncio.sleep(1)

            # Check metrics
            metrics = worker.metrics
            assert metrics.total_processed == 5
            assert metrics.total_succeeded == 5
            assert metrics.total_batches >= 2  # Should process in batches

            # Verify all games archived
            for game in games:
                archives = await backend.list_archives("game")
                assert any(game.id in archive for archive in archives)

        finally:
            await worker.stop()

    @pytest.mark.asyncio
    async def test_worker_priority_processing(self, tmp_path):
        """Test worker processes by priority."""
        # Setup
        backend = FileSystemArchiveBackend(base_path=str(tmp_path))
        strategy = GameArchivalStrategy(backend)

        worker = ArchivalWorker(
            strategy=strategy,
            policies={"game": ArchivalPolicy(name="test", entity_type="game")},
        )

        await worker.start()

        try:
            # Submit requests with different priorities
            priorities = [
                ArchivalPriority.LOW,
                ArchivalPriority.CRITICAL,
                ArchivalPriority.NORMAL,
                ArchivalPriority.HIGH,
            ]

            for i, priority in enumerate(priorities):
                game = Game(id=f"game-{i}", room_id=f"room-{i}")
                game.status = "completed"

                request = ArchivalRequest(
                    entity_id=game.id,
                    entity_type="game",
                    entity=game,
                    trigger=ArchivalTrigger.MANUAL,
                    priority=priority,
                )

                await worker.submit(request)

            # Wait for processing
            await asyncio.sleep(0.5)

            # Check priority distribution
            metrics = worker.metrics
            assert metrics.by_priority[ArchivalPriority.CRITICAL.name] > 0

        finally:
            await worker.stop()

    @pytest.mark.asyncio
    async def test_worker_retry_mechanism(self, tmp_path):
        """Test worker retries failed archives."""

        # Create a flaky backend
        class FlakyBackend:
            def __init__(self):
                self.attempts = {}
                self.real_backend = FileSystemArchiveBackend(base_path=str(tmp_path))

            async def archive(
                self, entity_id: str, entity_type: str, data: bytes
            ) -> str:
                # Fail first attempt
                self.attempts[entity_id] = self.attempts.get(entity_id, 0) + 1
                if self.attempts[entity_id] == 1:
                    raise Exception("Simulated failure")
                return await self.real_backend.archive(entity_id, entity_type, data)

            async def retrieve(self, location: str) -> bytes:
                return await self.real_backend.retrieve(location)

            async def delete(self, location: str) -> bool:
                return await self.real_backend.delete(location)

            async def list_archives(self, entity_type: str, **kwargs):
                return await self.real_backend.list_archives(entity_type, **kwargs)

        backend = FlakyBackend()
        strategy = GameArchivalStrategy(backend)

        worker = ArchivalWorker(
            strategy=strategy,
            policies={"game": ArchivalPolicy(name="test", entity_type="game")},
            max_retries=3,
            retry_delay=timedelta(seconds=0.1),
        )

        await worker.start()

        try:
            # Submit request
            game = Game(id="retry-game", room_id="room")
            game.status = "completed"

            request = ArchivalRequest(
                entity_id=game.id,
                entity_type="game",
                entity=game,
                trigger=ArchivalTrigger.MANUAL,
            )

            await worker.submit(request)

            # Wait for retry
            await asyncio.sleep(1)

            # Should succeed after retry
            archives = await backend.real_backend.list_archives("game")
            assert any("retry-game" in archive for archive in archives)

            # Check retry happened
            assert backend.attempts["retry-game"] > 1

        finally:
            await worker.stop()


class TestHybridGameRepository:
    """Test hybrid game repository."""

    @pytest.mark.asyncio
    async def test_active_game_performance(self):
        """Test active games maintain memory performance."""
        repo = HybridGameRepository(max_active_games=100, archive_on_completion=True)

        await repo.initialize()

        try:
            # Create active game
            game = Game(id="active-1", room_id="room-1")
            game.status = "active"
            game.created_at = datetime.utcnow()

            # Save game
            start = asyncio.get_event_loop().time()
            await repo.save(game)
            save_time = asyncio.get_event_loop().time() - start

            # Retrieve game
            start = asyncio.get_event_loop().time()
            retrieved = await repo.get_by_id("active-1")
            get_time = asyncio.get_event_loop().time() - start

            # Verify performance
            assert save_time < 0.001  # <1ms
            assert get_time < 0.001  # <1ms
            assert retrieved.id == game.id

            # Verify in active storage
            stats = repo.get_stats()
            assert stats["active_games"] == 1
            assert stats["completed_games"] == 0

        finally:
            await repo.shutdown()

    @pytest.mark.asyncio
    async def test_automatic_archival_on_completion(self, tmp_path):
        """Test games are archived when completed."""
        # Use temp directory for archives
        repo = HybridGameRepository(archive_on_completion=True, enable_compression=True)

        # Override archive backend
        repo._archive_backend = FileSystemArchiveBackend(base_path=str(tmp_path))

        await repo.initialize()

        try:
            # Create and save active game
            game = Game(id="game-to-complete", room_id="room-1")
            game.status = "active"
            await repo.save(game)

            # Complete the game
            game.status = "completed"
            game.completed_at = datetime.utcnow()
            await repo.save(game)

            # Wait for archival
            await asyncio.sleep(1)

            # Game should still be retrievable
            retrieved = await repo.get_by_id("game-to-complete")
            assert retrieved is not None
            assert retrieved.status == "completed"

            # Check if archived
            archives = await repo._archive_backend.list_archives("game")
            assert len(archives) > 0

        finally:
            await repo.shutdown()

    @pytest.mark.asyncio
    async def test_transparent_archive_retrieval(self, tmp_path):
        """Test transparent retrieval from archive."""
        repo = HybridGameRepository()
        repo._archive_backend = FileSystemArchiveBackend(base_path=str(tmp_path))

        await repo.initialize()

        try:
            # Create completed game
            game = Game(id="archived-game", room_id="room-1")
            game.status = "completed"
            game.completed_at = datetime.utcnow() - timedelta(hours=2)

            # Save and trigger archival
            await repo.save(game)
            await repo._archive_manager.archive_entity(
                entity_id=game.id,
                entity_type="game",
                trigger=ArchivalTrigger.GAME_COMPLETED,
            )

            # Remove from active storage
            await repo.delete(game.id)

            # Should still be retrievable from archive
            retrieved = await repo.get_by_id("archived-game")
            assert retrieved is not None
            assert retrieved.id == game.id
            assert retrieved.status == "completed"

        finally:
            await repo.shutdown()

    @pytest.mark.asyncio
    async def test_capacity_management(self):
        """Test repository manages capacity with archival."""
        repo = HybridGameRepository(max_active_games=5, archive_on_completion=True)

        await repo.initialize()

        try:
            # Fill repository with games
            for i in range(8):
                game = Game(id=f"game-{i}", room_id=f"room-{i}")

                # Make first 3 completed
                if i < 3:
                    game.status = "completed"
                    game.completed_at = datetime.utcnow() - timedelta(hours=1)
                else:
                    game.status = "active"

                await repo.save(game)

            # Wait for cleanup
            await asyncio.sleep(1)

            # Check capacity maintained
            stats = repo.get_stats()
            assert stats["active_games"] <= 5

            # Completed games should be archived
            active_games = await repo.list_active_games()
            completed_count = sum(1 for g in active_games if g.status == "completed")
            assert completed_count < 3  # Some should be archived

        finally:
            await repo.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_access_safety(self):
        """Test repository handles concurrent access safely."""
        repo = HybridGameRepository()
        await repo.initialize()

        try:
            game = Game(id="concurrent-game", room_id="room-1")
            await repo.save(game)

            # Concurrent reads and writes
            async def read_game():
                for _ in range(10):
                    await repo.get_by_id("concurrent-game")
                    await asyncio.sleep(0.001)

            async def update_game():
                for i in range(10):
                    game.current_round = i
                    await repo.save(game)
                    await asyncio.sleep(0.001)

            # Run concurrently
            await asyncio.gather(read_game(), read_game(), update_game(), update_game())

            # Verify final state
            final = await repo.get_by_id("concurrent-game")
            assert final is not None

        finally:
            await repo.shutdown()


class TestArchiveManager:
    """Test archive manager coordination."""

    @pytest.mark.asyncio
    async def test_archive_lifecycle_management(self, tmp_path):
        """Test complete archive lifecycle."""

        # Mock entity provider
        class MockProvider:
            def __init__(self):
                self.entities = {}

            async def get_entity(self, entity_id: str, entity_type: str):
                return self.entities.get(entity_id)

            async def list_entities(self, entity_type: str, filter_func=None):
                entities = [
                    e
                    for e in self.entities.values()
                    if getattr(e, "_type", None) == entity_type
                ]
                if filter_func:
                    entities = [e for e in entities if filter_func(e)]
                return entities

            async def delete_entity(self, entity_id: str, entity_type: str):
                if entity_id in self.entities:
                    del self.entities[entity_id]
                    return True
                return False

        provider = MockProvider()
        backend = FileSystemArchiveBackend(base_path=str(tmp_path))

        manager = ArchiveManager(
            entity_provider=provider, backend=backend, enable_worker=True
        )

        await manager.start()

        try:
            # Add test game
            game = Game(id="lifecycle-game", room_id="room-1")
            game.status = "completed"
            game.created_at = datetime.utcnow() - timedelta(days=2)
            game._type = "game"
            provider.entities[game.id] = game

            # Archive the game
            success = await manager.archive_entity(
                entity_id=game.id,
                entity_type="game",
                trigger=ArchivalTrigger.GAME_COMPLETED,
            )
            assert success

            # Wait for archival
            await asyncio.sleep(1)

            # Query archives
            query = ArchiveQuery(entity_type="game")
            results = await manager.query_archives(query)
            assert len(results) > 0

            # Get stats
            stats = await manager.get_stats()
            assert stats.total_entities["game"] > 0

            # Cleanup old archives (with short retention for test)
            policy = manager.policies["game"]
            policy.retention_period = timedelta(seconds=0)  # Immediate deletion

            deleted = await manager.cleanup_old_archives()
            assert deleted > 0

        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_archive_compression_optimization(self, tmp_path):
        """Test archive compression reduces storage."""
        backend = FileSystemArchiveBackend(
            base_path=str(tmp_path), use_compression=True
        )
        strategy = GameArchivalStrategy(backend)

        # Create large game with many rounds
        game = Game(id="large-game", room_id="room-1")
        game.status = "completed"

        # Add many rounds to increase size
        for i in range(100):
            round_obj = Round(number=i)
            game.rounds.append(round_obj)

        # Archive without compression
        policy_no_compress = ArchivalPolicy(
            name="no-compress", entity_type="game", compress_after=None
        )

        request = ArchivalRequest(
            entity_id=game.id,
            entity_type="game",
            entity=game,
            trigger=ArchivalTrigger.MANUAL,
        )

        result_no_compress = await strategy.archive_entity(request, policy_no_compress)

        # Archive with compression
        policy_compress = ArchivalPolicy(
            name="compress", entity_type="game", compress_after=timedelta(0)
        )

        request.entity_id = "large-game-compressed"
        result_compress = await strategy.archive_entity(request, policy_compress)

        # Compare sizes
        assert result_compress.compressed
        assert not result_no_compress.compressed
        assert result_compress.size_bytes < result_no_compress.size_bytes

        # Verify compression ratio
        compression_ratio = 1 - (
            result_compress.size_bytes / result_no_compress.size_bytes
        )
        assert compression_ratio > 0.3  # At least 30% reduction


@pytest.fixture
def cleanup_archives():
    """Cleanup test archives after tests."""
    temp_dirs = []

    def track_dir(path):
        temp_dirs.append(path)
        return path

    yield track_dir

    # Cleanup
    for temp_dir in temp_dirs:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
