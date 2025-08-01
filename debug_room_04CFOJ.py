#!/usr/bin/env python3

"""
Debug and inspect room 04CFOJ game state
Provides tools to check the current phase and manually trigger transitions
"""

import aiohttp
import asyncio
import json
import sys
import time
from typing import Dict, Any, Optional

# Debug endpoints
BASE_URL = "http://localhost:8000"
DEBUG_ENDPOINTS = {
    "events": f"{BASE_URL}/api/debug/events/04CFOJ",
    "replay": f"{BASE_URL}/api/debug/replay/04CFOJ", 
    "export": f"{BASE_URL}/api/debug/export/04CFOJ",
    "logs": f"{BASE_URL}/api/debug/logs?limit=50&search=04CFOJ",
    "live": f"{BASE_URL}/api/debug/logs/live",
    "stats": f"{BASE_URL}/api/debug/stats"
}

class Room04CFOJDebugger:
    """Debug tools for room 04CFOJ"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_server_status(self) -> bool:
        """Check if the backend server is running"""
        try:
            async with self.session.get(f"{BASE_URL}/api/debug/stats", timeout=5) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            return False
    
    async def get_room_events(self) -> Optional[Dict[str, Any]]:
        """Get all events for room 04CFOJ"""
        try:
            async with self.session.get(DEBUG_ENDPOINTS['events']) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"❌ Failed to get events: {resp.status}")
                    return None
        except Exception as e:
            print(f"❌ Error getting events: {e}")
            return None
    
    async def get_room_state(self) -> Optional[Dict[str, Any]]:
        """Get reconstructed room state from events"""
        try:
            async with self.session.get(DEBUG_ENDPOINTS['replay']) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"❌ Failed to get state: {resp.status}")
                    return None
        except Exception as e:
            print(f"❌ Error getting state: {e}")
            return None
    
    async def get_debug_logs(self) -> Optional[Dict[str, Any]]:
        """Get debug logs related to room 04CFOJ"""
        try:
            async with self.session.get(DEBUG_ENDPOINTS['logs']) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"❌ Failed to get logs: {resp.status}")
                    return None
        except Exception as e:
            print(f"❌ Error getting logs: {e}")
            return None
    
    async def export_room_history(self) -> Optional[Dict[str, Any]]:
        """Export complete room history"""
        try:
            async with self.session.get(DEBUG_ENDPOINTS['export']) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"❌ Failed to export history: {resp.status}")
                    return None
        except Exception as e:
            print(f"❌ Error exporting history: {e}")
            return None
    
    def analyze_phase_state(self, events_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the current phase state from events"""
        analysis = {
            "current_phase": "UNKNOWN",
            "last_phase_change": None,
            "preparation_events": [],
            "timeout_issues": [],
            "stuck_indicators": []
        }
        
        if not events_data or "events" not in events_data:
            return analysis
        
        events = events_data["events"]
        phase_changes = []
        preparation_events = []
        
        for event in events:
            event_type = event.get("event_type", "")
            payload = event.get("payload", {})
            timestamp = event.get("timestamp", "")
            
            # Track phase changes
            if event_type == "phase_change":
                phase = payload.get("phase", "")
                phase_changes.append({
                    "phase": phase,
                    "timestamp": timestamp,
                    "payload": payload
                })
                analysis["current_phase"] = phase
            
            # Track preparation-specific events
            if event_type in ["phase_change", "phase_data_update"] and "PREPARATION" in str(payload):
                preparation_events.append({
                    "event_type": event_type,
                    "timestamp": timestamp, 
                    "payload": payload
                })
        
        analysis["phase_changes"] = phase_changes
        analysis["preparation_events"] = preparation_events
        
        if phase_changes:
            analysis["last_phase_change"] = phase_changes[-1]
        
        # Check for timeout issues
        if analysis["current_phase"] == "PREPARATION":
            # Look for timeout-related events
            current_time = time.time()
            for prep_event in preparation_events:
                payload = prep_event.get("payload", {})
                if "timeout_warning" in payload or "decision_timeout" in payload:
                    analysis["timeout_issues"].append(prep_event)
                
                # Check if we've been stuck for too long
                event_time = prep_event.get("timestamp", 0)
                if current_time - event_time > 60:  # 1 minute
                    analysis["stuck_indicators"].append({
                        "reason": "phase_timeout",
                        "duration_seconds": current_time - event_time,
                        "event": prep_event
                    })
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Pretty print the analysis"""
        print("🔍 ROOM 04CFOJ PHASE ANALYSIS")
        print("=" * 50)
        
        print(f"Current Phase: {analysis['current_phase']}")
        
        if analysis["last_phase_change"]:
            last_change = analysis["last_phase_change"]
            print(f"Last Phase Change: {last_change['phase']} at {last_change['timestamp']}")
        
        if analysis["preparation_events"]:
            print(f"\n📋 Preparation Events ({len(analysis['preparation_events'])}):")
            for i, event in enumerate(analysis["preparation_events"][-5:]):  # Last 5 events
                print(f"  {i+1}. {event['event_type']} - {event['timestamp']}")
                if event['payload']:
                    print(f"     {json.dumps(event['payload'], indent=6)}")
        
        if analysis["timeout_issues"]:
            print(f"\n⏰ Timeout Issues ({len(analysis['timeout_issues'])}):")
            for issue in analysis["timeout_issues"]:
                print(f"  - {issue['event_type']}: {issue['payload']}")
        
        if analysis["stuck_indicators"]:
            print(f"\n🚨 Stuck Indicators ({len(analysis['stuck_indicators'])}):")
            for indicator in analysis["stuck_indicators"]:
                print(f"  - {indicator['reason']}: {indicator['duration_seconds']}s")
    
    def get_debug_recommendations(self, analysis: Dict[str, Any]) -> list:
        """Get recommendations for debugging the stuck state"""
        recommendations = []
        
        if analysis["current_phase"] == "PREPARATION":
            recommendations.extend([
                "1. Check if weak hands were detected and are awaiting redeal decisions",
                "2. Look for timeout mechanisms in preparation_state.py (_monitor_decision_timeout)",
                "3. Check if all bots have made redeal decisions via bot manager",
                "4. Verify the 30-second timeout is functioning (_force_timeout_decisions)",
                "5. Inspect weak_players_awaiting set and redeal_decisions dict"
            ])
        
        if analysis["timeout_issues"]:
            recommendations.append("6. Timeout warnings detected - phase should auto-advance soon")
        
        if analysis["stuck_indicators"]:
            recommendations.extend([
                "7. Phase appears stuck - consider manual intervention",
                "8. Check if _processing_decisions lock is stuck",
                "9. Verify transition conditions in check_transition_conditions()"
            ])
        
        recommendations.extend([
            "10. Use WebSocket to send manual redeal responses for any pending weak players",
            "11. Check backend logs for state machine processing errors",
            "12. Inspect the GameStateMachine._transition_to() calls"
        ])
        
        return recommendations

async def main():
    """Main debugging function"""
    print("🚀 ROOM 04CFOJ DEBUGGER")
    print("=" * 50)
    
    async with Room04CFOJDebugger() as debugger:
        # Check server status
        print("📡 Checking server status...")
        if not await debugger.check_server_status():
            print("❌ Backend server is not running!")
            print("💡 Start it with: cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
            return
        
        print("✅ Server is running")
        
        # Get room events
        print("\n📊 Fetching room events...")
        events_data = await debugger.get_room_events()
        
        if not events_data:
            print("❌ No events found for room 04CFOJ")
            print("💡 This could mean:")
            print("   - Room doesn't exist")
            print("   - Room was cleaned up")
            print("   - Room ID is different")
            return
        
        print(f"✅ Found {events_data.get('total_events', 0)} events")
        
        # Analyze phase state
        print("\n🔍 Analyzing phase state...")
        analysis = debugger.analyze_phase_state(events_data)
        debugger.print_analysis(analysis)
        
        # Get recommendations
        print("\n💡 DEBUG RECOMMENDATIONS:")
        recommendations = debugger.get_debug_recommendations(analysis)
        for rec in recommendations:
            print(f"   {rec}")
        
        # Get debug logs
        print("\n📋 Recent debug logs...")
        logs_data = await debugger.get_debug_logs()
        if logs_data and "logs" in logs_data:
            print(f"Found {len(logs_data['logs'])} relevant log entries:")
            for log in logs_data["logs"][-10:]:  # Last 10 logs
                print(f"  [{log.get('level', 'INFO')}] {log.get('message', '')}")
        
        print("\n🔧 MANUAL INTERVENTION OPTIONS:")
        print("=" * 50)
        print("1. WebSocket Event Injection:")
        print("   - Connect to ws://localhost:8000/ws/04CFOJ")
        print("   - Send redeal responses for weak players")
        print("   - Force phase transition events")
        
        print("\n2. Direct API Calls:")
        print("   - Use debug endpoints to inspect state")
        print("   - Check event history for stuck conditions")
        
        print("\n3. Backend Investigation:")
        print("   - Check preparation_state.py timeout mechanisms")
        print("   - Verify GameStateMachine transition logic")
        print("   - Inspect bot manager decision making")
        
        # Export full history for detailed analysis
        print("\n📤 Exporting full room history...")
        history = await debugger.export_room_history()
        if history:
            with open("room_04CFOJ_debug_export.json", "w") as f:
                json.dump(history, f, indent=2)
            print("   ✅ Exported to room_04CFOJ_debug_export.json")

if __name__ == "__main__":
    asyncio.run(main())