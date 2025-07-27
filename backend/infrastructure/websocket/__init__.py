"""
WebSocket infrastructure integration.

This module provides infrastructure components specifically designed for
WebSocket communication, including connection management, state synchronization,
and real-time event propagation.
"""

from .connection_manager import (
    ConnectionManager,
    ConnectionInfo,
    ConnectionState,
    IConnectionRegistry,
    InMemoryConnectionRegistry
)

from .websocket_repository import (
    WebSocketRepository,
    WebSocketUnitOfWork,
    RealtimeRepositoryMixin,
    SubscriptionManager
)

from .event_propagator import (
    EventPropagator,
    WebSocketEventBus,
    EventSubscription,
    BroadcastStrategy,
    TargetedBroadcast,
    RoomBroadcast
)

from .middleware import (
    WebSocketInfrastructureMiddleware,
    ConnectionTrackingMiddleware,
    RateLimitingMiddleware,
    ObservabilityMiddleware,
    ErrorHandlingMiddleware
)

from .state_sync import (
    StateSynchronizer,
    SyncStrategy,
    DeltaSync,
    FullSync,
    OptimisticSync
)

from .recovery import (
    ConnectionRecoveryManager,
    RecoveryStrategy,
    ReconnectionHandler,
    StateReconciliation
)

__all__ = [
    # Connection Management
    'ConnectionManager',
    'ConnectionInfo',
    'ConnectionState',
    'IConnectionRegistry',
    'InMemoryConnectionRegistry',
    
    # Repository Integration
    'WebSocketRepository',
    'WebSocketUnitOfWork',
    'RealtimeRepositoryMixin',
    'SubscriptionManager',
    
    # Event Propagation
    'EventPropagator',
    'WebSocketEventBus',
    'EventSubscription',
    'BroadcastStrategy',
    'TargetedBroadcast',
    'RoomBroadcast',
    
    # Middleware
    'WebSocketInfrastructureMiddleware',
    'ConnectionTrackingMiddleware',
    'RateLimitingMiddleware',
    'ObservabilityMiddleware',
    'ErrorHandlingMiddleware',
    
    # State Synchronization
    'StateSynchronizer',
    'SyncStrategy',
    'DeltaSync',
    'FullSync',
    'OptimisticSync',
    
    # Recovery
    'ConnectionRecoveryManager',
    'RecoveryStrategy',
    'ReconnectionHandler',
    'StateReconciliation'
]