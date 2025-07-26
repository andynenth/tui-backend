"""
Infrastructure adapters for bridging between layers.

These adapters enable gradual migration from legacy code to
clean architecture by providing compatibility layers.
"""

from .clean_architecture_adapter import CleanArchitectureAdapter
from .reconnection_adapter import ReconnectionAdapter

__all__ = [
    "CleanArchitectureAdapter",
    "ReconnectionAdapter"
]