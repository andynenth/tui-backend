// frontend/src/utils/performanceMonitor.js
/**
 * Enhanced performance monitoring for mobile bundle optimization
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = [];
    this.startTime = performance.now();
    this.bundleLoadTime = null;
    this.chunkLoadTimes = new Map();
    this.initialized = false;
  }

  init() {
    if (this.initialized) return;

    this.trackBundleLoading();
    this.trackChunkLoading();
    this.trackPageVisibility();
    this.trackMemoryUsage();

    this.initialized = true;
    console.log('📊 Performance monitor initialized');
  }

  trackBundleLoading() {
    // Track main bundle load time
    if (window.telemetry) {
      window.telemetry.log('bundle_performance_start', {
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        connection: navigator.connection ? {
          effectiveType: navigator.connection.effectiveType,
          downlink: navigator.connection.downlink,
          rtt: navigator.connection.rtt
        } : null
      });
    }

    // Monitor resource loading
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name.includes('bundle.js')) {
            this.bundleLoadTime = entry.duration;
            this.reportMetric('main_bundle_load', entry.duration, {
              transferSize: entry.transferSize,
              encodedBodySize: entry.encodedBodySize,
              decodedBodySize: entry.decodedBodySize
            });
          } else if (entry.name.includes('chunks/')) {
            const chunkName = this.extractChunkName(entry.name);
            this.chunkLoadTimes.set(chunkName, entry.duration);
            this.reportMetric('chunk_load', entry.duration, {
              chunkName,
              transferSize: entry.transferSize
            });
          }
        }
      });

      observer.observe({ entryTypes: ['resource'] });
    }
  }

  trackChunkLoading() {
    // Track dynamic imports (code splitting)
    const originalImport = window.__import__ || (async (specifier) => import(specifier));

    window.__import__ = async (specifier) => {
      const startTime = performance.now();

      try {
        const result = await originalImport(specifier);
        const loadTime = performance.now() - startTime;

        this.reportMetric('dynamic_import', loadTime, {
          specifier,
          success: true
        });

        return result;
      } catch (error) {
        const loadTime = performance.now() - startTime;

        this.reportMetric('dynamic_import', loadTime, {
          specifier,
          success: false,
          error: error.message
        });

        throw error;
      }
    };
  }

  trackPageVisibility() {
    document.addEventListener('visibilitychange', () => {
      this.reportMetric('page_visibility_change', performance.now(), {
        hidden: document.hidden,
        visibilityState: document.visibilityState
      });
    });
  }

  trackMemoryUsage() {
    if ('memory' in performance) {
      setInterval(() => {
        this.reportMetric('memory_usage', performance.now(), {
          usedJSHeapSize: Math.round(performance.memory.usedJSHeapSize / 1048576), // MB
          totalJSHeapSize: Math.round(performance.memory.totalJSHeapSize / 1048576), // MB
          jsHeapSizeLimit: Math.round(performance.memory.jsHeapSizeLimit / 1048576) // MB
        });
      }, 30000); // Every 30 seconds
    }
  }

  reportMetric(name, value, metadata = {}) {
    const metric = {
      name,
      value,
      timestamp: Date.now(),
      elapsed: performance.now() - this.startTime,
      metadata,
      // Context information
      url: window.location.pathname,
      userAgent: navigator.userAgent,
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      } : null
    };

    this.metrics.push(metric);

    // Send to telemetry if available
    if (window.telemetry) {
      window.telemetry.log('performance_metric', metric);
    }

    // Log significant metrics
    if (this.shouldLogMetric(name, value)) {
      console.log(`📊 Performance: ${name} = ${value.toFixed(2)}ms`, metadata);
    }
  }

  shouldLogMetric(name, value) {
    switch (name) {
      case 'main_bundle_load':
        return value > 1000; // Log if > 1s
      case 'chunk_load':
        return value > 500; // Log if > 500ms
      case 'dynamic_import':
        return value > 200; // Log if > 200ms
      default:
        return false;
    }
  }

  extractChunkName(url) {
    const match = url.match(/chunks\/([^-]+)/);
    return match ? match[1] : 'unknown';
  }

  getPerformanceSummary() {
    const summary = {
      bundleLoadTime: this.bundleLoadTime,
      chunkCount: this.chunkLoadTimes.size,
      averageChunkLoadTime: this.chunkLoadTimes.size > 0
        ? Array.from(this.chunkLoadTimes.values()).reduce((a, b) => a + b, 0) / this.chunkLoadTimes.size
        : 0,
      totalMetrics: this.metrics.length,
      sessionDuration: performance.now() - this.startTime
    };

    return summary;
  }

  // Mobile-specific performance tracking
  trackMobilePerformance() {
    if (this.isMobile()) {
      // Track mobile-specific metrics
      this.reportMetric('mobile_detection', performance.now(), {
        isMobile: true,
        screenWidth: screen.width,
        screenHeight: screen.height,
        devicePixelRatio: window.devicePixelRatio,
        orientation: screen.orientation?.type || 'unknown'
      });

      // Track touch interactions
      let touchStartTime = 0;
      document.addEventListener('touchstart', () => {
        touchStartTime = performance.now();
      });

      document.addEventListener('touchend', () => {
        if (touchStartTime > 0) {
          const touchDuration = performance.now() - touchStartTime;
          this.reportMetric('touch_interaction', touchDuration);
        }
      });
    }
  }

  isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  // Export metrics for analysis
  exportMetrics() {
    return {
      summary: this.getPerformanceSummary(),
      metrics: this.metrics,
      chunkLoadTimes: Object.fromEntries(this.chunkLoadTimes)
    };
  }
}

// Create global instance
const performanceMonitor = new PerformanceMonitor();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    performanceMonitor.init();
    performanceMonitor.trackMobilePerformance();
  });
} else {
  performanceMonitor.init();
  performanceMonitor.trackMobilePerformance();
}

export default performanceMonitor;

// Global access for debugging
window.performanceMonitor = performanceMonitor;
