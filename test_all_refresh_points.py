#!/usr/bin/env python3
"""Comprehensive test of refresh at every possible game state and action"""

import asyncio
import json
from playwright.async_api import async_playwright, Page
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

class ComprehensiveRefreshTester:
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.state_snapshots: List[Dict[str, Any]] = []
        self.console_logs: List[str] = []
        self.room_id: Optional[str] = None
        
    async def capture_console(self, msg):
        """Capture console messages for debugging"""
        try:
            text = msg.text
            self.console_logs.append(f"[{msg.type.upper()}] {text}")
            
            # Look for important messages
            if "phase_change" in text or "error" in text.lower():
                print(f"  📋 Console: {text[:100]}...")
        except Exception as e:
            pass
    
    async def capture_state(self, page: Page, context: str) -> Dict[str, Any]:
        """Capture complete game state"""
        state = await page.evaluate("""
            () => {
                const gameService = window.gameService;
                const state = gameService?.getState();
                
                // Get UI state too
                const gameElement = document.querySelector('[data-testid="game-container"]');
                const phaseText = document.querySelector('.phase-indicator')?.textContent || '';
                const currentPlayerText = document.querySelector('.current-player')?.textContent || '';
                
                return {
                    // Core state
                    phase: state?.phase,
                    currentRound: state?.currentRound,
                    turn_number: state?.turn_number,
                    
                    // Players
                    players: state?.players?.map(p => ({
                        name: p.name,
                        is_bot: p.is_bot,
                        avatar_color: p.avatar_color,
                        score: p.score,
                        declared: p.declared,
                        captured_piles: p.captured_piles,
                        zero_declares_in_a_row: p.zero_declares_in_a_row
                    })),
                    
                    // Phase-specific data
                    currentPlayer: state?.currentPlayer,
                    currentDeclarer: state?.currentDeclarer,
                    currentLeader: state?.currentLeader,
                    required_piece_count: state?.required_piece_count,
                    declared_counts: state?.declared_counts,
                    current_pile: state?.current_pile,
                    round_winner: state?.round_winner,
                    game_winner: state?.game_winner,
                    
                    // My data
                    myHand: state?.myHand?.length || 0,
                    playerName: state?.playerName,
                    
                    // UI state
                    uiPhaseText: phaseText,
                    uiCurrentPlayerText: currentPlayerText,
                    hasError: !!state?.error,
                    errorMessage: state?.error,
                    
                    // Timestamp
                    capturedAt: new Date().toISOString()
                };
            }
        """)
        
        return {
            'context': context,
            'state': state,
            'timestamp': datetime.now().isoformat()
        }
    
    async def test_refresh_at_point(self, page: Page, test_name: str, action_taken: str) -> Dict[str, Any]:
        """Test refresh at a specific point and compare states"""
        print(f"\n🧪 Testing: {test_name}")
        print(f"   Action: {action_taken}")
        
        # Capture state before refresh
        before = await self.capture_state(page, f"Before refresh - {test_name}")
        self.state_snapshots.append(before)
        
        print(f"   📸 Before state:")
        print(f"      Phase: {before['state']['phase']} (Round {before['state']['currentRound']})")
        print(f"      Turn: {before['state']['turn_number']}")
        print(f"      Current player: {before['state']['currentPlayer']}")
        
        # Clear console logs
        self.console_logs.clear()
        
        # Refresh the page
        print(f"   🔄 Refreshing page...")
        await page.reload()
        await asyncio.sleep(2)  # Wait for reconnection
        
        # Capture state after refresh
        after = await self.capture_state(page, f"After refresh - {test_name}")
        self.state_snapshots.append(after)
        
        print(f"   📸 After state:")
        print(f"      Phase: {after['state']['phase']} (Round {after['state']['currentRound']})")
        print(f"      Turn: {after['state']['turn_number']}")
        print(f"      Current player: {after['state']['currentPlayer']}")
        
        # Analyze differences
        issues = []
        
        # Check critical state preservation
        if before['state']['phase'] != 'waiting' and after['state']['phase'] == 'waiting':
            issues.append("Reverted to waiting phase")
        
        if before['state']['currentRound'] != after['state']['currentRound']:
            issues.append(f"Round changed: {before['state']['currentRound']} → {after['state']['currentRound']}")
        
        if before['state']['turn_number'] != after['state']['turn_number']:
            issues.append(f"Turn number changed: {before['state']['turn_number']} → {after['state']['turn_number']}")
        
        # Check player states
        if before['state']['players'] and after['state']['players']:
            for i, (bp, ap) in enumerate(zip(before['state']['players'], after['state']['players'])):
                if bp['is_bot'] != ap['is_bot']:
                    issues.append(f"{bp['name']}: is_bot changed {bp['is_bot']} → {ap['is_bot']}")
                if bp['avatar_color'] != ap['avatar_color']:
                    issues.append(f"{bp['name']}: avatar_color changed {bp['avatar_color']} → {ap['avatar_color']}")
                if bp['score'] != ap['score']:
                    issues.append(f"{bp['name']}: score changed {bp['score']} → {ap['score']}")
                if bp['declared'] != ap['declared']:
                    issues.append(f"{bp['name']}: declared changed {bp['declared']} → {ap['declared']}")
        
        # Check phase-specific data
        if before['state']['phase'] == after['state']['phase']:
            if before['state']['currentPlayer'] != after['state']['currentPlayer']:
                issues.append(f"Current player changed: {before['state']['currentPlayer']} → {after['state']['currentPlayer']}")
            if before['state']['currentDeclarer'] != after['state']['currentDeclarer']:
                issues.append(f"Current declarer changed: {before['state']['currentDeclarer']} → {after['state']['currentDeclarer']}")
        
        # Check for errors
        if after['state']['hasError']:
            issues.append(f"Error after refresh: {after['state']['errorMessage']}")
        
        result = {
            'test_name': test_name,
            'action_taken': action_taken,
            'before_state': before['state'],
            'after_state': after['state'],
            'issues': issues,
            'passed': len(issues) == 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        print(f"   Result: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
        if issues:
            for issue in issues:
                print(f"      ❌ {issue}")
        
        return result
    
    async def wait_for_phase(self, page: Page, phase: str, timeout: int = 10000):
        """Wait for a specific phase"""
        await page.wait_for_function(
            f"""() => {{
                const state = window.gameService?.getState();
                return state?.phase === '{phase}';
            }}""",
            timeout=timeout
        )
    
    async def wait_for_my_turn(self, page: Page, timeout: int = 30000):
        """Wait for it to be my turn"""
        await page.wait_for_function(
            """() => {
                const state = window.gameService?.getState();
                return state?.currentPlayer === state?.playerName;
            }""",
            timeout=timeout
        )
    
    async def get_clickable_pieces(self, page: Page) -> List[Any]:
        """Get all clickable piece elements"""
        return await page.query_selector_all('.piece-card:not(.disabled)')
    
    async def run_comprehensive_tests(self):
        """Run all refresh tests"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Set up console listener
            page.on("console", self.capture_console)
            
            try:
                print("🚀 Starting Comprehensive Refresh Testing")
                print("=" * 80)
                
                # Navigate to game
                await page.goto("http://localhost:5050")
                await page.wait_for_load_state("networkidle")
                
                # Test 1: Refresh before entering name
                await self.test_refresh_at_point(page, "Initial Page Load", "No action yet")
                
                # Enter name
                await page.fill("input[placeholder='Enter your name...']", "RefreshTester")
                
                # Test 2: Refresh after entering name but before lobby
                await self.test_refresh_at_point(page, "After Name Entry", "Entered name")
                
                # Enter lobby
                await page.click("button:has-text('Enter Lobby')")
                await asyncio.sleep(2)
                
                # Test 3: Refresh in lobby
                await self.test_refresh_at_point(page, "In Lobby", "Entered lobby")
                
                # Create room
                await page.click("button:has-text('Create Room')")
                await asyncio.sleep(2)
                
                # Get room ID
                room_id_element = await page.query_selector('.room-id, .room-code')
                if room_id_element:
                    self.room_id = await room_id_element.inner_text()
                    print(f"\n📍 Room ID: {self.room_id}")
                
                # Test 4: Refresh in room before starting
                await self.test_refresh_at_point(page, "In Room - Waiting", "Created room")
                
                # Start game
                await page.click("button:has-text('Start Game')")
                await asyncio.sleep(3)
                
                # === PREPARATION PHASE TESTS ===
                
                # Test 5: Refresh immediately after game start
                await self.test_refresh_at_point(page, "Preparation - Initial", "Game just started")
                
                # Check for weak hand
                try:
                    weak_hand_button = await page.query_selector("button:has-text('Request Redeal')")
                    if weak_hand_button:
                        # Test 6: Refresh with weak hand dialog
                        await self.test_refresh_at_point(page, "Preparation - Weak Hand Dialog", "Weak hand detected")
                        
                        # Continue without redeal
                        await page.click("button:has-text('Continue')")
                        await asyncio.sleep(2)
                except:
                    pass
                
                # Wait for declaration phase
                await self.wait_for_phase(page, 'declaration')
                
                # === DECLARATION PHASE TESTS ===
                
                # Test 7: Refresh at start of declaration phase
                await self.test_refresh_at_point(page, "Declaration - Start", "Entered declaration phase")
                
                # Check if it's my turn to declare
                my_turn = await page.evaluate("""
                    () => {
                        const state = window.gameService?.getState();
                        return state?.currentDeclarer === state?.playerName;
                    }
                """)
                
                if my_turn:
                    # Test 8: Refresh before making declaration
                    await self.test_refresh_at_point(page, "Declaration - My Turn Before", "My turn to declare")
                    
                    # Make declaration
                    await page.click("button:has-text('2')")
                    await asyncio.sleep(1)
                    
                    # Test 9: Refresh after making declaration
                    await self.test_refresh_at_point(page, "Declaration - My Turn After", "Made declaration")
                else:
                    # Test 10: Refresh during bot's turn
                    await self.test_refresh_at_point(page, "Declaration - Bot's Turn", "Waiting for bot")
                
                # Wait for turn phase
                await self.wait_for_phase(page, 'turn', timeout=20000)
                
                # === TURN PHASE TESTS ===
                
                # Test 11: Refresh at start of turn phase
                await self.test_refresh_at_point(page, "Turn - Start", "Entered turn phase")
                
                # Play through several turns
                for turn_num in range(3):  # Test first 3 turns
                    # Wait for any turn (mine or bot)
                    await asyncio.sleep(2)
                    
                    current_player = await page.evaluate("""
                        () => window.gameService?.getState()?.currentPlayer
                    """)
                    
                    is_my_turn = await page.evaluate("""
                        () => {
                            const state = window.gameService?.getState();
                            return state?.currentPlayer === state?.playerName;
                        }
                    """)
                    
                    if is_my_turn:
                        # Test: Refresh before playing
                        await self.test_refresh_at_point(
                            page, 
                            f"Turn {turn_num + 1} - My Turn Before Play", 
                            f"Turn {turn_num + 1}, my turn"
                        )
                        
                        # Select and play pieces
                        pieces = await self.get_clickable_pieces(page)
                        if pieces:
                            # Click first available piece
                            await pieces[0].click()
                            await asyncio.sleep(0.5)
                            
                            # Test: Refresh after selecting piece
                            await self.test_refresh_at_point(
                                page, 
                                f"Turn {turn_num + 1} - After Selection", 
                                "Selected piece"
                            )
                            
                            # Play the piece
                            play_button = await page.query_selector("button:has-text('Play')")
                            if play_button:
                                await play_button.click()
                                await asyncio.sleep(1)
                                
                                # Test: Refresh after playing
                                await self.test_refresh_at_point(
                                    page, 
                                    f"Turn {turn_num + 1} - After Play", 
                                    "Played piece"
                                )
                    else:
                        # Test: Refresh during bot's turn
                        await self.test_refresh_at_point(
                            page, 
                            f"Turn {turn_num + 1} - Bot Turn", 
                            f"Bot {current_player}'s turn"
                        )
                    
                    # Check if turn result is shown
                    await asyncio.sleep(2)
                    turn_result = await page.query_selector('.turn-result, .pile-result')
                    if turn_result:
                        # Test: Refresh during turn result display
                        await self.test_refresh_at_point(
                            page, 
                            f"Turn {turn_num + 1} - Result Display", 
                            "Turn result shown"
                        )
                
                # Check if we reached scoring phase
                phase = await page.evaluate("() => window.gameService?.getState()?.phase")
                if phase == 'scoring':
                    # === SCORING PHASE TESTS ===
                    
                    # Test: Refresh at scoring phase
                    await self.test_refresh_at_point(page, "Scoring - Display", "Showing scores")
                    
                    # Check for continue button
                    continue_button = await page.query_selector("button:has-text('Continue'), button:has-text('Next Round')")
                    if continue_button:
                        # Test: Refresh before continuing
                        await self.test_refresh_at_point(page, "Scoring - Before Continue", "Before clicking continue")
                        
                        await continue_button.click()
                        await asyncio.sleep(2)
                        
                        # Test: Refresh after continuing
                        await self.test_refresh_at_point(page, "Scoring - After Continue", "Clicked continue")
                
                print("\n" + "=" * 80)
                print("🏁 Testing Complete!")
                
            except Exception as e:
                print(f"\n❌ Test error: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                # Save results
                self.save_results()
                self.print_summary()
                
                # Keep browser open if there were failures
                if any(not r['passed'] for r in self.test_results):
                    print("\n🔍 Browser will stay open for debugging.")
                    print("Press Enter to close...")
                    input()
                
                await browser.close()
    
    def save_results(self):
        """Save detailed test results"""
        results = {
            'test_run': datetime.now().isoformat(),
            'room_id': self.room_id,
            'test_results': self.test_results,
            'state_snapshots': self.state_snapshots,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['passed']),
                'failed': sum(1 for r in self.test_results if not r['passed'])
            }
        }
        
        with open('comprehensive_refresh_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: comprehensive_refresh_test_results.json")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE REFRESH TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"\n📍 {result['test_name']}:")
                    print(f"   Action: {result['action_taken']}")
                    for issue in result['issues']:
                        print(f"   • {issue}")
        
        # Group issues by type
        issue_types = {}
        for result in self.test_results:
            for issue in result['issues']:
                issue_type = self.categorize_issue(issue)
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append({
                    'test': result['test_name'],
                    'issue': issue
                })
        
        if issue_types:
            print("\n🔍 ISSUES BY TYPE:")
            for issue_type, occurrences in issue_types.items():
                print(f"\n{issue_type} ({len(occurrences)} occurrences):")
                for occ in occurrences[:3]:  # Show first 3
                    print(f"   • {occ['test']}: {occ['issue']}")
                if len(occurrences) > 3:
                    print(f"   ... and {len(occurrences) - 3} more")
    
    def categorize_issue(self, issue: str) -> str:
        """Categorize an issue for grouping"""
        if "waiting phase" in issue.lower():
            return "⏸️ Reverted to Waiting"
        elif "round changed" in issue.lower():
            return "🔢 Round Number Changed"
        elif "turn number" in issue.lower():
            return "🎯 Turn Number Changed"
        elif "is_bot" in issue:
            return "🤖 Bot State Changed"
        elif "avatar_color" in issue:
            return "🎨 Avatar Color Changed"
        elif "score changed" in issue:
            return "📊 Score Changed"
        elif "declared changed" in issue:
            return "📣 Declaration Changed"
        elif "current player changed" in issue.lower():
            return "👤 Current Player Changed"
        elif "error" in issue.lower():
            return "❌ Error After Refresh"
        else:
            return "❓ Other Issue"

async def main():
    tester = ComprehensiveRefreshTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())