"""
Distributed tracing infrastructure for tracking requests across services.

Provides OpenTelemetry-compatible tracing with in-memory fallback.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import time
import asyncio
from contextlib import contextmanager
from functools import wraps
import json
import threading
from collections import defaultdict


class SpanKind(Enum):
    """Types of spans in distributed tracing."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Status of a span."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class TraceConfig:
    """Configuration for tracing system."""
    service_name: str = "liap-tui"
    sample_rate: float = 1.0  # 1.0 = 100% sampling
    max_spans_per_trace: int = 1000
    export_batch_size: int = 100
    export_interval_seconds: float = 5.0
    propagate_correlation_id: bool = True
    record_exceptions: bool = True
    record_attributes: bool = True


@dataclass
class SpanContext:
    """Context for a span in a trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 0
    trace_state: Dict[str, str] = field(default_factory=dict)
    
    def to_traceparent(self) -> str:
        """Convert to W3C traceparent format."""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}"
    
    @classmethod
    def from_traceparent(cls, traceparent: str) -> 'SpanContext':
        """Parse W3C traceparent format."""
        parts = traceparent.split('-')
        if len(parts) != 4:
            raise ValueError(f"Invalid traceparent: {traceparent}")
        
        return cls(
            trace_id=parts[1],
            span_id=parts[2],
            trace_flags=int(parts[3], 16)
        )


class ISpan(ABC):
    """Interface for a span in a trace."""
    
    @abstractmethod
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        pass
    
    @abstractmethod
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        pass
    
    @abstractmethod
    def set_status(self, status: SpanStatus, description: Optional[str] = None) -> None:
        """Set the span status."""
        pass
    
    @abstractmethod
    def record_exception(self, exception: Exception) -> None:
        """Record an exception on the span."""
        pass
    
    @abstractmethod
    def end(self) -> None:
        """End the span."""
        pass
    
    @abstractmethod
    def get_context(self) -> SpanContext:
        """Get the span context."""
        pass


class ISpanContext(ABC):
    """Interface for span context operations."""
    
    @abstractmethod
    def get_current_span(self) -> Optional[ISpan]:
        """Get the currently active span."""
        pass
    
    @abstractmethod
    def set_current_span(self, span: Optional[ISpan]) -> None:
        """Set the currently active span."""
        pass


class ITracer(ABC):
    """Interface for creating and managing spans."""
    
    @abstractmethod
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> ISpan:
        """Start a new span."""
        pass
    
    @abstractmethod
    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for creating a span."""
        pass
    
    @abstractmethod
    def inject(self, carrier: Dict[str, Any], context: Optional[SpanContext] = None) -> None:
        """Inject trace context into a carrier."""
        pass
    
    @abstractmethod
    def extract(self, carrier: Dict[str, Any]) -> Optional[SpanContext]:
        """Extract trace context from a carrier."""
        pass


class InMemorySpan(ISpan):
    """In-memory implementation of a span."""
    
    def __init__(
        self,
        tracer: 'InMemoryTracer',
        name: str,
        context: SpanContext,
        kind: SpanKind,
        start_time: Optional[float] = None
    ):
        """Initialize span."""
        self.tracer = tracer
        self.name = name
        self.context = context
        self.kind = kind
        self.start_time = start_time or time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status = SpanStatus.UNSET
        self.status_description: Optional[str] = None
        self.exception: Optional[Exception] = None
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        if self.end_time is not None:
            return  # Span already ended
        
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        if self.end_time is not None:
            return
        
        event = {
            'name': name,
            'timestamp': time.time(),
            'attributes': attributes or {}
        }
        self.events.append(event)
    
    def set_status(self, status: SpanStatus, description: Optional[str] = None) -> None:
        """Set the span status."""
        if self.end_time is not None:
            return
        
        self.status = status
        self.status_description = description
    
    def record_exception(self, exception: Exception) -> None:
        """Record an exception on the span."""
        if self.end_time is not None:
            return
        
        self.exception = exception
        self.set_status(SpanStatus.ERROR, str(exception))
        
        # Add exception event
        self.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
            "exception.stacktrace": self._format_stacktrace(exception)
        })
    
    def end(self) -> None:
        """End the span."""
        if self.end_time is not None:
            return
        
        self.end_time = time.time()
        self.tracer._record_span(self)
    
    def get_context(self) -> SpanContext:
        """Get the span context."""
        return self.context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            'trace_id': self.context.trace_id,
            'span_id': self.context.span_id,
            'parent_span_id': self.context.parent_span_id,
            'name': self.name,
            'kind': self.kind.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': (self.end_time - self.start_time) if self.end_time else None,
            'attributes': self.attributes,
            'events': self.events,
            'status': self.status.value,
            'status_description': self.status_description
        }
    
    def _format_stacktrace(self, exception: Exception) -> str:
        """Format exception stacktrace."""
        import traceback
        return ''.join(traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
        ))


# Thread-local storage for current span
_span_storage = threading.local()


class InMemoryTracer(ITracer):
    """
    In-memory tracer implementation.
    
    Features:
    - Thread-safe span management
    - Configurable sampling
    - Span storage and export
    """
    
    def __init__(self, config: TraceConfig):
        """Initialize tracer."""
        self.config = config
        self._lock = threading.RLock()
        self._traces: Dict[str, List[InMemorySpan]] = defaultdict(list)
        self._completed_spans: List[InMemorySpan] = []
        self._export_queue: List[InMemorySpan] = []
        
        # Start export worker
        self._export_task = None
        if config.export_interval_seconds > 0:
            self._start_export_worker()
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> ISpan:
        """Start a new span."""
        # Check sampling
        if not self._should_sample():
            # Return no-op span
            return NoOpSpan()
        
        # Get parent context
        if parent is None:
            current_span = self.get_current_span()
            if current_span:
                parent = current_span.get_context()
        
        # Create span context
        if parent:
            context = SpanContext(
                trace_id=parent.trace_id,
                span_id=self._generate_span_id(),
                parent_span_id=parent.span_id,
                trace_flags=parent.trace_flags
            )
        else:
            context = SpanContext(
                trace_id=self._generate_trace_id(),
                span_id=self._generate_span_id(),
                trace_flags=1 if self._should_sample() else 0
            )
        
        # Create span
        span = InMemorySpan(self, name, context, kind)
        
        # Set initial attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        # Set service name
        span.set_attribute("service.name", self.config.service_name)
        
        # Store in traces
        with self._lock:
            self._traces[context.trace_id].append(span)
            
            # Limit spans per trace
            if len(self._traces[context.trace_id]) > self.config.max_spans_per_trace:
                self._traces[context.trace_id].pop(0)
        
        return span
    
    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for creating a span."""
        span = self.start_span(name, kind, attributes=attributes)
        old_span = self.get_current_span()
        self.set_current_span(span)
        
        try:
            yield span
        except Exception as e:
            if self.config.record_exceptions:
                span.record_exception(e)
            raise
        finally:
            span.end()
            self.set_current_span(old_span)
    
    def inject(self, carrier: Dict[str, Any], context: Optional[SpanContext] = None) -> None:
        """Inject trace context into a carrier."""
        if context is None:
            current_span = self.get_current_span()
            if current_span:
                context = current_span.get_context()
        
        if context:
            carrier['traceparent'] = context.to_traceparent()
            
            if context.trace_state:
                carrier['tracestate'] = ','.join(
                    f"{k}={v}" for k, v in context.trace_state.items()
                )
    
    def extract(self, carrier: Dict[str, Any]) -> Optional[SpanContext]:
        """Extract trace context from a carrier."""
        traceparent = carrier.get('traceparent')
        if not traceparent:
            return None
        
        try:
            context = SpanContext.from_traceparent(traceparent)
            
            # Parse trace state
            tracestate = carrier.get('tracestate')
            if tracestate:
                for item in tracestate.split(','):
                    key, value = item.split('=', 1)
                    context.trace_state[key] = value
            
            return context
            
        except ValueError:
            return None
    
    def get_current_span(self) -> Optional[ISpan]:
        """Get the currently active span."""
        return getattr(_span_storage, 'current_span', None)
    
    def set_current_span(self, span: Optional[ISpan]) -> None:
        """Set the currently active span."""
        _span_storage.current_span = span
    
    def get_traces(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all traces as dictionaries."""
        with self._lock:
            return {
                trace_id: [span.to_dict() for span in spans]
                for trace_id, spans in self._traces.items()
            }
    
    def _record_span(self, span: InMemorySpan) -> None:
        """Record a completed span."""
        with self._lock:
            self._completed_spans.append(span)
            self._export_queue.append(span)
    
    def _should_sample(self) -> bool:
        """Determine if a trace should be sampled."""
        import random
        return random.random() < self.config.sample_rate
    
    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return uuid.uuid4().hex
    
    def _generate_span_id(self) -> str:
        """Generate a unique span ID."""
        return uuid.uuid4().hex[:16]
    
    def _start_export_worker(self) -> None:
        """Start background export worker."""
        def export_loop():
            while True:
                time.sleep(self.config.export_interval_seconds)
                self._export_spans()
        
        self._export_task = threading.Thread(
            target=export_loop,
            daemon=True
        )
        self._export_task.start()
    
    def _export_spans(self) -> None:
        """Export completed spans."""
        with self._lock:
            if not self._export_queue:
                return
            
            # Get batch
            batch = self._export_queue[:self.config.export_batch_size]
            self._export_queue = self._export_queue[self.config.export_batch_size:]
            
        # In production, would send to tracing backend
        # For now, just log
        if batch:
            print(f"Exporting {len(batch)} spans")


class NoOpSpan(ISpan):
    """No-operation span for when sampling is disabled."""
    
    def set_attribute(self, key: str, value: Any) -> None:
        pass
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        pass
    
    def set_status(self, status: SpanStatus, description: Optional[str] = None) -> None:
        pass
    
    def record_exception(self, exception: Exception) -> None:
        pass
    
    def end(self) -> None:
        pass
    
    def get_context(self) -> SpanContext:
        return SpanContext(
            trace_id="00000000000000000000000000000000",
            span_id="0000000000000000"
        )


# Global tracer
_tracer: Optional[ITracer] = None


def configure_tracing(
    app_name: str = "liap-tui",
    config: Optional[TraceConfig] = None
) -> None:
    """Configure global tracing."""
    global _tracer
    
    if config is None:
        config = TraceConfig(service_name=app_name)
    
    _tracer = InMemoryTracer(config)


def get_tracer() -> ITracer:
    """Get the global tracer."""
    if _tracer is None:
        configure_tracing()
    
    return _tracer


def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
) -> ISpan:
    """Create a new span."""
    return get_tracer().start_span(name, kind, attributes=attributes)


def inject_context(carrier: Dict[str, Any]) -> None:
    """Inject current trace context into carrier."""
    get_tracer().inject(carrier)


def extract_context(carrier: Dict[str, Any]) -> Optional[SpanContext]:
    """Extract trace context from carrier."""
    return get_tracer().extract(carrier)


def trace(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    Decorator for tracing functions.
    
    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        attributes: Initial span attributes
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.span(span_name, kind, attributes) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.span(span_name, kind, attributes) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# OpenTelemetry compatibility layer

class OpenTelemetryTracer(ITracer):
    """
    OpenTelemetry-compatible tracer.
    
    This is a placeholder for when OpenTelemetry SDK is available.
    """
    
    def __init__(self, config: TraceConfig):
        """Initialize OpenTelemetry tracer."""
        # In production, would initialize OpenTelemetry SDK
        self._fallback = InMemoryTracer(config)
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> ISpan:
        """Start a new span."""
        # In production, would use OpenTelemetry API
        return self._fallback.start_span(name, kind, parent, attributes)
    
    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Context manager for creating a span."""
        # In production, would use OpenTelemetry API
        with self._fallback.span(name, kind, attributes) as span:
            yield span
    
    def inject(self, carrier: Dict[str, Any], context: Optional[SpanContext] = None) -> None:
        """Inject trace context into a carrier."""
        self._fallback.inject(carrier, context)
    
    def extract(self, carrier: Dict[str, Any]) -> Optional[SpanContext]:
        """Extract trace context from a carrier."""
        return self._fallback.extract(carrier)