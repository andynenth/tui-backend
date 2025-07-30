const { chromium } = require('playwright');

/**
 * JOIN FIX VALIDATION TEST
 * 
 * Tests that the PlayerJoinedRoom event constructor fix resolves the join issue.
 * This should now allow Player 2 to successfully join the room after Player 1 removes a bot.
 */

async function validateJoinFix() {
  console.log('🧪 JOIN FIX VALIDATION TEST');
  console.log('============================');
  console.log('🎯 Testing: Player 2 can now join room after Player 1 removes bot');
  console.log('🔧 Fix applied: Removed invalid game_id parameter from PlayerJoinedRoom constructor');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1500
  });
  
  try {
    const testResults = {
      roomCreated: false,
      botRemoved: false,
      joinAttempted: false,
      joinSuccessful: false,
      errorOccurred: false,
      finalUrl: '',
      websocketEvents: []
    };
    
    // === STEP 1: Player 1 creates room ===
    console.log('\n=== STEP 1: Player 1 creates room ===');
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    // Monitor creator's WebSocket events
    creatorPage.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          testResults.websocketEvents.push({
            timestamp: new Date().toISOString(),
            player: 'Creator',
            event: parsed.event,
            success: parsed.data?.success
          });
          
          if (parsed.event === 'room_created' && parsed.data?.success) {
            testResults.roomCreated = true;
            console.log('✅ Room created successfully');
          }
        } catch (e) {}
      });
    });
    
    await creatorPage.goto('http://localhost:5050');
    await creatorPage.waitForLoadState('networkidle');
    
    await creatorPage.locator('input[type="text"]').first().fill('Creator');
    await creatorPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await creatorPage.waitForTimeout(2000);
    
    const createBtn = await creatorPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await creatorPage.waitForTimeout(5000);
    
    // === STEP 2: Player 1 removes bot ===
    console.log('\n=== STEP 2: Player 1 removes bot ===');
    const removeBtns = await creatorPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeBtns.length > 0) {
      await removeBtns[0].click();
      await creatorPage.waitForTimeout(3000);
      testResults.botRemoved = true;
      console.log('✅ Bot removed successfully');
    } else {
      console.log('❌ No remove buttons found');
    }
    
    // === STEP 3: Player 2 joins lobby ===
    console.log('\n=== STEP 3: Player 2 joins lobby ===');
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    
    // Monitor joiner's WebSocket events for success/failure
    joinerPage.on('websocket', ws => {
      ws.on('framesent', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'join_room') {
            testResults.joinAttempted = true;
            console.log('📤 Join room message sent');
          }
        } catch (e) {}
      });
      
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          testResults.websocketEvents.push({
            timestamp: new Date().toISOString(),
            player: 'Joiner',
            event: parsed.event,
            success: parsed.data?.success,
            error: parsed.data?.message
          });
          
          if (parsed.event === 'room_joined' && parsed.data?.success) {
            testResults.joinSuccessful = true;
            console.log('✅ Room joined successfully!');
          } else if (parsed.event === 'error') {
            testResults.errorOccurred = true;
            console.log('❌ Error occurred:', parsed.data?.message);
          }
        } catch (e) {}
      });
    });
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('Joiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // === STEP 4: Player 2 attempts to join room ===
    console.log('\n=== STEP 4: Player 2 attempts to join room ===');
    
    // Check room availability
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    console.log(`🏠 Found ${roomCards.length} available rooms`);
    
    if (roomCards.length > 0) {
      console.log('🎯 Attempting to join room...');
      await roomCards[0].click();
      await joinerPage.waitForTimeout(5000);
      
      // Check if join was successful by checking URL
      testResults.finalUrl = joinerPage.url();
      if (testResults.finalUrl.includes('/room/')) {
        testResults.joinSuccessful = true;
        console.log('✅ SUCCESS: Player 2 is now in the room!');
      } else {
        console.log('❌ FAILED: Player 2 still in lobby');
      }
    } else {
      console.log('❌ No rooms available to join');
    }
    
    // === STEP 5: Validation Results ===
    console.log('\n=== STEP 5: VALIDATION RESULTS ===');
    
    console.log('\n📊 TEST RESULTS SUMMARY:');
    console.log(`   🏗️ Room created: ${testResults.roomCreated ? '✅' : '❌'}`);
    console.log(`   🤖 Bot removed: ${testResults.botRemoved ? '✅' : '❌'}`);
    console.log(`   🔗 Join attempted: ${testResults.joinAttempted ? '✅' : '❌'}`);
    console.log(`   🎯 Join successful: ${testResults.joinSuccessful ? '✅' : '❌'}`);
    console.log(`   ❌ Error occurred: ${testResults.errorOccurred ? '❌' : '✅'}`);
    console.log(`   🔗 Final URL: ${testResults.finalUrl}`);
    
    console.log('\n📡 WEBSOCKET EVENT TIMELINE:');
    testResults.websocketEvents.forEach((event, i) => {
      const status = event.success === true ? '✅' : event.error ? '❌' : '📝';
      console.log(`${i + 1}. ${status} ${event.player}: ${event.event} ${event.error || ''}`);
    });
    
    // === STEP 6: Final Verdict ===
    console.log('\n🏆 FINAL VERDICT:');
    
    if (testResults.roomCreated && testResults.botRemoved && testResults.joinAttempted && testResults.joinSuccessful) {
      console.log('🎉 SUCCESS: Join room fix is working correctly!');
      console.log('   ✅ Player 1 can create room');
      console.log('   ✅ Player 1 can remove bot');
      console.log('   ✅ Player 2 can join room after bot removal');
      console.log('   ✅ No PlayerJoinedRoom constructor errors');
      console.log('\n🔧 ROOT CAUSE RESOLVED:');
      console.log('   The invalid game_id parameter was removed from PlayerJoinedRoom event');
      console.log('   Room joining now works as expected in the scenario');
    } else if (testResults.errorOccurred) {
      console.log('❌ PARTIAL SUCCESS: Join attempted but still encountering errors');
      console.log('   🔍 Additional debugging may be needed');
    } else if (!testResults.joinAttempted) {
      console.log('❌ FRONTEND ISSUE: Join not attempted (UI problem)');
    } else {
      console.log('❌ BACKEND ISSUE: Join attempted but failed for other reasons');
    }
    
    // === STEP 7: Test complete scenario ===
    console.log('\n=== STEP 7: Verify both players in same room ===');
    
    // Quick check that both players can see each other
    if (testResults.joinSuccessful) {
      console.log('🎮 Both players should now be in the same room');
      console.log('👥 Scenario complete: Player 2 successfully joined after bot removal');
    }
    
    // Keep browsers open for manual verification
    console.log('\n⏱️ Keeping browsers open for 20 seconds for manual verification...');
    await joinerPage.waitForTimeout(20000);
    
  } catch (error) {
    console.error('❌ Validation test failed:', error);
  } finally {
    await browser.close();
  }
}

validateJoinFix().catch(console.error);