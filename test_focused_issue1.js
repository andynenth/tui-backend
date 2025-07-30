/**
 * Focused Issue 1 test with detailed frontend logging
 * This test replicates the exact comprehensive test setup but focuses only on Issue 1
 */

const { chromium } = require('playwright');

async function testIssue1() {
    console.log('🔍 FOCUSED ISSUE 1 TEST: Host UI Persistence');
    console.log('============================================');
    
    const browser = await chromium.launch({ headless: false });
    
    // Player 1 (Host)
    const player1Context = await browser.newContext();
    const player1Page = await player1Context.newPage();
    
    // Player 2 (Joiner)
    const player2Context = await browser.newContext();  
    const player2Page = await player2Context.newPage();
    
    // Enable console logging
    player1Page.on('console', msg => {
        if (msg.text().includes('HOST_DEBUG') || msg.text().includes('ROOM_UPDATE')) {
            console.log(`[P1] ${msg.type()}: ${msg.text()}`);
        }
    });
    
    try {
        console.log('\n=== COMPREHENSIVE SETUP (REPLICATING EXACT TEST) ===');
        
        // Player 1: Create room (Step 1-2)
        console.log('🎯 Player 1: Join lobby and create room...');
        await player1Page.goto('http://localhost:5050/');
        await player1Page.fill('input[placeholder*="name"]', 'TestHost');
        await player1Page.click('text=Lobby');
        await player1Page.waitForURL('**/lobby');
        await player1Page.click('text=Create Room');
        await player1Page.waitForURL('**/room/**');
        
        const roomUrl = player1Page.url();
        const roomId = roomUrl.split('/room/')[1];
        console.log(`📋 Room created: ${roomId}`);
        
        // Wait for initial room state
        await player1Page.waitForTimeout(2000);
        
        // Step 3: Remove bot (critical for replicating the issue)
        console.log('🗑️ Player 1: Remove bot (Step 3)...');
        const removeButtons = await player1Page.locator('button:has-text("Remove")');
        const removeCount = await removeButtons.count();
        console.log(`Found ${removeCount} remove buttons`);
        
        if (removeCount > 0) {
            await removeButtons.first().click();
            await player1Page.waitForTimeout(1500); // Wait for bot removal to process
        }
        
        // Player 2: Join room (Steps 4-5)
        console.log('🎯 Player 2: Join lobby and room...');
        await player2Page.goto('http://localhost:5050/');
        await player2Page.fill('input[placeholder*="name"]', 'TestJoiner');
        await player2Page.click('text=Lobby');
        await player2Page.waitForURL('**/lobby');
        
        // Join room
        try {
            await player2Page.waitForSelector(`text=${roomId}`, { timeout: 3000 });
            await player2Page.click(`text=${roomId}`);
        } catch {
            // Alternative method
            const roomElements = await player2Page.locator('[class*="room"], [class*="Room"], button:has-text("ROOM")');
            if (await roomElements.count() > 0) {
                await roomElements.first().click();
            }
        }
        await player2Page.waitForURL('**/room/**');
        console.log('✅ Player 2 joined room');
        
        // Wait for room state to settle
        await player1Page.waitForTimeout(2000);
        
        console.log('\n=== ISSUE 1 TEST: NON-HOST PLAYER LEAVE ===');
        
        // Check UI state before
        const beforeRemoveButtons = await player1Page.locator('button:has-text("Remove")').count();
        const beforeAddBotButtons = await player1Page.locator('button:has-text("Add Bot")').count();
        const beforeHostBadges = await player1Page.locator('[class*="host"], [class*="Host"]').count();
        const beforeTotalActionButtons = beforeRemoveButtons + beforeAddBotButtons;
        
        console.log(`📊 BEFORE leave: ${beforeRemoveButtons} remove, ${beforeAddBotButtons} add bot, ${beforeHostBadges} host badges (${beforeTotalActionButtons} total actions)`);
        
        // Player 2 leaves
        console.log('🚪 Player 2 leaving room voluntarily...');
        await player2Page.click('text=Leave Room');
        
        // Wait for room update and check browser console for debug logs
        console.log('⏳ Waiting for room update and debug logs...');
        await player1Page.waitForTimeout(3000);
        
        // Check UI state after
        const afterRemoveButtons = await player1Page.locator('button:has-text("Remove")').count();
        const afterAddBotButtons = await player1Page.locator('button:has-text("Add Bot")').count();
        const afterHostBadges = await player1Page.locator('[class*="host"], [class*="Host"]').count();
        const afterTotalActionButtons = afterRemoveButtons + afterAddBotButtons;
        
        console.log(`📊 AFTER leave: ${afterRemoveButtons} remove, ${afterAddBotButtons} add bot, ${afterHostBadges} host badges (${afterTotalActionButtons} total actions)`);
        
        console.log('\n=== ANALYSIS ===');
        const removeButtonsLost = beforeRemoveButtons - afterRemoveButtons;
        const addBotButtonsChange = afterAddBotButtons - beforeAddBotButtons;
        const totalActionButtonsLost = beforeTotalActionButtons - afterTotalActionButtons;
        const badgesLost = beforeHostBadges - afterHostBadges;
        
        console.log(`Remove buttons: ${beforeRemoveButtons} → ${afterRemoveButtons} (Change: ${-removeButtonsLost})`);
        console.log(`Add Bot buttons: ${beforeAddBotButtons} → ${afterAddBotButtons} (Change: ${addBotButtonsChange})`);
        console.log(`Total action buttons: ${beforeTotalActionButtons} → ${afterTotalActionButtons} (Lost: ${totalActionButtonsLost})`);
        console.log(`Host badges: ${beforeHostBadges} → ${afterHostBadges} (Lost: ${badgesLost})`);
        
        // The correct behavior: Player 2 slot should become "Add Bot", so total action buttons should remain the same
        if (totalActionButtonsLost > 0 || badgesLost > 0) {
            console.log('❌ BUG CONFIRMED: Host lost UI control elements');
        } else {
            console.log('✅ WORKING: Host retained all UI control elements');
        }
        
        // Keep browsers open for manual inspection
        console.log('\n⏱️ Keeping browsers open for 30 seconds...');
        await player1Page.waitForTimeout(30000);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

testIssue1().catch(console.error);