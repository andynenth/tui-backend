# backend/engine/dependency_injection/container.py

import asyncio
import logging
from typing import Dict, Type, Any, Optional, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"     # Single instance for entire application
    SCOPED = "scoped"          # Single instance per scope (e.g., per game room)
    TRANSIENT = "transient"    # New instance every time


class ServiceDescriptor:
    """Describes how to create and manage a service."""
    
    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        **kwargs
    ):
        self.service_type = service_type
        self.implementation = implementation or service_type
        self.factory = factory
        self.lifetime = lifetime
        self.init_kwargs = kwargs
        
    def __repr__(self):
        return f"ServiceDescriptor({self.service_type.__name__}, {self.lifetime.value})"


class DependencyInjectionContainer:
    """
    🎯 **Dependency Injection Container** - Phase 3.2 Circular Dependency Resolution
    
    Provides loose coupling between components to eliminate circular dependencies.
    Manages service lifetimes and dependency resolution.
    
    Features:
    - Service registration with lifetime management
    - Automatic dependency resolution
    - Scoped instances (per game room)
    - Factory pattern support
    - Interface-based service resolution
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}  # scope_id -> service_type -> instance
        self._lock = asyncio.Lock()
        
    # === Service Registration ===
    
    def register_singleton(self, service_type: Type, implementation: Optional[Type] = None, **kwargs):
        """Register a singleton service (single instance for entire application)."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SINGLETON,
            **kwargs
        )
        logger.debug(f"📝 REGISTERED singleton: {service_type.__name__}")
        return self
    
    def register_scoped(self, service_type: Type, implementation: Optional[Type] = None, **kwargs):
        """Register a scoped service (single instance per scope, e.g., per room)."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SCOPED,
            **kwargs
        )
        logger.debug(f"📝 REGISTERED scoped: {service_type.__name__}")
        return self
    
    def register_transient(self, service_type: Type, implementation: Optional[Type] = None, **kwargs):
        """Register a transient service (new instance every time)."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.TRANSIENT,
            **kwargs
        )
        logger.debug(f"📝 REGISTERED transient: {service_type.__name__}")
        return self
    
    def register_factory(self, service_type: Type, factory: Callable, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON):
        """Register a service with a custom factory function."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )
        logger.debug(f"📝 REGISTERED factory: {service_type.__name__} ({lifetime.value})")
        return self
    
    def register_instance(self, service_type: Type, instance: Any):
        """Register a pre-created instance as a singleton."""
        self._services[service_type] = ServiceDescriptor(
            service_type=service_type,
            lifetime=ServiceLifetime.SINGLETON
        )
        self._singletons[service_type] = instance
        logger.debug(f"📝 REGISTERED instance: {service_type.__name__}")
        return self
    
    # === Service Resolution ===
    
    async def resolve(self, service_type: Type[T], scope_id: Optional[str] = None) -> T:
        """
        Resolve a service instance based on its registration.
        
        Args:
            service_type: The type of service to resolve
            scope_id: Scope identifier for scoped services (e.g., room_id)
        """
        async with self._lock:
            if service_type not in self._services:
                raise ValueError(f"Service {service_type.__name__} not registered")
            
            descriptor = self._services[service_type]
            
            # Handle different lifetimes
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                return await self._resolve_singleton(descriptor)
            
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                if scope_id is None:
                    raise ValueError(f"Scoped service {service_type.__name__} requires scope_id")
                return await self._resolve_scoped(descriptor, scope_id)
            
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                return await self._create_instance(descriptor)
            
            else:
                raise ValueError(f"Unknown lifetime: {descriptor.lifetime}")
    
    async def _resolve_singleton(self, descriptor: ServiceDescriptor):
        """Resolve singleton service (create once, reuse always)."""
        if descriptor.service_type in self._singletons:
            return self._singletons[descriptor.service_type]
        
        instance = await self._create_instance(descriptor)
        self._singletons[descriptor.service_type] = instance
        logger.debug(f"🏭 CREATED singleton: {descriptor.service_type.__name__}")
        return instance
    
    async def _resolve_scoped(self, descriptor: ServiceDescriptor, scope_id: str):
        """Resolve scoped service (create once per scope)."""
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
        
        scope_services = self._scoped_instances[scope_id]
        
        if descriptor.service_type in scope_services:
            return scope_services[descriptor.service_type]
        
        instance = await self._create_instance(descriptor)
        scope_services[descriptor.service_type] = instance
        logger.debug(f"🏭 CREATED scoped: {descriptor.service_type.__name__} (scope: {scope_id})")
        return instance
    
    async def _create_instance(self, descriptor: ServiceDescriptor):
        """Create a new instance using factory or constructor."""
        try:
            if descriptor.factory:
                # Use custom factory
                if asyncio.iscoroutinefunction(descriptor.factory):
                    return await descriptor.factory(self)
                else:
                    return descriptor.factory(self)
            else:
                # Use constructor with dependency injection
                return await self._create_with_dependency_injection(descriptor)
                
        except Exception as e:
            logger.error(f"❌ Failed to create {descriptor.service_type.__name__}: {str(e)}")
            raise
    
    async def _create_with_dependency_injection(self, descriptor: ServiceDescriptor):
        """
        Create instance with automatic dependency injection.
        
        Analyzes constructor parameters and injects registered services.
        """
        import inspect
        
        constructor = descriptor.implementation.__init__
        signature = inspect.signature(constructor)
        
        # Resolve constructor parameters
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            # Check if parameter type is registered
            if param.annotation and param.annotation in self._services:
                # Inject dependency
                dependency = await self.resolve(param.annotation)
                kwargs[param_name] = dependency
            elif param_name in descriptor.init_kwargs:
                # Use provided init kwargs
                kwargs[param_name] = descriptor.init_kwargs[param_name]
            elif param.default is not inspect.Parameter.empty:
                # Use default value
                pass
            else:
                logger.warning(f"⚠️ Cannot resolve parameter '{param_name}' for {descriptor.service_type.__name__}")
        
        return descriptor.implementation(**kwargs)
    
    # === Scope Management ===
    
    def create_scope(self, scope_id: str) -> 'DIScope':
        """Create a new dependency injection scope."""
        return DIScope(self, scope_id)
    
    async def dispose_scope(self, scope_id: str):
        """Dispose of a scope and all its instances."""
        if scope_id in self._scoped_instances:
            scope_services = self._scoped_instances[scope_id]
            
            # Call dispose on services that support it
            for service in scope_services.values():
                if hasattr(service, 'dispose') and callable(service.dispose):
                    try:
                        if asyncio.iscoroutinefunction(service.dispose):
                            await service.dispose()
                        else:
                            service.dispose()
                    except Exception as e:
                        logger.error(f"❌ Error disposing service: {str(e)}")
            
            del self._scoped_instances[scope_id]
            logger.debug(f"🗑️ DISPOSED scope: {scope_id}")
    
    # === Utilities ===
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services
    
    def get_registration_info(self) -> Dict[str, str]:
        """Get information about all registered services."""
        return {
            service_type.__name__: f"{descriptor.lifetime.value} - {descriptor.implementation.__name__}"
            for service_type, descriptor in self._services.items()
        }


class DIScope:
    """
    Dependency injection scope for managing scoped services.
    
    Used for game rooms where services should be isolated per room.
    """
    
    def __init__(self, container: DependencyInjectionContainer, scope_id: str):
        self.container = container
        self.scope_id = scope_id
    
    async def resolve(self, service_type: Type[T]) -> T:
        """Resolve service within this scope."""
        return await self.container.resolve(service_type, self.scope_id)
    
    async def dispose(self):
        """Dispose this scope and all its services."""
        await self.container.dispose_scope(self.scope_id)


# Global container instance
_global_container: Optional[DependencyInjectionContainer] = None


def get_global_container() -> DependencyInjectionContainer:
    """Get or create the global dependency injection container."""
    global _global_container
    if _global_container is None:
        _global_container = DependencyInjectionContainer()
    return _global_container


def reset_global_container():
    """Reset the global container (used for testing)."""
    global _global_container
    _global_container = None