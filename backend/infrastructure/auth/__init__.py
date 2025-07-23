# infrastructure/auth/__init__.py
"""
Authentication infrastructure.
"""

from .simple_auth_adapter import SimpleAuthAdapter

__all__ = [
    'SimpleAuthAdapter',
]