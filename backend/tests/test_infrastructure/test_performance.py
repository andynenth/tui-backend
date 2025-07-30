"""
Performance tests for clean architecture implementation.

These tests ensure the clean architecture doesn't introduce
unacceptable performance overhead.
"""

import pytest
import time
import asyncio
from statistics import mean, stdev
from typing import List
import gc

from domain.entities import Room, Player
from domain.value_objects import RoomId, PlayerId

from application.use_cases.room_management.create_room import CreateRoomUseCase
from application.use_cases.room_management.join_room import JoinRoomUseCase
from application.dto.room_management import CreateRoomRequest, JoinRoomRequest

from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.events.application_event_publisher import InMemoryEventPublisher
from infrastructure.repositories import InMemoryRoomRepository


class TestPerformance:
    """Performance tests for clean architecture components."""

    @pytest.fixture
    def setup(self):
        """Set up test components."""
        return {
            "uow": InMemoryUnitOfWork(),
            "publisher": InMemoryEventPublisher(),
            "metrics": None,
        }

    @pytest.mark.asyncio
    async def test_repository_performance(self):
        """Test repository operation performance."""
        storage = {}
        repo = InMemoryRoomRepository(storage)

        # Measure add performance
        add_times = []
        for i in range(1000):
            room = Room(
                room_id=RoomId(f"room_{i}"), room_code=f"CODE{i:04d}", name=f"Room {i}"
            )

            start = time.perf_counter()
            await repo.add(room)
            end = time.perf_counter()

            add_times.append((end - start) * 1000)  # Convert to ms

        avg_add_time = mean(add_times)
        assert avg_add_time < 0.1  # Should be less than 0.1ms per add

        # Measure get performance
        get_times = []
        for i in range(1000):
            start = time.perf_counter()
            room = await repo.get_by_id(RoomId(f"room_{i}"))
            end = time.perf_counter()

            get_times.append((end - start) * 1000)
            assert room is not None

        avg_get_time = mean(get_times)
        assert avg_get_time < 0.05  # Should be less than 0.05ms per get

        print(f"\nRepository Performance:")
        print(f"  Add: {avg_add_time:.3f}ms avg (std: {stdev(add_times):.3f}ms)")
        print(f"  Get: {avg_get_time:.3f}ms avg (std: {stdev(get_times):.3f}ms)")

    @pytest.mark.asyncio
    async def test_unit_of_work_performance(self):
        """Test unit of work transaction performance."""
        uow = InMemoryUnitOfWork()

        # Measure transaction overhead
        transaction_times = []

        for i in range(100):
            start = time.perf_counter()

            async with uow:
                room = Room(
                    room_id=RoomId(f"perf_{i}"),
                    room_code=f"PERF{i:04d}",
                    name=f"Performance Test {i}",
                )
                await uow.rooms.add(room)
                await uow.commit()

            end = time.perf_counter()
            transaction_times.append((end - start) * 1000)

        avg_transaction_time = mean(transaction_times)
        assert avg_transaction_time < 1.0  # Should be less than 1ms per transaction

        print(f"\nUoW Performance:")
        print(f"  Transaction: {avg_transaction_time:.3f}ms avg")

    @pytest.mark.asyncio
    async def test_use_case_performance(self, setup):
        """Test use case execution performance."""
        uow = setup["uow"]
        publisher = setup["publisher"]

        # Create room use case performance
        create_use_case = CreateRoomUseCase(uow, publisher)
        create_times = []

        for i in range(100):
            request = CreateRoomRequest(
                host_player_id=f"host_{i}",
                host_player_name=f"Host {i}",
                room_name=f"Room {i}",
            )

            start = time.perf_counter()
            response = await create_use_case.execute(request)
            end = time.perf_counter()

            create_times.append((end - start) * 1000)
            assert response.success is True

        avg_create_time = mean(create_times)
        assert avg_create_time < 2.0  # Should be less than 2ms per create

        # Join room use case performance
        join_use_case = JoinRoomUseCase(uow, publisher, None)
        join_times = []

        # Get a room code
        async with uow:
            rooms = await uow.rooms.list_all()
            room_code = rooms[0].room_code

        for i in range(100):
            request = JoinRoomRequest(
                player_id=f"player_{i}", player_name=f"Player {i}", room_code=room_code
            )

            start = time.perf_counter()
            response = await join_use_case.execute(request)
            end = time.perf_counter()

            if i < 3:  # First 3 should succeed (room has 4 max)
                join_times.append((end - start) * 1000)

        avg_join_time = mean(join_times)
        assert avg_join_time < 2.0  # Should be less than 2ms per join

        print(f"\nUse Case Performance:")
        print(f"  Create Room: {avg_create_time:.3f}ms avg")
        print(f"  Join Room: {avg_join_time:.3f}ms avg")

    @pytest.mark.asyncio
    async def test_event_publishing_performance(self):
        """Test event publishing performance."""
        publisher = InMemoryEventPublisher()

        # Create test events
        from domain.events.room_events import RoomCreated
        from datetime import datetime

        publish_times = []

        for i in range(1000):
            event = RoomCreated(
                room_id=f"room_{i}",
                room_code=f"CODE{i}",
                host_id=f"host_{i}",
                timestamp=datetime.utcnow(),
            )

            start = time.perf_counter()
            await publisher.publish(event)
            end = time.perf_counter()

            publish_times.append((end - start) * 1000)

        avg_publish_time = mean(publish_times)
        assert avg_publish_time < 0.1  # Should be less than 0.1ms per publish

        # Test batch publishing
        events = [
            RoomCreated(
                room_id=f"batch_{i}",
                room_code=f"BTCH{i}",
                host_id=f"host_{i}",
                timestamp=datetime.utcnow(),
            )
            for i in range(100)
        ]

        start = time.perf_counter()
        await publisher.publish_batch(events)
        end = time.perf_counter()

        batch_time = (end - start) * 1000
        assert batch_time < 10  # Should be less than 10ms for 100 events

        print(f"\nEvent Publishing Performance:")
        print(f"  Single: {avg_publish_time:.3f}ms avg")
        print(f"  Batch (100): {batch_time:.3f}ms total")

    @pytest.mark.asyncio
    async def test_memory_usage(self, setup):
        """Test memory usage of clean architecture components."""
        uow = setup["uow"]
        publisher = setup["publisher"]

        # Force garbage collection
        gc.collect()

        # Create many rooms and track memory
        create_use_case = CreateRoomUseCase(uow, publisher)

        initial_objects = len(gc.get_objects())

        # Create 1000 rooms
        for i in range(1000):
            request = CreateRoomRequest(
                host_player_id=f"host_{i}",
                host_player_name=f"Host {i}",
                room_name=f"Room {i}",
            )
            await create_use_case.execute(request)

        # Force garbage collection
        gc.collect()

        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects

        # Should not leak excessive objects
        # Rough estimate: ~10-20 objects per room is reasonable
        assert object_increase < 20000  # Less than 20 objects per room

        print(f"\nMemory Usage:")
        print(
            f"  Objects created: {object_increase} ({object_increase/1000:.1f} per room)"
        )

    @pytest.mark.asyncio
    async def test_concurrent_performance(self, setup):
        """Test performance under concurrent load."""
        uow = setup["uow"]
        publisher = setup["publisher"]

        # Create a room first
        create_use_case = CreateRoomUseCase(uow, publisher)
        response = await create_use_case.execute(
            CreateRoomRequest(
                host_player_id="host",
                host_player_name="Host",
                room_name="Concurrent Test",
            )
        )
        room_code = response.room_code

        # Simulate concurrent joins
        join_use_case = JoinRoomUseCase(uow, publisher, None)

        async def join_player(player_id: str):
            start = time.perf_counter()
            await join_use_case.execute(
                JoinRoomRequest(
                    player_id=player_id,
                    player_name=f"Player {player_id}",
                    room_code=room_code,
                )
            )
            end = time.perf_counter()
            return (end - start) * 1000

        # Run 10 concurrent joins
        start_concurrent = time.perf_counter()
        tasks = [join_player(f"p{i}") for i in range(10)]
        times = await asyncio.gather(*tasks, return_exceptions=True)
        end_concurrent = time.perf_counter()

        # Filter out failures (room full)
        valid_times = [t for t in times if isinstance(t, float)]

        total_concurrent_time = (end_concurrent - start_concurrent) * 1000
        avg_concurrent_time = mean(valid_times) if valid_times else 0

        print(f"\nConcurrent Performance:")
        print(f"  10 concurrent joins: {total_concurrent_time:.3f}ms total")
        print(f"  Average per join: {avg_concurrent_time:.3f}ms")

        # Concurrent operations should complete reasonably fast
        assert total_concurrent_time < 50  # Less than 50ms for 10 concurrent ops
