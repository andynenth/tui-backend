# backend/api/middleware/error_handlers.py
"""
Custom error handlers for standardized error responses.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from backend.models.error_responses import create_error_response, ErrorCodes
import json


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTPException to return standardized error response.
    """
    # Check if the detail is already our custom error response
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        # It's already a standardized error response
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Otherwise, create a standardized error response
    error_code = ErrorCodes.INTERNAL_ERROR

    # Map status codes to error codes
    if exc.status_code == 404:
        error_code = ErrorCodes.ROOM_NOT_FOUND
    elif exc.status_code == 400:
        error_code = ErrorCodes.INVALID_PARAMETER
    elif exc.status_code == 422:
        error_code = ErrorCodes.MISSING_PARAMETER

    error_response, _ = create_error_response(
        code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )


async def custom_validation_exception_handler(request: Request, exc):
    """
    Custom handler for validation errors to return standardized format.
    """
    from backend.models.error_responses import create_validation_error_response

    errors = []
    for error in exc.errors():
        field_path = ".".join(
            str(loc) for loc in error["loc"][1:]
        )  # Skip first element (usually "body")
        # Handle bytes input that can't be JSON serialized
        input_value = error.get("input")
        if isinstance(input_value, bytes):
            try:
                input_value = input_value.decode("utf-8")
            except UnicodeDecodeError:
                input_value = f"<bytes data of length {len(input_value)}>"

        errors.append(
            {
                "code": ErrorCodes.INVALID_PARAMETER,
                "message": error["msg"],
                "field": field_path if field_path else None,
                "context": {"type": error["type"], "input": input_value},
            }
        )

    validation_response, status_code = create_validation_error_response(
        errors=errors, path=str(request.url.path)
    )

    return JSONResponse(
        status_code=status_code, content=validation_response.model_dump()
    )
