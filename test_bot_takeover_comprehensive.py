#!/usr/bin/env python3
"""
Comprehensive test plan for bot takeover data collection using Playwright MCP

Test Strategy:
1. Start server with ./start.sh (manual step - run in separate terminal)
2. Use Playwright to simulate real player behavior
3. Test disconnect/reconnect cycle
4. Verify all events are collected
5. Check debug endpoints work correctly

Prerequisites:
- Run in terminal 1: ./start.sh
- Run in terminal 2: python test_bot_takeover_comprehensive.py
"""

import time
import requests
import asyncio

class BotTakeoverTest:
    def __init__(self):
        self.base_url = "http://localhost:5050"
        self.ws_url = "ws://localhost:5050"
        self.room_id = None
        self.players = []
        
    def wait_for_server(self, timeout=30):
        """Wait for server to be ready"""
        print("⏳ Waiting for server to be ready...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/health")
                if resp.status_code == 200:
                    print("✅ Server is ready")
                    return True
            except:
                pass
            time.sleep(1)
        raise Exception("Server failed to start")
    
    def verify_event_exists(self, event_type, player_name=None, timeout=10):
        """Check if event exists in database"""
        print(f"🔍 Checking for {event_type} event...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/debug/events/{self.room_id}?event_type={event_type}")
                if resp.status_code == 200:
                    events = resp.json()["events"]
                    if player_name:
                        events = [e for e in events if e.get("player_id") == player_name]
                    if events:
                        print(f"✅ Found {event_type} event")
                        return events[0]
            except:
                pass
            time.sleep(0.5)
        print(f"❌ {event_type} event not found")
        return None
    
    def check_timeline(self):
        """Check connection timeline endpoint"""
        print("\n📊 Checking connection timeline...")
        resp = requests.get(f"{self.base_url}/api/debug/connection-timeline/{self.room_id}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Timeline has {data['timeline_events']} events")
            print(f"   Issues found: {len(data['issues_found'])}")
            for issue in data['issues_found']:
                print(f"   ⚠️  {issue['severity']}: {issue['issue']} - {issue['player']}")
            return data
        else:
            print(f"❌ Timeline endpoint failed: {resp.status_code}")
            return None
    
    def check_bot_analysis(self):
        """Check bot control analysis endpoint"""
        print("\n📊 Checking bot control analysis...")
        resp = requests.get(f"{self.base_url}/api/debug/bot-control-analysis/{self.room_id}")
        if resp.status_code == 200:
            data = resp.json()
            summary = data['summary']
            print(f"✅ Bot analysis complete")
            print(f"   Total disconnections: {summary['total_disconnections']}")
            print(f"   Total takeovers: {summary['total_takeovers']}")
            print(f"   Failed releases: {summary['total_failed_releases']}")
            print(f"   Blocked actions: {summary['total_blocked_actions']}")
            if summary['average_takeover_duration']:
                print(f"   Avg takeover duration: {summary['average_takeover_duration']:.1f}s")
            return data
        else:
            print(f"❌ Bot analysis endpoint failed: {resp.status_code}")
            return None

# Test execution plan using Playwright MCP
test_plan = """
COMPREHENSIVE TEST PLAN FOR BOT TAKEOVER DATA COLLECTION

=== SETUP ===
1. Terminal 1: Run ./start.sh and keep it open to see logs
2. Terminal 2: Run this test script

=== PLAYWRIGHT TEST SEQUENCE ===

Step 1: Setup
- Navigate to http://localhost:5050
- Create a new room
- Add 3 bot players
- Start the game

Step 2: Play to Turn Phase
- Complete declarations
- Play until it's human player's turn

Step 3: Simulate Disconnection
- Note the exact time
- Close the browser tab (disconnection)
- Wait exactly 6 seconds for bot takeover

Step 4: Monitor Bot Takeover
- Open new browser to spectate
- Verify bot is playing for disconnected player
- Let bot complete at least one action

Step 5: Reconnect Player
- Navigate back to room with same player name
- Verify reconnection successful
- Check if bot control is released

Step 6: Test Human Control
- Try to make a move as human
- Verify move is accepted (not blocked)

Step 7: Test Rapid Disconnect/Reconnect
- Disconnect again
- Reconnect within 3 seconds (before grace period)
- Verify bot takeover was cancelled

=== VERIFICATION CHECKLIST ===

Events to verify:
□ player_disconnected - with full game context
□ bot_takeover_scheduled - with 5s delay
□ bot_takeover_activated - after grace period
□ bot_action - when bot plays
□ player_reconnected - with pre-state
□ bot_control_released - on reconnection
□ human_action - after reconnection
□ action_blocked - if human tries during bot control

Debug endpoints to test:
□ /api/debug/connection-timeline/{room_id}
  - Shows complete timeline
  - Calculates time gaps
  - Identifies issues

□ /api/debug/bot-control-analysis/{room_id}
  - Shows takeover statistics
  - Calculates durations
  - Identifies patterns

=== EDGE CASES TO TEST ===

1. Grace Period Cancellation
   - Disconnect and reconnect within 5s
   - Should see bot_takeover_cancelled event

2. Multiple Disconnects
   - Disconnect/reconnect multiple times rapidly
   - Each cycle should have complete events

3. Concurrent Players
   - Have 2 players disconnect at same time
   - Events shouldn't interfere

4. Bot Control Verification
   - Try to act while bot has control
   - Should see action_blocked event

=== MANUAL PLAYWRIGHT COMMANDS ===

# Start by opening browser
mcp__playwright__browser_navigate(url="http://localhost:5050")

# Create room flow
mcp__playwright__browser_click(element="Create New Room button", ref="[button containing 'Create']")
# ... continue with game setup

# Disconnect simulation
mcp__playwright__browser_close()  # This simulates disconnection

# Reconnect flow
mcp__playwright__browser_navigate(url="http://localhost:5050/game/{room_id}")
# ... continue with reconnection

=== SUCCESS CRITERIA ===

1. All 13 new event types are stored
2. Timeline shows correct sequence
3. No bot_control_failed_release events
4. Bot releases control on reconnection
5. Human can play after reconnection
6. All debug endpoints return data
"""

if __name__ == "__main__":
    print(test_plan)
    
    # Basic verification that we can do programmatically
    test = BotTakeoverTest()
    
    print("\n" + "="*60)
    print("AUTOMATED VERIFICATION (run after manual Playwright test)")
    print("="*60)
    
    # Wait for server
    test.wait_for_server()
    
    # Set room ID after manual test creates it
    test.room_id = input("\n🎮 Enter room ID from manual test: ").strip()
    
    if test.room_id:
        # Verify events
        print("\n📝 Verifying events...")
        test.verify_event_exists("player_disconnected")
        test.verify_event_exists("bot_takeover_scheduled")
        test.verify_event_exists("bot_takeover_activated")
        test.verify_event_exists("bot_action")
        test.verify_event_exists("player_reconnected")
        test.verify_event_exists("bot_control_released")
        test.verify_event_exists("human_action")
        
        # Check endpoints
        test.check_timeline()
        test.check_bot_analysis()
        
        print("\n✅ Verification complete!")