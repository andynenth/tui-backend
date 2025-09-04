#!/usr/bin/env python3
"""
Automated test runner for bot takeover data collection tests.
Executes test cases and generates a comprehensive report.
"""

import subprocess
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class BotTakeoverTestRunner:
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.results = []
        self.room_id = None
        self.start_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "")
        print(f"[{timestamp}] {symbol} {message}")
        
    def api_call(self, endpoint: str) -> Optional[Dict]:
        """Make API call and return JSON response"""
        try:
            result = subprocess.run(
                ["curl", "-s", f"{self.base_url}{endpoint}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
            return None
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            self.log(f"API call failed: {endpoint} - {str(e)}", "ERROR")
            return None
            
    def check_server_health(self) -> bool:
        """Verify server is healthy"""
        response = self.api_call("/api/health")
        if response and response.get("status") == "healthy":
            self.log("Server is healthy", "SUCCESS")
            return True
        self.log("Server health check failed", "ERROR")
        return False
        
    def get_events(self, event_type: Optional[str] = None) -> List[Dict]:
        """Get events for the room, optionally filtered by type"""
        if not self.room_id:
            return []
            
        endpoint = f"/api/debug/events/{self.room_id}"
        if event_type:
            endpoint += f"?event_type={event_type}"
            
        response = self.api_call(endpoint)
        return response.get("events", []) if response else []
        
    def get_event_count(self, event_type: str) -> int:
        """Get count of specific event type"""
        events = self.get_events(event_type)
        return len(events)
        
    def wait_for_event(self, event_type: str, timeout: int = 10) -> Tuple[bool, float]:
        """Wait for an event to appear, return (success, time_waited)"""
        self.log(f"Waiting for event: {event_type} (timeout: {timeout}s)")
        start = time.time()
        
        while time.time() - start < timeout:
            if self.get_event_count(event_type) > 0:
                waited = time.time() - start
                self.log(f"Event {event_type} detected after {waited:.1f}s", "SUCCESS")
                return True, waited
            time.sleep(0.5)
            
        self.log(f"Timeout waiting for event: {event_type}", "WARNING")
        return False, timeout
        
    def check_server_logs(self, error_pattern: str = "ERROR|AttributeError|TypeError") -> List[str]:
        """Check server logs for errors"""
        try:
            result = subprocess.run(
                ["grep", "-E", error_pattern, "test_server_full.log"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip().split('\n')[-10:]  # Last 10 errors
            return []
        except:
            return []
            
    def get_connection_timeline(self, player_name: Optional[str] = None) -> Dict:
        """Get connection timeline for analysis"""
        endpoint = f"/api/debug/connection-timeline/{self.room_id}"
        if player_name:
            endpoint += f"?player_name={player_name}"
        return self.api_call(endpoint) or {}
        
    def get_bot_control_analysis(self) -> Dict:
        """Get bot control analysis"""
        endpoint = f"/api/debug/bot-control-analysis/{self.room_id}"
        return self.api_call(endpoint) or {}
        
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        self.log(f"\n{'='*60}")
        self.log(f"Running test: {test_name}")
        self.log(f"{'='*60}")
        
        # Clear any existing errors
        initial_errors = len(self.check_server_logs())
        
        start_time = time.time()
        test_result = {
            "name": test_name,
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING",
            "events_captured": {},
            "errors": []
        }
        
        try:
            # Run the test
            success, details = test_func()
            duration = time.time() - start_time
            
            # Check for new server errors
            final_errors = self.check_server_logs()
            new_errors = final_errors[initial_errors:] if len(final_errors) > initial_errors else []
            
            test_result.update({
                "status": "PASS" if success and not new_errors else "FAIL",
                "duration": f"{duration:.2f}s",
                "details": details,
                "server_errors": new_errors
            })
            
            if success and not new_errors:
                self.log(f"Test {test_name}: PASSED in {duration:.2f}s", "SUCCESS")
            else:
                self.log(f"Test {test_name}: FAILED", "ERROR")
                if new_errors:
                    self.log(f"Server errors detected: {len(new_errors)}", "ERROR")
                    
        except Exception as e:
            test_result.update({
                "status": "ERROR",
                "error": str(e),
                "duration": f"{time.time() - start_time:.2f}s"
            })
            self.log(f"Test {test_name}: ERROR - {e}", "ERROR")
            
        self.results.append(test_result)
        return test_result["status"] == "PASS"
        
    # Test Case Implementations
    
    def test_server_health(self) -> Tuple[bool, Dict]:
        """Test Case 0: Verify server is healthy and endpoints work"""
        details = {"checks": {}}
        
        # Health check
        health = self.check_server_health()
        details["checks"]["health"] = health
        
        # Event endpoint
        events_work = self.api_call(f"/api/debug/events/{self.room_id}") is not None
        details["checks"]["events_endpoint"] = events_work
        
        # Timeline endpoint  
        timeline_work = self.api_call(f"/api/debug/connection-timeline/{self.room_id}") is not None
        details["checks"]["timeline_endpoint"] = timeline_work
        
        # Bot analysis endpoint
        analysis_work = self.api_call(f"/api/debug/bot-control-analysis/{self.room_id}") is not None
        details["checks"]["analysis_endpoint"] = analysis_work
        
        all_pass = all(details["checks"].values())
        return all_pass, details
        
    def test_basic_event_collection(self) -> Tuple[bool, Dict]:
        """Test Case 1: Verify basic event collection is working"""
        details = {"event_counts": {}}
        
        # Check that we can retrieve events
        all_events = self.get_events()
        details["total_events"] = len(all_events)
        
        # Check specific event types
        event_types = ["game_started", "round_started", "hands_dealt", "human_action", "bot_action"]
        for event_type in event_types:
            count = self.get_event_count(event_type)
            details["event_counts"][event_type] = count
            
        # Should have at least some events
        has_events = details["total_events"] > 0
        has_game_events = details["event_counts"].get("game_started", 0) > 0
        
        return has_events and has_game_events, details
        
    def test_action_attribution(self) -> Tuple[bool, Dict]:
        """Test Case 2: Verify actions are properly attributed to human/bot"""
        details = {
            "human_actions": 0,
            "bot_actions": 0,
            "unattributed_actions": 0
        }
        
        # Get all action events
        human_actions = self.get_events("human_action")
        bot_actions = self.get_events("bot_action")
        
        details["human_actions"] = len(human_actions)
        details["bot_actions"] = len(bot_actions)
        
        # Verify action details
        if human_actions:
            first_human = human_actions[0].get("payload", {})
            details["sample_human_action"] = {
                "player": first_human.get("player_name"),
                "is_bot": first_human.get("is_bot"),
                "action_type": first_human.get("action_type")
            }
            
        if bot_actions:
            first_bot = bot_actions[0].get("payload", {})
            details["sample_bot_action"] = {
                "player": first_bot.get("player_name"),
                "is_bot": first_bot.get("is_bot"),
                "action_type": first_bot.get("action_type")
            }
        
        # Should have both types
        has_both = details["human_actions"] > 0 and details["bot_actions"] > 0
        
        # Verify is_bot flag is correct
        human_correct = all(not a.get("payload", {}).get("is_bot", True) for a in human_actions)
        bot_correct = all(a.get("payload", {}).get("is_bot", False) for a in bot_actions)
        
        return has_both and human_correct and bot_correct, details
        
    def simulate_disconnection_scenario(self) -> Tuple[bool, Dict]:
        """Test Case 3: Simulate disconnection (requires manual browser action)"""
        details = {
            "events_before": {},
            "events_after": {},
            "timeline": []
        }
        
        # Get baseline
        details["events_before"]["disconnected"] = self.get_event_count("player_disconnected")
        details["events_before"]["scheduled"] = self.get_event_count("bot_takeover_scheduled")
        details["events_before"]["activated"] = self.get_event_count("bot_takeover_activated")
        
        self.log("MANUAL ACTION REQUIRED: Close browser to simulate disconnection")
        self.log("Waiting 10 seconds for manual disconnection...")
        time.sleep(10)
        
        # Check what happened
        details["events_after"]["disconnected"] = self.get_event_count("player_disconnected")
        details["events_after"]["scheduled"] = self.get_event_count("bot_takeover_scheduled")
        details["events_after"]["activated"] = self.get_event_count("bot_takeover_activated")
        
        # Calculate changes
        new_disconnects = details["events_after"]["disconnected"] - details["events_before"]["disconnected"]
        new_scheduled = details["events_after"]["scheduled"] - details["events_before"]["scheduled"]
        new_activated = details["events_after"]["activated"] - details["events_before"]["activated"]
        
        details["new_events"] = {
            "disconnected": new_disconnects,
            "scheduled": new_scheduled,
            "activated": new_activated
        }
        
        # Check timeline
        timeline = self.get_connection_timeline()
        details["timeline_events"] = timeline.get("timeline_events", 0)
        
        # Success if we see disconnection events
        success = new_disconnects > 0 or new_scheduled > 0
        
        return success, details
        
    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        print("\n\n" + "="*80)
        print("BOT TAKEOVER DATA COLLECTION TEST REPORT")
        print("="*80)
        print(f"Room ID: {self.room_id}")
        print(f"Generated: {datetime.now()}")
        print(f"Total Duration: {total_duration:.1f}s")
        print()
        
        # Test Summary
        print("TEST SUMMARY")
        print("-" * 40)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Errors: {errors}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        print()
        
        # Individual Test Results
        print("INDIVIDUAL TEST RESULTS")
        print("-" * 40)
        for result in self.results:
            status_symbol = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}.get(result["status"], "❓")
            print(f"\n{status_symbol} {result['name']}")
            print(f"   Status: {result['status']}")
            print(f"   Duration: {result.get('duration', 'N/A')}")
            
            if result.get("details"):
                print("   Details:")
                self._print_details(result["details"], indent=6)
                
            if result.get("server_errors"):
                print(f"   Server Errors: {len(result['server_errors'])}")
                for error in result["server_errors"][:3]:  # Show first 3
                    print(f"      - {error[:100]}...")
                    
            if result.get("error"):
                print(f"   Error: {result['error']}")
        
        # Event Summary
        print("\n\nEVENT COLLECTION SUMMARY")
        print("-" * 40)
        self._print_event_summary()
        
        # Bot Control Analysis
        print("\n\nBOT CONTROL ANALYSIS")
        print("-" * 40)
        analysis = self.get_bot_control_analysis()
        if analysis.get("summary"):
            summary = analysis["summary"]
            print(f"Total Players: {summary.get('total_players', 0)}")
            print(f"Total Disconnections: {summary.get('total_disconnections', 0)}")
            print(f"Total Takeovers: {summary.get('total_takeovers', 0)}")
            print(f"Failed Releases: {summary.get('total_failed_releases', 0)}")
            print(f"Blocked Actions: {summary.get('total_blocked_actions', 0)}")
            
        # Recommendations
        print("\n\nRECOMMENDATIONS")
        print("-" * 40)
        self._generate_recommendations()
        
    def _print_details(self, details: Dict, indent: int = 0):
        """Pretty print nested details"""
        prefix = " " * indent
        for key, value in details.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self._print_details(value, indent + 2)
            elif isinstance(value, list):
                print(f"{prefix}{key}: [{len(value)} items]")
            else:
                print(f"{prefix}{key}: {value}")
                
    def _print_event_summary(self):
        """Print summary of all events collected"""
        event_types = [
            "player_disconnected", "bot_takeover_scheduled", "bot_takeover_activated",
            "bot_takeover_cancelled", "player_reconnected", "bot_control_released",
            "human_action", "bot_action", "action_blocked", "connection_lost"
        ]
        
        for event_type in event_types:
            count = self.get_event_count(event_type)
            if count > 0:
                print(f"{event_type}: {count}")
                # Show sample
                events = self.get_events(event_type)
                if events:
                    sample = events[0].get("payload", {})
                    print(f"  Sample: {json.dumps(sample, default=str)[:100]}...")
                    
    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for missing events
        if self.get_event_count("player_disconnected") == 0:
            recommendations.append("❌ No disconnection events captured - check WebSocket handlers")
            
        if self.get_event_count("bot_takeover_activated") == 0:
            recommendations.append("⚠️ No bot takeover activations - verify grace period logic")
            
        # Check for errors
        errors_found = any(r.get("server_errors") for r in self.results)
        if errors_found:
            recommendations.append("❌ Server errors detected - review and fix before production")
            
        # Check event attribution
        human_count = self.get_event_count("human_action")
        bot_count = self.get_event_count("bot_action")
        if human_count == 0 or bot_count == 0:
            recommendations.append("⚠️ Missing action attribution - verify is_bot detection")
            
        if not recommendations:
            recommendations.append("✅ All key events are being captured correctly")
            recommendations.append("✅ Ready to deploy to production for real-world data collection")
            
        for rec in recommendations:
            print(f"• {rec}")
            
    def run_all_tests(self, room_id: str):
        """Run all test cases"""
        self.room_id = room_id
        self.start_time = time.time()
        
        self.log(f"Starting Bot Takeover Test Suite for room {room_id}")
        
        # Run tests in sequence
        self.run_test("Server Health Check", self.test_server_health)
        self.run_test("Basic Event Collection", self.test_basic_event_collection)
        self.run_test("Action Attribution", self.test_action_attribution)
        self.run_test("Disconnection Simulation", self.simulate_disconnection_scenario)
        
        # Generate final report
        self.generate_report()
        
        # Save report to file
        report_file = f"bot_takeover_test_report_{room_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "room_id": room_id,
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - self.start_time,
                "results": self.results
            }, f, indent=2, default=str)
        self.log(f"\nReport saved to: {report_file}", "SUCCESS")

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_bot_takeover_tests.py <room_id>")
        print("\nExample: python run_bot_takeover_tests.py ABC123")
        print("\nNote: Make sure server is running and you have an active game in the specified room")
        sys.exit(1)
        
    room_id = sys.argv[1]
    
    # Check if log file exists
    if not os.path.exists("test_server_full.log"):
        print("WARNING: test_server_full.log not found. Server logs will not be checked.")
        print("Make sure server is running with: ./start.sh > test_server_full.log 2>&1 &")
        
    runner = BotTakeoverTestRunner()
    runner.run_all_tests(room_id)

if __name__ == "__main__":
    main()