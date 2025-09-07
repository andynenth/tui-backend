// frontend/src/utils/telemetryService.js
/**
 * Enhanced React App Telemetry Service
 * Comprehensive client-side telemetry for performance and error tracking
 */

class TelemetryService {
  constructor() {
    this.queue = [];
    this.batchSize = 10;
    this.flushInterval = 30000; // 30 seconds
    this.sessionStart = Date.now();

    // Inherit session from initial page load telemetry
    this.sessionId = window.telemetry?.sessionId || Math.random().toString(36).substring(7);

    // Initialize tracking
    this.init();
  }

  init() {
    this.startBatchTimer();
    this.trackRouteChanges();
    this.trackUnhandledErrors();
    this.trackLongTasks();
    this.trackResourceLoading();

    console.log('📊 React Telemetry Service initialized');
  }

  track(event, data = {}) {
    const entry = {
      timestamp: Date.now(),
      elapsed: Date.now() - this.sessionStart,
      event,
      ...data,
      // React-specific context
      route: window.location.pathname,
      reactVersion: '19.1.0', // From package.json
      // Memory usage if available
      memory: performance.memory ? {
        usedJSHeapSize: Math.round(performance.memory.usedJSHeapSize / 1048576),
        totalJSHeapSize: Math.round(performance.memory.totalJSHeapSize / 1048576),
        jsHeapSizeLimit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
      } : null,
      // Network state
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt,
        saveData: navigator.connection.saveData
      } : null,
      // Viewport context
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
        pixelRatio: window.devicePixelRatio
      }
    };

    this.queue.push(entry);

    // Send critical events immediately
    if (this.isCriticalEvent(event)) {
      this.flush();
    } else if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }

  isCriticalEvent(event) {
    return [
      'app_error', 'component_error', 'chunk_load_failed',
      'websocket_error', 'game_error', 'fatal_error'
    ].includes(event);
  }

  trackError(error, context = {}) {
    this.track('app_error', {
      message: error.message,
      stack: error.stack,
      name: error.name,
      ...context
    });
  }

  trackComponentError(error, errorInfo, componentName) {
    this.track('component_error', {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      componentName,
      errorBoundary: true
    });
  }

  trackPerformance(metric, value, metadata = {}) {
    this.track('performance_metric', {
      metric,
      value,
      ...metadata
    });
  }

  trackUserInteraction(action, target, metadata = {}) {
    this.track('user_interaction', {
      action, // click, scroll, input, etc.
      target, // button, form, game-board, etc.
      ...metadata
    });
  }

  trackChunkLoad(chunkName, loadTime, success = true, error = null) {
    this.track(success ? 'chunk_load_success' : 'chunk_load_failed', {
      chunkName,
      loadTime,
      success,
      error: error?.message
    });
  }

  trackGameEvent(eventType, gameData = {}) {
    this.track('game_event', {
      eventType,
      ...gameData
    });
  }

  trackWebSocketEvent(eventType, data = {}) {
    this.track('websocket_event', {
      eventType,
      ...data
    });
  }

  trackRouteChanges() {
    let currentRoute = window.location.pathname;

    // Track initial route
    this.track('route_visit', {
      route: currentRoute,
      isInitial: true
    });

    // Listen for route changes (React Router)
    const trackRoute = () => {
      const newRoute = window.location.pathname;
      if (newRoute !== currentRoute) {
        this.track('route_change', {
          from: currentRoute,
          to: newRoute,
          method: 'navigation'
        });
        currentRoute = newRoute;
      }
    };

    // Multiple ways to detect route changes
    window.addEventListener('popstate', trackRoute);

    // Override pushState and replaceState to catch programmatic navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      setTimeout(trackRoute, 0);
    };

    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      setTimeout(trackRoute, 0);
    };
  }

  trackUnhandledErrors() {
    // Global error handler (if not already handled by page-level telemetry)
    window.addEventListener('error', (e) => {
      this.track('javascript_error', {
        message: e.message,
        filename: e.filename,
        line: e.lineno,
        column: e.colno,
        stack: e.error?.stack,
        source: 'react_app'
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (e) => {
      this.track('unhandled_rejection', {
        reason: e.reason?.toString(),
        promise: e.promise?.toString(),
        source: 'react_app'
      });
    });
  }

  trackLongTasks() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            // Track tasks longer than 50ms (blocking)
            if (entry.duration > 50) {
              this.track('long_task', {
                duration: entry.duration,
                startTime: entry.startTime,
                name: entry.name || 'unknown'
              });
            }
          }
        });

        observer.observe({ entryTypes: ['longtask'] });
      } catch (error) {
        console.warn('Long task observer not supported:', error);
      }
    }
  }

  trackResourceLoading() {
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          // Track chunk loading
          if (entry.name.includes('/chunks/')) {
            const chunkName = this.extractChunkName(entry.name);
            this.trackChunkLoad(chunkName, entry.duration, true);
          }

          // Track slow resources (> 2s)
          if (entry.duration > 2000) {
            this.track('slow_resource', {
              url: entry.name,
              duration: entry.duration,
              transferSize: entry.transferSize,
              type: this.getResourceType(entry.name)
            });
          }
        }
      });

      observer.observe({ entryTypes: ['resource'] });
    }
  }

  extractChunkName(url) {
    const match = url.match(/chunks\/([^-]+)/);
    return match ? match[1] : 'unknown';
  }

  getResourceType(url) {
    if (url.includes('.js')) return 'javascript';
    if (url.includes('.css')) return 'stylesheet';
    if (url.includes('.png') || url.includes('.jpg') || url.includes('.svg')) return 'image';
    return 'other';
  }

  flush() {
    if (this.queue.length === 0) return;

    const events = [...this.queue];
    this.queue = [];

    // Send to backend
    this.send(events);
  }

  send(events) {
    const payload = {
      sessionId: this.sessionId,
      events
    };

    // Use sendBeacon if available (more reliable for page unload)
    if (navigator.sendBeacon) {
      const success = navigator.sendBeacon(
        '/api/telemetry',
        JSON.stringify(payload)
      );
      if (success) return;
    }

    // Fallback to fetch
    fetch('/api/telemetry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true
    }).catch(error => {
      // Re-queue events on failure
      this.queue.unshift(...events);
      console.warn('Telemetry send failed:', error);
    });
  }

  startBatchTimer() {
    setInterval(() => this.flush(), this.flushInterval);

    // Flush before page unload
    window.addEventListener('beforeunload', () => {
      this.track('react_app_unload', {
        sessionDuration: Date.now() - this.sessionStart,
        eventsCollected: this.queue.length
      });
      this.flush();
    });
  }

  // Mobile-specific tracking
  trackMobileInteractions() {
    if (this.isMobile()) {
      let touchStart = null;

      document.addEventListener('touchstart', (e) => {
        touchStart = {
          timestamp: Date.now(),
          x: e.touches[0].clientX,
          y: e.touches[0].clientY
        };
      });

      document.addEventListener('touchend', (e) => {
        if (touchStart) {
          const touchDuration = Date.now() - touchStart.timestamp;
          const touchEnd = e.changedTouches[0];

          this.track('mobile_touch', {
            duration: touchDuration,
            startX: touchStart.x,
            startY: touchStart.y,
            endX: touchEnd.clientX,
            endY: touchEnd.clientY,
            distance: Math.sqrt(
              Math.pow(touchEnd.clientX - touchStart.x, 2) +
              Math.pow(touchEnd.clientY - touchStart.y, 2)
            )
          });
        }
      });

      // Track orientation changes
      window.addEventListener('orientationchange', () => {
        setTimeout(() => {
          this.track('orientation_change', {
            orientation: screen.orientation?.type || window.orientation,
            viewport: {
              width: window.innerWidth,
              height: window.innerHeight
            }
          });
        }, 100);
      });
    }
  }

  isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  // Utility method to get session summary
  getSessionSummary() {
    return {
      sessionId: this.sessionId,
      sessionDuration: Date.now() - this.sessionStart,
      eventsQueued: this.queue.length,
      route: window.location.pathname,
      memory: performance.memory ? {
        used: Math.round(performance.memory.usedJSHeapSize / 1048576),
        total: Math.round(performance.memory.totalJSHeapSize / 1048576)
      } : null
    };
  }
}

// Create singleton instance
export const telemetryService = new TelemetryService();

// Initialize mobile tracking if on mobile device
if (telemetryService.isMobile()) {
  telemetryService.trackMobileInteractions();
}

// Global access for debugging
window.telemetryService = telemetryService;

export default telemetryService;
