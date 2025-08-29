# backend/api/services/telemetry_cleanup.py
"""
Telemetry data retention and privacy compliance service.
Handles automatic cleanup of old telemetry data and privacy-compliant data processing.
"""

import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import hashlib
import re

logger = logging.getLogger(__name__)

class TelemetryCleanupService:
    """Service for managing telemetry data retention and privacy compliance"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.retention_policies = {
            # Event-specific retention periods (in days)
            'bundle_load_success': 7,      # Keep success events for 7 days
            'bundle_error': 30,            # Keep errors for 30 days
            'load_timeout': 30,            # Keep timeouts for 30 days
            'load_failed': 30,             # Keep failures for 30 days
            'javascript_error': 30,        # Keep JS errors for 30 days
            'unhandled_rejection': 30,     # Keep unhandled rejections for 30 days
            'component_error': 30,         # Keep component errors for 30 days
            'performance_metrics': 14,     # Keep performance data for 14 days
            'page_load_start': 3,          # Keep page loads for 3 days
            'user_interaction': 7,         # Keep interactions for 7 days
            'default': 14                  # Default retention for other events
        }
        self.max_retention_days = 90       # Maximum retention period
        self.cleanup_enabled = True
        
    async def start_cleanup_scheduler(self):
        """Start the background cleanup scheduler"""
        logger.info("🧹 Starting telemetry cleanup scheduler")
        
        while self.cleanup_enabled:
            try:
                await self.perform_cleanup()
                # Run cleanup every 24 hours
                await asyncio.sleep(24 * 60 * 60)
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {str(e)}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(60 * 60)
    
    async def perform_cleanup(self):
        """Perform comprehensive data cleanup"""
        logger.info("🧹 Starting telemetry data cleanup")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up old events based on retention policies
            events_cleaned = await self._cleanup_events(cursor)
            
            # Clean up orphaned sessions
            sessions_cleaned = await self._cleanup_orphaned_sessions(cursor)
            
            # Clean up old statistics
            stats_cleaned = await self._cleanup_old_statistics(cursor)
            
            # Commit all cleanup operations first
            conn.commit()
            conn.close()
            
            # Vacuum database to reclaim space (must be outside transaction)
            if events_cleaned > 0 or sessions_cleaned > 0 or stats_cleaned > 0:
                vacuum_conn = sqlite3.connect(self.db_path)
                vacuum_conn.execute("VACUUM")
                vacuum_conn.close()
            
            logger.info(
                f"🧹 Cleanup completed: "
                f"{events_cleaned} events, "
                f"{sessions_cleaned} sessions, "
                f"{stats_cleaned} stats removed"
            )
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def _cleanup_events(self, cursor) -> int:
        """Clean up old telemetry events based on retention policies"""
        total_cleaned = 0
        
        for event_type, retention_days in self.retention_policies.items():
            if event_type == 'default':
                continue
                
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            cursor.execute('''
                DELETE FROM telemetry_events 
                WHERE event = ? AND received_at < ?
            ''', (event_type, cutoff_date))
            
            cleaned = cursor.rowcount
            total_cleaned += cleaned
            
            if cleaned > 0:
                logger.debug(f"Cleaned {cleaned} {event_type} events older than {retention_days} days")
        
        # Clean up any remaining events older than max retention
        max_cutoff = datetime.utcnow() - timedelta(days=self.max_retention_days)
        cursor.execute('''
            DELETE FROM telemetry_events 
            WHERE received_at < ?
        ''', (max_cutoff,))
        
        max_cleaned = cursor.rowcount
        total_cleaned += max_cleaned
        
        if max_cleaned > 0:
            logger.info(f"Cleaned {max_cleaned} events older than {self.max_retention_days} days (max retention)")
        
        return total_cleaned
    
    async def _cleanup_orphaned_sessions(self, cursor) -> int:
        """Clean up session records that no longer have associated events"""
        cursor.execute('''
            DELETE FROM telemetry_sessions 
            WHERE session_id NOT IN (
                SELECT DISTINCT session_id FROM telemetry_events
            )
        ''')
        
        cleaned = cursor.rowcount
        if cleaned > 0:
            logger.debug(f"Cleaned {cleaned} orphaned session records")
        
        return cleaned
    
    async def _cleanup_old_statistics(self, cursor) -> int:
        """Clean up old daily statistics (keep last 90 days)"""
        cutoff_date = datetime.utcnow().date() - timedelta(days=90)
        
        cursor.execute('''
            DELETE FROM telemetry_stats 
            WHERE stat_date < ?
        ''', (cutoff_date,))
        
        cleaned = cursor.rowcount
        if cleaned > 0:
            logger.debug(f"Cleaned {cleaned} old daily statistics")
        
        return cleaned
    
    def stop_cleanup_scheduler(self):
        """Stop the cleanup scheduler"""
        logger.info("🧹 Stopping telemetry cleanup scheduler")
        self.cleanup_enabled = False
    
    @staticmethod
    def sanitize_telemetry_data(data: Dict) -> Dict:
        """
        Sanitize telemetry data for privacy compliance.
        Removes or hashes sensitive information.
        """
        sanitized = data.copy()
        
        # Remove or hash potentially sensitive data
        if 'url' in sanitized:
            # Remove query parameters that might contain sensitive data
            url = sanitized['url']
            if '?' in url:
                sanitized['url'] = url.split('?')[0]
        
        # Hash IP addresses for privacy
        if 'clientIp' in sanitized:
            sanitized['clientIp'] = TelemetryCleanupService._hash_ip(sanitized['clientIp'])
        
        # Truncate error messages that might contain sensitive data
        if 'error' in sanitized and len(str(sanitized['error'])) > 200:
            sanitized['error'] = str(sanitized['error'])[:200] + '...'
        
        # Remove stack traces that might contain file paths
        if 'stack' in sanitized:
            sanitized['stack'] = TelemetryCleanupService._sanitize_stack_trace(sanitized['stack'])
        
        # Sanitize user agent (keep browser/version info only)
        if 'userAgent' in sanitized:
            sanitized['userAgent'] = TelemetryCleanupService._sanitize_user_agent(sanitized['userAgent'])
        
        return sanitized
    
    @staticmethod
    def _hash_ip(ip: str) -> str:
        """Hash IP address for privacy while maintaining uniqueness for analytics"""
        # Use SHA-256 hash with a salt for privacy
        salt = "telemetry_ip_salt_2024"
        hash_input = f"{ip}:{salt}".encode('utf-8')
        return f"ip_{hashlib.sha256(hash_input).hexdigest()[:10]}"
    
    @staticmethod
    def _sanitize_stack_trace(stack_trace: str) -> str:
        """Remove file paths and keep only function/line info from stack traces"""
        if not stack_trace:
            return ""
        
        # Remove file paths but keep function names and line numbers
        sanitized_lines = []
        for line in stack_trace.split('\n'):
            # Remove file paths (anything that looks like a file path)
            line = re.sub(r'[a-zA-Z]:[\\\/][^\s]+', '[FILE_PATH]', line)
            line = re.sub(r'\/[^\s]+\/', '[PATH]/', line)
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines[:10])  # Limit to first 10 lines
    
    @staticmethod
    def _sanitize_user_agent(user_agent: str) -> str:
        """Extract only browser and platform info from user agent"""
        if not user_agent:
            return "Unknown"
        
        # Extract browser info
        browser_patterns = {
            'Chrome': r'Chrome/(\d+)',
            'Safari': r'Version/(\d+).*Safari',
            'Firefox': r'Firefox/(\d+)',
            'Edge': r'Edge/(\d+)',
        }
        
        browser = "Other"
        version = ""
        
        for browser_name, pattern in browser_patterns.items():
            match = re.search(pattern, user_agent)
            if match:
                browser = browser_name
                version = match.group(1)
                break
        
        # Extract platform info
        if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
            platform = "Mobile"
        elif 'iPad' in user_agent:
            platform = "Tablet"
        else:
            platform = "Desktop"
        
        return f"{browser}/{version} ({platform})" if version else f"{browser} ({platform})"

class TelemetryPrivacyService:
    """Service for handling privacy-compliant telemetry operations"""
    
    @staticmethod
    def generate_privacy_report() -> Dict:
        """Generate a privacy compliance report"""
        return {
            "data_collection": {
                "purpose": "Performance monitoring and error tracking",
                "types": [
                    "Browser performance metrics",
                    "JavaScript error messages",
                    "Network connection information",
                    "Device screen resolution",
                    "Bundle loading statistics"
                ],
                "retention": "7-90 days based on data type",
                "anonymization": "IP addresses hashed, stack traces sanitized"
            },
            "user_rights": {
                "data_deletion": "Automatic after retention period",
                "data_access": "Not supported (anonymized data)",
                "opt_out": "Disable JavaScript or use privacy mode"
            },
            "security": {
                "encryption": "Data encrypted in transit (HTTPS/WSS)",
                "access_control": "Restricted to authorized monitoring systems",
                "storage": "Local SQLite database with file system permissions"
            },
            "compliance": {
                "gdpr": "Data minimization, purpose limitation, retention limits",
                "ccpa": "No sale of personal data, automatic deletion",
                "coppa": "No intentional collection from children under 13"
            }
        }
    
    @staticmethod
    def export_user_data(session_id: str, db_path: Path) -> Dict:
        """
        Export all data for a specific session (for data portability requests).
        Note: This is primarily for compliance, data is largely anonymized.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get session data
            cursor.execute('''
                SELECT * FROM telemetry_sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            session_data = cursor.fetchone()
            
            # Get event data
            cursor.execute('''
                SELECT timestamp, event, data FROM telemetry_events 
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))
            
            events = cursor.fetchall()
            conn.close()
            
            return {
                "session_id": session_id,
                "session_data": dict(zip([col[0] for col in cursor.description], session_data)) if session_data else None,
                "events": [
                    {
                        "timestamp": event[0],
                        "type": event[1],
                        "data": event[2]
                    } for event in events
                ],
                "export_date": datetime.utcnow().isoformat(),
                "note": "Data has been anonymized for privacy protection"
            }
            
        except Exception as e:
            logger.error(f"Error exporting user data: {str(e)}")
            return {"error": "Failed to export data"}
    
    @staticmethod
    def delete_user_data(session_id: str, db_path: Path) -> bool:
        """Delete all data for a specific session (for deletion requests)"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Delete events
            cursor.execute('DELETE FROM telemetry_events WHERE session_id = ?', (session_id,))
            events_deleted = cursor.rowcount
            
            # Delete session
            cursor.execute('DELETE FROM telemetry_sessions WHERE session_id = ?', (session_id,))
            session_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted user data: {events_deleted} events, {session_deleted} session")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {str(e)}")
            return False