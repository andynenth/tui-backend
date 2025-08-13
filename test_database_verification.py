#!/usr/bin/env python3
"""
Database Verification Test

This test verifies that game data was written correctly to the database
through the optimization pipeline. Can be used to check any room ID.

Usage:
    python test_database_verification.py E2A1DF
    python test_database_verification.py --all
"""

import asyncio
import sqlite3
import json
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseVerifier:
    """Verifies database writes and optimization pipeline effectiveness"""
    
    def __init__(self, db_path: str = "game_events.db"):
        self.db_path = db_path
        
    def test_room_data(self, room_id: str) -> Dict[str, Any]:
        """
        Test if room data was written correctly to the database
        
        Args:
            room_id: The room to check (e.g., 'E2A1DF')
            
        Returns:
            Dict with test results
        """
        results = {
            "room_id": room_id,
            "v1_events": 0,
            "v2_game_summary": None,
            "v2_round_snapshots": [],
            "v2_events": 0,
            "optimization_working": False,
            "data_completeness": {},
            "errors": []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Check V1 schema (old EventStore)
            results["v1_events"] = self._check_v1_events(conn, room_id)
            
            # Check V2 schema (optimized)
            results["v2_game_summary"] = self._check_v2_game_summary(conn, room_id)
            results["v2_round_snapshots"] = self._check_v2_round_snapshots(conn, room_id)
            results["v2_events"] = self._check_v2_events(conn, room_id)
            
            # Analyze optimization effectiveness
            results["optimization_working"] = self._analyze_optimization(results)
            results["data_completeness"] = self._check_data_completeness(results)
            
            conn.close()
            
        except Exception as e:
            results["errors"].append(f"Database error: {e}")
            logger.error(f"Error checking room {room_id}: {e}")
            
        return results
    
    def _check_v1_events(self, conn: sqlite3.Connection, room_id: str) -> int:
        """Check V1 EventStore events"""
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM game_events WHERE room_id = ?",
                (room_id,)
            )
            return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Table doesn't exist
            return 0
    
    def _check_v2_game_summary(self, conn: sqlite3.Connection, room_id: str) -> Optional[Dict]:
        """Check V2 game summary"""
        try:
            cursor = conn.execute(
                """SELECT room_id, players, total_rounds, final_scores, 
                          winner, started_at, completed_at, duration_seconds
                   FROM game_summaries WHERE room_id = ?""",
                (room_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "room_id": row[0],
                    "players": json.loads(row[1]) if row[1] else [],
                    "total_rounds": row[2],
                    "final_scores": json.loads(row[3]) if row[3] else {},
                    "winner": row[4],
                    "started_at": row[5],
                    "completed_at": row[6],
                    "duration_seconds": row[7]
                }
        except (sqlite3.OperationalError, json.JSONDecodeError):
            pass
        return None
    
    def _check_v2_round_snapshots(self, conn: sqlite3.Connection, room_id: str) -> List[Dict]:
        """Check V2 round snapshots"""
        try:
            cursor = conn.execute(
                """SELECT round_number, starter_player, starter_reason,
                          initial_hands, declarations, turn_sequence, 
                          round_scores, cumulative_scores, created_at, total_turns
                   FROM round_snapshots WHERE room_id = ? ORDER BY round_number""",
                (room_id,)
            )
            
            rounds = []
            for row in cursor.fetchall():
                try:
                    rounds.append({
                        "round_number": row[0],
                        "starter_player": row[1],
                        "starter_reason": row[2],
                        "initial_hands": json.loads(row[3]) if row[3] else {},
                        "declarations": json.loads(row[4]) if row[4] else {},
                        "turn_sequence": json.loads(row[5]) if row[5] else [],
                        "round_scores": json.loads(row[6]) if row[6] else {},
                        "cumulative_scores": json.loads(row[7]) if row[7] else {},
                        "created_at": row[8],
                        "total_turns": row[9] if len(row) > 9 else 0
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error in round {row[0]}: {e}")
            
            return rounds
        except sqlite3.OperationalError:
            return []
    
    def _check_v2_events(self, conn: sqlite3.Connection, room_id: str) -> int:
        """Check V2 minimal events"""
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM game_events_v2 WHERE room_id = ?",
                (room_id,)
            )
            return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            return 0
    
    def _analyze_optimization(self, results: Dict) -> bool:
        """Determine if optimization pipeline is working"""
        # Optimization is working if:
        # 1. We have V2 data (round snapshots or game summary)
        # 2. V2 events are much fewer than V1 events (compression working)
        
        has_v2_data = (
            results["v2_game_summary"] is not None or 
            len(results["v2_round_snapshots"]) > 0
        )
        
        # If we have both V1 and V2, check compression ratio
        if results["v1_events"] > 0 and results["v2_events"] > 0:
            compression_ratio = results["v2_events"] / results["v1_events"]
            compression_effective = compression_ratio < 0.5  # 50%+ reduction
        else:
            compression_effective = True  # Can't measure, assume working
        
        return has_v2_data and compression_effective
    
    def _check_data_completeness(self, results: Dict) -> Dict[str, Any]:
        """Check if all expected data is present"""
        completeness = {
            "has_game_summary": results["v2_game_summary"] is not None,
            "has_round_data": len(results["v2_round_snapshots"]) > 0,
            "round_data_complete": True,
            "missing_fields": []
        }
        
        # Check round data completeness
        for round_data in results["v2_round_snapshots"]:
            required_fields = [
                "round_number", "starter_player", "declarations", 
                "round_scores", "cumulative_scores"
            ]
            for field in required_fields:
                if not round_data.get(field):
                    completeness["missing_fields"].append(f"Round {round_data['round_number']}: {field}")
                    completeness["round_data_complete"] = False
        
        return completeness
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        room_id = results["room_id"]
        
        print(f"\n{'='*60}")
        print(f"DATABASE VERIFICATION RESULTS - ROOM {room_id}")
        print(f"{'='*60}")
        
        # Overall status
        if results["optimization_working"]:
            print("✅ OPTIMIZATION PIPELINE: WORKING")
        else:
            print("❌ OPTIMIZATION PIPELINE: NOT WORKING")
        
        print(f"\n📊 EVENT COUNTS:")
        print(f"   V1 Events (old schema): {results['v1_events']}")
        print(f"   V2 Events (optimized):  {results['v2_events']}")
        
        if results["v1_events"] > 0 and results["v2_events"] > 0:
            reduction = (1 - results["v2_events"] / results["v1_events"]) * 100
            print(f"   Compression ratio:      {reduction:.1f}% reduction")
        
        # V2 Game Summary
        print(f"\n🎮 GAME SUMMARY (V2):")
        if results["v2_game_summary"]:
            summary = results["v2_game_summary"]
            print(f"   ✅ Found: {len(summary['players'])} players, {summary['total_rounds']} rounds")
            if summary["winner"]:
                print(f"   🏆 Winner: {summary['winner']}")
            if summary["completed_at"]:
                duration = summary["duration_seconds"] or 0
                print(f"   ⏱️  Duration: {duration//60}m {duration%60}s")
        else:
            print("   ❌ No game summary found")
        
        # V2 Round Snapshots
        print(f"\n🔄 ROUND SNAPSHOTS (V2):")
        if results["v2_round_snapshots"]:
            for round_data in results["v2_round_snapshots"]:
                round_num = round_data["round_number"]
                starter = round_data["starter_player"]
                declarations = round_data["declarations"]
                scores = round_data["round_scores"]
                
                print(f"   ✅ Round {round_num}: Starter={starter}")
                print(f"      📋 Declarations: {len(declarations)} players")
                print(f"      🏆 Scores: {len(scores)} players")
                
                # Show sample data
                if declarations:
                    sample_player = list(declarations.keys())[0]
                    print(f"      📝 Sample: {sample_player} declared {declarations[sample_player]}")
        else:
            print("   ❌ No round snapshots found")
        
        # Data Completeness
        print(f"\n📋 DATA COMPLETENESS:")
        completeness = results["data_completeness"]
        if completeness["round_data_complete"]:
            print("   ✅ All required fields present")
        else:
            print("   ❌ Missing fields detected:")
            for field in completeness["missing_fields"]:
                print(f"      - {field}")
        
        # Errors
        if results["errors"]:
            print(f"\n❌ ERRORS:")
            for error in results["errors"]:
                print(f"   - {error}")
        
        print(f"\n{'='*60}")
    
    def list_all_rooms(self) -> List[str]:
        """List all rooms in the database"""
        rooms = set()
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Check V1 schema
            try:
                cursor = conn.execute("SELECT DISTINCT room_id FROM game_events")
                rooms.update(row[0] for row in cursor.fetchall())
            except sqlite3.OperationalError:
                pass
            
            # Check V2 schema
            try:
                cursor = conn.execute("SELECT DISTINCT room_id FROM game_summaries")
                rooms.update(row[0] for row in cursor.fetchall())
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor = conn.execute("SELECT DISTINCT room_id FROM round_snapshots")
                rooms.update(row[0] for row in cursor.fetchall())
            except sqlite3.OperationalError:
                pass
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error listing rooms: {e}")
        
        return sorted(list(rooms))


def main():
    """Main test function"""
    verifier = DatabaseVerifier()
    
    if len(sys.argv) < 2:
        print("Usage: python test_database_verification.py <ROOM_ID>")
        print("       python test_database_verification.py --all")
        print("\nExample: python test_database_verification.py E2A1DF")
        return
    
    if sys.argv[1] == "--all":
        # Test all rooms
        rooms = verifier.list_all_rooms()
        print(f"Found {len(rooms)} rooms in database: {rooms}")
        
        for room_id in rooms:
            results = verifier.test_room_data(room_id)
            verifier.print_results(results)
    else:
        # Test specific room
        room_id = sys.argv[1].upper()
        print(f"Testing room: {room_id}")
        
        results = verifier.test_room_data(room_id)
        verifier.print_results(results)
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not results["optimization_working"]:
            print("   - Check if events are flowing through MigrationAdapter")
            print("   - Verify MIGRATION_MODE environment variable")
            print("   - Check application logs for MigrationAdapter debug messages")
        
        if not results["data_completeness"]["round_data_complete"]:
            print("   - Some game data may not have been stored completely")
            print("   - Check for errors during round completion")
        
        if results["v1_events"] > 0 and results["v2_events"] == 0:
            print("   - Events are going to V1 schema only (old path)")
            print("   - Optimization pipeline may not be active")
        
        if results["v2_events"] > 0 and not results["v2_round_snapshots"]:
            print("   - V2 events exist but no round snapshots")
            print("   - Check round completion logic")


if __name__ == "__main__":
    main()