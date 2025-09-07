#!/usr/bin/env python3
"""
Join Room Health Monitor
Monitors the health of the join room system and alerts on issues.
"""

import sqlite3
import time
from datetime import datetime
from typing import Dict, Any, List
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))


class JoinRoomHealthMonitor:
    """Monitor join room operations for health and performance issues."""

    def __init__(self, db_path: str = "data/game_events.db"):
        """Initialize the health monitor."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def check_join_health(self, window_seconds: int = 300) -> Dict[str, Any]:
        """
        Check overall join system health.

        Args:
            window_seconds: Time window to analyze (default: 5 minutes)

        Returns:
            Dict with health metrics and status
        """
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total_attempts,
                SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
                AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms,
                MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait_ms
            FROM game_events_v2
            WHERE event_type = 'join_attempt'
              AND timestamp > unixepoch('now') - ?
        """, (window_seconds,))

        row = cursor.fetchone()

        if not row or row['total_attempts'] == 0:
            return {
                'status': 'NO_DATA',
                'message': 'No join attempts in time window',
                'total_attempts': 0
            }

        success_rate = (row['successful'] / row['total_attempts']) * 100 if row['total_attempts'] > 0 else 100

        health = {
            'timestamp': datetime.now().isoformat(),
            'window_seconds': window_seconds,
            'total_attempts': row['total_attempts'],
            'successful': row['successful'],
            'success_rate': round(success_rate, 2),
            'avg_lock_wait_ms': round(row['avg_lock_wait_ms'] or 0, 1),
            'max_lock_wait_ms': row['max_lock_wait_ms'] or 0,
            'status': 'HEALTHY',
            'alerts': []
        }

        # Check thresholds
        if health['max_lock_wait_ms'] > 3000:
            health['status'] = 'DEGRADED'
            health['alerts'].append({
                'severity': 'WARNING',
                'message': f"High lock contention detected: {health['max_lock_wait_ms']}ms max wait"
            })

        if health['success_rate'] < 80:
            health['status'] = 'UNHEALTHY'
            health['alerts'].append({
                'severity': 'CRITICAL',
                'message': f"Low join success rate: {health['success_rate']}%"
            })

        return health

    def detect_race_conditions(self, window_seconds: int = 3600) -> List[Dict[str, Any]]:
        """
        Detect potential race conditions in join operations.

        Args:
            window_seconds: Time window to analyze (default: 1 hour)

        Returns:
            List of rooms with potential race conditions
        """
        cursor = self.conn.execute("""
            WITH concurrent_joins AS (
                SELECT
                    e1.room_id,
                    e1.player_id as player1,
                    e2.player_id as player2,
                    e1.timestamp as t1,
                    e2.timestamp as t2,
                    ABS(e1.timestamp - e2.timestamp) as time_diff,
                    json_extract(e1.payload, '$.success') as p1_success,
                    json_extract(e2.payload, '$.success') as p2_success,
                    json_extract(e1.payload, '$.slot') as p1_slot,
                    json_extract(e2.payload, '$.slot') as p2_slot
                FROM game_events_v2 e1
                JOIN game_events_v2 e2
                  ON e1.room_id = e2.room_id
                  AND e1.id < e2.id
                  AND ABS(e1.timestamp - e2.timestamp) < 0.5
                WHERE e1.event_type = 'join_attempt'
                  AND e2.event_type = 'join_attempt'
                  AND e1.timestamp > unixepoch('now') - ?
            )
            SELECT
                room_id,
                COUNT(*) as concurrent_pairs,
                MIN(time_diff) as min_gap_seconds,
                SUM(CASE
                    WHEN p1_success = 1 AND p2_success = 1
                    AND p1_slot = p2_slot
                    THEN 1 ELSE 0
                END) as same_slot_successes
            FROM concurrent_joins
            GROUP BY room_id
            HAVING same_slot_successes > 0
        """, (window_seconds,))

        issues = []
        for row in cursor:
            issues.append({
                'room_id': row['room_id'],
                'concurrent_pairs': row['concurrent_pairs'],
                'min_gap_seconds': round(row['min_gap_seconds'], 3),
                'same_slot_successes': row['same_slot_successes'],
                'severity': 'CRITICAL'
            })

        return issues

    def get_high_contention_rooms(self, threshold_attempts: int = 10) -> List[Dict[str, Any]]:
        """
        Find rooms with high join contention.

        Args:
            threshold_attempts: Minimum attempts to consider high contention

        Returns:
            List of rooms with high contention
        """
        cursor = self.conn.execute("""
            SELECT
                room_id,
                COUNT(*) as total_attempts,
                COUNT(DISTINCT player_id) as unique_players,
                SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
                AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait,
                MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait,
                (MAX(timestamp) - MIN(timestamp)) as duration_seconds
            FROM game_events_v2
            WHERE event_type = 'join_attempt'
              AND timestamp > unixepoch('now') - 3600
            GROUP BY room_id
            HAVING total_attempts >= ?
            ORDER BY total_attempts DESC
        """, (threshold_attempts,))

        rooms = []
        for row in cursor:
            rooms.append({
                'room_id': row['room_id'],
                'total_attempts': row['total_attempts'],
                'unique_players': row['unique_players'],
                'successful': row['successful'],
                'success_rate': round((row['successful'] / row['total_attempts']) * 100, 2),
                'avg_lock_wait_ms': round(row['avg_lock_wait'] or 0, 1),
                'max_lock_wait_ms': row['max_lock_wait'] or 0,
                'duration_seconds': round(row['duration_seconds'], 1)
            })

        return rooms

    def get_error_distribution(self) -> Dict[str, int]:
        """Get distribution of join error types in the last hour."""
        cursor = self.conn.execute("""
            SELECT
                json_extract(payload, '$.error_type') as error_type,
                COUNT(*) as count
            FROM game_events_v2
            WHERE event_type = 'join_attempt'
              AND json_extract(payload, '$.success') = 0
              AND timestamp > unixepoch('now') - 3600
            GROUP BY error_type
            ORDER BY count DESC
        """)

        errors = {}
        for row in cursor:
            errors[row['error_type'] or 'unknown'] = row['count']

        return errors

    def continuous_monitoring(self, check_interval: int = 30):
        """
        Run continuous monitoring with alerts.

        Args:
            check_interval: Seconds between checks
        """
        print("Starting Join Room Health Monitor...")
        print(f"Checking every {check_interval} seconds")
        print("-" * 80)

        while True:
            try:
                # Check overall health
                health = self.check_join_health()

                print(f"\n[{health['timestamp']}] Join System Status: {health['status']}")
                print(f"  Attempts: {health['total_attempts']} | Success Rate: {health['success_rate']}%")
                print(f"  Lock Wait: avg={health['avg_lock_wait_ms']}ms, max={health['max_lock_wait_ms']}ms")

                # Print alerts
                for alert in health.get('alerts', []):
                    print(f"  🚨 {alert['severity']}: {alert['message']}")

                # Check for race conditions
                race_conditions = self.detect_race_conditions()
                if race_conditions:
                    print(f"  ⚠️  RACE CONDITIONS DETECTED in {len(race_conditions)} rooms!")
                    for rc in race_conditions[:3]:  # Show top 3
                        print(f"    - Room {rc['room_id']}: {rc['same_slot_successes']} conflicts")

                # Check high contention rooms
                high_contention = self.get_high_contention_rooms()
                if high_contention:
                    print(f"  📊 High contention in {len(high_contention)} rooms")
                    for room in high_contention[:3]:  # Show top 3
                        print(f"    - Room {room['room_id']}: {room['total_attempts']} attempts, "
                              f"{room['success_rate']}% success")

                # Show error distribution if any
                errors = self.get_error_distribution()
                if errors:
                    print("  📈 Error Distribution:")
                    for error_type, count in list(errors.items())[:3]:
                        print(f"    - {error_type}: {count}")

            except Exception as e:
                print(f"\n❌ Monitor error: {e}")

            time.sleep(check_interval)

    def generate_report(self) -> str:
        """Generate a comprehensive health report."""
        report = []
        report.append("=" * 80)
        report.append("JOIN ROOM HEALTH REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)

        # Overall health
        health = self.check_join_health()
        report.append(f"\nOVERALL HEALTH: {health['status']}")
        report.append(f"Success Rate: {health['success_rate']}%")
        report.append(f"Lock Performance: avg={health['avg_lock_wait_ms']}ms, max={health['max_lock_wait_ms']}ms")

        # Race conditions
        race_conditions = self.detect_race_conditions()
        report.append(f"\nRACE CONDITIONS: {len(race_conditions)} detected")
        if race_conditions:
            report.append("Affected rooms:")
            for rc in race_conditions:
                report.append(f"  - {rc['room_id']}: {rc['same_slot_successes']} conflicts")

        # High contention
        high_contention = self.get_high_contention_rooms()
        report.append(f"\nHIGH CONTENTION ROOMS: {len(high_contention)}")
        for room in high_contention[:5]:
            report.append(f"  - {room['room_id']}: {room['total_attempts']} attempts, "
                         f"{room['success_rate']}% success, max wait {room['max_lock_wait_ms']}ms")

        # Error distribution
        errors = self.get_error_distribution()
        report.append("\nERROR DISTRIBUTION:")
        for error_type, count in errors.items():
            report.append(f"  - {error_type}: {count}")

        return "\n".join(report)


def main():
    """Main entry point for the monitor."""
    import argparse

    parser = argparse.ArgumentParser(description="Join Room Health Monitor")
    parser.add_argument("--db", default="data/game_events.db", help="Path to database")
    parser.add_argument("--report", action="store_true", help="Generate report and exit")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")

    args = parser.parse_args()

    monitor = JoinRoomHealthMonitor(args.db)

    if args.report:
        print(monitor.generate_report())
    else:
        try:
            monitor.continuous_monitoring(args.interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


if __name__ == "__main__":
    main()
