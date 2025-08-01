#!/usr/bin/env python3
"""
Phase Transition Debug Test using Playwright MCP

This script uses Playwright to automate the exact user flow:
Player 1 >> Enter Lobby >> Create Room >> Start Game

And captures all debug information to identify why the frontend
doesn't transition to the next phase.
"""

import asyncio
import json
import time
from datetime import datetime

# Simulated MCP Playwright functions (will be replaced with actual MCP calls)
class PlaywrightMCP:
    def __init__(self):
        self.messages = []
        self.console_logs = []
    
    async def browser_navigate(self, url):
        print(f"🌐 Navigating to: {url}")
        return {"success": True}
    
    async def browser_snapshot(self):
        print("📸 Taking page snapshot...")
        # This will be replaced with actual MCP call
        return {
            "type": "WebPage",
            "children": [
                {"role": "button", "name": "Enter Lobby", "ref": "e25"},
                {"role": "textbox", "name": "Player Name", "ref": "e15", "value": "TestPlayer"}
            ]
        }
    
    async def browser_click(self, element, ref):
        print(f"🖱️ Clicking: {element} (ref: {ref})")
        return {"success": True}
    
    async def browser_wait_for(self, text=None, timeout=5000):
        print(f"⏳ Waiting for: {text} (timeout: {timeout}ms)")
        return {"success": True}
    
    async def browser_console_messages(self):
        print("📝 Getting console messages...")
        # This will capture actual console logs
        return []
    
    async def browser_evaluate(self, function):
        print(f"⚡ Executing: {function}")
        return {"result": "executed"}

# Global playwright instance
playwright = PlaywrightMCP()

async def capture_websocket_messages():
    """Inject WebSocket message capturing into the page"""
    await playwright.browser_evaluate({
        "function": """() => {
            window.__wsMessages = [];
            window.__originalWebSocket = window.WebSocket;
            
            window.WebSocket = function(url, protocols) {
                console.log('🔌 WebSocket created:', url);
                const ws = new window.__originalWebSocket(url, protocols);
                
                ws.addEventListener('message', (event) => {
                    const timestamp = new Date().toISOString();
                    let parsedData = null;
                    
                    try {
                        parsedData = JSON.parse(event.data);
                    } catch (e) {
                        parsedData = event.data;
                    }
                    
                    const messageInfo = {
                        timestamp,
                        type: 'received',
                        data: parsedData,
                        raw: event.data
                    };
                    
                    window.__wsMessages.push(messageInfo);
                    
                    // Special logging for phase_change events
                    if (parsedData && parsedData.event === 'phase_change') {
                        console.log('🔄 PHASE_CHANGE EVENT RECEIVED:', {
                            phase: parsedData.data?.phase,
                            previous_phase: parsedData.data?.previous_phase,
                            phase_data: parsedData.data?.phase_data,
                            timestamp
                        });
                    }
                    
                    console.log('📨 WebSocket message received:', messageInfo);
                });
                
                ws.addEventListener('open', () => {
                    console.log('🔗 WebSocket connected');
                });
                
                ws.addEventListener('close', () => {
                    console.log('🔌 WebSocket disconnected');
                });
                
                const originalSend = ws.send;
                ws.send = function(data) {
                    const timestamp = new Date().toISOString();
                    let parsedData = null;
                    
                    try {
                        parsedData = JSON.parse(data);
                    } catch (e) {
                        parsedData = data;
                    }
                    
                    const messageInfo = {
                        timestamp,
                        type: 'sent',
                        data: parsedData,
                        raw: data
                    };
                    
                    window.__wsMessages.push(messageInfo);
                    console.log('📤 WebSocket message sent:', messageInfo);
                    
                    return originalSend.call(this, data);
                };
                
                return ws;
            };
        }"""
    })

async def capture_gameservice_debug():
    """Inject GameService debugging"""
    await playwright.browser_evaluate({
        "function": """() => {
            // Monitor GameService state changes
            window.__gameServiceDebug = [];
            
            // Try to access GameService instance
            if (window.gameService) {
                const originalSetState = window.gameService.setState;
                if (originalSetState) {
                    window.gameService.setState = function(newState, eventInfo) {
                        const timestamp = new Date().toISOString();
                        const debugInfo = {
                            timestamp,
                            phase: newState.phase,
                            playerName: newState.playerName,
                            roomId: newState.roomId,
                            isConnected: newState.isConnected,
                            myHandLength: newState.myHand?.length || 0,
                            eventInfo
                        };
                        
                        window.__gameServiceDebug.push(debugInfo);
                        console.log('🎮 GameService state change:', debugInfo);
                        
                        // Special logging for phase changes
                        if (newState.phase !== this.state?.phase) {
                            console.log('📈 PHASE TRANSITION:', {
                                from: this.state?.phase,
                                to: newState.phase,
                                timestamp,
                                hasHand: !!newState.myHand?.length
                            });
                        }
                        
                        return originalSetState.call(this, newState, eventInfo);
                    };
                }
            }
            
            // Monitor React component renders
            window.__componentRenders = [];
        }"""
    })

async def get_captured_messages():
    """Retrieve all captured WebSocket messages"""
    result = await playwright.browser_evaluate({
        "function": "() => window.__wsMessages || []"
    })
    return result.get("result", [])

async def get_gameservice_debug():
    """Retrieve GameService debug information"""
    result = await playwright.browser_evaluate({
        "function": "() => window.__gameServiceDebug || []"
    })
    return result.get("result", [])

async def wait_for_phase_transition(expected_phase="preparation", timeout=10):
    """Wait for a specific phase transition"""
    print(f"⏳ Waiting for phase transition to: {expected_phase}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Check current phase via GameService
        result = await playwright.browser_evaluate({
            "function": f"""() => {{
                if (window.gameService && window.gameService.getState) {{
                    const state = window.gameService.getState();
                    return {{
                        phase: state.phase,
                        isConnected: state.isConnected,
                        playerName: state.playerName,
                        myHandLength: state.myHand?.length || 0
                    }};
                }}
                return null;
            }}"""
        })
        
        current_state = result.get("result")
        if current_state:
            print(f"📊 Current state: {current_state}")
            if current_state.get("phase") == expected_phase:
                print(f"✅ Phase transition to {expected_phase} detected!")
                return True
        
        await asyncio.sleep(0.5)
    
    print(f"❌ Timeout waiting for phase transition to {expected_phase}")
    return False

async def analyze_phase_transition_failure():
    """Analyze why phase transition failed"""
    print("\n🔍 ANALYZING PHASE TRANSITION FAILURE...")
    
    # Get WebSocket messages
    ws_messages = await get_captured_messages()
    print(f"\n📨 Total WebSocket messages: {len(ws_messages)}")
    
    phase_change_events = []
    for msg in ws_messages:
        if (isinstance(msg.get("data"), dict) and 
            msg["data"].get("event") == "phase_change"):
            phase_change_events.append(msg)
    
    print(f"🔄 Phase change events received: {len(phase_change_events)}")
    
    for i, event in enumerate(phase_change_events):
        print(f"\n📈 Phase change event #{i+1}:")
        event_data = event["data"]["data"]
        print(f"   Phase: {event_data.get('phase', 'unknown')}")
        print(f"   Previous: {event_data.get('previous_phase', 'unknown')}")
        print(f"   Timestamp: {event.get('timestamp', 'unknown')}")
        
        if "phase_data" in event_data:
            phase_data = event_data["phase_data"]
            print(f"   Has phase_data: {bool(phase_data)}")
            if phase_data and "players" in phase_data:
                players = phase_data["players"]
                print(f"   Players in phase_data: {list(players.keys()) if players else 'none'}")
                for player, data in players.items():
                    hand_length = len(data.get("hand", [])) if data else 0
                    print(f"     {player}: {hand_length} cards")
    
    # Get GameService debug info
    gs_debug = await get_gameservice_debug()
    print(f"\n🎮 GameService state changes: {len(gs_debug)}")
    
    for i, debug in enumerate(gs_debug):
        print(f"\n📊 State change #{i+1}:")
        print(f"   Phase: {debug.get('phase', 'unknown')}")
        print(f"   Connected: {debug.get('isConnected', 'unknown')}")
        print(f"   Hand length: {debug.get('myHandLength', 0)}")
        print(f"   Timestamp: {debug.get('timestamp', 'unknown')}")
    
    # Check console logs
    console_messages = await playwright.browser_console_messages()
    print(f"\n📝 Console messages: {len(console_messages)}")
    
    return {
        "ws_messages": ws_messages,
        "phase_change_events": phase_change_events,
        "gameservice_debug": gs_debug,
        "console_messages": console_messages
    }

async def test_phase_transition():
    """Main test function to debug phase transitions"""
    print("🚀 Starting Phase Transition Debug Test")
    print("=" * 60)
    
    try:
        # Step 1: Navigate to the application
        print("\n📍 STEP 1: Navigate to application")
        await playwright.browser_navigate("http://localhost:5050")
        
        # Step 2: Set up debugging
        print("\n📍 STEP 2: Setting up debug monitoring")
        await capture_websocket_messages()
        await capture_gameservice_debug()
        
        # Step 3: Enter Lobby
        print("\n📍 STEP 3: Enter Lobby")
        snapshot = await playwright.browser_snapshot()
        
        # Find Enter Lobby button
        enter_lobby_btn = None
        for child in snapshot.get("children", []):
            if child.get("name") == "Enter Lobby":
                enter_lobby_btn = child
                break
        
        if enter_lobby_btn:
            await playwright.browser_click("Enter Lobby button", enter_lobby_btn["ref"])
            await playwright.browser_wait_for("Game Lobby", timeout=5000)
            print("✅ Successfully entered lobby")
        else:
            print("❌ Enter Lobby button not found")
            return
        
        # Step 4: Create Room
        print("\n📍 STEP 4: Create Room")
        await asyncio.sleep(1)  # Let lobby load
        snapshot = await playwright.browser_snapshot()
        
        # Find Create Room button
        create_room_btn = None
        for child in snapshot.get("children", []):
            if "Create Room" in child.get("name", ""):
                create_room_btn = child
                break
        
        if create_room_btn:
            await playwright.browser_click("Create Room button", create_room_btn["ref"])
            await playwright.browser_wait_for("Start Game", timeout=5000)
            print("✅ Successfully created room")
        else:
            print("❌ Create Room button not found")
            return
        
        # Step 5: Start Game
        print("\n📍 STEP 5: Start Game")
        await asyncio.sleep(1)  # Let room load
        snapshot = await playwright.browser_snapshot()
        
        # Find Start Game button
        start_game_btn = None
        for child in snapshot.get("children", []):
            if "Start Game" in child.get("name", ""):
                start_game_btn = child
                break
        
        if start_game_btn:
            print("🎯 Clicking Start Game - monitoring for phase transition...")
            await playwright.browser_click("Start Game button", start_game_btn["ref"])
            
            # Step 6: Wait for phase transition
            print("\n📍 STEP 6: Monitoring phase transition")
            success = await wait_for_phase_transition("preparation", timeout=10)
            
            if not success:
                print("\n❌ PHASE TRANSITION FAILED!")
                await analyze_phase_transition_failure()
            else:
                print("\n✅ PHASE TRANSITION SUCCESSFUL!")
                
        else:
            print("❌ Start Game button not found")
            return
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Phase Transition Debug Test Complete")

# Replace this with actual MCP Playwright calls when available
async def main():
    """Main entry point - replace with MCP calls"""
    print("🔧 This is a template script for Playwright MCP debugging")
    print("Replace PlaywrightMCP class with actual MCP function calls:")
    print()
    print("Example MCP calls:")
    print("- mcp__playwright__browser_navigate")
    print("- mcp__playwright__browser_snapshot")
    print("- mcp__playwright__browser_click")
    print("- mcp__playwright__browser_wait_for")
    print("- mcp__playwright__browser_console_messages")
    print("- mcp__playwright__browser_evaluate")
    print()
    print("When ready, run the actual test with:")
    print("await test_phase_transition()")

if __name__ == "__main__":
    asyncio.run(main())