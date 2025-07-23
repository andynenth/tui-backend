# application/interfaces/__init__.py
"""
Application interfaces define contracts with infrastructure.

These interfaces:
- Abstract infrastructure concerns
- Enable dependency inversion
- Allow testing with mocks
- Support multiple implementations
"""

from .notification_service import NotificationService, NotificationType, Notification
from .authentication_service import AuthenticationService, PlayerIdentity, AuthToken

__all__ = [
    'NotificationService',
    'NotificationType',
    'Notification',
    'AuthenticationService',
    'PlayerIdentity',
    'AuthToken',
]