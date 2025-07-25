"""
Application layer exceptions.

These exceptions represent application-level errors that occur during
use case execution. They are distinct from domain exceptions and
infrastructure exceptions.
"""

from typing import Optional, Dict, Any


class ApplicationException(Exception):
    """
    Base exception for all application layer errors.
    
    Application exceptions represent errors in business workflows,
    validation, or orchestration logic.
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the application exception.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


class ValidationException(ApplicationException):
    """Raised when request validation fails."""
    
    def __init__(self, errors: Dict[str, str]):
        """
        Initialize validation exception.
        
        Args:
            errors: Dictionary of field names to error messages
        """
        message = "Validation failed"
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"errors": errors}
        )
        self.errors = errors


class AuthorizationException(ApplicationException):
    """Raised when a user is not authorized to perform an action."""
    
    def __init__(self, action: str, resource: Optional[str] = None):
        """
        Initialize authorization exception.
        
        Args:
            action: The action that was attempted
            resource: The resource being accessed
        """
        message = f"Not authorized to {action}"
        if resource:
            message += f" on {resource}"
        
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details={"action": action, "resource": resource}
        )


class ResourceNotFoundException(ApplicationException):
    """Raised when a requested resource cannot be found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        """
        Initialize resource not found exception.
        
        Args:
            resource_type: Type of resource (e.g., "Room", "Game")
            resource_id: Identifier of the missing resource
        """
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class ConflictException(ApplicationException):
    """Raised when an operation conflicts with current state."""
    
    def __init__(self, operation: str, reason: str):
        """
        Initialize conflict exception.
        
        Args:
            operation: The operation that was attempted
            reason: Why it conflicts with current state
        """
        super().__init__(
            message=f"Cannot {operation}: {reason}",
            code="CONFLICT",
            details={"operation": operation, "reason": reason}
        )


class ConcurrencyException(ApplicationException):
    """Raised when a concurrency conflict occurs."""
    
    def __init__(self, resource: str, expected_version: int, actual_version: int):
        """
        Initialize concurrency exception.
        
        Args:
            resource: The resource with version conflict
            expected_version: Version expected by client
            actual_version: Current version in system
        """
        super().__init__(
            message=f"Version conflict on {resource}",
            code="CONCURRENCY_ERROR",
            details={
                "resource": resource,
                "expected_version": expected_version,
                "actual_version": actual_version
            }
        )


class UseCaseException(ApplicationException):
    """Raised when a use case cannot complete its operation."""
    
    def __init__(self, use_case: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize use case exception.
        
        Args:
            use_case: Name of the use case that failed
            reason: Why the use case failed
            details: Additional error details
        """
        super().__init__(
            message=f"{use_case} failed: {reason}",
            code="USE_CASE_ERROR",
            details={
                "use_case": use_case,
                "reason": reason,
                **(details or {})
            }
        )