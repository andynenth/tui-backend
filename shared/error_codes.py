"""
Standardized Error Classification System

This module defines a unified error code system that is shared between
the frontend and backend to ensure consistent error handling and user experience.
"""

from enum import IntEnum
from typing import Dict, Any, Optional


class ErrorCode(IntEnum):
    """Standardized error codes for the Liap TUI application."""
    
    # Validation Errors (1000-1999)
    VALIDATION_REQUIRED_FIELD = 1001
    VALIDATION_INVALID_FORMAT = 1002
    VALIDATION_OUT_OF_RANGE = 1003
    VALIDATION_INVALID_TYPE = 1004
    VALIDATION_DUPLICATE_VALUE = 1005
    VALIDATION_CONSTRAINT_VIOLATION = 1006
    
    # Authentication/Authorization (2000-2999)
    AUTH_INVALID_CREDENTIALS = 2001
    AUTH_SESSION_EXPIRED = 2002
    AUTH_INSUFFICIENT_PERMISSIONS = 2003
    AUTH_ACCOUNT_LOCKED = 2004
    
    # Game Logic Errors (3000-3999)
    GAME_INVALID_ACTION = 3001
    GAME_NOT_YOUR_TURN = 3002
    GAME_INVALID_PIECES = 3003
    GAME_INVALID_PHASE = 3004
    GAME_ALREADY_DECLARED = 3005
    GAME_ROOM_FULL = 3006
    GAME_ROOM_NOT_FOUND = 3007
    GAME_PLAYER_NOT_IN_ROOM = 3008
    GAME_INSUFFICIENT_PIECES = 3009
    GAME_DECLARATION_CONSTRAINT = 3010
    GAME_WEAK_HAND_INVALID = 3011
    
    # Network/Connection (4000-4999)
    NETWORK_CONNECTION_LOST = 4001
    NETWORK_TIMEOUT = 4002
    NETWORK_WEBSOCKET_ERROR = 4003
    NETWORK_MESSAGE_QUEUE_FULL = 4004
    NETWORK_INVALID_MESSAGE = 4005
    NETWORK_RECONNECTION_FAILED = 4006
    
    # System Errors (5000-5999)
    SYSTEM_INTERNAL_ERROR = 5001
    SYSTEM_SERVICE_UNAVAILABLE = 5002
    SYSTEM_DATABASE_ERROR = 5003
    SYSTEM_MEMORY_ERROR = 5004
    SYSTEM_CONFIGURATION_ERROR = 5005


class ErrorSeverity:
    """Error severity levels for logging and user notification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high" 
    CRITICAL = "critical"


class StandardError:
    """Standardized error response format."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
        severity: str = ErrorSeverity.MEDIUM,
        request_id: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details
        self.context = context or {}
        self.retryable = retryable
        self.severity = severity
        self.request_id = request_id
        self.timestamp = self._get_timestamp()
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for JSON serialization."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "context": self.context,
            "retryable": self.retryable,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "request_id": self.request_id
        }
    
    def to_websocket_message(self) -> Dict[str, Any]:
        """Convert error to WebSocket message format."""
        return {
            "event": "error",
            "data": self.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardError':
        """Create StandardError from dictionary."""
        return cls(
            code=ErrorCode(data["code"]),
            message=data["message"],
            details=data.get("details"),
            context=data.get("context", {}),
            retryable=data.get("retryable", False),
            severity=data.get("severity", ErrorSeverity.MEDIUM),
            request_id=data.get("request_id")
        )


# Error code metadata for determining behavior
ERROR_METADATA = {
    # Validation errors - usually not retryable, low to medium severity
    ErrorCode.VALIDATION_REQUIRED_FIELD: {
        "retryable": False,
        "severity": ErrorSeverity.LOW,
        "user_message": "Required field is missing"
    },
    ErrorCode.VALIDATION_INVALID_FORMAT: {
        "retryable": False,
        "severity": ErrorSeverity.LOW,
        "user_message": "Invalid format provided"
    },
    ErrorCode.VALIDATION_OUT_OF_RANGE: {
        "retryable": False,
        "severity": ErrorSeverity.LOW,
        "user_message": "Value is out of acceptable range"
    },
    
    # Game logic errors - context-dependent retryability
    ErrorCode.GAME_INVALID_ACTION: {
        "retryable": False,
        "severity": ErrorSeverity.MEDIUM,
        "user_message": "This action is not allowed right now"
    },
    ErrorCode.GAME_NOT_YOUR_TURN: {
        "retryable": False,
        "severity": ErrorSeverity.LOW,
        "user_message": "It's not your turn yet"
    },
    ErrorCode.GAME_ROOM_FULL: {
        "retryable": True,
        "severity": ErrorSeverity.MEDIUM,
        "user_message": "Game room is full, please try again later"
    },
    
    # Network errors - usually retryable, higher severity
    ErrorCode.NETWORK_CONNECTION_LOST: {
        "retryable": True,
        "severity": ErrorSeverity.HIGH,
        "user_message": "Connection lost, attempting to reconnect..."
    },
    ErrorCode.NETWORK_TIMEOUT: {
        "retryable": True,
        "severity": ErrorSeverity.MEDIUM,
        "user_message": "Request timed out, please try again"
    },
    
    # System errors - retryable for transient issues, critical severity
    ErrorCode.SYSTEM_INTERNAL_ERROR: {
        "retryable": True,
        "severity": ErrorSeverity.CRITICAL,
        "user_message": "An unexpected error occurred, please try again"
    },
    ErrorCode.SYSTEM_SERVICE_UNAVAILABLE: {
        "retryable": True,
        "severity": ErrorSeverity.HIGH,
        "user_message": "Service is temporarily unavailable"
    }
}


def get_error_metadata(code: ErrorCode) -> Dict[str, Any]:
    """Get metadata for an error code."""
    return ERROR_METADATA.get(code, {
        "retryable": False,
        "severity": ErrorSeverity.MEDIUM,
        "user_message": "An error occurred"
    })


def create_standard_error(
    code: ErrorCode,
    message: str,
    details: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> StandardError:
    """Create a StandardError with metadata applied."""
    metadata = get_error_metadata(code)
    
    return StandardError(
        code=code,
        message=message,
        details=details,
        context=context,
        retryable=metadata["retryable"],
        severity=metadata["severity"],
        request_id=request_id
    )