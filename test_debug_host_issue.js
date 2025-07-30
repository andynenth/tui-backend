/**
 * Debug test for Issue 1 - Host UI persistence after player leave
 * This test focuses only on the problematic scenario to get clear debug logs
 */

const { chromium } = require('playwright');

async function debugHostIssue() {
    console.log('🐛 DEBUG TEST: Host UI Persistence Issue');
    console.log('=====================================');
    
    const browser = await chromium.launch({ headless: false });
    
    // Player 1 (Host)
    const player1Context = await browser.newContext();
    const player1Page = await player1Context.newPage();
    
    // Player 2 (Joiner)
    const player2Context = await browser.newContext();  
    const player2Page = await player2Context.newPage();
    
    try {
        console.log('\n=== SETUP ===');
        
        // Player 1: Create room
        console.log('🎯 Player 1 creating room...');
        await player1Page.goto('http://localhost:5050/');
        
        // Wait for page to load and check what elements are available
        await player1Page.waitForTimeout(2000);
        console.log('📄 Page title:', await player1Page.title());
        console.log('📄 Page URL:', player1Page.url());
        
        // Try different selectors for the name input
        let nameInput = null;
        const selectors = [
            'input[placeholder="Enter your name"]',
            'input[placeholder*="name"]',
            'input[type="text"]',
            'input:first-of-type'
        ];
        
        for (const selector of selectors) {
            try {
                await player1Page.waitForSelector(selector, { timeout: 2000 });
                nameInput = selector;
                console.log(`✅ Found name input: ${selector}`);
                break;
            } catch (e) {
                console.log(`❌ Selector not found: ${selector}`);
            }
        }
        
        if (!nameInput) {
            throw new Error('Could not find name input field');
        }
        
        await player1Page.fill(nameInput, 'TestHost');
        
        // Try different button selectors
        const buttonSelectors = [
            'text=Continue to Lobby',
            'text=Continue',
            'text=Lobby', 
            'button:has-text("Continue")',
            'button:has-text("Lobby")',
            'button[type="submit"]',
            'button:first-of-type'
        ];
        
        let continueButton = null;
        for (const selector of buttonSelectors) {
            try {
                await player1Page.waitForSelector(selector, { timeout: 2000 });
                continueButton = selector;
                console.log(`✅ Found continue button: ${selector}`);
                break;
            } catch (e) {
                console.log(`❌ Button selector not found: ${selector}`);  
            }
        }
        
        if (!continueButton) {
            throw new Error('Could not find continue button');
        }
        
        await player1Page.click(continueButton);
        await player1Page.waitForURL('**/lobby');
        await player1Page.click('text=Create Room');
        await player1Page.waitForURL('**/room/**');
        
        const roomUrl = player1Page.url();
        const roomId = roomUrl.split('/room/')[1];
        console.log(`📋 Room created: ${roomId}`);
        
        // Wait for initial room state
        await player1Page.waitForTimeout(1000);
        
        // Player 2: Join room  
        console.log('🎯 Player 2 joining room...');
        await player2Page.goto('http://localhost:5050/');
        await player2Page.waitForTimeout(2000);
        
        // Find name input for Player 2
        let nameInput2 = null;
        for (const selector of selectors) {
            try {
                await player2Page.waitForSelector(selector, { timeout: 2000 });
                nameInput2 = selector;
                console.log(`✅ Found P2 name input: ${selector}`);
                break;
            } catch (e) {
                console.log(`❌ P2 selector not found: ${selector}`);
            }
        }
        
        if (!nameInput2) {
            throw new Error('Could not find P2 name input field');
        }
        
        await player2Page.fill(nameInput2, 'TestJoiner');
        
        // Find continue button for Player 2
        let continueButton2 = null;
        for (const selector of buttonSelectors) {
            try {
                await player2Page.waitForSelector(selector, { timeout: 2000 });
                continueButton2 = selector;
                console.log(`✅ Found P2 continue button: ${selector}`);
                break;
            } catch (e) {
                console.log(`❌ P2 button selector not found: ${selector}`);
            }
        }
        
        if (!continueButton2) {
            throw new Error('Could not find P2 continue button');
        }
        
        await player2Page.click(continueButton2);
        await player2Page.waitForURL('**/lobby');
        console.log('✅ Player 2 reached lobby');
        
        // Look for room to join
        try {
            await player2Page.waitForSelector(`text=${roomId}`, { timeout: 5000 });
            console.log(`✅ Found room ${roomId} in lobby`);
            await player2Page.click(`text=${roomId}`);
            await player2Page.waitForURL('**/room/**', { timeout: 10000 });
            console.log('✅ Player 2 joined room');
        } catch (e) {
            console.log('❌ Failed to join room, trying alternative approaches...');
            // Try clicking any room-like element
            const roomElements = await player2Page.locator('[class*="room"], [class*="Room"], button:has-text("ROOM"), button:has-text("JOIN")').count();
            console.log(`Found ${roomElements} room-like elements`);
            
            if (roomElements > 0) {
                await player2Page.locator('[class*="room"], [class*="Room"], button:has-text("ROOM"), button:has-text("JOIN")').first().click();
                await player2Page.waitForURL('**/room/**', { timeout: 10000 });
                console.log('✅ Player 2 joined room via alternative method');
            } else {
                throw new Error('Could not find any way to join room');
            }
        }
        
        // Wait for room state to settle
        await player1Page.waitForTimeout(2000);
        
        console.log('\n=== BEFORE PLAYER LEAVE ===');
        
        // Count host elements before
        const beforeRemoveButtons = await player1Page.locator('button:has-text("Remove")').count();
        const beforeHostBadges = await player1Page.locator('[class*="host"], [class*="Host"]').count();
        
        console.log(`📊 Host UI state BEFORE leave:`);
        console.log(`   Remove buttons: ${beforeRemoveButtons}`);
        console.log(`   Host badges: ${beforeHostBadges}`);
        
        console.log('\n=== PLAYER LEAVE (Issue 1 Trigger) ===');
        console.log('🚪 Player 2 leaving room voluntarily...');
        
        // Player 2 leaves voluntarily
        await player2Page.click('text=Leave Room');
        
        // Wait for room update
        await player1Page.waitForTimeout(3000);
        
        console.log('\n=== AFTER PLAYER LEAVE ===');
        
        // Count host elements after
        const afterRemoveButtons = await player1Page.locator('button:has-text("Remove")').count();
        const afterHostBadges = await player1Page.locator('[class*="host"], [class*="Host"]').count();
        
        console.log(`📊 Host UI state AFTER leave:`);
        console.log(`   Remove buttons: ${afterRemoveButtons}`);
        console.log(`   Host badges: ${afterHostBadges}`);
        
        console.log('\n=== ANALYSIS ===');
        console.log(`Remove buttons: ${beforeRemoveButtons} → ${afterRemoveButtons} (Lost: ${beforeRemoveButtons - afterRemoveButtons})`);
        console.log(`Host badges: ${beforeHostBadges} → ${afterHostBadges} (Lost: ${beforeHostBadges - afterHostBadges})`);
        
        if (beforeRemoveButtons > afterRemoveButtons || beforeHostBadges > afterHostBadges) {
            console.log('❌ BUG CONFIRMED: Host lost UI elements');
        } else {
            console.log('✅ WORKING: Host retained UI elements');
        }
        
        console.log('\n🐛 Check backend logs for [HOST_DEBUG] messages to see room state details');
        
        // Keep browser open for inspection
        console.log('\n⏱️ Keeping browsers open for 30 seconds for manual inspection...');
        await player1Page.waitForTimeout(30000);
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        await browser.close();
    }
}

debugHostIssue().catch(console.error);