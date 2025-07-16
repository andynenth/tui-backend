# backend/shared/error_codes.py

from enum import Enum
from typing import Dict, Any

class ErrorCode(Enum):
    """Standard error codes for the application"""
    INVALID_MESSAGE = "INVALID_MESSAGE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

def create_standard_error(code: ErrorCode, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a standard error response"""
    error = {
        "error": {
            "code": code.value,
            "message": message
        }
    }
    
    if details:
        error["error"]["details"] = details
    
    return error