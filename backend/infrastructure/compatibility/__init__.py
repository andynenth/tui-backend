# infrastructure/compatibility/__init__.py
"""
Compatibility layer for gradual migration to clean architecture.
"""

from .message_adapter import MessageAdapter
from .legacy_adapter import LegacyAdapter
from .feature_flags import FeatureFlags

__all__ = [
    'MessageAdapter',
    'LegacyAdapter',
    'FeatureFlags',
]