import asyncio
from playwright.async_api import async_playwright
import time

async def test_preparation_phase():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Enable Chrome DevTools Protocol for console logs
        context = await browser.new_context()
        
        # Create 4 pages for 4 players
        pages = []
        for i in range(4):
            page = await context.new_page()
            pages.append(page)
            
            # Listen to console logs
            page.on("console", lambda msg, idx=i: print(f"Player {idx+1} console: {msg.text}"))
            
        # Player 1: Create room
        print("\n=== Player 1: Creating room ===")
        await pages[0].goto("http://localhost:5050")
        await pages[0].wait_for_load_state('networkidle')
        
        # Wait for the input field to be visible and ready
        await pages[0].wait_for_selector('input[placeholder="Enter your name..."]', state='visible')
        await pages[0].fill('input[placeholder="Enter your name..."]', "Player1")
        await pages[0].click('text="Continue"')
        await pages[0].wait_for_selector('text="Create Room"')
        await pages[0].click('text="Create Room"')
        await pages[0].wait_for_selector('.rp-roomIdValue')
        room_id = await pages[0].text_content('.rp-roomIdValue')
        print(f"Room created: {room_id}")
        
        # Wait for Player 1 to fully connect
        await pages[0].wait_for_selector('text="Connected"')
        
        # Players 2-4: Join room
        for i in range(1, 4):
            print(f"\n=== Player {i+1}: Joining room ===")
            await pages[i].goto("http://localhost:5050")
            await pages[i].fill('input[placeholder="Enter your name..."]', f"Player{i+1}")
            await pages[i].click('text="Continue"')
            await pages[i].wait_for_selector('input[placeholder="Enter room ID"]')
            await pages[i].fill('input[placeholder="Enter room ID"]', room_id)
            await pages[i].click('text="Join Room"')
            await pages[i].wait_for_selector('.rp-roomIdValue')
            await pages[i].wait_for_selector('text="Connected"')
            print(f"Player {i+1} joined room")
        
        # Wait for all players to be visible
        print("\n=== Waiting for all players to be visible ===")
        for i in range(4):
            await pages[i].wait_for_selector('text="4 / 4"')
        
        # Start game
        print("\n=== Starting game ===")
        await pages[0].click('text="Start Game"')
        
        # Wait for navigation to game page
        print("\n=== Waiting for game to start ===")
        for i in range(4):
            await pages[i].wait_for_url(f"**/game/{room_id}")
            print(f"Player {i+1} navigated to game page")
        
        # Wait for preparation phase and check pieces
        print("\n=== Checking preparation phase ===")
        await asyncio.sleep(3)  # Give time for phase_change events
        
        for i in range(4):
            try:
                # Check if pieces are displayed
                pieces = await pages[i].query_selector_all('.piece-item')
                print(f"Player {i+1} has {len(pieces)} pieces displayed")
                
                # Check game phase
                phase_text = await pages[i].text_content('.game-phase-indicator')
                print(f"Player {i+1} sees phase: {phase_text}")
                
                # Check if PieceTray is visible
                piece_tray = await pages[i].query_selector('.piece-tray')
                if piece_tray:
                    print(f"Player {i+1} has PieceTray component visible")
                else:
                    print(f"Player {i+1} PieceTray not found")
                    
            except Exception as e:
                print(f"Error checking Player {i+1}: {e}")
        
        print("\n=== Test completed ===")
        await asyncio.sleep(5)  # Keep browser open to observe
        await browser.close()

asyncio.run(test_preparation_phase())