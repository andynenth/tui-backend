# backend/models/error_responses.py
"""
Standardized error response models for the API.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error: ErrorDetail
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z", description="Error timestamp in ISO format")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "ROOM_NOT_FOUND",
                    "message": "Room with ID 'ABC123' not found",
                    "context": {
                        "room_id": "ABC123"
                    }
                },
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/api/rooms/ABC123/play-history"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    errors: List[ErrorDetail]
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    path: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "errors": [
                    {
                        "code": "INVALID_RANGE",
                        "message": "'from' must be less than or equal to 'to'",
                        "field": "from",
                        "context": {
                            "from": 5,
                            "to": 2
                        }
                    }
                ],
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/api/rooms/ABC123/play-history/rounds"
            }
        }


# Error code constants
class ErrorCodes:
    """Centralized error codes for consistency."""
    # Resource errors
    ROOM_NOT_FOUND = "ROOM_NOT_FOUND"
    GAME_NOT_FOUND = "GAME_NOT_FOUND"
    ROUND_NOT_FOUND = "ROUND_NOT_FOUND"
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    
    # State errors
    NO_ACTIVE_GAME = "NO_ACTIVE_GAME"
    GAME_NOT_STARTED = "GAME_NOT_STARTED"
    INVALID_GAME_STATE = "INVALID_GAME_STATE"
    
    # Validation errors
    INVALID_RANGE = "INVALID_RANGE"
    INVALID_ROUND_NUMBER = "INVALID_ROUND_NUMBER"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    
    # Data errors
    CORRUPT_GAME_DATA = "CORRUPT_GAME_DATA"
    MISSING_PLAYER_DATA = "MISSING_PLAYER_DATA"
    INCOMPLETE_ROUND_DATA = "INCOMPLETE_ROUND_DATA"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"


def create_error_response(
    code: str,
    message: str,
    status_code: int = 400,
    field: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None
) -> tuple[ErrorResponse, int]:
    """
    Create a standardized error response.
    
    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    error_detail = ErrorDetail(
        code=code,
        message=message,
        field=field,
        context=context
    )
    
    error_response = ErrorResponse(
        error=error_detail,
        path=path
    )
    
    return error_response, status_code


def create_validation_error_response(
    errors: List[Dict[str, Any]],
    path: Optional[str] = None
) -> tuple[ValidationErrorResponse, int]:
    """
    Create a validation error response with multiple errors.
    
    Returns:
        Tuple of (ValidationErrorResponse, status_code)
    """
    error_details = []
    for error in errors:
        error_details.append(ErrorDetail(
            code=error.get("code", ErrorCodes.INVALID_PARAMETER),
            message=error["message"],
            field=error.get("field"),
            context=error.get("context")
        ))
    
    validation_response = ValidationErrorResponse(
        errors=error_details,
        path=path
    )
    
    return validation_response, 422