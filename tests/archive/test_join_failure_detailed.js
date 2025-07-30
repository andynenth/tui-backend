const { chromium } = require('playwright');

/**
 * DETAILED JOIN FAILURE INVESTIGATION
 * 
 * The previous test showed Player 2 can see the room but clicking doesn't trigger join_room.
 * This test will capture the exact mechanism of join failure and UI interactions.
 */

async function investigateJoinFailureDetailed() {
  console.log('🔍 DETAILED JOIN FAILURE INVESTIGATION');
  console.log('======================================');
  console.log('🎯 Previous finding: Room visible but click doesn\'t trigger join_room message');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1500
  });
  
  try {
    const evidence = {
      websocketMessages: [],
      uiInteractions: [],
      roomCardDetails: [],
      consoleErrors: []
    };
    
    // Setup WebSocket and console monitoring
    const setupMonitoring = (page, playerName) => {
      // Console errors
      page.on('console', msg => {
        if (msg.type() === 'error') {
          evidence.consoleErrors.push({
            timestamp: new Date().toISOString(),
            player: playerName,
            message: msg.text()
          });
          console.log(`🚫 ${playerName} console error: ${msg.text()}`);
        }
      });
      
      // WebSocket messages
      page.on('websocket', ws => {
        ws.on('framereceived', data => {
          try {
            const parsed = JSON.parse(data.payload);
            evidence.websocketMessages.push({
              timestamp: new Date().toISOString(),
              player: playerName,
              direction: 'received',
              event: parsed.event,
              data: parsed.data
            });
            
            if (['room_list_update', 'join_room', 'error'].includes(parsed.event)) {
              console.log(`📥 ${playerName}: ${parsed.event}`, 
                parsed.event === 'error' ? parsed.data?.message : '');
            }
          } catch (e) {}
        });
        
        ws.on('framesent', data => {
          try {
            const parsed = JSON.parse(data.payload);
            evidence.websocketMessages.push({
              timestamp: new Date().toISOString(),
              player: playerName,
              direction: 'sent',
              event: parsed.event,
              data: parsed.data
            });
            
            if (parsed.event === 'join_room') {
              console.log(`📤 ${playerName}: join_room`, parsed.data);
            }
          } catch (e) {}
        });
      });
    };
    
    // === STEP 1: Setup Player 1 and create room ===
    console.log('\n=== STEP 1: Setup Player 1 and create room ===');
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    setupMonitoring(creatorPage, 'Creator');
    
    await creatorPage.goto('http://localhost:5050');
    await creatorPage.waitForLoadState('networkidle');
    
    await creatorPage.locator('input[type="text"]').first().fill('Creator');
    await creatorPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await creatorPage.waitForTimeout(2000);
    
    const createBtn = await creatorPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await creatorPage.waitForTimeout(5000);
    
    // === STEP 2: Remove bot ===
    console.log('\n=== STEP 2: Remove bot ===');
    const removeBtns = await creatorPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeBtns.length > 0) {
      await removeBtns[0].click();
      await creatorPage.waitForTimeout(3000);
      console.log('✅ Bot removed');
    }
    
    // === STEP 3: Setup Player 2 ===
    console.log('\n=== STEP 3: Setup Player 2 ===');
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    setupMonitoring(joinerPage, 'Joiner');
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('Joiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // === STEP 4: Detailed room card analysis ===
    console.log('\n=== STEP 4: Analyze room cards in detail ===');
    
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    console.log(`🏠 Found ${roomCards.length} room cards`);
    
    for (let i = 0; i < roomCards.length; i++) {
      try {
        const card = roomCards[i];
        const cardText = await card.textContent();
        const isVisible = await card.isVisible();
        const isEnabled = await card.isEnabled();
        
        // Try to get room details
        const roomName = await card.locator('.room-name, [class*="name"]').textContent().catch(() => 'N/A');
        const playerCount = await card.locator('.player-count, [class*="count"], [class*="player"]').textContent().catch(() => 'N/A');
        
        const cardDetails = {
          index: i,
          text: cardText,
          roomName,
          playerCount,
          isVisible,
          isEnabled
        };
        
        evidence.roomCardDetails.push(cardDetails);
        console.log(`   Card ${i}: "${roomName}" - ${playerCount} - visible:${isVisible} enabled:${isEnabled}`);
      } catch (error) {
        console.log(`   Card ${i}: Error reading details - ${error.message}`);
      }
    }
    
    // === STEP 5: Attempt join with detailed logging ===
    console.log('\n=== STEP 5: Detailed join attempt ===');
    
    if (roomCards.length > 0) {
      const targetCard = roomCards[0];
      
      console.log('🎯 About to click on first room card...');
      evidence.uiInteractions.push({
        timestamp: new Date().toISOString(),
        action: 'click_room_card',
        target: 'first_room_card'
      });
      
      // Take screenshot before click
      await joinerPage.screenshot({ path: 'before_join_click.png' });
      console.log('📸 Screenshot taken before click');
      
      // Click the room card
      await targetCard.click();
      console.log('✅ Room card clicked');
      
      // Wait and check what happened
      await joinerPage.waitForTimeout(5000);
      
      // Take screenshot after click
      await joinerPage.screenshot({ path: 'after_join_click.png' });
      console.log('📸 Screenshot taken after click');
      
      // Check if URL changed (successful join)
      const currentUrl = joinerPage.url();
      console.log(`🔗 Current URL: ${currentUrl}`);
      
      if (currentUrl.includes('/room/')) {
        console.log('✅ SUCCESS: Joined room (URL changed)');
      } else {
        console.log('❌ FAILED: Still in lobby (URL unchanged)');
        
        // Try to understand why - check for any error messages or modal dialogs
        try {
          const errorMsg = await joinerPage.locator('.error, .toast, [class*="error"], [class*="modal"]').textContent({ timeout: 2000 });
          console.log(`⚠️ Error message: ${errorMsg}`);
        } catch (e) {
          console.log('💭 No visible error messages found');
        }
        
        // Check if the room is actually full by looking at player count
        try {
          const roomCountDisplay = await joinerPage.locator('.lp-roomCount').textContent();
          console.log(`📊 Room count display: ${roomCountDisplay}`);
          
          // Look for room details that might show why join failed
          const roomDetails = await targetCard.textContent();
          console.log(`🏠 Room card details: ${roomDetails}`);
          
        } catch (e) {
          console.log('💭 Could not read room details');
        }
      }
    } else {
      console.log('❌ No room cards found - room disappeared from lobby');
    }
    
    // === STEP 6: Analysis ===
    console.log('\n=== STEP 6: EVIDENCE ANALYSIS ===');
    
    const joinRoomSent = evidence.websocketMessages.filter(m => m.event === 'join_room' && m.direction === 'sent');
    const joinRoomReceived = evidence.websocketMessages.filter(m => m.event === 'join_room' && m.direction === 'received');
    const errorMessages = evidence.websocketMessages.filter(m => m.event === 'error');
    
    console.log(`📤 join_room messages sent: ${joinRoomSent.length}`);
    console.log(`📥 join_room responses received: ${joinRoomReceived.length}`);
    console.log(`❌ Error messages: ${errorMessages.length}`);
    console.log(`🚫 Console errors: ${evidence.consoleErrors.length}`);
    
    if (joinRoomSent.length === 0) {
      console.log('\n🔍 ROOT CAUSE ANALYSIS:');
      console.log('❌ PROBLEM: No join_room WebSocket message was sent');
      console.log('💡 This suggests the issue is in the FRONTEND click handler');
      console.log('   Possible causes:');
      console.log('   1. Click handler not attached to room card');
      console.log('   2. Room card is disabled/unclickable');
      console.log('   3. JavaScript error preventing join action');
      console.log('   4. Room data missing required fields for join');
      
      if (evidence.consoleErrors.length > 0) {
        console.log('\n🚫 CONSOLE ERRORS FOUND:');
        evidence.consoleErrors.forEach(err => {
          console.log(`   ${err.player}: ${err.message}`);
        });
      }
      
      console.log('\n📊 ROOM CARD ANALYSIS:');
      evidence.roomCardDetails.forEach(card => {
        console.log(`   Card ${card.index}: enabled=${card.isEnabled}, visible=${card.isVisible}`);
        console.log(`      Text: "${card.text}"`);
      });
      
    } else {
      console.log('\n🔍 ROOT CAUSE ANALYSIS:');
      console.log('✅ join_room message was sent - backend validation issue');
      
      if (errorMessages.length > 0) {
        console.log('❌ Backend errors found:');
        errorMessages.forEach(err => {
          console.log(`   ${err.data?.message || 'Unknown error'}`);
        });
      }
    }
    
    // Keep browsers open for manual inspection
    console.log('\n⏱️ Keeping browsers open for manual inspection...');
    await joinerPage.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Investigation failed:', error);
  } finally {
    await browser.close();
  }
}

investigateJoinFailureDetailed().catch(console.error);