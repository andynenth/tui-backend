"""
Base classes for the application layer.

Provides foundational classes for use cases, services, and other
application layer components.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# Type variables for request/response
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class UseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base class for all use cases.

    A use case represents a single business operation that orchestrates
    domain logic to achieve a specific goal. Each use case:
    - Has a single responsibility
    - Represents one transaction boundary
    - Returns a specific response type
    - Handles its own error cases
    """

    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """
        Execute the use case with the given request.

        Args:
            request: The request data for this use case

        Returns:
            The response data from this use case

        Raises:
            ApplicationException: If the use case cannot be completed
        """
        pass

    def _log_execution(self, request: TRequest, response: TResponse) -> None:
        """Log use case execution for monitoring."""
        logger.debug(
            f"{self.__class__.__name__} executed",
            extra={
                "use_case": self.__class__.__name__,
                "request": str(request),
                "response": str(response),
            },
        )


class ApplicationService(ABC):
    """
    Base class for application services.

    Application services provide high-level orchestration of multiple
    use cases and cross-cutting concerns. They:
    - Coordinate complex workflows
    - Manage transaction boundaries
    - Handle cross-cutting concerns
    - Provide a facade for related operations
    """

    def __init__(self):
        """Initialize the application service."""
        self._logger = logging.getLogger(self.__class__.__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: Dict[str, str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = {}

    def add_error(self, field: str, message: str) -> None:
        """Add a validation error."""
        self.errors[field] = message
        self.is_valid = False


class Validator(ABC):
    """Base class for request validators."""

    @abstractmethod
    def validate(self, request: Any) -> ValidationResult:
        """
        Validate a request object.

        Args:
            request: The request to validate

        Returns:
            ValidationResult indicating success or errors
        """
        pass


class UnitOfWork(ABC):
    """
    Defines a transaction boundary for the application layer.

    The unit of work pattern ensures that all operations within
    a use case are atomic - they either all succeed or all fail.
    """

    @abstractmethod
    async def __aenter__(self):
        """Begin the unit of work."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete or rollback the unit of work."""
        pass

    @abstractmethod
    async def commit(self):
        """Commit all changes in this unit of work."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback all changes in this unit of work."""
        pass
