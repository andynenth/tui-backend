"""
OpenTelemetry tracing integration for state machines.

Provides distributed tracing capabilities for state transitions,
action processing, and system operations.
"""

from typing import Dict, Any, Optional, List, Callable, ContextManager
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, field
import uuid
import asyncio
from enum import Enum

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.sdk.trace import TracerProvider, Tracer
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Provide fallback implementations
    trace = None
    Status = StatusCode = Span = None
    TracerProvider = Tracer = None
    BatchSpanProcessor = ConsoleSpanExporter = None
    Resource = None
    PrometheusMetricsExporter = None


class SpanKind(Enum):
    """Types of spans for different operations."""
    STATE_TRANSITION = "state_transition"
    ACTION_PROCESSING = "action_processing"
    PHASE_EXECUTION = "phase_execution"
    WEBSOCKET_MESSAGE = "websocket_message"
    DATABASE_OPERATION = "database_operation"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class TraceContext:
    """Context for distributed tracing."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    correlation_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    def child_context(self) -> 'TraceContext':
        """Create child context."""
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=self.span_id,
            correlation_id=self.correlation_id,
            baggage=self.baggage.copy()
        )


class MockSpan:
    """Mock span implementation when OpenTelemetry is not available."""
    
    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        self.events = []
        self.status = None
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add event to span."""
        self.events.append({
            'name': name,
            'attributes': attributes or {},
            'timestamp': datetime.utcnow()
        })
    
    def set_status(self, status: Any) -> None:
        """Set span status."""
        self.status = status
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class StateTracer:
    """
    Distributed tracing for state machines.
    
    Features:
    - State transition tracing
    - Action processing spans
    - Performance measurement
    - Error tracking
    - Correlation ID propagation
    """
    
    def __init__(
        self,
        service_name: str = "liap-tui",
        enable_console_export: bool = False
    ):
        """Initialize state tracer."""
        self.service_name = service_name
        self._tracer = None
        self._trace_contexts: Dict[str, TraceContext] = {}
        
        if OTEL_AVAILABLE:
            self._setup_tracing(enable_console_export)
        else:
            print("OpenTelemetry not available, using mock tracing")
    
    def _setup_tracing(self, enable_console_export: bool) -> None:
        """Set up OpenTelemetry tracing."""
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add span processor
        if enable_console_export:
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer
        self._tracer = trace.get_tracer(__name__)
    
    def get_tracer(self) -> Any:
        """Get tracer instance."""
        if self._tracer:
            return self._tracer
        
        # Return mock tracer
        return self
    
    def start_span(self, name: str, kind: SpanKind = SpanKind.STATE_TRANSITION) -> Any:
        """Start a new span."""
        if self._tracer:
            return self._tracer.start_span(
                name,
                kind=trace.SpanKind.INTERNAL,
                attributes={"span.kind": kind.value}
            )
        
        return MockSpan(name)
    
    @contextmanager
    def trace_state_transition(
        self,
        game_id: str,
        from_state: str,
        to_state: str,
        context: Optional[TraceContext] = None
    ) -> ContextManager[Any]:
        """Trace a state transition."""
        span_name = f"state_transition.{from_state}_to_{to_state}"
        
        with self.start_span(span_name, SpanKind.STATE_TRANSITION) as span:
            # Set attributes
            span.set_attribute("game.id", game_id)
            span.set_attribute("state.from", from_state)
            span.set_attribute("state.to", to_state)
            
            if context:
                span.set_attribute("trace.id", context.trace_id)
                span.set_attribute("correlation.id", context.correlation_id or "")
                
                # Add baggage
                for key, value in context.baggage.items():
                    span.set_attribute(f"baggage.{key}", value)
            
            try:
                yield span
                
                # Success event
                span.add_event("state_transition_completed", {
                    "from_state": from_state,
                    "to_state": to_state
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Error event
                span.add_event("state_transition_failed", {
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(
                        Status(StatusCode.ERROR, f"Transition failed: {str(e)}")
                    )
                
                raise
    
    @contextmanager
    def trace_action_processing(
        self,
        game_id: str,
        action_type: str,
        player_id: str,
        context: Optional[TraceContext] = None
    ) -> ContextManager[Any]:
        """Trace action processing."""
        span_name = f"action.{action_type}"
        
        with self.start_span(span_name, SpanKind.ACTION_PROCESSING) as span:
            # Set attributes
            span.set_attribute("game.id", game_id)
            span.set_attribute("action.type", action_type)
            span.set_attribute("player.id", player_id)
            
            if context:
                span.set_attribute("trace.id", context.trace_id)
                span.set_attribute("parent.span.id", context.parent_span_id or "")
            
            try:
                yield span
                
                span.add_event("action_processed", {
                    "action_type": action_type,
                    "player_id": player_id
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                span.add_event("action_failed", {
                    "error": str(e),
                    "action_type": action_type
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(
                        Status(StatusCode.ERROR, f"Action failed: {str(e)}")
                    )
                
                raise
    
    @contextmanager
    def trace_phase_execution(
        self,
        game_id: str,
        phase: str,
        context: Optional[TraceContext] = None
    ) -> ContextManager[Any]:
        """Trace phase execution."""
        span_name = f"phase.{phase}"
        
        with self.start_span(span_name, SpanKind.PHASE_EXECUTION) as span:
            span.set_attribute("game.id", game_id)
            span.set_attribute("phase.name", phase)
            
            if context:
                span.set_attribute("trace.id", context.trace_id)
            
            start_time = datetime.utcnow()
            
            try:
                yield span
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                span.set_attribute("phase.duration_seconds", duration)
                
                span.add_event("phase_completed", {
                    "phase": phase,
                    "duration_seconds": duration
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                span.add_event("phase_failed", {
                    "error": str(e),
                    "phase": phase
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(
                        Status(StatusCode.ERROR, f"Phase failed: {str(e)}")
                    )
                
                raise
    
    def create_trace_context(
        self,
        correlation_id: Optional[str] = None,
        parent_context: Optional[TraceContext] = None
    ) -> TraceContext:
        """Create a new trace context."""
        if parent_context:
            context = parent_context.child_context()
        else:
            context = TraceContext(correlation_id=correlation_id)
        
        # Store context
        self._trace_contexts[context.trace_id] = context
        
        return context
    
    def get_trace_context(self, trace_id: str) -> Optional[TraceContext]:
        """Get trace context by ID."""
        return self._trace_contexts.get(trace_id)
    
    def propagate_context(
        self,
        context: TraceContext,
        carrier: Dict[str, Any]
    ) -> None:
        """Propagate trace context to carrier."""
        carrier['trace_id'] = context.trace_id
        carrier['span_id'] = context.span_id
        carrier['parent_span_id'] = context.parent_span_id
        carrier['correlation_id'] = context.correlation_id
        
        # Add baggage with prefix
        for key, value in context.baggage.items():
            carrier[f'baggage_{key}'] = value
    
    def extract_context(self, carrier: Dict[str, Any]) -> Optional[TraceContext]:
        """Extract trace context from carrier."""
        trace_id = carrier.get('trace_id')
        if not trace_id:
            return None
        
        # Extract baggage
        baggage = {}
        for key, value in carrier.items():
            if key.startswith('baggage_'):
                baggage_key = key[8:]  # Remove 'baggage_' prefix
                baggage[baggage_key] = value
        
        return TraceContext(
            trace_id=trace_id,
            span_id=carrier.get('span_id', str(uuid.uuid4())),
            parent_span_id=carrier.get('parent_span_id'),
            correlation_id=carrier.get('correlation_id'),
            baggage=baggage
        )
    
    async def trace_async_operation(
        self,
        operation_name: str,
        operation: Callable,
        context: Optional[TraceContext] = None,
        **kwargs
    ) -> Any:
        """Trace an async operation."""
        with self.start_span(operation_name) as span:
            if context:
                span.set_attribute("trace.id", context.trace_id)
            
            # Add kwargs as attributes
            for key, value in kwargs.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"param.{key}", value)
            
            try:
                result = await operation(**kwargs)
                
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))
                
                return result
                
            except Exception as e:
                span.add_event("operation_failed", {
                    "error": str(e),
                    "operation": operation_name
                })
                
                if OTEL_AVAILABLE:
                    span.set_status(
                        Status(StatusCode.ERROR, f"Operation failed: {str(e)}")
                    )
                
                raise
    
    def get_active_traces(self) -> List[Dict[str, Any]]:
        """Get information about active traces."""
        return [
            {
                'trace_id': context.trace_id,
                'correlation_id': context.correlation_id,
                'span_count': 1,  # Would need to track this
                'start_time': None  # Would need to track this
            }
            for context in self._trace_contexts.values()
        ]
    
    def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """Clean up old trace contexts."""
        # In a real implementation, would track creation time
        # and clean up based on age
        old_count = len(self._trace_contexts)
        # For now, just clear if too many
        if old_count > 10000:
            self._trace_contexts.clear()
            return old_count
        return 0


# Global tracer instance
_global_tracer: Optional[StateTracer] = None


def get_tracer() -> StateTracer:
    """Get global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = StateTracer()
    return _global_tracer


def configure_tracing(
    service_name: str = "liap-tui",
    enable_console_export: bool = False
) -> StateTracer:
    """Configure global tracing."""
    global _global_tracer
    _global_tracer = StateTracer(service_name, enable_console_export)
    return _global_tracer