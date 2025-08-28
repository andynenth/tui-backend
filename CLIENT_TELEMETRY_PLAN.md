# Client Device Telemetry and Feedback System

## Overview
Implement comprehensive client-side telemetry to understand what's happening on user devices, especially during bundle loading failures.

## Implementation Plan

### 1. Client-Side Error Tracking

#### 1.1 Enhanced Bundle Loading with Telemetry
```html
<!-- frontend/index.html - Enhanced error tracking -->
<script>
  // Client telemetry system
  const telemetry = {
    sessionId: Math.random().toString(36).substring(7),
    startTime: Date.now(),
    events: [],
    
    log(event, data) {
      const entry = {
        timestamp: Date.now(),
        elapsed: Date.now() - this.startTime,
        event,
        ...data,
        // Device context
        userAgent: navigator.userAgent,
        connection: navigator.connection ? {
          effectiveType: navigator.connection.effectiveType,
          rtt: navigator.connection.rtt,
          downlink: navigator.connection.downlink,
          saveData: navigator.connection.saveData
        } : null,
        screen: {
          width: screen.width,
          height: screen.height,
          pixelRatio: window.devicePixelRatio
        }
      };
      
      this.events.push(entry);
      
      // Send immediately for critical events
      if (event === 'bundle_error' || event === 'load_timeout') {
        this.send([entry]);
      }
    },
    
    send(events = this.events) {
      if (events.length === 0) return;
      
      // Use sendBeacon for reliability
      const data = JSON.stringify({
        sessionId: this.sessionId,
        events: events
      });
      
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/telemetry', data);
      } dangerous fallback to fetch
        fetch('/api/telemetry', {
          method: 'POST',
          body: data,
          headers: { 'Content-Type': 'application/json' },
          keepalive: true
        }).catch(() => {});
      }
      
      // Clear sent events
      this.events = this.events.filter(e => !events.includes(e));
    }
  };
  
  // Track page visibility changes
  document.addEventListener('visibilitychange', () => {
    telemetry.log('visibility_change', { hidden: document.hidden });
    if (document.hidden) {
      telemetry.send(); // Send before user leaves
    }
  });
  
  // Send telemetry before page unload
  window.addEventListener('beforeunload', () => telemetry.send());
  
  // Enhanced bundle loading with detailed tracking
  (function() {
    let retryCount = 0;
    const maxRetries = 3;
    const baseDelay = 2000;
    
    telemetry.log('page_load_start', {
      referrer: document.referrer,
      url: window.location.href
    });
    
    function loadBundle() {
      const loadStart = Date.now();
      const script = document.createElement('script');
      script.src = '/bundle.js';
      
      if (retryCount > 0) {
        script.src += '?retry=' + Date.now();
      }
      
      telemetry.log('bundle_load_attempt', {
        attempt: retryCount + 1,
        url: script.src
      });
      
      // Monitor loading progress
      let progressTimer = setInterval(() => {
        if (script.readyState) {
          telemetry.log('bundle_state_change', {
            state: script.readyState,
            elapsed: Date.now() - loadStart
          });
        }
      }, 500);
      
      script.onload = function() {
        clearInterval(progressTimer);
        const loadTime = Date.now() - loadStart;
        
        telemetry.log('bundle_load_success', {
          attempt: retryCount + 1,
          loadTime,
          size: performance.getEntriesByName(script.src)[0]?.transferSize
        });
        
        // Report performance metrics
        if (window.performance && performance.getEntriesByType) {
          const perfData = performance.getEntriesByType('resource')
            .find(entry => entry.name.includes('bundle.js'));
          
          if (perfData) {
            telemetry.log('performance_metrics', {
              dns: perfData.domainLookupEnd - perfData.domainLookupStart,
              tcp: perfData.connectEnd - perfData.connectStart,
              request: perfData.responseStart - perfData.requestStart,
              response: perfData.responseEnd - perfData.responseStart,
              total: perfData.duration,
              transferSize: perfData.transferSize,
              encodedBodySize: perfData.encodedBodySize,
              decodedBodySize: perfData.decodedBodySize
            });
          }
        }
        
        telemetry.send();
      };
      
      script.onerror = function(error) {
        clearInterval(progressTimer);
        const loadTime = Date.now() - loadStart;
        
        telemetry.log('bundle_load_error', {
          attempt: retryCount + 1,
          loadTime,
          error: error.message || 'Script load failed',
          // Try to get more error details
          readyState: script.readyState,
          status: script.getAttribute('data-status')
        });
        
        retryCount++;
        
        if (retryCount < maxRetries) {
          const delay = baseDelay * Math.pow(2, retryCount - 1);
          setTimeout(loadBundle, delay);
        } else {
          telemetry.log('bundle_load_failed', {
            totalAttempts: retryCount,
            finalError: 'Max retries exceeded'
          });
          telemetry.send();
        }
      };
      
      // Timeout detection
      setTimeout(() => {
        if (!script.loaded && script.parentNode) {
          telemetry.log('bundle_load_timeout', {
            attempt: retryCount + 1,
            elapsed: Date.now() - loadStart
          });
          script.onerror(new Error('Load timeout'));
        }
      }, 30000); // 30 second timeout
      
      document.body.appendChild(script);
    }
    
    loadBundle();
  })();
  
  // Track other errors
  window.addEventListener('error', function(e) {
    telemetry.log('javascript_error', {
      message: e.message,
      filename: e.filename,
      line: e.lineno,
      column: e.colno,
      stack: e.error?.stack
    });
  });
  
  // Track unhandled promise rejections
  window.addEventListener('unhandledrejection', function(e) {
    telemetry.log('unhandled_rejection', {
      reason: e.reason?.toString(),
      promise: e.promise?.toString()
    });
  });
</script>
```

#### 1.2 React App Telemetry Integration
```javascript
// frontend/src/utils/telemetry.js
class TelemetryService {
  constructor() {
    this.queue = [];
    this.batchSize = 10;
    this.flushInterval = 30000; // 30 seconds
    
    // Inherit session from initial page load
    this.sessionId = window.telemetry?.sessionId || Math.random().toString(36).substring(7);
    
    // Start flush timer
    this.startBatchTimer();
  }
  
  track(event, data = {}) {
    const entry = {
      timestamp: Date.now(),
      event,
      ...data,
      // React-specific context
      route: window.location.pathname,
      reactVersion: React.version,
      // Memory usage if available
      memory: performance.memory ? {
        usedJSHeapSize: Math.round(performance.memory.usedJSHeapSize / 1048576),
        totalJSHeapSize: Math.round(performance.memory.totalJSHeapSize / 1048576),
        jsHeapSizeLimit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
      } : null
    };
    
    this.queue.push(entry);
    
    // Flush if queue is full
    if (this.queue.length >= this.batchSize) {
      this.flush();
    }
  }
  
  trackError(error, context = {}) {
    this.track('app_error', {
      message: error.message,
      stack: error.stack,
      ...context
    });
    
    // Errors are sent immediately
    this.flush();
  }
  
  trackPerformance(metric, value, metadata = {}) {
    this.track('performance_metric', {
      metric,
      value,
      ...metadata
    });
  }
  
  flush() {
    if (this.queue.length === 0) return;
    
    const events = [...this.queue];
    this.queue = [];
    
    fetch('/api/telemetry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: this.sessionId,
        events
      })
    }).catch(error => {
      // Re-queue events on failure
      this.queue.unshift(...events);
      console.error('Telemetry send failed:', error);
    });
  }
  
  startBatchTimer() {
    setInterval(() => this.flush(), this.flushInterval);
  }
}

export const telemetry = new TelemetryService();

// React Error Boundary integration
export class TelemetryErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    telemetry.trackError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true
    });
  }
  
  render() {
    if (this.state?.hasError) {
      return this.props.fallback || <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}
```

### 2. Backend Telemetry API

#### 2.1 Telemetry Endpoint
```python
# backend/api/routes/telemetry.py
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])
logger = logging.getLogger(__name__)

class TelemetryEvent(BaseModel):
    timestamp: int
    event: str
    elapsed: Optional[int] = None
    userAgent: Optional[str] = None
    connection: Optional[Dict[str, Any]] = None
    screen: Optional[Dict[str, Any]] = None
    # Allow additional fields
    class Config:
        extra = "allow"

class TelemetryPayload(BaseModel):
    sessionId: str
    events: List[Dict[str, Any]]

@router.post("")
async def receive_telemetry(
    payload: TelemetryPayload,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Receive telemetry data from clients"""
    
    # Add server-side context
    client_ip = request.client.host
    received_at = datetime.utcnow()
    
    # Process in background to not block response
    background_tasks.add_task(
        process_telemetry,
        payload,
        client_ip,
        received_at
    )
    
    return {"status": "accepted"}

async def process_telemetry(
    payload: TelemetryPayload,
    client_ip: str,
    received_at: datetime
):
    """Process telemetry data asynchronously"""
    
    for event in payload.events:
        # Enrich with server-side data
        event['sessionId'] = payload.sessionId
        event['clientIp'] = client_ip
        event['receivedAt'] = received_at.isoformat()
        
        # Log based on event type
        if event.get('event') in ['bundle_load_error', 'bundle_load_timeout', 'bundle_load_failed']:
            logger.error(
                f"Client bundle load failure",
                extra={
                    'telemetry_event': event,
                    'session_id': payload.sessionId,
                    'user_agent': event.get('userAgent', 'Unknown')
                }
            )
            
            # Trigger alerts for high-priority events
            await check_alert_conditions(event)
            
        elif event.get('event') == 'performance_metrics':
            logger.info(
                f"Client performance metrics",
                extra={'telemetry_event': event}
            )
            
        else:
            logger.info(
                f"Client telemetry: {event.get('event')}",
                extra={'telemetry_event': event}
            )
    
    # Store in database for analysis
    await store_telemetry(payload)

async def check_alert_conditions(event: Dict[str, Any]):
    """Check if event should trigger alerts"""
    
    # Alert on mobile Safari bundle failures
    if 'Safari' in event.get('userAgent', '') and 'Mobile' in event.get('userAgent', ''):
        logger.critical(
            "Mobile Safari bundle load failure detected",
            extra={'event': event}
        )
    
    # Alert on slow connections
    connection = event.get('connection', {})
    if connection.get('effectiveType') in ['slow-2g', '2g']:
        logger.warning(
            "Bundle load failure on slow connection",
            extra={'event': event}
        )
```

#### 2.2 Telemetry Analytics API
```python
# backend/api/routes/analytics.py
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/bundle-load-stats")
async def get_bundle_load_stats(
    hours: int = Query(24, description="Hours to look back"),
    group_by: Optional[str] = Query(None, description="Group by: country, device, connection")
):
    """Get bundle loading statistics"""
    
    # Query telemetry data
    stats = await query_telemetry_stats(
        event_type="bundle_load_*",
        since=datetime.utcnow() - timedelta(hours=hours),
        group_by=group_by
    )
    
    return {
        "period": f"last_{hours}_hours",
        "summary": {
            "total_loads": stats['total'],
            "successful": stats['successful'],
            "failed": stats['failed'],
            "success_rate": stats['success_rate'],
            "avg_load_time": stats['avg_load_time'],
            "retry_rate": stats['retry_rate']
        },
        "by_group": stats.get('groups', {}),
        "top_errors": stats.get('top_errors', [])
    }

@router.get("/client-errors")
async def get_client_errors(
    hours: int = Query(24, description="Hours to look back"),
    min_occurrences: int = Query(2, description="Minimum occurrences to include")
):
    """Get client-side errors grouped by type"""
    
    errors = await query_error_telemetry(
        since=datetime.utcnow() - timedelta(hours=hours),
        min_occurrences=min_occurrences
    )
    
    return {
        "period": f"last_{hours}_hours",
        "total_errors": len(errors),
        "unique_errors": len(set(e['signature'] for e in errors)),
        "errors": errors
    }

@router.get("/device-breakdown")
async def get_device_breakdown():
    """Get breakdown of devices accessing the application"""
    
    breakdown = await analyze_user_agents()
    
    return {
        "browsers": breakdown['browsers'],
        "operating_systems": breakdown['os'],
        "device_types": breakdown['devices'],
        "connection_types": breakdown['connections']
    }
```

### 3. Real-Time Monitoring Dashboard

#### 3.1 WebSocket Live Feed
```python
# backend/api/routes/monitoring.py
from fastapi import APIRouter, WebSocket
from typing import Set
import json

router = APIRouter()
connected_monitors: Set[WebSocket] = set()

@router.websocket("/ws/monitoring")
async def monitoring_websocket(websocket: WebSocket):
    """Live telemetry feed for monitoring dashboard"""
    await websocket.accept()
    connected_monitors.add(websocket)
    
    try:
        # Send current stats on connection
        stats = await get_current_stats()
        await websocket.send_json(stats)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        connected_monitors.remove(websocket)

async def broadcast_telemetry_event(event: Dict):
    """Broadcast important events to monitoring clients"""
    if not connected_monitors:
        return
    
    # Filter sensitive data
    safe_event = {
        'type': 'telemetry',
        'timestamp': event.get('timestamp'),
        'event': event.get('event'),
        'sessionId': event.get('sessionId'),
        'userAgent': event.get('userAgent'),
        'connection': event.get('connection'),
        'error': event.get('error') if event.get('event') == 'bundle_load_error' else None
    }
    
    for websocket in connected_monitors.copy():
        try:
            await websocket.send_json(safe_event)
        except:
            connected_monitors.discard(websocket)
```

#### 3.2 Monitoring Dashboard UI
```html
<!-- monitoring-dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Client Telemetry Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .metric { 
            display: inline-block; 
            margin: 10px; 
            padding: 15px; 
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .metric h3 { margin: 0 0 10px 0; }
        .error { background-color: #ffebee; }
        .success { background-color: #e8f5e9; }
        .warning { background-color: #fff3e0; }
        #live-feed {
            height: 300px;
            overflow-y: scroll;
            border: 1px solid #ddd;
            padding: 10px;
            margin-top: 20px;
        }
        .event-item {
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid #2196f3;
        }
        .event-error { border-color: #f44336; }
        .event-success { border-color: #4caf50; }
    </style>
</head>
<body>
    <h1>Client Telemetry Dashboard</h1>
    
    <div id="metrics">
        <div class="metric">
            <h3>Success Rate</h3>
            <div id="success-rate">--</div>
        </div>
        <div class="metric">
            <h3>Avg Load Time</h3>
            <div id="avg-load-time">--</div>
        </div>
        <div class="metric">
            <h3>Active Sessions</h3>
            <div id="active-sessions">--</div>
        </div>
        <div class="metric error">
            <h3>Errors (24h)</h3>
            <div id="error-count">--</div>
        </div>
    </div>
    
    <h2>Live Feed</h2>
    <div id="live-feed"></div>
    
    <h2>Error Breakdown</h2>
    <canvas id="error-chart" width="400" height="200"></canvas>
    
    <script>
        const ws = new WebSocket('ws://localhost:5050/ws/monitoring');
        const liveFeed = document.getElementById('live-feed');
        const maxFeedItems = 50;
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'stats') {
                updateMetrics(data);
            } else if (data.type === 'telemetry') {
                addToFeed(data);
            }
        };
        
        function updateMetrics(stats) {
            document.getElementById('success-rate').textContent = 
                (stats.successRate * 100).toFixed(1) + '%';
            document.getElementById('avg-load-time').textContent = 
                stats.avgLoadTime.toFixed(0) + 'ms';
            document.getElementById('active-sessions').textContent = 
                stats.activeSessions;
            document.getElementById('error-count').textContent = 
                stats.errorCount;
        }
        
        function addToFeed(event) {
            const item = document.createElement('div');
            item.className = 'event-item';
            
            if (event.event.includes('error') || event.event.includes('fail')) {
                item.className += ' event-error';
            } else if (event.event.includes('success')) {
                item.className += ' event-success';
            }
            
            const time = new Date(event.timestamp).toLocaleTimeString();
            const connection = event.connection ? 
                ` [${event.connection.effectiveType}]` : '';
            
            item.innerHTML = `
                <strong>${time}</strong> - 
                ${event.event}${connection} - 
                Session: ${event.sessionId.substring(0, 6)}...
                ${event.error ? `<br>Error: ${event.error}` : ''}
            `;
            
            liveFeed.insertBefore(item, liveFeed.firstChild);
            
            // Keep feed size limited
            while (liveFeed.children.length > maxFeedItems) {
                liveFeed.removeChild(liveFeed.lastChild);
            }
        }
        
        // Fetch analytics data every 30 seconds
        setInterval(async () => {
            const response = await fetch('/api/analytics/bundle-load-stats');
            const data = await response.json();
            updateMetrics({
                successRate: data.summary.success_rate,
                avgLoadTime: data.summary.avg_load_time,
                activeSessions: data.summary.active_sessions || 0,
                errorCount: data.summary.failed
            });
        }, 30000);
    </script>
</body>
</html>
```

### 4. Automated Alerts

#### 4.1 Alert Configuration
```python
# backend/api/services/alerts.py
from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta

class TelemetryAlertService:
    def __init__(self):
        self.alert_rules = [
            {
                'name': 'high_failure_rate',
                'condition': lambda stats: stats['failure_rate'] > 0.1,  # 10%
                'message': 'Bundle load failure rate exceeds 10%',
                'severity': 'critical'
            },
            {
                'name': 'slow_load_times',
                'condition': lambda stats: stats['p95_load_time'] > 10000,  # 10s
                'message': 'P95 load time exceeds 10 seconds',
                'severity': 'warning'
            },
            {
                'name': 'mobile_safari_issues',
                'condition': lambda stats: stats['mobile_safari_failure_rate'] > 0.05,
                'message': 'Mobile Safari experiencing high failure rate',
                'severity': 'critical'
            }
        ]
    
    async def check_alerts(self):
        """Check alert conditions periodically"""
        while True:
            try:
                stats = await self.calculate_current_stats()
                
                for rule in self.alert_rules:
                    if rule['condition'](stats):
                        await self.trigger_alert(rule, stats)
            
            except Exception as e:
                logger.error(f"Alert check failed: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    async def trigger_alert(self, rule: Dict, stats: Dict):
        """Trigger an alert"""
        alert = {
            'timestamp': datetime.utcnow(),
            'rule': rule['name'],
            'message': rule['message'],
            'severity': rule['severity'],
            'stats': stats
        }
        
        # Log alert
        logger.warning(f"ALERT: {rule['message']}", extra={'alert': alert})
        
        # Send notifications (email, Slack, etc.)
        await self.send_notifications(alert)
    
    async def calculate_current_stats(self) -> Dict[str, Any]:
        """Calculate current telemetry statistics"""
        # Query recent telemetry data
        recent_events = await query_telemetry(
            since=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Calculate stats
        total = len([e for e in recent_events if e['event'].startswith('bundle_load_')])
        failed = len([e for e in recent_events if e['event'] in ['bundle_load_error', 'bundle_load_failed']])
        
        load_times = [
            e['loadTime'] for e in recent_events 
            if e['event'] == 'bundle_load_success' and 'loadTime' in e
        ]
        
        return {
            'total_loads': total,
            'failed_loads': failed,
            'failure_rate': failed / total if total > 0 else 0,
            'avg_load_time': sum(load_times) / len(load_times) if load_times else 0,
            'p95_load_time': sorted(load_times)[int(len(load_times) * 0.95)] if load_times else 0,
            'mobile_safari_failure_rate': self.calculate_mobile_safari_failure_rate(recent_events)
        }
```

### 5. Privacy and Security Considerations

#### 5.1 Data Sanitization
```javascript
// frontend/src/utils/telemetry-privacy.js
export function sanitizeTelemetryData(data) {
  // Remove or hash sensitive data
  const sanitized = { ...data };
  
  // Don't send full URLs if they contain sensitive params
  if (sanitized.url) {
    const url = new URL(sanitized.url);
    // Remove query params that might be sensitive
    url.search = '';
    sanitized.url = url.toString();
  }
  
  // Hash IP addresses
  if (sanitized.clientIp) {
    sanitized.clientIp = hashIP(sanitized.clientIp);
  }
  
  // Truncate error messages that might contain sensitive data
  if (sanitized.error && sanitized.error.length > 200) {
    sanitized.error = sanitized.error.substring(0, 200) + '...';
  }
  
  return sanitized;
}

function hashIP(ip) {
  // Simple hash to preserve uniqueness without storing actual IP
  return 'ip_' + btoa(ip).substring(0, 10);
}
```

### 6. Data Retention Policy
```python
# backend/api/services/telemetry_cleanup.py
async def cleanup_old_telemetry():
    """Remove old telemetry data based on retention policy"""
    retention_days = {
        'bundle_load_success': 7,      # Keep success events for 7 days
        'bundle_load_error': 30,       # Keep errors for 30 days
        'performance_metrics': 14,      # Keep performance data for 14 days
        'javascript_error': 30,        # Keep JS errors for 30 days
    }
    
    cutoff_date = datetime.utcnow() - timedelta(days=90)  # Max retention 90 days
    
    # Delete old data
    await delete_telemetry_before(cutoff_date)
```

## Benefits

1. **Real-time Visibility**: See exactly what's happening on client devices
2. **Proactive Alerts**: Get notified before users complain
3. **Data-Driven Decisions**: Make improvements based on actual user data
4. **Regional Insights**: Understand performance across different regions/networks
5. **Device-Specific Issues**: Identify problems with specific browsers/devices
6. **Performance Tracking**: Monitor improvements over time