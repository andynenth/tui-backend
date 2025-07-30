/**
 * Final validation test for both Issue 1 and Issue 2 
 * This test verifies that both host privilege issues are resolved
 */

const { chromium } = require('playwright');

async function finalValidationTest() {
    console.log('🎯 FINAL VALIDATION TEST: Both Issues Fixed');
    console.log('==========================================');
    
    const browser = await chromium.launch({ headless: false });
    
    // Player 1 (Host)
    const player1Context = await browser.newContext();
    const player1Page = await player1Context.newPage();
    
    // Player 2 (Joiner)
    const player2Context = await browser.newContext();  
    const player2Page = await player2Context.newPage();
    
    try {
        console.log('\n=== SETUP ===');
        
        // Player 1: Create room with bot removal (replicating original test conditions)
        console.log('🎯 Player 1: Create room and remove bot...');
        await player1Page.goto('http://localhost:5050/');
        await player1Page.fill('input[placeholder*="name"]', 'TestHost');
        await player1Page.click('text=Lobby');
        await player1Page.waitForURL('**/lobby');
        await player1Page.click('text=Create Room');
        await player1Page.waitForURL('**/room/**');
        
        const roomUrl = player1Page.url();
        const roomId = roomUrl.split('/room/')[1];
        console.log(`📋 Room created: ${roomId}`);
        
        // Remove a bot to replicate original test conditions
        const removeButtons = await player1Page.locator('button:has-text("Remove")');
        if (await removeButtons.count() > 0) {
            await removeButtons.first().click();
            await player1Page.waitForTimeout(1000);
        }
        
        // Player 2: Join room
        console.log('🎯 Player 2: Join room...');
        await player2Page.goto('http://localhost:5050/');
        await player2Page.fill('input[placeholder*="name"]', 'TestJoiner');
        await player2Page.click('text=Lobby');
        await player2Page.waitForURL('**/lobby');
        
        try {
            await player2Page.waitForSelector(`text=${roomId}`, { timeout: 3000 });
            await player2Page.click(`text=${roomId}`);
            await player2Page.waitForURL('**/room/**');
        } catch {
            console.log('Room ID not found, trying alternative...');
            const roomElements = await player2Page.locator('[class*="room"], [class*="Room"], button:has-text("ROOM")');
            if (await roomElements.count() > 0) {
                await roomElements.first().click();
                await player2Page.waitForURL('**/room/**');
            } else {
                throw new Error('Cannot find room to join');
            }
        }
        await player1Page.waitForTimeout(1500);
        
        console.log('\n=== ISSUE 1 TEST: NON-HOST PLAYER LEAVE ===');
        
        // Check UI before
        const beforeRemoveButtons = await player1Page.locator('button:has-text("Remove")').count();
        const beforeAddBotButtons = await player1Page.locator('button:has-text("Add Bot")').count();
        const beforeHostBadges = await player1Page.locator('[class*="host"], [class*="Host"]').count();
        const beforeTotalActions = beforeRemoveButtons + beforeAddBotButtons;
        
        console.log(`📊 BEFORE Player 2 leave: ${beforeRemoveButtons} remove, ${beforeAddBotButtons} add bot, ${beforeHostBadges} host badges (${beforeTotalActions} total)`);
        
        // Player 2 leaves voluntarily
        await player2Page.click('text=Leave Room');
        await player1Page.waitForTimeout(2000);
        
        // Check UI after leave
        const afterLeaveRemoveButtons = await player1Page.locator('button:has-text("Remove")').count();
        const afterLeaveAddBotButtons = await player1Page.locator('button:has-text("Add Bot")').count();
        const afterLeaveHostBadges = await player1Page.locator('[class*="host"], [class*="Host"]').count();
        const afterLeaveTotalActions = afterLeaveRemoveButtons + afterLeaveAddBotButtons;
        
        console.log(`📊 AFTER Player 2 leave: ${afterLeaveRemoveButtons} remove, ${afterLeaveAddBotButtons} add bot, ${afterLeaveHostBadges} host badges (${afterLeaveTotalActions} total)`);
        
        const issue1Fixed = (afterLeaveTotalActions === beforeTotalActions) && (afterLeaveHostBadges === beforeHostBadges);
        console.log(`📋 Issue 1 (Host UI persistence): ${issue1Fixed ? '✅ FIXED' : '❌ BROKEN'}`);
        
        console.log('\n=== ISSUE 2 TEST: HOST REMOVES PLAYER ===');
        
        // Player 2 rejoins for removal test
        console.log('🎯 Player 2: Rejoining for removal test...');
        await player2Page.goto('http://localhost:5050/');
        await player2Page.fill('input[placeholder*="name"]', 'TestJoiner2');
        await player2Page.click('text=Lobby');
        await player2Page.waitForURL('**/lobby');
        
        try {
            await player2Page.waitForSelector(`text=${roomId}`, { timeout: 3000 });
            await player2Page.click(`text=${roomId}`);
            await player2Page.waitForURL('**/room/**');
        } catch {
            console.log('Room ID not found, trying alternative...');
            const roomElements = await player2Page.locator('[class*="room"], [class*="Room"], button:has-text("ROOM")');
            if (await roomElements.count() > 0) {
                await roomElements.first().click();
                await player2Page.waitForURL('**/room/**');
            } else {
                throw new Error('Cannot find room to join');
            }
        }
        await player1Page.waitForTimeout(1500);
        
        // Host removes Player 2
        console.log('🗑️ Host removing Player 2...');
        const removeButtonsForRemoval = await player1Page.locator('button:has-text("Remove")');
        if (await removeButtonsForRemoval.count() > 0) {
            await removeButtonsForRemoval.first().click();
            await player1Page.waitForTimeout(2000);
        }
        
        // Check if Player 2 was redirected to lobby
        const player2FinalURL = player2Page.url();
        const player2InLobby = player2FinalURL.includes('/lobby');
        
        console.log(`📊 Player 2 final URL: ${player2FinalURL}`);
        console.log(`📋 Issue 2 (Player redirection): ${player2InLobby ? '✅ FIXED' : '❌ BROKEN'}`);
        
        console.log('\n=== FINAL RESULTS ===');
        console.log(`Issue 1 (Host UI persistence): ${issue1Fixed ? '✅ FIXED' : '❌ BROKEN'}`);
        console.log(`Issue 2 (Player redirection): ${player2InLobby ? '✅ FIXED' : '❌ BROKEN'}`);
        
        if (issue1Fixed && player2InLobby) {
            console.log('🎉 SUCCESS: Both issues are completely resolved!');
        } else {
            console.log('⚠️ Some issues remain unresolved');
        }
        
        // Keep browsers open briefly for inspection
        console.log('\n⏱️ Keeping browsers open for 15 seconds...');
        await player1Page.waitForTimeout(15000);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

finalValidationTest().catch(console.error);