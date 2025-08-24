/**
 * iOS Debug Helper
 * Provides enhanced error logging for iOS Safari debugging
 */

// Check if we're on iOS
export const isIOS = () => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
};

// Initialize error logging
export const initializeIOSDebugger = () => {
  // Override console methods to ensure they work on iOS
  const originalConsole = {
    log: console.log,
    error: console.error,
    warn: console.warn,
    info: console.info,
  };

  // Create a debug panel for iOS
  if (isIOS()) {
    const debugPanel = document.createElement('div');
    debugPanel.id = 'ios-debug-panel';
    debugPanel.style.cssText = `
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      max-height: 200px;
      overflow-y: auto;
      background: rgba(0,0,0,0.9);
      color: white;
      font-family: monospace;
      font-size: 12px;
      z-index: 99999;
      display: none;
      padding: 10px;
    `;
    document.body.appendChild(debugPanel);

    // Show debug panel on triple tap
    let tapCount = 0;
    let tapTimer = null;
    document.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        tapCount++;
        if (tapCount === 3) {
          debugPanel.style.display = debugPanel.style.display === 'none' ? 'block' : 'none';
          tapCount = 0;
        }
        clearTimeout(tapTimer);
        tapTimer = setTimeout(() => {
          tapCount = 0;
        }, 500);
      }
    });

    // Override console methods to also write to debug panel
    const logToPanel = (level, ...args) => {
      const message = args.map(arg => {
        if (typeof arg === 'object') {
          try {
            return JSON.stringify(arg, null, 2);
          } catch (e) {
            return String(arg);
          }
        }
        return String(arg);
      }).join(' ');

      const entry = document.createElement('div');
      entry.style.cssText = `
        margin: 2px 0;
        padding: 2px;
        border-left: 3px solid ${
          level === 'error' ? 'red' : 
          level === 'warn' ? 'yellow' : 
          level === 'info' ? 'blue' : 'green'
        };
        padding-left: 6px;
      `;
      entry.textContent = `[${level.toUpperCase()}] ${new Date().toTimeString().split(' ')[0]} ${message}`;
      debugPanel.appendChild(entry);
      debugPanel.scrollTop = debugPanel.scrollHeight;
    };

    // Override console methods
    console.log = (...args) => {
      originalConsole.log(...args);
      logToPanel('log', ...args);
    };

    console.error = (...args) => {
      originalConsole.error(...args);
      logToPanel('error', ...args);
    };

    console.warn = (...args) => {
      originalConsole.warn(...args);
      logToPanel('warn', ...args);
    };

    console.info = (...args) => {
      originalConsole.info(...args);
      logToPanel('info', ...args);
    };
  }

  // Global error handler
  window.addEventListener('error', (event) => {
    console.error('Global error:', {
      message: event.message,
      filename: event.filename,
      line: event.lineno,
      column: event.colno,
      error: event.error?.stack || event.error,
    });
  });

  // Unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', {
      reason: event.reason,
      promise: event.promise,
    });
  });

  // Log initial page load info
  console.log('iOS Debug Helper initialized', {
    userAgent: navigator.userAgent,
    isIOS: isIOS(),
    url: window.location.href,
    timestamp: new Date().toISOString(),
  });
};

// Log resource loading errors
export const logResourceError = (resource, error) => {
  console.error('Resource loading error:', {
    resource,
    error: error?.message || error,
    timestamp: new Date().toISOString(),
  });
};

// Log WebSocket connection info
export const logWebSocketInfo = (url, status) => {
  console.info('WebSocket connection:', {
    url,
    status,
    timestamp: new Date().toISOString(),
  });
};