# backend/api/routes/telemetry.py
"""
Enhanced telemetry system for comprehensive client-side tracking and analytics.
Includes database storage, smart alerting, and performance analytics.
"""

from fastapi import APIRouter, BackgroundTasks, Request, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import sqlite3
import asyncio
import os
from pathlib import Path

# WebSocket notification function will be imported dynamically to avoid circular imports

router = APIRouter(tags=["telemetry"])
logger = logging.getLogger(__name__)

# Database setup - use same pattern as game database with environment variable support
def get_telemetry_db_path() -> str:
    """Get telemetry database path with same pattern as game database."""
    # Check environment variable first (for production/Docker)
    env_db_path = os.getenv('TELEMETRY_DB_PATH')
    if env_db_path:
        # Ensure directory exists
        db_dir = Path(env_db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        return env_db_path
    else:
        # Fall back to data directory (for local development)
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent.parent
        return str(project_root / "data" / "telemetry_data.db")

DB_PATH = get_telemetry_db_path()

def init_telemetry_db():
    """Initialize telemetry database with required tables"""
    # Ensure the data directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Telemetry events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            elapsed INTEGER,
            event TEXT NOT NULL,
            data TEXT NOT NULL,  -- JSON string
            user_agent TEXT,
            connection_type TEXT,
            screen_width INTEGER,
            screen_height INTEGER,
            viewport_width INTEGER,
            viewport_height INTEGER,
            memory_used_mb INTEGER,
            client_ip TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes separately for SQLite compatibility
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON telemetry_events(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON telemetry_events(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_event ON telemetry_events(event)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_received_at ON telemetry_events(received_at)')
    
    # Telemetry sessions table for session-level analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_sessions (
            session_id TEXT PRIMARY KEY,
            first_event TIMESTAMP,
            last_event TIMESTAMP,
            total_events INTEGER DEFAULT 0,
            user_agent TEXT,
            initial_route TEXT,
            device_type TEXT,  -- mobile, desktop, tablet
            connection_type TEXT,
            errors_count INTEGER DEFAULT 0,
            bundle_load_success BOOLEAN DEFAULT FALSE,
            bundle_load_time_ms INTEGER,
            total_duration_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Telemetry statistics for quick analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_stats (
            stat_date DATE PRIMARY KEY,
            total_sessions INTEGER DEFAULT 0,
            total_events INTEGER DEFAULT 0,
            bundle_success_rate REAL DEFAULT 0.0,
            avg_bundle_load_time_ms REAL DEFAULT 0.0,
            error_rate REAL DEFAULT 0.0,
            mobile_sessions INTEGER DEFAULT 0,
            desktop_sessions INTEGER DEFAULT 0,
            slow_connections INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on module load
init_telemetry_db()

class TelemetryPayload(BaseModel):
    sessionId: str
    events: List[Dict[str, Any]]

@router.post("/telemetry")
async def receive_telemetry(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Enhanced telemetry endpoint with database storage and smart alerting.
    
    Receives comprehensive client-side telemetry data including:
    - Bundle loading performance and errors
    - User interactions and performance metrics
    - Device and network context
    - JavaScript errors and crashes
    """
    try:
        # Handle both JSON and binary data from sendBeacon
        body = await request.body()
        
        if not body:
            return {"status": "error", "message": "Empty request body"}
        
        # Try to parse as JSON
        try:
            if isinstance(body, bytes):
                body_str = body.decode('utf-8')
                payload_data = json.loads(body_str)
            else:
                payload_data = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse telemetry data: {str(e)}")
            return {"status": "error", "message": "Invalid JSON data"}
        
        # Validate the payload structure
        try:
            payload = TelemetryPayload(**payload_data)
        except Exception as e:
            logger.error(f"Invalid telemetry payload structure: {str(e)}")
            return {"status": "error", "message": "Invalid payload structure"}
        
        # Add server-side context
        client_ip = request.client.host if request.client else 'unknown'
        received_at = datetime.utcnow()
        
        # Process in background to not block response
        background_tasks.add_task(
            process_telemetry_data,
            payload,
            client_ip,
            received_at
        )
        
        return {"status": "accepted", "events_received": len(payload.events)}
        
    except Exception as e:
        logger.error(f"Failed to receive telemetry: {str(e)}")
        return {"status": "error", "message": "Failed to process telemetry"}

async def process_telemetry_data(
    payload: TelemetryPayload,
    client_ip: str,
    received_at: datetime
):
    """Process telemetry data asynchronously with database storage and alerting"""
    
    try:
        # Store events in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        session_events = []
        bundle_load_success = False
        bundle_load_time = None
        errors_count = 0
        
        for event in payload.events:
            event_type = event.get('event', 'unknown')
            timestamp = event.get('timestamp', int(received_at.timestamp() * 1000))
            elapsed = event.get('elapsed', 0)
            
            # Extract and sanitize device context for privacy compliance
            from backend.api.services.telemetry_cleanup import TelemetryCleanupService
            
            # Sanitize the entire event for privacy compliance
            sanitized_event = TelemetryCleanupService.sanitize_telemetry_data(event)
            
            user_agent = sanitized_event.get('userAgent', '')
            connection = sanitized_event.get('connection', {})
            screen = sanitized_event.get('screen', {})
            viewport = sanitized_event.get('viewport', {})
            memory = sanitized_event.get('memory', {})
            
            # Store event in database
            cursor.execute('''
                INSERT INTO telemetry_events 
                (session_id, timestamp, elapsed, event, data, user_agent, 
                 connection_type, screen_width, screen_height, viewport_width, 
                 viewport_height, memory_used_mb, client_ip, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payload.sessionId,
                timestamp,
                elapsed,
                event_type,
                json.dumps(sanitized_event),
                user_agent,
                connection.get('effectiveType', ''),
                screen.get('width'),
                screen.get('height'),
                viewport.get('width'),
                viewport.get('height'),
                memory.get('usedJSHeapSize'),
                client_ip,
                received_at
            ))
            
            session_events.append(event)
            
            # Track bundle loading
            if event_type == 'bundle_load_success':
                bundle_load_success = True
                bundle_load_time = event.get('loadTime')
            
            # Consider session successful if React app initialized (even without bundle events)
            # This handles SPA navigation where bundle is already cached
            if event_type == 'react_app_init' and not bundle_load_success:
                bundle_load_success = True  # App is running, bundle must have loaded
            
            # Count errors
            if event_type in ['bundle_error', 'load_timeout', 'load_failed', 
                             'javascript_error', 'unhandled_rejection', 'component_error']:
                errors_count += 1
            
            # Log critical events
            if event_type in ['bundle_error', 'load_timeout', 'load_failed']:
                logger.error(
                    f"Client bundle load failure: {event_type}",
                    extra={
                        'session_id': payload.sessionId,
                        'user_agent': user_agent,
                        'attempt': event.get('attempt', 1),
                        'load_time': event.get('loadTime'),
                        'connection': connection,
                        'error': event.get('error', 'Unknown error'),
                        'client_ip': client_ip
                    }
                )
                
                # Check for alert conditions
                await check_alert_conditions(event_type, event, connection, user_agent)
                
                # Notify monitoring dashboard (import dynamically to avoid circular imports)
                try:
                    from backend.api.routes.telemetry_websocket import notify_monitoring_dashboard
                    await notify_monitoring_dashboard({
                        "sessionId": payload.sessionId,
                        "event": event_type,
                        "userAgent": user_agent,
                        "connection": connection,
                        "error": event.get("error", "Unknown error"),
                        "loadTime": event.get("loadTime"),
                        "attempt": event.get("attempt", 1)
                    })
                except ImportError:
                    pass  # WebSocket monitoring not available
                
            elif event_type in ['javascript_error', 'unhandled_rejection', 'component_error']:
                logger.error(
                    f"Client error: {event_type}",
                    extra={
                        'session_id': payload.sessionId,
                        'error': event.get('message', event.get('error', 'Unknown')),
                        'stack': event.get('stack', ''),
                        'user_agent': user_agent,
                        'client_ip': client_ip
                    }
                )
                
                # Notify monitoring dashboard for JavaScript errors
                try:
                    from backend.api.routes.telemetry_websocket import notify_monitoring_dashboard
                    await notify_monitoring_dashboard({
                        "sessionId": payload.sessionId,
                        "event": event_type,
                        "userAgent": user_agent,
                        "connection": connection,
                        "error": event.get('message', event.get('error', 'Unknown error')),
                        "filename": event.get('filename', 'Unknown file')
                    })
                except ImportError:
                    pass  # WebSocket monitoring not available
            
            elif event_type == 'bundle_load_success':
                logger.info(
                    f"Bundle loaded successfully",
                    extra={
                        'session_id': payload.sessionId,
                        'attempt': event.get('attempt', 1),
                        'load_time': event.get('loadTime'),
                        'connection': connection
                    }
                )
            
        # Update or create session record
        device_type = detect_device_type(session_events[0].get('userAgent', '') if session_events else '')
        initial_route = None
        
        for event in session_events:
            if event.get('event') == 'page_load_start':
                initial_route = event.get('url', '').split('/')[-1] or 'home'
                break
        
        cursor.execute('''
            INSERT OR REPLACE INTO telemetry_sessions
            (session_id, first_event, last_event, total_events, user_agent, 
             initial_route, device_type, connection_type, errors_count, 
             bundle_load_success, bundle_load_time_ms, updated_at)
            VALUES (?, ?, ?, 
                    COALESCE((SELECT total_events FROM telemetry_sessions WHERE session_id = ?), 0) + ?, 
                    ?, ?, ?, ?, 
                    COALESCE((SELECT errors_count FROM telemetry_sessions WHERE session_id = ?), 0) + ?,
                    ?, ?, CURRENT_TIMESTAMP)
        ''', (
            payload.sessionId,
            received_at,
            received_at,
            payload.sessionId,
            len(session_events),
            user_agent,
            initial_route,
            device_type,
            connection.get('effectiveType', ''),
            payload.sessionId,
            errors_count,
            bundle_load_success,
            bundle_load_time
        ))
        
        conn.commit()
        conn.close()
        
        # Update daily statistics
        await update_daily_statistics(received_at.date())
        
    except Exception as e:
        logger.error(f"Failed to process telemetry data: {str(e)}")

def detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent"""
    user_agent = user_agent.lower()
    if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif 'ipad' in user_agent or 'tablet' in user_agent:
        return 'tablet'
    else:
        return 'desktop'

async def check_alert_conditions(event_type: str, event: Dict[str, Any], 
                                connection: Dict[str, Any], user_agent: str):
    """Check if event should trigger alerts"""
    
    # Alert on mobile Safari bundle failures
    if 'safari' in user_agent.lower() and 'mobile' in user_agent.lower():
        logger.critical(
            "Mobile Safari bundle load failure detected",
            extra={'event': event, 'event_type': event_type}
        )
    
    # Alert on slow connections
    if connection.get('effectiveType') in ['slow-2g', '2g']:
        logger.warning(
            "Bundle load failure on slow connection",
            extra={'event': event, 'connection': connection}
        )
    
    # Alert on repeated failures
    attempt = event.get('attempt', 1)
    if attempt >= 3:  # Max retries reached
        logger.critical(
            f"Bundle load failed after {attempt} attempts",
            extra={'event': event, 'final_failure': True}
        )

async def update_daily_statistics(stat_date):
    """Update daily statistics for analytics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate daily stats
        date_str = stat_date.strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(*) as total_events,
                SUM(CASE WHEN bundle_load_success THEN 1 ELSE 0 END) * 1.0 / 
                    NULLIF(COUNT(DISTINCT CASE WHEN bundle_load_success IS NOT NULL THEN session_id END), 0) as success_rate,
                AVG(bundle_load_time_ms) as avg_load_time,
                SUM(errors_count) * 1.0 / NULLIF(COUNT(*), 0) as error_rate,
                SUM(CASE WHEN device_type = 'mobile' THEN 1 ELSE 0 END) as mobile_sessions,
                SUM(CASE WHEN device_type = 'desktop' THEN 1 ELSE 0 END) as desktop_sessions,
                SUM(CASE WHEN connection_type IN ('slow-2g', '2g') THEN 1 ELSE 0 END) as slow_connections
            FROM telemetry_sessions 
            WHERE DATE(created_at) = ?
        ''', (date_str,))
        
        stats = cursor.fetchone()
        if stats:
            cursor.execute('''
                INSERT OR REPLACE INTO telemetry_stats
                (stat_date, total_sessions, total_events, bundle_success_rate,
                 avg_bundle_load_time_ms, error_rate, mobile_sessions, 
                 desktop_sessions, slow_connections)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (stat_date,) + stats)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to update daily statistics: {str(e)}")

# Analytics API Endpoints

@router.get("/analytics/bundle-load-stats")
async def get_bundle_load_stats(
    hours: int = Query(24, description="Hours to look back", ge=1, le=168),
    group_by: Optional[str] = Query(None, description="Group by: device, connection, location")
):
    """Get bundle loading statistics and performance metrics"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calculate time window
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get overall stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(DISTINCT CASE WHEN bundle_load_success THEN session_id END) as successful_loads,
                COUNT(DISTINCT CASE WHEN NOT bundle_load_success OR bundle_load_success IS NULL THEN session_id END) as failed_loads,
                AVG(bundle_load_time_ms) as avg_load_time,
                COUNT(DISTINCT CASE WHEN device_type = 'mobile' THEN session_id END) as mobile_sessions,
                COUNT(DISTINCT CASE WHEN connection_type IN ('slow-2g', '2g') THEN session_id END) as slow_connections,
                SUM(errors_count) as total_errors
            FROM telemetry_sessions 
            WHERE created_at >= ?
        ''', (since,))
        
        stats = cursor.fetchone()
        
        if not stats or stats[0] == 0:
            return {
                "period": f"last_{hours}_hours",
                "summary": {
                    "total_sessions": 0,
                    "successful_loads": 0,
                    "failed_loads": 0,
                    "success_rate": 0.0,
                    "avg_load_time": 0.0,
                    "mobile_percentage": 0.0,
                    "slow_connections": 0,
                    "total_errors": 0
                },
                "groups": {}
            }
        
        total_sessions, successful, failed, avg_time, mobile, slow_conn, errors = stats
        success_rate = successful / total_sessions if total_sessions > 0 else 0.0
        
        summary = {
            "total_sessions": total_sessions,
            "successful_loads": successful,
            "failed_loads": failed,
            "success_rate": round(success_rate, 3),
            "avg_load_time": round(avg_time, 1) if avg_time else 0.0,
            "mobile_percentage": round(mobile / total_sessions * 100, 1) if total_sessions > 0 else 0.0,
            "slow_connections": slow_conn,
            "total_errors": errors
        }
        
        # Group by analysis
        groups = {}
        if group_by:
            if group_by == "device":
                cursor.execute('''
                    SELECT 
                        device_type,
                        COUNT(DISTINCT session_id) as sessions,
                        COUNT(DISTINCT CASE WHEN bundle_load_success THEN session_id END) as successful,
                        AVG(bundle_load_time_ms) as avg_time
                    FROM telemetry_sessions 
                    WHERE created_at >= ?
                    GROUP BY device_type
                ''', (since,))
                
                for row in cursor.fetchall():
                    device, sessions, successful, avg_time = row
                    groups[device] = {
                        "sessions": sessions,
                        "success_rate": round(successful / sessions, 3) if sessions > 0 else 0.0,
                        "avg_load_time": round(avg_time, 1) if avg_time else 0.0
                    }
            
            elif group_by == "connection":
                cursor.execute('''
                    SELECT 
                        connection_type,
                        COUNT(DISTINCT session_id) as sessions,
                        COUNT(DISTINCT CASE WHEN bundle_load_success THEN session_id END) as successful,
                        AVG(bundle_load_time_ms) as avg_time
                    FROM telemetry_sessions 
                    WHERE created_at >= ?
                    GROUP BY connection_type
                ''', (since,))
                
                for row in cursor.fetchall():
                    conn_type, sessions, successful, avg_time = row
                    groups[conn_type or 'unknown'] = {
                        "sessions": sessions,
                        "success_rate": round(successful / sessions, 3) if sessions > 0 else 0.0,
                        "avg_load_time": round(avg_time, 1) if avg_time else 0.0
                    }
        
        conn.close()
        
        return {
            "period": f"last_{hours}_hours",
            "summary": summary,
            "groups": groups
        }
        
    except Exception as e:
        logger.error(f"Failed to get bundle load stats: {str(e)}")
        return {"error": "Failed to retrieve statistics"}

@router.get("/analytics/client-errors")
async def get_client_errors(
    hours: int = Query(24, description="Hours to look back", ge=1, le=168),
    min_occurrences: int = Query(2, description="Minimum occurrences to include", ge=1)
):
    """Get client-side errors grouped by type and frequency"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT 
                event,
                JSON_EXTRACT(data, '$.message') as error_message,
                JSON_EXTRACT(data, '$.filename') as filename,
                COUNT(*) as occurrences,
                COUNT(DISTINCT session_id) as unique_sessions,
                MAX(received_at) as last_seen
            FROM telemetry_events 
            WHERE received_at >= ? 
              AND event IN ('javascript_error', 'unhandled_rejection', 'component_error', 
                           'bundle_error', 'load_timeout', 'load_failed')
            GROUP BY event, JSON_EXTRACT(data, '$.message'), JSON_EXTRACT(data, '$.filename')
            HAVING COUNT(*) >= ?
            ORDER BY occurrences DESC
        ''', (since, min_occurrences))
        
        errors = []
        for row in cursor.fetchall():
            event_type, message, filename, count, sessions, last_seen = row
            errors.append({
                "type": event_type,
                "message": message or "Unknown error",
                "filename": filename or "Unknown file",
                "occurrences": count,
                "unique_sessions": sessions,
                "last_seen": last_seen,
                "severity": "critical" if event_type in ['bundle_error', 'load_failed'] else "warning"
            })
        
        conn.close()
        
        return {
            "period": f"last_{hours}_hours",
            "total_error_types": len(errors),
            "total_occurrences": sum(e["occurrences"] for e in errors),
            "unique_sessions_affected": len(set(e["unique_sessions"] for e in errors)),
            "errors": errors[:50]  # Limit to top 50
        }
        
    except Exception as e:
        logger.error(f"Failed to get client errors: {str(e)}")
        return {"error": "Failed to retrieve error data"}

@router.get("/analytics/device-breakdown")
async def get_device_breakdown(
    hours: int = Query(24, description="Hours to look back", ge=1, le=168)
):
    """Get breakdown of devices, browsers, and connection types"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Device types
        cursor.execute('''
            SELECT device_type, COUNT(DISTINCT session_id) as sessions
            FROM telemetry_sessions 
            WHERE created_at >= ?
            GROUP BY device_type
        ''', (since,))
        
        devices = dict(cursor.fetchall())
        
        # Connection types
        cursor.execute('''
            SELECT connection_type, COUNT(DISTINCT session_id) as sessions
            FROM telemetry_sessions 
            WHERE created_at >= ?
            GROUP BY connection_type
        ''', (since,))
        
        connections = dict(cursor.fetchall())
        
        # Browser breakdown (simplified from user agent)
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN user_agent LIKE '%Chrome%' THEN 'Chrome'
                    WHEN user_agent LIKE '%Safari%' AND user_agent NOT LIKE '%Chrome%' THEN 'Safari'
                    WHEN user_agent LIKE '%Firefox%' THEN 'Firefox'
                    WHEN user_agent LIKE '%Edge%' THEN 'Edge'
                    ELSE 'Other'
                END as browser,
                COUNT(DISTINCT session_id) as sessions
            FROM telemetry_sessions 
            WHERE created_at >= ?
            GROUP BY browser
        ''', (since,))
        
        browsers = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "period": f"last_{hours}_hours",
            "devices": devices,
            "browsers": browsers,
            "connections": connections
        }
        
    except Exception as e:
        logger.error(f"Failed to get device breakdown: {str(e)}")
        return {"error": "Failed to retrieve device data"}

@router.get("/analytics/performance-trends")
async def get_performance_trends(
    hours: int = Query(24, description="Hours to look back", ge=1, le=168),
    interval: str = Query("1h", description="Time interval: 1h, 6h, 24h")
):
    """Get performance trends over time"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Determine grouping interval
        if interval == "1h":
            time_format = "%Y-%m-%d %H:00:00"
        elif interval == "6h":
            time_format = "%Y-%m-%d " + str((datetime.utcnow().hour // 6) * 6).zfill(2) + ":00:00"
        else:  # 24h
            time_format = "%Y-%m-%d 00:00:00"
        
        cursor.execute(f'''
            SELECT 
                strftime(?, created_at) as time_bucket,
                COUNT(DISTINCT session_id) as sessions,
                COUNT(DISTINCT CASE WHEN bundle_load_success THEN session_id END) as successful_loads,
                AVG(bundle_load_time_ms) as avg_load_time,
                SUM(errors_count) as total_errors
            FROM telemetry_sessions 
            WHERE created_at >= ?
            GROUP BY time_bucket
            ORDER BY time_bucket
        ''', (time_format, since))
        
        trends = []
        for row in cursor.fetchall():
            time_bucket, sessions, successful, avg_time, errors = row
            trends.append({
                "timestamp": time_bucket,
                "sessions": sessions,
                "success_rate": round(successful / sessions, 3) if sessions > 0 else 0.0,
                "avg_load_time": round(avg_time, 1) if avg_time else 0.0,
                "error_rate": round(errors / sessions, 2) if sessions > 0 else 0.0
            })
        
        conn.close()
        
        return {
            "period": f"last_{hours}_hours",
            "interval": interval,
            "data_points": len(trends),
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance trends: {str(e)}")
        return {"error": "Failed to retrieve trend data"}

# Privacy and Data Management Endpoints

@router.get("/privacy/report")
async def get_privacy_report():
    """Get telemetry privacy compliance report"""
    from backend.api.services.telemetry_cleanup import TelemetryPrivacyService
    
    return TelemetryPrivacyService.generate_privacy_report()

@router.get("/privacy/export/{session_id}")
async def export_session_data(session_id: str):
    """Export all telemetry data for a specific session (GDPR compliance)"""
    from backend.api.services.telemetry_cleanup import TelemetryPrivacyService
    
    if len(session_id) < 5:  # Basic validation
        return {"error": "Invalid session ID"}
    
    data = TelemetryPrivacyService.export_user_data(session_id, DB_PATH)
    return data

@router.delete("/privacy/delete/{session_id}")
async def delete_session_data(session_id: str):
    """Delete all telemetry data for a specific session (Right to be forgotten)"""
    from backend.api.services.telemetry_cleanup import TelemetryPrivacyService
    
    if len(session_id) < 5:  # Basic validation
        return {"error": "Invalid session ID"}
    
    success = TelemetryPrivacyService.delete_user_data(session_id, DB_PATH)
    
    if success:
        return {"message": "Session data deleted successfully", "session_id": session_id}
    else:
        return {"error": "Failed to delete session data"}

@router.post("/privacy/cleanup")
async def manual_cleanup():
    """Manually trigger telemetry data cleanup"""
    from backend.api.services.telemetry_cleanup import TelemetryCleanupService
    
    try:
        cleanup_service = TelemetryCleanupService(DB_PATH)
        await cleanup_service.perform_cleanup()
        return {"message": "Cleanup completed successfully"}
    except Exception as e:
        logger.error(f"Manual cleanup failed: {str(e)}")
        return {"error": "Cleanup failed"}

@router.get("/privacy/data-summary")
async def get_data_summary():
    """Get summary of stored telemetry data for transparency"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Count events by type
        cursor.execute('''
            SELECT event, COUNT(*) as count 
            FROM telemetry_events 
            GROUP BY event 
            ORDER BY count DESC
        ''')
        event_counts = dict(cursor.fetchall())
        
        # Count sessions by device type
        cursor.execute('''
            SELECT device_type, COUNT(*) as count 
            FROM telemetry_sessions 
            GROUP BY device_type
        ''')
        device_counts = dict(cursor.fetchall())
        
        # Get date range
        cursor.execute('''
            SELECT MIN(received_at), MAX(received_at), COUNT(DISTINCT session_id) 
            FROM telemetry_events
        ''')
        date_info = cursor.fetchone()
        
        conn.close()
        
        return {
            "summary": {
                "total_events": sum(event_counts.values()),
                "total_sessions": date_info[2] if date_info else 0,
                "oldest_data": date_info[0] if date_info else None,
                "newest_data": date_info[1] if date_info else None
            },
            "events_by_type": event_counts,
            "sessions_by_device": device_counts,
            "data_retention": "7-90 days depending on event type",
            "privacy_note": "All data is anonymized and automatically cleaned up"
        }
        
    except Exception as e:
        logger.error(f"Failed to get data summary: {str(e)}")
        return {"error": "Failed to retrieve data summary"}