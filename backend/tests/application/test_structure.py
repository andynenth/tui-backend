"""
Test that the application layer structure is set up correctly.
"""

import pytest
import importlib
import inspect


def test_application_package_exists():
    """Test that application package can be imported."""
    application = importlib.import_module("application")
    assert application is not None


def test_base_classes_exist():
    """Test that base classes are properly defined."""
    from application.base import (
        UseCase,
        ApplicationService,
        Validator,
        ValidationResult,
    )

    # Check UseCase is abstract
    assert inspect.isabstract(UseCase)
    assert hasattr(UseCase, "execute")

    # Check ApplicationService is abstract
    assert inspect.isabstract(ApplicationService)

    # Check Validator is abstract
    assert inspect.isabstract(Validator)
    assert hasattr(Validator, "validate")

    # Check ValidationResult is concrete
    assert not inspect.isabstract(ValidationResult)


def test_exceptions_hierarchy():
    """Test that exception hierarchy is properly defined."""
    from application.exceptions import (
        ApplicationException,
        ValidationException,
        AuthorizationException,
        ResourceNotFoundException,
        ConflictException,
        ConcurrencyException,
        UseCaseException,
    )

    # All should inherit from ApplicationException
    assert issubclass(ValidationException, ApplicationException)
    assert issubclass(AuthorizationException, ApplicationException)
    assert issubclass(ResourceNotFoundException, ApplicationException)
    assert issubclass(ConflictException, ApplicationException)
    assert issubclass(ConcurrencyException, ApplicationException)
    assert issubclass(UseCaseException, ApplicationException)

    # Test exception creation
    exc = ValidationException({"field": "error"})
    assert exc.code == "VALIDATION_ERROR"
    assert exc.errors == {"field": "error"}


def test_interfaces_defined():
    """Test that interfaces are properly defined."""
    from application.interfaces import (
        RoomRepository,
        GameRepository,
        PlayerStatsRepository,
        EventPublisher,
        NotificationService,
        BotService,
        MetricsCollector,
        Logger,
        UnitOfWork,
    )

    # All should be abstract
    assert inspect.isabstract(RoomRepository)
    assert inspect.isabstract(GameRepository)
    assert inspect.isabstract(PlayerStatsRepository)
    assert inspect.isabstract(EventPublisher)
    assert inspect.isabstract(NotificationService)
    assert inspect.isabstract(BotService)
    assert inspect.isabstract(MetricsCollector)
    assert inspect.isabstract(Logger)
    assert inspect.isabstract(UnitOfWork)


def test_dto_base_classes():
    """Test that DTO base classes work correctly."""
    from application.dto import Request, Response
    from application.dto.base import ErrorResponse, PagedResponse

    # Test Request
    assert inspect.isabstract(Request)

    # Test Response
    assert inspect.isabstract(Response)

    # Test ErrorResponse
    error = ErrorResponse(error_code="TEST_ERROR", error_message="Test error")
    assert error.success is False
    assert error.error_code == "TEST_ERROR"

    # Test response serialization
    data = error.to_dict()
    assert data["success"] is False
    assert data["data"]["error_code"] == "TEST_ERROR"


def test_common_dtos():
    """Test that common DTOs are properly defined."""
    from application.dto.common import (
        PlayerInfo,
        RoomInfo,
        GameStateInfo,
        PlayerStatus,
        RoomStatus,
    )

    # Test enums
    assert PlayerStatus.CONNECTED == "connected"
    assert RoomStatus.WAITING == "waiting"

    # Test PlayerInfo
    player = PlayerInfo(
        player_id="p1",
        player_name="Test",
        is_bot=False,
        is_host=True,
        status=PlayerStatus.CONNECTED,
    )
    assert player.player_id == "p1"
    assert player.status == PlayerStatus.CONNECTED

    # Test RoomInfo
    room = RoomInfo(
        room_id="r1",
        room_code="ABC123",
        room_name="Test Room",
        host_id="p1",
        status=RoomStatus.WAITING,
        players=[player],
        max_players=4,
        created_at=None,
        game_in_progress=False,
    )
    assert room.player_count == 1
    assert not room.is_full
    assert room.is_joinable


def test_use_case_packages():
    """Test that use case packages are set up."""
    from application import use_cases

    # Check subpackages exist
    assert hasattr(use_cases, "connection")
    assert hasattr(use_cases, "room_management")
    assert hasattr(use_cases, "lobby")
    assert hasattr(use_cases, "game")
