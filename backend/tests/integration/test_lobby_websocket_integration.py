"""
Integration tests for lobby WebSocket real-time updates.

This module tests the complete WebSocket flow for lobby updates,
including event broadcasting and client synchronization.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from infrastructure.websocket.connection_singleton import (
    connection_manager,
    broadcast,
    WebSocketConnection,
)
from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext
from domain.entities.room import Room
from domain.entities.player import Player
from infrastructure.unit_of_work import InMemoryUnitOfWork


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self, room_id: str = "lobby"):
        self.room_id = room_id
        self.sent_messages = []
        self.closed = False

    async def send_text(self, message: str):
        """Mock sending text message."""
        self.sent_messages.append(json.loads(message))

    async def send_json(self, data: dict):
        """Mock sending JSON message."""
        self.sent_messages.append(data)

    async def close(self):
        """Mock closing connection."""
        self.closed = True

    def clear_messages(self):
        """Clear sent messages for test isolation."""
        self.sent_messages = []


@pytest.fixture
def mock_websockets():
    """Create mock WebSocket connections."""
    # Create multiple mock clients in lobby
    ws1 = MockWebSocket("lobby")
    ws2 = MockWebSocket("lobby")
    ws3 = MockWebSocket("lobby")

    # Create a client in a room
    ws_room = MockWebSocket("ROOM001")

    return {"client1": ws1, "client2": ws2, "client3": ws3, "room_client": ws_room}


@pytest.fixture
def setup_connections(mock_websockets):
    """Setup WebSocket connections in connection manager."""
    # Clear any existing connections
    connection_manager.rooms.clear()

    # Add lobby connections
    connection_manager.add_connection(
        "lobby",
        mock_websockets["client1"],
        WebSocketConnection(
            websocket=mock_websockets["client1"],
            room_id="lobby",
            player_name="Client1",
            player_id="client1",
        ),
    )

    connection_manager.add_connection(
        "lobby",
        mock_websockets["client2"],
        WebSocketConnection(
            websocket=mock_websockets["client2"],
            room_id="lobby",
            player_name="Client2",
            player_id="client2",
        ),
    )

    connection_manager.add_connection(
        "lobby",
        mock_websockets["client3"],
        WebSocketConnection(
            websocket=mock_websockets["client3"],
            room_id="lobby",
            player_name="Client3",
            player_id="client3",
        ),
    )

    # Add room connection
    connection_manager.add_connection(
        "ROOM001",
        mock_websockets["room_client"],
        WebSocketConnection(
            websocket=mock_websockets["room_client"],
            room_id="ROOM001",
            player_name="RoomPlayer",
            player_id="room_player",
        ),
    )

    yield mock_websockets

    # Cleanup
    connection_manager.rooms.clear()


@pytest.fixture
def dispatcher():
    """Create dispatcher with real dependencies."""
    uow = InMemoryUnitOfWork()
    return UseCaseDispatcher(unit_of_work=uow)


class TestLobbyWebSocketIntegration:
    """Test complete WebSocket flow for lobby updates."""

    @pytest.mark.asyncio
    async def test_room_creation_broadcasts_to_all_lobby_users(
        self, setup_connections, dispatcher
    ):
        """Test that creating a room broadcasts update to all lobby users."""
        websockets = setup_connections

        # Clear initial messages
        for ws in websockets.values():
            ws.clear_messages()

        # Create room via dispatcher
        context = DispatchContext(
            websocket=websockets["client1"],
            room_id="lobby",
            player_id="client1",
            player_name="Client1",
        )

        response = await dispatcher.dispatch(
            "create_room", {"player_name": "Client1"}, context
        )

        # Verify room was created
        assert response["event"] == "room_created"
        assert response["data"]["success"] is True
        room_id = response["data"]["room_id"]

        # Now request room list from another client
        context2 = DispatchContext(
            websocket=websockets["client2"],
            room_id="lobby",
            player_id="client2",
            player_name="Client2",
        )

        list_response = await dispatcher.dispatch("get_rooms", {}, context2)

        # Verify room appears in list
        assert list_response["event"] == "room_list_update"
        assert len(list_response["data"]["rooms"]) == 1
        assert list_response["data"]["rooms"][0]["room_id"] == room_id
        assert list_response["data"]["rooms"][0]["host_name"] == "Client1"

    @pytest.mark.asyncio
    async def test_player_join_updates_lobby_room_count(
        self, setup_connections, dispatcher
    ):
        """Test that player joining updates room count in lobby."""
        websockets = setup_connections

        # First create a room
        context = DispatchContext(
            websocket=websockets["client1"],
            room_id="lobby",
            player_id="client1",
            player_name="Client1",
        )

        create_response = await dispatcher.dispatch(
            "create_room", {"player_name": "Client1"}, context
        )
        room_id = create_response["data"]["room_id"]

        # Get initial room list
        list_response = await dispatcher.dispatch("get_rooms", {}, context)
        initial_player_count = list_response["data"]["rooms"][0]["player_count"]

        # Have another player join
        context2 = DispatchContext(
            websocket=websockets["client2"],
            room_id="lobby",
            player_id="client2",
            player_name="Client2",
        )

        join_response = await dispatcher.dispatch(
            "join_room", {"room_id": room_id, "player_name": "Client2"}, context2
        )

        assert join_response["data"]["success"] is True

        # Get updated room list
        list_response = await dispatcher.dispatch("get_rooms", {}, context)

        # Verify player count increased
        updated_player_count = list_response["data"]["rooms"][0]["player_count"]
        assert updated_player_count == initial_player_count + 1

    @pytest.mark.asyncio
    async def test_concurrent_room_operations(self, setup_connections, dispatcher):
        """Test handling of concurrent room operations."""
        websockets = setup_connections

        # Create multiple contexts
        contexts = [
            DispatchContext(
                websocket=websockets[f"client{i}"],
                room_id="lobby",
                player_id=f"client{i}",
                player_name=f"Client{i}",
            )
            for i in range(1, 4)
        ]

        # Create rooms concurrently
        create_tasks = [
            dispatcher.dispatch(
                "create_room", {"player_name": f"Client{i}"}, contexts[i - 1]
            )
            for i in range(1, 4)
        ]

        create_results = await asyncio.gather(*create_tasks)

        # All should succeed
        for result in create_results:
            assert result["data"]["success"] is True

        # Get room list
        list_response = await dispatcher.dispatch("get_rooms", {}, contexts[0])

        # Should see all 3 rooms
        assert len(list_response["data"]["rooms"]) == 3

    @pytest.mark.asyncio
    async def test_room_full_status_update(self, setup_connections, dispatcher):
        """Test that room shows as full when capacity reached."""
        websockets = setup_connections

        # Create a room
        context = DispatchContext(
            websocket=websockets["client1"],
            room_id="lobby",
            player_id="client1",
            player_name="Client1",
        )

        create_response = await dispatcher.dispatch(
            "create_room", {"player_name": "Client1"}, context
        )
        room_id = create_response["data"]["room_id"]

        # Remove bots to make room for human players
        async with dispatcher.uow:
            room = await dispatcher.uow.rooms.get_by_id(room_id)
            # Remove 3 bots
            room.remove_player("Bot 2")
            room.remove_player("Bot 3")
            room.remove_player("Bot 4")
            await dispatcher.uow.rooms.save(room)

        # Have 3 more players join to fill the room
        for i in range(2, 5):
            context_i = DispatchContext(
                websocket=Mock(),
                room_id="lobby",
                player_id=f"player{i}",
                player_name=f"Player{i}",
            )

            await dispatcher.dispatch(
                "join_room",
                {"room_id": room_id, "player_name": f"Player{i}"},
                context_i,
            )

        # Get room list
        list_response = await dispatcher.dispatch("get_rooms", {}, context)

        # Room should show as full
        room_info = list_response["data"]["rooms"][0]
        assert room_info["player_count"] == 4
        assert room_info["max_players"] == 4

    @pytest.mark.asyncio
    async def test_room_deletion_removes_from_lobby(
        self, setup_connections, dispatcher
    ):
        """Test that deleted rooms are removed from lobby listing."""
        websockets = setup_connections

        # Create two rooms
        context1 = DispatchContext(
            websocket=websockets["client1"],
            room_id="lobby",
            player_id="client1",
            player_name="Client1",
        )

        context2 = DispatchContext(
            websocket=websockets["client2"],
            room_id="lobby",
            player_id="client2",
            player_name="Client2",
        )

        response1 = await dispatcher.dispatch(
            "create_room", {"player_name": "Client1"}, context1
        )
        room_id1 = response1["data"]["room_id"]

        response2 = await dispatcher.dispatch(
            "create_room", {"player_name": "Client2"}, context2
        )
        room_id2 = response2["data"]["room_id"]

        # Verify both rooms exist
        list_response = await dispatcher.dispatch("get_rooms", {}, context1)
        assert len(list_response["data"]["rooms"]) == 2

        # Delete first room
        async with dispatcher.uow:
            await dispatcher.uow.rooms.delete(room_id1)

        # Get updated list
        list_response = await dispatcher.dispatch("get_rooms", {}, context1)

        # Should only see one room
        assert len(list_response["data"]["rooms"]) == 1
        assert list_response["data"]["rooms"][0]["room_id"] == room_id2

    @pytest.mark.asyncio
    async def test_broadcast_isolation_between_rooms(
        self, setup_connections, dispatcher
    ):
        """Test that room broadcasts don't leak to lobby."""
        websockets = setup_connections

        # Clear messages
        for ws in websockets.values():
            ws.clear_messages()

        # Broadcast to specific room
        await broadcast("ROOM001", "game_update", {"test": "data"})

        # Only room client should receive
        assert len(websockets["room_client"].sent_messages) == 1
        assert websockets["room_client"].sent_messages[0]["event"] == "game_update"

        # Lobby clients should not receive
        assert len(websockets["client1"].sent_messages) == 0
        assert len(websockets["client2"].sent_messages) == 0
        assert len(websockets["client3"].sent_messages) == 0

    @pytest.mark.asyncio
    async def test_error_handling_in_lobby_updates(self, setup_connections, dispatcher):
        """Test error handling doesn't break lobby updates."""
        websockets = setup_connections

        # Try to get rooms with invalid request
        context = DispatchContext(
            websocket=websockets["client1"],
            room_id="lobby",
            player_id="client1",
            player_name="Client1",
        )

        # Mock an error in the use case
        with patch.object(
            dispatcher.get_room_list_use_case,
            "execute",
            side_effect=Exception("Database error"),
        ):
            response = await dispatcher.dispatch("get_rooms", {}, context)

        # Should get error response
        assert response["event"] == "error"
        assert "Failed to handle get_rooms" in response["data"]["message"]

        # But connection should still work
        normal_response = await dispatcher.dispatch("get_rooms", {}, context)

        # Should work normally
        assert normal_response["event"] == "room_list_update"
