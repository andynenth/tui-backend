#!/usr/bin/env python3
"""
Single-terminal comprehensive test for bot takeover data collection
This script handles everything in one process, including server startup
"""

import subprocess
import time
import requests
import asyncio
import os
import signal
import sys

class SingleTerminalTest:
    def __init__(self):
        self.base_url = "http://localhost:5050"
        self.ws_url = "ws://localhost:5050"
        self.server_process = None
        self.room_id = None
        
    def start_server(self):
        """Start the server in background and capture logs"""
        print("🚀 Starting server in background...")
        
        # Start server with output to file
        self.log_file = open("test_server.log", "w")
        self.server_process = subprocess.Popen(
            ["./start.sh"],
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Wait for server to be ready
        print("⏳ Waiting for server startup...")
        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                resp = requests.get(f"{self.base_url}/api/health")
                if resp.status_code == 200:
                    print("✅ Server is ready!")
                    return True
            except:
                pass
            time.sleep(1)
        
        raise Exception("Server failed to start within 30 seconds")
    
    def stop_server(self):
        """Stop the server and cleanup"""
        if self.server_process:
            print("🛑 Stopping server...")
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process.wait()
            self.log_file.close()
    
    def tail_logs(self, lines=20):
        """Show recent server logs"""
        print(f"\n📜 Recent server logs (last {lines} lines):")
        print("-" * 60)
        os.system(f"tail -n {lines} test_server.log")
        print("-" * 60)
    
    def verify_event(self, event_type, player_name=None, show_details=False):
        """Verify an event exists"""
        try:
            resp = requests.get(f"{self.base_url}/api/debug/events/{self.room_id}?event_type={event_type}")
            if resp.status_code == 200:
                events = resp.json()["events"]
                if player_name:
                    events = [e for e in events if e.get("player_id") == player_name]
                if events:
                    print(f"✅ {event_type}: Found {len(events)} event(s)")
                    if show_details and events:
                        print(f"   Details: {events[0].get('payload', {})}")
                    return True
                else:
                    print(f"❌ {event_type}: No events found")
                    return False
        except Exception as e:
            print(f"❌ {event_type}: Error - {e}")
            return False
    
    def run_playwright_test(self):
        """Run the actual test using Playwright MCP"""
        print("\n🎭 Starting Playwright test...")
        
        # This is where we'll use Playwright MCP commands
        # For now, let's create a test plan that you can execute
        
        test_script = """
# PLAYWRIGHT MCP TEST COMMANDS

# 1. Open browser and navigate to lobby
mcp__playwright__browser_navigate(url="http://localhost:5050")

# 2. Create a new room
mcp__playwright__browser_snapshot()  # See current state
mcp__playwright__browser_click(element="Create Room button", ref="<button ref>")

# 3. Wait for room creation and note room ID
# The room ID will be in the URL after creation

# 4. Add 3 bot players
mcp__playwright__browser_click(element="Add Bot button", ref="<button ref>")
# Repeat 3 times

# 5. Start the game
mcp__playwright__browser_click(element="Start Game button", ref="<button ref>")

# 6. Play through declarations
# Make declarations as needed

# 7. Get to turn phase where it's human player's turn
# Play until human's turn

# 8. DISCONNECT TEST - Close the browser
mcp__playwright__browser_close()

# 9. Wait 6 seconds for bot takeover
# (Python script will handle this)

# 10. RECONNECT TEST - Open new browser and go to game
mcp__playwright__browser_navigate(url="http://localhost:5050/game/{room_id}")

# 11. Try to make a move
mcp__playwright__browser_click(element="Card to play", ref="<card ref>")
mcp__playwright__browser_click(element="Play button", ref="<button ref>")

# 12. Verify move succeeded
mcp__playwright__browser_snapshot()
"""
        return test_script
    
    def verify_all_events(self):
        """Verify all expected events were collected"""
        print("\n📊 Verifying data collection...")
        
        events_to_check = [
            ("player_disconnected", "Connection tracking"),
            ("bot_takeover_scheduled", "Grace period scheduling"),
            ("bot_takeover_activated", "Bot activation"),
            ("bot_action", "Bot playing"),
            ("player_reconnected", "Reconnection tracking"),
            ("bot_control_released", "Control release"),
            ("human_action", "Human playing"),
        ]
        
        all_good = True
        for event_type, description in events_to_check:
            if not self.verify_event(event_type):
                all_good = False
                print(f"   Missing: {description}")
        
        return all_good
    
    def check_debug_endpoints(self):
        """Test the new debug endpoints"""
        print("\n🔍 Testing debug endpoints...")
        
        # Connection timeline
        try:
            resp = requests.get(f"{self.base_url}/api/debug/connection-timeline/{self.room_id}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Timeline: {data['timeline_events']} events, {len(data['issues_found'])} issues")
            else:
                print(f"❌ Timeline endpoint failed: {resp.status_code}")
        except Exception as e:
            print(f"❌ Timeline endpoint error: {e}")
        
        # Bot control analysis  
        try:
            resp = requests.get(f"{self.base_url}/api/debug/bot-control-analysis/{self.room_id}")
            if resp.status_code == 200:
                data = resp.json()
                summary = data['summary']
                print(f"✅ Bot analysis: {summary['total_takeovers']} takeovers, "
                      f"{summary['total_failed_releases']} failures")
            else:
                print(f"❌ Bot analysis endpoint failed: {resp.status_code}")
        except Exception as e:
            print(f"❌ Bot analysis endpoint error: {e}")

def main():
    test = SingleTerminalTest()
    
    try:
        # Start server
        test.start_server()
        
        print("\n" + "="*60)
        print("SERVER STARTED - Ready for testing")
        print("="*60)
        
        # Show test script
        script = test.run_playwright_test()
        print("\n📝 PLAYWRIGHT TEST SCRIPT:")
        print(script)
        
        # Get room ID from user after they run Playwright commands
        print("\n⏸️  Run the Playwright MCP commands above, then...")
        test.room_id = input("Enter the room ID created: ").strip()
        
        if test.room_id:
            print(f"\n🎮 Testing room: {test.room_id}")
            
            # After disconnect/reconnect cycle
            input("\n⏸️  Complete the disconnect/reconnect test, then press Enter...")
            
            # Verify events
            test.verify_all_events()
            
            # Check endpoints
            test.check_debug_endpoints()
            
            # Show logs
            test.tail_logs(30)
            
            print("\n✅ Test complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        test.tail_logs(50)
    finally:
        test.stop_server()
        print("\n🏁 Cleanup complete")

if __name__ == "__main__":
    main()