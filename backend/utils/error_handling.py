"""
Centralized Error Handling Service for Backend

Provides a unified interface for error handling, logging, validation,
and response formatting across the backend application.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from ..shared.error_codes import (
    ErrorCode, ErrorSeverity, StandardError, 
    create_standard_error, get_error_metadata
)


class ErrorHandlingService:
    """Centralized error handling service for the backend."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}  # For monitoring and alerting
        
    def create_http_exception(
        self, 
        code: ErrorCode, 
        message: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> HTTPException:
        """Create an HTTPException with standardized error format."""
        
        error = create_standard_error(
            code=code,
            message=message,
            details=details,
            context=context,
            request_id=request_id
        )
        
        http_status = self._map_error_code_to_http_status(code)
        
        # Log the error
        self._log_error(error, context)
        
        # Track error for monitoring
        self._track_error(code)
        
        return HTTPException(
            status_code=http_status,
            detail=error.to_dict()
        )
    
    def create_websocket_error(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a WebSocket error message with standardized format."""
        
        error = create_standard_error(
            code=code,
            message=message,
            details=details,
            context=context,
            request_id=request_id
        )
        
        # Log the error
        self._log_error(error, context)
        
        # Track error for monitoring
        self._track_error(code)
        
        return error.to_websocket_message()
    
    def handle_validation_error(
        self,
        field: str,
        value: Any,
        constraint: str,
        request_id: Optional[str] = None
    ) -> HTTPException:
        """Handle validation errors with standardized format."""
        
        code = self._determine_validation_error_code(constraint)
        message = f"Validation failed for field '{field}': {constraint}"
        
        return self.create_http_exception(
            code=code,
            message=message,
            details=f"Invalid value: {value}",
            context={"field": field, "value": str(value), "constraint": constraint},
            request_id=request_id
        )
    
    def handle_game_logic_error(
        self,
        code: ErrorCode,
        player_name: str,
        action: str,
        game_phase: str,
        additional_context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle game logic errors for WebSocket responses."""
        
        metadata = get_error_metadata(code)
        message = metadata.get("user_message", "Game action failed")
        
        context = {
            "player_name": player_name,
            "action": action,
            "game_phase": game_phase,
            **(additional_context or {})
        }
        
        return self.create_websocket_error(
            code=code,
            message=message,
            context=context,
            request_id=request_id
        )
    
    def handle_network_error(
        self,
        code: ErrorCode,
        connection_id: str,
        room_id: Optional[str] = None,
        details: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle network-related errors."""
        
        metadata = get_error_metadata(code)
        message = metadata.get("user_message", "Network error occurred")
        
        context = {
            "connection_id": connection_id,
            "room_id": room_id
        }
        
        return self.create_websocket_error(
            code=code,
            message=message,
            details=details,
            context=context,
            request_id=request_id
        )
    
    def handle_system_error(
        self,
        original_error: Exception,
        operation: str,
        request_id: Optional[str] = None
    ) -> HTTPException:
        """Handle unexpected system errors."""
        
        # Don't expose internal error details in production
        import os
        is_development = os.getenv("ENVIRONMENT", "production") == "development"
        
        message = "An internal error occurred"
        details = str(original_error) if is_development else None
        
        context = {
            "operation": operation,
            "error_type": type(original_error).__name__
        }
        
        # Log the full error details
        self.logger.error(
            f"System error in {operation}: {original_error}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        
        return self.create_http_exception(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message=message,
            details=details,
            context=context,
            request_id=request_id
        )
    
    def _map_error_code_to_http_status(self, code: ErrorCode) -> int:
        """Map error codes to appropriate HTTP status codes."""
        
        # Validation errors
        if 1000 <= code < 2000:
            return status.HTTP_400_BAD_REQUEST
        
        # Authentication/Authorization errors
        elif 2000 <= code < 3000:
            if code == ErrorCode.AUTH_INVALID_CREDENTIALS:
                return status.HTTP_401_UNAUTHORIZED
            elif code == ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS:
                return status.HTTP_403_FORBIDDEN
            elif code == ErrorCode.AUTH_ACCOUNT_LOCKED:
                return status.HTTP_423_LOCKED
            else:
                return status.HTTP_401_UNAUTHORIZED
        
        # Game logic errors
        elif 3000 <= code < 4000:
            if code == ErrorCode.GAME_ROOM_NOT_FOUND:
                return status.HTTP_404_NOT_FOUND
            elif code == ErrorCode.GAME_ROOM_FULL:
                return status.HTTP_409_CONFLICT
            else:
                return status.HTTP_400_BAD_REQUEST
        
        # Network errors
        elif 4000 <= code < 5000:
            if code == ErrorCode.NETWORK_TIMEOUT:
                return status.HTTP_408_REQUEST_TIMEOUT
            elif code == ErrorCode.NETWORK_MESSAGE_QUEUE_FULL:
                return status.HTTP_429_TOO_MANY_REQUESTS
            else:
                return status.HTTP_400_BAD_REQUEST
        
        # System errors
        elif 5000 <= code < 6000:
            if code == ErrorCode.SYSTEM_SERVICE_UNAVAILABLE:
                return status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                return status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Default
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def _determine_validation_error_code(self, constraint: str) -> ErrorCode:
        """Determine the appropriate validation error code based on constraint."""
        
        constraint_lower = constraint.lower()
        
        if "required" in constraint_lower or "missing" in constraint_lower:
            return ErrorCode.VALIDATION_REQUIRED_FIELD
        elif "format" in constraint_lower or "pattern" in constraint_lower:
            return ErrorCode.VALIDATION_INVALID_FORMAT
        elif "range" in constraint_lower or "min" in constraint_lower or "max" in constraint_lower:
            return ErrorCode.VALIDATION_OUT_OF_RANGE
        elif "type" in constraint_lower:
            return ErrorCode.VALIDATION_INVALID_TYPE
        elif "duplicate" in constraint_lower or "unique" in constraint_lower:
            return ErrorCode.VALIDATION_DUPLICATE_VALUE
        else:
            return ErrorCode.VALIDATION_CONSTRAINT_VIOLATION
    
    def _log_error(self, error: StandardError, context: Optional[Dict[str, Any]] = None):
        """Log error with appropriate level and context."""
        
        log_data = {
            "error_code": error.code.value,
            "error_message": error.message,
            "error_details": error.details,
            "error_context": error.context,
            "request_id": error.request_id,
            "timestamp": error.timestamp,
            "severity": error.severity
        }
        
        if context:
            log_data["additional_context"] = context
        
        # Choose log level based on severity
        if error.severity == ErrorSeverity.LOW:
            self.logger.info(f"Error {error.code}: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Error {error.code}: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"Error {error.code}: {error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Error {error.code}: {error.message}", extra=log_data)
    
    def _track_error(self, code: ErrorCode):
        """Track error occurrences for monitoring."""
        
        if code not in self.error_counts:
            self.error_counts[code] = 0
        self.error_counts[code] += 1
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        
        return {
            "error_counts": {code.name: count for code, count in self.error_counts.items()},
            "total_errors": sum(self.error_counts.values()),
            "timestamp": int(time.time() * 1000)
        }
    
    def reset_error_statistics(self):
        """Reset error statistics (useful for periodic reporting)."""
        self.error_counts.clear()


# Global error handling service instance
error_handler = ErrorHandlingService()


def generate_request_id() -> str:
    """Generate a unique request ID for error tracking."""
    return str(uuid.uuid4())


def validate_required_field(value: Any, field_name: str, request_id: Optional[str] = None):
    """Validate that a required field is present and not empty."""
    
    if value is None or (isinstance(value, str) and not value.strip()):
        raise error_handler.handle_validation_error(
            field=field_name,
            value=value,
            constraint="required field",
            request_id=request_id
        )


def validate_field_type(value: Any, expected_type: type, field_name: str, request_id: Optional[str] = None):
    """Validate that a field has the expected type."""
    
    if not isinstance(value, expected_type):
        raise error_handler.handle_validation_error(
            field=field_name,
            value=value,
            constraint=f"must be of type {expected_type.__name__}",
            request_id=request_id
        )


def validate_field_range(value: Any, min_val: Any, max_val: Any, field_name: str, request_id: Optional[str] = None):
    """Validate that a field value is within the specified range."""
    
    if value < min_val or value > max_val:
        raise error_handler.handle_validation_error(
            field=field_name,
            value=value,
            constraint=f"must be between {min_val} and {max_val}",
            request_id=request_id
        )


class ErrorMiddleware:
    """Middleware for handling unhandled exceptions and standardizing error responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request_id = generate_request_id()
        
        # Add request ID to scope for access in route handlers
        scope["request_id"] = request_id
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Handle unhandled exceptions
            error_response = error_handler.handle_system_error(
                original_error=exc,
                operation=f"{scope.get('method', 'UNKNOWN')} {scope.get('path', '/')}",
                request_id=request_id
            )
            
            response = JSONResponse(
                status_code=error_response.status_code,
                content=error_response.detail
            )
            
            await response(scope, receive, send)