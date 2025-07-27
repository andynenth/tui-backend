"""
Specific middleware implementations for common cross-cutting concerns.

Provides ready-to-use middleware for correlation, validation, security, etc.
"""

from typing import TypeVar, Callable, Optional, Dict, Any, List, Set
from dataclasses import dataclass
import asyncio
import gzip
import json
import hashlib
import time
from datetime import datetime, timedelta

from .base import IMiddleware, MiddlewareContext
from ..monitoring.correlation import get_correlation_id, set_correlation_id
from ..resilience.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
from ..resilience.retry import Retry, RetryConfig
from ..caching.cache_manager import get_cache_manager
from ..observability.metrics import get_metrics_collector


TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class CorrelationIdMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for correlation ID propagation.
    
    Ensures all requests have a correlation ID for tracking.
    """
    
    def __init__(
        self,
        header_name: str = "X-Correlation-ID",
        generate_if_missing: bool = True
    ):
        """Initialize correlation middleware."""
        self.header_name = header_name
        self.generate_if_missing = generate_if_missing
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with correlation ID."""
        # Try to get correlation ID from request
        correlation_id = None
        if hasattr(request, 'headers'):
            correlation_id = request.headers.get(self.header_name)
        
        # Use existing or generate new
        if not correlation_id:
            correlation_id = get_correlation_id()
            if not correlation_id and self.generate_if_missing:
                correlation_id = set_correlation_id()
        else:
            set_correlation_id(correlation_id)
        
        # Add to context
        context.correlation_id = correlation_id
        
        try:
            # Process request
            response = await next_handler(request, context)
            
            # Add correlation ID to response if possible
            if hasattr(response, 'headers'):
                response.headers[self.header_name] = correlation_id
            
            return response
            
        finally:
            # Clear correlation context
            from ..monitoring.correlation import clear_correlation
            clear_correlation()


class RequestTimingMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for detailed request timing with metrics.
    
    Records timing metrics for monitoring.
    """
    
    def __init__(self, metric_prefix: str = "request"):
        """Initialize timing middleware."""
        self.metric_prefix = metric_prefix
        self.metrics = get_metrics_collector()
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with timing."""
        timer = self.metrics.timer(f"{self.metric_prefix}.duration")
        
        # Get request path if available
        path = "unknown"
        if hasattr(request, 'path'):
            path = request.path
        elif hasattr(request, 'url'):
            path = str(request.url.path)
        
        start_time = time.perf_counter()
        
        try:
            with timer.time():
                response = await next_handler(request, context)
            
            # Record success
            self.metrics.increment(f"{self.metric_prefix}.success", tags=[
                ("path", path),
                ("method", getattr(request, 'method', 'unknown'))
            ])
            
            return response
            
        except Exception as e:
            # Record failure
            self.metrics.increment(f"{self.metric_prefix}.error", tags=[
                ("path", path),
                ("method", getattr(request, 'method', 'unknown')),
                ("error", type(e).__name__)
            ])
            raise
        
        finally:
            # Record timing
            elapsed = time.perf_counter() - start_time
            context.add_metadata('request_duration_seconds', elapsed)


class ValidationMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for request validation.
    
    Validates requests against configured rules.
    """
    
    def __init__(self, validators: Optional[List[Callable]] = None):
        """Initialize validation middleware."""
        self.validators = validators or []
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with validation."""
        # Run validators
        for validator in self.validators:
            try:
                if asyncio.iscoroutinefunction(validator):
                    await validator(request, context)
                else:
                    validator(request, context)
            except Exception as e:
                context.add_error(e)
                context.add_metadata('validation_error', str(e))
                raise
        
        # Process valid request
        return await next_handler(request, context)
    
    def add_validator(self, validator: Callable) -> None:
        """Add validator to middleware."""
        self.validators.append(validator)


class ResponseCompressionMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for response compression.
    
    Compresses responses based on Accept-Encoding header.
    """
    
    def __init__(
        self,
        min_size: int = 1024,
        compression_level: int = 6
    ):
        """Initialize compression middleware."""
        self.min_size = min_size
        self.compression_level = compression_level
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with response compression."""
        # Check if client accepts compression
        accept_encoding = ""
        if hasattr(request, 'headers'):
            accept_encoding = request.headers.get('Accept-Encoding', '')
        
        # Process request
        response = await next_handler(request, context)
        
        # Check if should compress
        if 'gzip' in accept_encoding and hasattr(response, 'body'):
            body = response.body
            
            # Check size threshold
            if isinstance(body, (str, bytes)) and len(body) >= self.min_size:
                # Compress body
                if isinstance(body, str):
                    body = body.encode('utf-8')
                
                compressed = gzip.compress(body, compresslevel=self.compression_level)
                
                # Update response
                response.body = compressed
                if hasattr(response, 'headers'):
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Content-Length'] = str(len(compressed))
                
                context.add_metadata('response_compressed', True)
                context.add_metadata('compression_ratio', len(compressed) / len(body))
        
        return response


class SecurityHeadersMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for adding security headers.
    
    Adds common security headers to responses.
    """
    
    def __init__(self, custom_headers: Optional[Dict[str, str]] = None):
        """Initialize security headers middleware."""
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'"
        }
        
        if custom_headers:
            self.headers.update(custom_headers)
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with security headers."""
        # Process request
        response = await next_handler(request, context)
        
        # Add security headers
        if hasattr(response, 'headers'):
            for header, value in self.headers.items():
                if header not in response.headers:
                    response.headers[header] = value
        
        return response


class RequestDeduplicationMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for request deduplication.
    
    Prevents duplicate request processing within a time window.
    """
    
    def __init__(
        self,
        cache_ttl: timedelta = timedelta(seconds=60),
        key_extractor: Optional[Callable[[TRequest], str]] = None
    ):
        """Initialize deduplication middleware."""
        self.cache_ttl = cache_ttl
        self.key_extractor = key_extractor or self._default_key_extractor
        self.cache = get_cache_manager().get_cache("deduplication")
        self._pending_requests: Dict[str, asyncio.Future] = {}
    
    def _default_key_extractor(self, request: TRequest) -> str:
        """Extract cache key from request."""
        # Create key from request attributes
        parts = []
        
        if hasattr(request, 'method'):
            parts.append(request.method)
        
        if hasattr(request, 'path'):
            parts.append(request.path)
        elif hasattr(request, 'url'):
            parts.append(str(request.url))
        
        if hasattr(request, 'body'):
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8', errors='ignore')
            parts.append(hashlib.md5(str(body).encode()).hexdigest())
        
        return ':'.join(parts)
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with deduplication."""
        # Get cache key
        cache_key = self.key_extractor(request)
        
        # Check if request is already pending
        if cache_key in self._pending_requests:
            context.add_metadata('deduplicated', True)
            # Wait for pending request
            return await self._pending_requests[cache_key]
        
        # Check cache
        cached_response = await self.cache.get(cache_key)
        if cached_response is not None:
            context.add_metadata('cache_hit', True)
            return cached_response
        
        # Create future for pending request
        future = asyncio.Future()
        self._pending_requests[cache_key] = future
        
        try:
            # Process request
            response = await next_handler(request, context)
            
            # Cache response
            await self.cache.set(
                cache_key,
                response,
                ttl=int(self.cache_ttl.total_seconds())
            )
            
            # Complete future
            future.set_result(response)
            
            return response
            
        except Exception as e:
            # Complete future with exception
            future.set_exception(e)
            raise
            
        finally:
            # Remove from pending
            self._pending_requests.pop(cache_key, None)


class CircuitBreakerMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for circuit breaker pattern.
    
    Protects against cascading failures.
    """
    
    def __init__(
        self,
        name: str = "default",
        config: Optional[CircuitBreakerConfig] = None
    ):
        """Initialize circuit breaker middleware."""
        self.circuit_breaker = get_circuit_breaker(name, config)
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with circuit breaker."""
        # Add circuit breaker state to context
        context.add_metadata('circuit_breaker_state', self.circuit_breaker.state.value)
        
        # Execute with circuit breaker
        return await self.circuit_breaker.call_async(
            next_handler,
            request,
            context
        )


class RetryMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for retry logic.
    
    Retries failed requests with configurable backoff.
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry middleware."""
        self.retry = Retry(config)
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with retry."""
        # Add retry attempt to context
        attempt = 0
        
        async def handler_with_context(req: TRequest, ctx: MiddlewareContext) -> TResponse:
            nonlocal attempt
            attempt += 1
            ctx.add_metadata('retry_attempt', attempt)
            return await next_handler(req, ctx)
        
        # Execute with retry
        response = await self.retry.execute_async(
            handler_with_context,
            request,
            context
        )
        
        # Add retry stats to context
        stats = self.retry.get_stats()
        context.add_metadata('retry_stats', stats)
        
        return response


class RateLimitMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Middleware for rate limiting.
    
    Limits request rate per client or globally.
    """
    
    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: int = 20,
        key_extractor: Optional[Callable[[TRequest], str]] = None
    ):
        """Initialize rate limit middleware."""
        from ..caching.rate_limiter import TokenBucketRateLimiter
        
        self.rate_limiter = TokenBucketRateLimiter(
            rate=requests_per_second,
            capacity=burst_size
        )
        self.key_extractor = key_extractor or self._default_key_extractor
    
    def _default_key_extractor(self, request: TRequest) -> str:
        """Extract rate limit key from request."""
        # Try to get client IP
        if hasattr(request, 'client'):
            return f"ip:{request.client.host}"
        elif hasattr(request, 'remote_addr'):
            return f"ip:{request.remote_addr}"
        else:
            return "global"
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with rate limiting."""
        # Get rate limit key
        key = self.key_extractor(request)
        
        # Check rate limit
        allowed = await self.rate_limiter.allow_request(key)
        
        if not allowed:
            context.add_metadata('rate_limited', True)
            raise Exception("Rate limit exceeded")
        
        # Process request
        return await next_handler(request, context)


class MetricsMiddleware(IMiddleware[TRequest, TResponse]):
    """
    Comprehensive metrics collection middleware.
    
    Collects detailed metrics for monitoring.
    """
    
    def __init__(self, service_name: str = "api"):
        """Initialize metrics middleware."""
        self.service_name = service_name
        self.metrics = get_metrics_collector()
    
    async def process(
        self,
        request: TRequest,
        context: MiddlewareContext,
        next_handler: Callable[[TRequest, MiddlewareContext], TResponse]
    ) -> TResponse:
        """Process request with metrics collection."""
        # Extract request info
        method = getattr(request, 'method', 'unknown')
        path = getattr(request, 'path', 'unknown')
        
        # Record request
        self.metrics.increment(f"{self.service_name}.requests", tags=[
            ("method", method),
            ("path", path)
        ])
        
        # Time request
        timer = self.metrics.timer(f"{self.service_name}.request_duration")
        
        try:
            with timer.time():
                response = await next_handler(request, context)
            
            # Record response
            status = getattr(response, 'status_code', 200)
            self.metrics.increment(f"{self.service_name}.responses", tags=[
                ("method", method),
                ("path", path),
                ("status", str(status))
            ])
            
            return response
            
        except Exception as e:
            # Record error
            self.metrics.increment(f"{self.service_name}.errors", tags=[
                ("method", method),
                ("path", path),
                ("error", type(e).__name__)
            ])
            raise