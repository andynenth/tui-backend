#!/usr/bin/env python3
"""
Comprehensive test to reproduce the WebSocket reconnection bug
Tests refreshing at every phase and action to find the exact scenario
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright, Page, ConsoleMessage
from typing import List, Dict, Any, Optional
from datetime import datetime

class RefreshBugTester:
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.console_logs: List[str] = []
        self.current_test_phase = ""
        self.current_test_action = ""
        
    async def capture_console(self, msg: ConsoleMessage):
        """Capture console messages for analysis"""
        try:
            text = msg.text
            self.console_logs.append(f"[{msg.type.upper()}] {text}")
            
            # Track important state messages
            if "phase_change" in text or "PHASE_CHANGE" in text:
                print(f"  📋 Phase change detected: {text[:100]}")
            elif "round" in text.lower() and "undefined" in text.lower():
                print(f"  🚨 ROUND UNDEFINED: {text}")
            elif "pieces data" in text and "undefined" in text:
                print(f"  🚨 PIECES UNDEFINED: {text}")
                
        except Exception as e:
            print(f"Console capture error: {e}")
    
    async def wait_for_phase(self, page: Page, phase_name: str, timeout: int = 10) -> bool:
        """Wait for a specific game phase"""
        try:
            print(f"  ⏳ Waiting for phase: {phase_name}")
            await page.wait_for_function(
                f"""() => {{
                    const phaseText = document.body.innerText;
                    return phaseText.includes('{phase_name}');
                }}""",
                timeout=timeout * 1000
            )
            return True
        except Exception as e:
            print(f"  ❌ Phase '{phase_name}' not reached: {e}")
            return False
    
    async def check_game_state(self, page: Page) -> Dict[str, Any]:
        """Check current game state after refresh"""
        await asyncio.sleep(2)  # Wait for state to stabilize
        
        state = {
            "phase": self.current_test_phase,
            "action": self.current_test_action,
            "timestamp": datetime.now().isoformat(),
            "issues": []
        }
        
        # Check page content
        content = await page.content()
        inner_text = await page.inner_text("body")
        
        # Check for common issues
        if "Waiting for Game" in inner_text:
            state["issues"].append("Shows 'Waiting for Game' instead of game state")
        
        if "undefined" in inner_text.lower():
            state["issues"].append(f"Undefined values in UI: {inner_text[:200]}")
        
        if "Connecting to game..." in inner_text:
            state["issues"].append("Stuck in connecting state")
            
        # Check console for errors
        error_logs = [log for log in self.console_logs[-20:] if "[ERROR]" in log or "undefined" in log.lower()]
        if error_logs:
            state["issues"].append(f"Console errors: {error_logs}")
        
        # Get snapshot
        try:
            snapshot = await page.accessibility.snapshot()
            state["snapshot"] = str(snapshot)[:500] if snapshot else "No snapshot"
        except:
            state["snapshot"] = "Failed to get snapshot"
        
        state["has_issues"] = len(state["issues"]) > 0
        
        return state
    
    async def test_refresh_at_point(self, page: Page, phase: str, action: str) -> Dict[str, Any]:
        """Test refresh at a specific point in the game"""
        self.current_test_phase = phase
        self.current_test_action = action
        self.console_logs.clear()
        
        print(f"\n🔄 Testing refresh at: {phase} - {action}")
        
        # Capture current URL and state
        url_before = page.url
        
        # Perform refresh
        await page.reload()
        await asyncio.sleep(3)  # Wait for reconnection
        
        # Check state after refresh
        state = await self.check_game_state(page)
        state["url_before"] = url_before
        state["url_after"] = page.url
        
        if state["has_issues"]:
            print(f"  🐛 BUG FOUND! Issues: {state['issues']}")
        else:
            print(f"  ✅ No issues detected")
        
        self.test_results.append(state)
        return state
    
    async def run_comprehensive_test(self):
        """Run comprehensive refresh tests across all game phases"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Set up console listener
            page.on("console", self.capture_console)
            
            try:
                print("🚀 Starting comprehensive refresh bug test")
                
                # Navigate to game
                await page.goto("http://localhost:5050")
                await page.wait_for_load_state("networkidle")
                
                # Enter name
                await page.fill("input[placeholder='Enter your name...']", "RefreshTester")
                await page.click("button:has-text('Enter Lobby')")
                await asyncio.sleep(2)
                
                # Create room
                await page.click("button:has-text('Create Room')")
                await asyncio.sleep(2)
                
                # Test 1: Refresh in room (before game start)
                await self.test_refresh_at_point(page, "ROOM", "before_start")
                
                # Start game
                await page.click("button:has-text('Start Game')")
                await asyncio.sleep(3)
                
                # Test 2: Refresh during PREPARATION phase
                if await self.wait_for_phase(page, "Preparation Phase"):
                    await self.test_refresh_at_point(page, "PREPARATION", "initial")
                    
                    # If there's a redeal dialog, handle it
                    try:
                        if "weak hand" in await page.inner_text("body"):
                            await self.test_refresh_at_point(page, "PREPARATION", "weak_hand_dialog")
                            await page.click("button:has-text('Continue')")
                            await asyncio.sleep(2)
                    except:
                        pass
                
                # Test 3: Refresh during DECLARATION phase
                if await self.wait_for_phase(page, "Declaration Phase"):
                    await self.test_refresh_at_point(page, "DECLARATION", "before_declare")
                    
                    # Make a declaration
                    try:
                        await page.click("button:has-text('1')")
                        await asyncio.sleep(1)
                        await self.test_refresh_at_point(page, "DECLARATION", "after_declare")
                    except:
                        print("  ⚠️ Could not make declaration")
                
                # Test 4: Refresh during TURN phase
                if await self.wait_for_phase(page, "Turn Phase"):
                    await self.test_refresh_at_point(page, "TURN", "initial")
                    
                    # Try to select and play pieces
                    try:
                        # Click on a piece
                        pieces = await page.query_selector_all(".piece-card")
                        if pieces:
                            await pieces[0].click()
                            await asyncio.sleep(1)
                            await self.test_refresh_at_point(page, "TURN", "piece_selected")
                            
                            # Play the piece
                            await page.click("button:has-text('Play')")
                            await asyncio.sleep(2)
                            await self.test_refresh_at_point(page, "TURN", "after_play")
                    except Exception as e:
                        print(f"  ⚠️ Could not play piece: {e}")
                
                # Test 5: Refresh during SCORING phase
                if await self.wait_for_phase(page, "Round Complete"):
                    await self.test_refresh_at_point(page, "SCORING", "round_complete")
                
                # Additional edge case tests
                print("\n🔍 Testing edge cases...")
                
                # Test rapid refreshes
                print("\n⚡ Testing rapid refreshes...")
                for i in range(3):
                    await page.reload()
                    await asyncio.sleep(1)
                state = await self.check_game_state(page)
                state["phase"] = "EDGE_CASE"
                state["action"] = "rapid_refresh"
                self.test_results.append(state)
                
                # Test refresh during network activity
                print("\n🌐 Testing refresh during network activity...")
                # This would need coordination with actually triggering network activity
                
            except Exception as e:
                print(f"\n❌ Test error: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                # Generate report
                self.generate_report()
                
                # Keep browser open for manual inspection if bugs found
                bugs_found = any(r["has_issues"] for r in self.test_results)
                if bugs_found:
                    print("\n🐛 BUGS FOUND! Browser will stay open for inspection.")
                    print("Press Enter to close...")
                    input()
                
                await browser.close()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        failed_tests = [r for r in self.test_results if r["has_issues"]]
        
        print(f"\nTotal tests: {total_tests}")
        print(f"Failed tests: {len(failed_tests)}")
        print(f"Success rate: {((total_tests - len(failed_tests)) / total_tests * 100):.1f}%")
        
        if failed_tests:
            print("\n🐛 FAILED TESTS:")
            for test in failed_tests:
                print(f"\n  Phase: {test['phase']} - Action: {test['action']}")
                print(f"  Issues:")
                for issue in test['issues']:
                    print(f"    - {issue}")
        
        # Save detailed results
        with open("refresh_bug_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print("\n📁 Detailed results saved to: refresh_bug_test_results.json")
        
        # Identify patterns
        if failed_tests:
            print("\n🔍 PATTERNS IDENTIFIED:")
            phases = [t["phase"] for t in failed_tests]
            actions = [t["action"] for t in failed_tests]
            
            from collections import Counter
            phase_counts = Counter(phases)
            action_counts = Counter(actions)
            
            print(f"  Most problematic phases: {phase_counts.most_common(3)}")
            print(f"  Most problematic actions: {action_counts.most_common(3)}")

async def main():
    tester = RefreshBugTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())