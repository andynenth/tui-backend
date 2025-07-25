"""
Base classes for DTOs.

Provides foundational classes for request and response objects
used by use cases.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


class Request(ABC):
    """
    Base class for all use case requests.
    
    Requests contain the data needed to execute a use case.
    They should be immutable and contain only data, no behavior.
    
    Note: This is not a dataclass to avoid field ordering issues.
    Subclasses should be dataclasses and include these fields.
    """
    pass


def request_fields():
    """Get the standard request fields for dataclasses."""
    return {
        'request_id': field(default_factory=lambda: str(uuid.uuid4())),
        'timestamp': field(default_factory=datetime.utcnow),
        'user_id': None,
        'correlation_id': None
    }


class Response(ABC):
    """
    Base class for all use case responses.
    
    Responses contain the result of executing a use case.
    They should be immutable and contain only data, no behavior.
    
    Note: This is not a dataclass to avoid field ordering issues.
    Subclasses should be dataclasses and include these fields.
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return {
            "success": getattr(self, 'success', True),
            "request_id": getattr(self, 'request_id', None),
            "timestamp": getattr(self, 'timestamp', datetime.utcnow()).isoformat(),
            "data": self._get_data()
        }
    
    def _get_data(self) -> Dict[str, Any]:
        """
        Get response-specific data.
        
        Override in subclasses to provide custom serialization.
        """
        # Default implementation - exclude base fields
        data = {}
        for key, value in self.__dict__.items():
            if key not in ["success", "request_id", "timestamp"]:
                data[key] = value
        return data


def response_fields():
    """Get the standard response fields for dataclasses."""
    return {
        'success': True,
        'request_id': None,
        'timestamp': field(default_factory=datetime.utcnow)
    }


@dataclass
class ErrorResponse(Response):
    """Response indicating an error occurred."""
    
    success: bool = False
    error_code: str = "UNKNOWN_ERROR"
    error_message: str = "An error occurred"
    error_details: Optional[Dict[str, Any]] = None
    
    def _get_data(self) -> Dict[str, Any]:
        """Include error information in response data."""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_details": self.error_details or {}
        }


@dataclass 
class PagedResponse(Response, ABC):
    """Base class for paginated responses."""
    
    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    
    def __post_init__(self):
        """Calculate total pages after initialization."""
        if self.page_size > 0:
            self.total_pages = (self.total_items + self.page_size - 1) // self.page_size