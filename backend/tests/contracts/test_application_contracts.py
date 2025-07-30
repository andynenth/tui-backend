"""
Contract Tests for Application Layer

These tests ensure that application layer implementations
correctly implement the defined contracts.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from application.interfaces.websocket_contracts import (
    IMessageHandler,
    IMessageRouter,
    IConnectionContext,
    IEventPublisher,
    IMessageValidator,
    WebSocketMessage,
    WebSocketResponse,
)
from application.websocket.contract_implementations import (
    UseCaseMessageHandler,
    ApplicationMessageRouter,
    WebSocketConnectionContext,
    ApplicationEventPublisher,
    ApplicationMessageValidator,
    create_message_handler,
    create_message_router,
    create_event_publisher,
    create_message_validator,
    create_connection_context,
)


class TestMessageHandlerContract:
    """Test that UseCaseMessageHandler implements IMessageHandler correctly"""

    @pytest.fixture
    def handler(self):
        """Create a message handler"""
        with patch("application.websocket.contract_implementations.UseCaseDispatcher"):
            return UseCaseMessageHandler()

    @pytest.mark.asyncio
    async def test_handle_message(self, handler):
        """Test handle_message implementation"""
        # Setup mock dispatcher
        handler.dispatcher.dispatch = AsyncMock(
            return_value={"event": "response", "data": {"result": "success"}}
        )

        # Create message and context
        message = WebSocketMessage(event="test", data={"key": "value"})
        context = {"room_id": "room1", "player_id": "player1"}

        # Handle message
        response = await handler.handle_message(message, context)

        # Verify response
        assert response is not None
        assert isinstance(response, WebSocketResponse)
        assert response.event == "response"
        assert response.data == {"result": "success"}
        assert response.success is True

    def test_can_handle(self, handler):
        """Test can_handle implementation"""
        # Setup supported events
        handler._supported_events = {"event1", "event2"}

        assert handler.can_handle("event1") is True
        assert handler.can_handle("event2") is True
        assert handler.can_handle("event3") is False

    def test_get_supported_events(self, handler):
        """Test get_supported_events implementation"""
        # Setup supported events
        handler._supported_events = {"event1", "event2"}

        events = handler.get_supported_events()
        assert isinstance(events, list)
        assert len(events) == 2
        assert "event1" in events
        assert "event2" in events

    def test_implements_interface(self, handler):
        """Test that handler implements all required methods"""
        assert isinstance(handler, IMessageHandler)
        assert hasattr(handler, "handle_message")
        assert hasattr(handler, "can_handle")
        assert hasattr(handler, "get_supported_events")


class TestMessageRouterContract:
    """Test that ApplicationMessageRouter implements IMessageRouter correctly"""

    @pytest.fixture
    def router(self):
        """Create a message router"""
        with patch(
            "application.websocket.contract_implementations.UseCaseMessageHandler"
        ):
            return ApplicationMessageRouter()

    @pytest.mark.asyncio
    async def test_route(self, router):
        """Test route implementation"""
        # Create mock handler
        mock_handler = Mock(spec=IMessageHandler)
        mock_handler.handle_message = AsyncMock(
            return_value=WebSocketResponse(event="response", data={"result": "success"})
        )

        # Register handler
        router._handlers["test"] = mock_handler

        # Route message
        message = WebSocketMessage(event="test", data={"key": "value"})
        context = {"room_id": "room1"}
        response = await router.route(message, context)

        # Verify
        assert response is not None
        assert response.event == "response"
        assert response.data == {"result": "success"}
        mock_handler.handle_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_no_handler(self, router):
        """Test route with no handler"""
        # Route message with no handler
        message = WebSocketMessage(event="unknown", data={})
        context = {}
        response = await router.route(message, context)

        # Verify error response
        assert response is not None
        assert response.event == "error"
        assert response.success is False
        assert "no handler" in response.data["type"]

    def test_register_handler(self, router):
        """Test register_handler implementation"""
        # Create mock handler
        mock_handler = Mock(spec=IMessageHandler)
        mock_handler.get_supported_events.return_value = ["event1", "event2"]

        # Register handler
        router.register_handler(mock_handler)

        # Verify registration
        assert router._handlers["event1"] == mock_handler
        assert router._handlers["event2"] == mock_handler

    def test_get_handler_for_event(self, router):
        """Test get_handler_for_event implementation"""
        # Setup handlers
        handler1 = Mock(spec=IMessageHandler)
        handler2 = Mock(spec=IMessageHandler)
        router._handlers["event1"] = handler1
        router._handlers["event2"] = handler2

        # Get handlers
        assert router.get_handler_for_event("event1") == handler1
        assert router.get_handler_for_event("event2") == handler2
        assert router.get_handler_for_event("event3") is None

    def test_implements_interface(self, router):
        """Test that router implements all required methods"""
        assert isinstance(router, IMessageRouter)
        assert hasattr(router, "route")
        assert hasattr(router, "register_handler")
        assert hasattr(router, "get_handler_for_event")


class TestConnectionContextContract:
    """Test that WebSocketConnectionContext implements IConnectionContext correctly"""

    @pytest.fixture
    def context(self):
        """Create a connection context"""
        return WebSocketConnectionContext("conn1", "room1")

    def test_get_player_id(self, context):
        """Test get_player_id implementation"""
        assert context.get_player_id() is None
        context.player_id = "player1"
        assert context.get_player_id() == "player1"

    def test_get_room_id(self, context):
        """Test get_room_id implementation"""
        assert context.get_room_id() == "room1"

    def test_get_connection_id(self, context):
        """Test get_connection_id implementation"""
        assert context.get_connection_id() == "conn1"

    def test_set_player_info(self, context):
        """Test set_player_info implementation"""
        context.set_player_info("player1", "Player One")
        assert context.player_id == "player1"
        assert context.player_name == "Player One"

    def test_set_room_id(self, context):
        """Test set_room_id implementation"""
        context.set_room_id("room2")
        assert context.room_id == "room2"

    def test_to_dict(self, context):
        """Test to_dict implementation"""
        context.set_player_info("player1", "Player One")
        context.metadata["custom"] = "value"

        result = context.to_dict()
        assert result["connection_id"] == "conn1"
        assert result["room_id"] == "room1"
        assert result["player_id"] == "player1"
        assert result["player_name"] == "Player One"
        assert result["metadata"]["custom"] == "value"

    def test_implements_interface(self, context):
        """Test that context implements all required methods"""
        assert isinstance(context, IConnectionContext)
        assert hasattr(context, "get_player_id")
        assert hasattr(context, "get_room_id")
        assert hasattr(context, "get_connection_id")
        assert hasattr(context, "set_player_info")
        assert hasattr(context, "set_room_id")
        assert hasattr(context, "to_dict")


class TestEventPublisherContract:
    """Test that ApplicationEventPublisher implements IEventPublisher correctly"""

    @pytest.fixture
    def publisher(self):
        """Create an event publisher"""
        return ApplicationEventPublisher()

    @pytest.mark.asyncio
    async def test_publish_event_to_room(self, publisher):
        """Test publish_event with room_id"""
        with patch(
            "application.websocket.contract_implementations.broadcast"
        ) as mock_broadcast:
            mock_broadcast.return_value = None

            await publisher.publish_event(
                "test_event", {"data": "value"}, room_id="room1"
            )

            mock_broadcast.assert_called_once_with(
                "room1", "test_event", {"data": "value"}
            )

    @pytest.mark.asyncio
    async def test_publish_to_room(self, publisher):
        """Test publish_to_room implementation"""
        with patch(
            "application.websocket.contract_implementations.broadcast"
        ) as mock_broadcast:
            mock_broadcast.return_value = None

            await publisher.publish_to_room("room1", "test_event", {"data": "value"})

            mock_broadcast.assert_called_once_with(
                "room1", "test_event", {"data": "value"}
            )

    @pytest.mark.asyncio
    async def test_publish_to_player(self, publisher):
        """Test publish_to_player implementation"""
        # This is not yet implemented, so we just verify it doesn't crash
        await publisher.publish_to_player("player1", "test_event", {"data": "value"})

    def test_implements_interface(self, publisher):
        """Test that publisher implements all required methods"""
        assert isinstance(publisher, IEventPublisher)
        assert hasattr(publisher, "publish_event")
        assert hasattr(publisher, "publish_to_room")
        assert hasattr(publisher, "publish_to_player")


class TestMessageValidatorContract:
    """Test that ApplicationMessageValidator implements IMessageValidator correctly"""

    @pytest.fixture
    def validator(self):
        """Create a message validator"""
        return ApplicationMessageValidator()

    def test_validate_message_bypass(self, validator):
        """Test validate_message with bypass"""
        with patch.object(validator, "should_bypass_validation", return_value=True):
            message = {"event": "test", "data": {"key": "value"}}
            is_valid, error, data = validator.validate_message(message)

            assert is_valid is True
            assert error is None
            assert data == {"key": "value"}

    def test_validate_message_legacy(self, validator):
        """Test validate_message with legacy validation"""
        with patch.object(validator, "should_bypass_validation", return_value=False):
            with patch(
                "application.websocket.contract_implementations.validate_websocket_message"
            ) as mock_validate:
                mock_validate.return_value = (True, None, {"sanitized": "data"})

                message = {"event": "test", "data": {"key": "value"}}
                is_valid, error, data = validator.validate_message(message)

                assert is_valid is True
                assert error is None
                assert data == {"sanitized": "data"}
                mock_validate.assert_called_once_with(message)

    def test_validate_event(self, validator):
        """Test validate_event implementation"""
        with patch(
            "application.websocket.contract_implementations.websocket_config"
        ) as mock_config:
            mock_config.use_case_events = {"event1", "event2"}

            # Test use case event
            assert validator.validate_event("event1") is True

            # Test legacy event
            with patch(
                "api.validation.websocket_validators.WebSocketMessageValidator"
            ) as mock_validator:
                mock_validator.ALLOWED_EVENTS = {"legacy_event"}
                assert validator.validate_event("legacy_event") is True
                assert validator.validate_event("unknown_event") is False

    def test_should_bypass_validation(self, validator):
        """Test should_bypass_validation implementation"""
        with patch(
            "application.websocket.contract_implementations.websocket_config"
        ) as mock_config:
            mock_config.should_bypass_validation.return_value = True
            assert validator.should_bypass_validation("test") is True

            mock_config.should_bypass_validation.return_value = False
            assert validator.should_bypass_validation("test") is False

    def test_implements_interface(self, validator):
        """Test that validator implements all required methods"""
        assert isinstance(validator, IMessageValidator)
        assert hasattr(validator, "validate_message")
        assert hasattr(validator, "validate_event")
        assert hasattr(validator, "should_bypass_validation")


class TestFactoryFunctions:
    """Test factory functions create correct implementations"""

    def test_create_message_handler(self):
        """Test create_message_handler factory"""
        with patch("application.websocket.contract_implementations.UseCaseDispatcher"):
            handler = create_message_handler()
            assert isinstance(handler, IMessageHandler)
            assert isinstance(handler, UseCaseMessageHandler)

    def test_create_message_router(self):
        """Test create_message_router factory"""
        with patch(
            "application.websocket.contract_implementations.UseCaseMessageHandler"
        ):
            router = create_message_router()
            assert isinstance(router, IMessageRouter)
            assert isinstance(router, ApplicationMessageRouter)

    def test_create_event_publisher(self):
        """Test create_event_publisher factory"""
        publisher = create_event_publisher()
        assert isinstance(publisher, IEventPublisher)
        assert isinstance(publisher, ApplicationEventPublisher)

    def test_create_message_validator(self):
        """Test create_message_validator factory"""
        validator = create_message_validator()
        assert isinstance(validator, IMessageValidator)
        assert isinstance(validator, ApplicationMessageValidator)

    def test_create_connection_context(self):
        """Test create_connection_context factory"""
        context = create_connection_context("conn1", "room1")
        assert isinstance(context, IConnectionContext)
        assert isinstance(context, WebSocketConnectionContext)
        assert context.connection_id == "conn1"
        assert context.room_id == "room1"
