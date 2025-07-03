# backend/engine/dependency_injection/__init__.py

"""
🎯 **Dependency Injection Module** - Phase 3 Circular Dependency Resolution

This module provides dependency injection to eliminate circular dependencies
and create loose coupling between components.
"""

from .container import (
    DependencyInjectionContainer,
    DIScope,
    ServiceLifetime,
    ServiceDescriptor,
    get_global_container,
    reset_global_container
)

from .interfaces import (
    IStateMachine,
    IBroadcaster,
    IActionHandler,
    IPhaseTransitioner,
    IBotNotifier,
    IEventStore,
    IGameRepository
)

__all__ = [
    'DependencyInjectionContainer',
    'DIScope', 
    'ServiceLifetime',
    'ServiceDescriptor',
    'get_global_container',
    'reset_global_container',
    'IStateMachine',
    'IBroadcaster',
    'IActionHandler',
    'IPhaseTransitioner',
    'IBotNotifier',
    'IEventStore',
    'IGameRepository'
]