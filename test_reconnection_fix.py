#!/usr/bin/env python3
"""Test script to verify reconnection bug fixes"""

import asyncio
import json
from playwright.async_api import async_playwright, Page
from typing import Dict, List, Any
from datetime import datetime

class ReconnectionTester:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.console_logs: List[str] = []
        
    async def capture_console(self, msg):
        """Capture console messages"""
        try:
            text = msg.text
            self.console_logs.append(f"[{msg.type.upper()}] {text}")
            
            # Look for key messages
            if "avatar_color" in text:
                print(f"  🎨 Avatar color message: {text[:100]}")
            elif "is_bot" in text:
                print(f"  🤖 Bot state message: {text[:100]}")
            elif "phase_change" in text:
                print(f"  📋 Phase change message: {text[:100]}")
        except Exception as e:
            print(f"Console capture error: {e}")
        
    async def test_scenario(self, page: Page, scenario_name: str, refresh_phase: str) -> Dict[str, Any]:
        """Test a specific refresh scenario"""
        print(f"\n🧪 Testing: {scenario_name}")
        print(f"  Current Phase: {refresh_phase}")
        
        # Wait a moment for state to stabilize
        await asyncio.sleep(1)
        
        # Capture state before refresh
        before_state = await page.evaluate("""
            () => {
                const gameService = window.gameService;
                const state = gameService?.getState();
                console.log('🔍 Before refresh state:', state);
                return {
                    phase: state?.phase,
                    currentRound: state?.currentRound,
                    players: state?.players?.map(p => ({
                        name: p.name,
                        is_bot: p.is_bot,
                        avatar_color: p.avatar_color,
                        score: p.score
                    })),
                    myHand: state?.myHand?.length || 0,
                    currentPlayer: state?.currentPlayer,
                    currentDeclarer: state?.currentDeclarer
                };
            }
        """)
        
        print(f"  📸 Before refresh:")
        print(f"     Phase: {before_state['phase']}")
        print(f"     Players:")
        for p in before_state['players'] or []:
            print(f"       - {p['name']}: is_bot={p['is_bot']}, avatar_color={p['avatar_color']}")
        
        # Clear console logs
        self.console_logs.clear()
        
        # Refresh page
        print(f"  🔄 Refreshing page...")
        await page.reload()
        await asyncio.sleep(3)  # Wait for reconnection
        
        # Capture state after refresh
        after_state = await page.evaluate("""
            () => {
                const gameService = window.gameService;
                const state = gameService?.getState();
                console.log('🔍 After refresh state:', state);
                return {
                    phase: state?.phase,
                    currentRound: state?.currentRound,
                    players: state?.players?.map(p => ({
                        name: p.name,
                        is_bot: p.is_bot,
                        avatar_color: p.avatar_color,
                        score: p.score
                    })),
                    myHand: state?.myHand?.length || 0,
                    currentPlayer: state?.currentPlayer,
                    currentDeclarer: state?.currentDeclarer,
                    error: state?.error
                };
            }
        """)
        
        print(f"  📸 After refresh:")
        print(f"     Phase: {after_state['phase']}")
        print(f"     Players:")
        for p in after_state['players'] or []:
            print(f"       - {p['name']}: is_bot={p['is_bot']}, avatar_color={p['avatar_color']}")
        
        # Check for errors
        if after_state.get('error'):
            print(f"  ⚠️ Error in state: {after_state['error']}")
        
        # Verify results
        passed = True
        issues = []
        
        # Check phase restoration
        if after_state['phase'] == 'waiting' and before_state['phase'] != 'waiting':
            passed = False
            issues.append(f"Stuck in 'waiting' phase (was {before_state['phase']})")
        elif after_state['phase'] != before_state['phase']:
            # Phase might legitimately change (e.g., preparation -> declaration)
            print(f"  ℹ️ Phase changed: {before_state['phase']} → {after_state['phase']}")
        
        # Check player states
        if before_state['players'] and after_state['players']:
            for before_player, after_player in zip(before_state['players'], after_state['players']):
                # Check bot state
                if before_player['is_bot'] != after_player['is_bot']:
                    passed = False
                    issues.append(f"{before_player['name']}: is_bot {before_player['is_bot']} → {after_player['is_bot']}")
                
                # Check avatar color
                if before_player['avatar_color'] != after_player['avatar_color']:
                    passed = False
                    issues.append(f"{before_player['name']}: avatar_color {before_player['avatar_color']} → {after_player['avatar_color']}")
        
        # Check round persistence
        if before_state['currentRound'] != after_state['currentRound']:
            passed = False
            issues.append(f"Round changed: {before_state['currentRound']} → {after_state['currentRound']}")
        
        result = {
            'scenario': scenario_name,
            'phase': refresh_phase,
            'passed': passed,
            'issues': issues,
            'before_state': before_state,
            'after_state': after_state,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        print(f"  Result: {'✅ PASSED' if passed else '❌ FAILED'}")
        if issues:
            for issue in issues:
                print(f"    ❌ {issue}")
        
        return result
    
    async def run_all_tests(self):
        """Run comprehensive reconnection tests"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Set up console listener
            page.on("console", self.capture_console)
            
            try:
                print("🚀 Starting Reconnection Bug Fix Verification")
                print("="*60)
                
                # Navigate to game
                await page.goto("http://localhost:5050")
                await page.wait_for_load_state("networkidle")
                
                # Enter name
                await page.fill("input[placeholder='Enter your name...']", "TestPlayer")
                await page.click("button:has-text('Enter Lobby')")
                await asyncio.sleep(2)
                
                # Create room
                await page.click("button:has-text('Create Room')")
                await asyncio.sleep(2)
                
                # Test refresh in room before game start
                await self.test_scenario(page, "Room Before Start", "waiting")
                
                # Start game
                print("\n🎮 Starting game...")
                await page.click("button:has-text('Start Game')")
                await asyncio.sleep(3)
                
                # Test 1: Preparation phase
                await self.test_scenario(page, "Preparation Phase", "preparation")
                
                # Handle weak hand if present
                try:
                    weak_hand_text = await page.inner_text("body")
                    if "weak hand" in weak_hand_text.lower():
                        print("\n  ℹ️ Weak hand detected, continuing...")
                        await page.click("button:has-text('Continue')")
                        await asyncio.sleep(2)
                except:
                    pass
                
                # Wait for Declaration phase
                print("\n⏳ Waiting for Declaration phase...")
                await page.wait_for_function(
                    """() => {
                        const state = window.gameService?.getState();
                        return state?.phase === 'declaration';
                    }""",
                    timeout=10000
                )
                
                # Test 2: Declaration phase
                await self.test_scenario(page, "Declaration Phase", "declaration")
                
                # Make declaration
                print("\n📣 Making declaration...")
                await page.click("button:has-text('2')")
                await asyncio.sleep(1)
                
                # Wait for bot declarations
                print("\n⏳ Waiting for Turn phase...")
                await page.wait_for_function(
                    """() => {
                        const state = window.gameService?.getState();
                        return state?.phase === 'turn';
                    }""",
                    timeout=15000
                )
                
                # Test 3: Turn phase
                await self.test_scenario(page, "Turn Phase", "turn")
                
                # Test 4: Multiple rapid refreshes
                print("\n⚡ Testing rapid refreshes...")
                for i in range(3):
                    await page.reload()
                    await asyncio.sleep(1)
                
                rapid_state = await page.evaluate("""
                    () => {
                        const state = window.gameService?.getState();
                        return {
                            phase: state?.phase,
                            players: state?.players?.map(p => ({
                                name: p.name,
                                is_bot: p.is_bot,
                                avatar_color: p.avatar_color
                            }))
                        };
                    }
                """)
                
                # Check rapid refresh results
                rapid_passed = rapid_state['phase'] != 'waiting'
                self.results.append({
                    'scenario': 'Rapid Refreshes (3x)',
                    'phase': 'turn',
                    'passed': rapid_passed,
                    'issues': [] if rapid_passed else ['Still stuck in waiting after rapid refreshes'],
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"\n  Rapid refresh test: {'✅ PASSED' if rapid_passed else '❌ FAILED'}")
                
            except Exception as e:
                print(f"\n❌ Test error: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                # Generate report
                self.print_report()
                
                # Keep browser open if tests failed
                if any(not r['passed'] for r in self.results):
                    print("\n🔍 Browser will stay open for debugging.")
                    print("Press Enter to close...")
                    input()
                
                await browser.close()
    
    def print_report(self):
        """Print comprehensive test report"""
        print("\n" + "="*60)
        print("📊 RECONNECTION BUG FIX VERIFICATION REPORT")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        if any(not r['passed'] for r in self.results):
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['passed']:
                    print(f"\n  📍 {result['scenario']} (Phase: {result['phase']}):")
                    for issue in result['issues']:
                        print(f"     • {issue}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.results:
            if result['passed']:
                print(f"  • {result['scenario']}")
        
        # Save detailed results
        with open("reconnection_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📁 Detailed results saved to: reconnection_test_results.json")
        
        # Summary
        print("\n🎯 KEY FINDINGS:")
        print("  1. Avatar Color Preservation:", "✅ FIXED" if self.check_avatar_colors() else "❌ STILL BROKEN")
        print("  2. Bot State Accuracy:", "✅ FIXED" if self.check_bot_states() else "❌ STILL BROKEN")
        print("  3. Game State Restoration:", "✅ FIXED" if self.check_game_states() else "❌ STILL BROKEN")
        
    def check_avatar_colors(self) -> bool:
        """Check if avatar colors are preserved"""
        for result in self.results:
            for issue in result['issues']:
                if 'avatar_color' in issue:
                    return False
        return True
    
    def check_bot_states(self) -> bool:
        """Check if bot states are accurate"""
        for result in self.results:
            for issue in result['issues']:
                if 'is_bot' in issue:
                    return False
        return True
    
    def check_game_states(self) -> bool:
        """Check if game states are restored"""
        for result in self.results:
            for issue in result['issues']:
                if "Stuck in 'waiting'" in issue:
                    return False
        return True

async def main():
    tester = ReconnectionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())