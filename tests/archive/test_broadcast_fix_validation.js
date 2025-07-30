const { chromium } = require('playwright');

/**
 * BROADCAST FIX VALIDATION TEST
 * 
 * Validates that the room_update broadcast fixes are working correctly.
 * Tests specifically that host_name and started fields are now populated.
 */

async function validateBroadcastFix() {
  console.log('🧪 BROADCAST FIX VALIDATION TEST');
  console.log('==================================');
  console.log('🔧 Fix applied: Updated broadcast_handlers.py to include actual room state');
  console.log('🔧 Fix applied: Disabled duplicate event_broadcast_mapper registrations');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    const evidence = {
      roomUpdates: [],
      playerJoins: [],
      testResults: {}
    };
    
    const captureMessages = (page, playerName) => {
      page.on('websocket', ws => {
        ws.on('framereceived', data => {
          try {
            const parsed = JSON.parse(data.payload);
            
            if (parsed.event === 'room_update') {
              const update = {
                timestamp: new Date().toISOString(),
                receiver: playerName,
                room_id: parsed.data?.room_id,
                host_name: parsed.data?.host_name,
                started: parsed.data?.started,
                players: parsed.data?.players || [],
                hasValidHostName: parsed.data?.host_name && parsed.data?.host_name !== 'undefined' && parsed.data?.host_name !== '',
                hasValidStarted: parsed.data?.started !== undefined && parsed.data?.started !== null
              };
              
              evidence.roomUpdates.push(update);
              
              console.log(`📥 ${playerName} room_update:`);
              console.log(`   Host: "${update.host_name}" (valid: ${update.hasValidHostName})`);
              console.log(`   Started: "${update.started}" (valid: ${update.hasValidStarted})`);
              console.log(`   Players: ${update.players.length} (${update.players.map(p => p?.name || 'null').join(', ')})`);
            }
            
            if (parsed.event === 'room_joined') {
              evidence.playerJoins.push({
                timestamp: new Date().toISOString(),
                receiver: playerName,
                success: parsed.data?.success,
                room_id: parsed.data?.room_id
              });
              
              console.log(`🔗 ${playerName} room_joined: ${parsed.data?.success ? 'SUCCESS' : 'FAILED'}`);
            }
          } catch (e) {}
        });
      });
    };
    
    // === Test 1: Room Creation ===
    console.log('\n=== TEST 1: Room Creation ===');
    const hostContext = await browser.newContext();
    const hostPage = await hostContext.newPage();
    captureMessages(hostPage, 'Host');
    
    await hostPage.goto('http://localhost:5050');
    await hostPage.waitForLoadState('networkidle');
    
    await hostPage.locator('input[type="text"]').first().fill('TestHost');
    await hostPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await hostPage.waitForTimeout(2000);
    
    const createBtn = await hostPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await hostPage.waitForTimeout(5000);
    
    // === Test 2: Player Join ===
    console.log('\n=== TEST 2: Player Join ===');
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    captureMessages(joinerPage, 'Joiner');
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('TestJoiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // Join room
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      console.log('🎯 Attempting to join room...');
      await roomCards[0].click();
      await joinerPage.waitForTimeout(5000);
    } else {
      console.log('❌ No room cards found');
    }
    
    // === Test 3: Bot Removal (triggers room_update) ===
    console.log('\n=== TEST 3: Bot Removal ===');
    const removeBtns = await hostPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeBtns.length > 0) {
      console.log('🤖 Removing bot to trigger room_update...');
      await removeBtns[0].click();
      await hostPage.waitForTimeout(3000);
    }
    
    // === Analysis ===
    console.log('\n=== BROADCAST FIX ANALYSIS ===');
    
    console.log(`\n📊 Statistics:`);
    console.log(`   Total room_update messages: ${evidence.roomUpdates.length}`);
    console.log(`   Player join messages: ${evidence.playerJoins.length}`);
    
    // Check for valid host_name fields
    const validHostNames = evidence.roomUpdates.filter(u => u.hasValidHostName);
    const invalidHostNames = evidence.roomUpdates.filter(u => !u.hasValidHostName);
    
    console.log(`\n🏠 Host Name Validation:`);
    console.log(`   Valid host names: ${validHostNames.length}/${evidence.roomUpdates.length}`);
    console.log(`   Invalid host names: ${invalidHostNames.length}/${evidence.roomUpdates.length}`);
    
    if (invalidHostNames.length > 0) {
      console.log(`   ❌ Invalid host name examples:`);
      invalidHostNames.slice(0, 3).forEach(update => {
        console.log(`      ${update.receiver}: "${update.host_name}"`);
      });
    }
    
    // Check for valid started fields
    const validStarted = evidence.roomUpdates.filter(u => u.hasValidStarted);
    const invalidStarted = evidence.roomUpdates.filter(u => !u.hasValidStarted);
    
    console.log(`\n🎮 Started Field Validation:`);
    console.log(`   Valid started fields: ${validStarted.length}/${evidence.roomUpdates.length}`);
    console.log(`   Invalid started fields: ${invalidStarted.length}/${evidence.roomUpdates.length}`);
    
    // Check for proper player data
    const roomUpdatesWithPlayers = evidence.roomUpdates.filter(u => u.players.length > 0);
    
    console.log(`\n👥 Player Data Validation:`);
    console.log(`   Updates with player data: ${roomUpdatesWithPlayers.length}/${evidence.roomUpdates.length}`);
    
    // Final verdict
    console.log(`\n🏆 FINAL VERDICT:`);
    
    const allFieldsValid = evidence.roomUpdates.length > 0 && 
                          invalidHostNames.length === 0 && 
                          invalidStarted.length === 0 &&
                          roomUpdatesWithPlayers.length > 0;
    
    if (allFieldsValid) {
      console.log('✅ SUCCESS: All room_update broadcasts now include complete data');
      console.log('   ✅ host_name fields are populated');
      console.log('   ✅ started fields are populated'); 
      console.log('   ✅ player data is included');
      console.log('\n🔧 ROOT CAUSE RESOLVED:');
      console.log('   Fixed broadcast_handlers.py to query actual room state');
      console.log('   Disabled duplicate event_broadcast_mapper registrations');
    } else if (evidence.roomUpdates.length === 0) {
      console.log('❓ INCONCLUSIVE: No room_update messages captured');
      console.log('   This could indicate the events are not being triggered');
    } else {
      console.log('❌ PARTIAL SUCCESS: Some issues remain');
      if (invalidHostNames.length > 0) {
        console.log('   ❌ host_name fields still incomplete');
      }
      if (invalidStarted.length > 0) {
        console.log('   ❌ started fields still incomplete');
      }
      if (roomUpdatesWithPlayers.length === 0) {
        console.log('   ❌ player data missing from broadcasts');
      }
    }
    
    // Store results for validation
    evidence.testResults = {
      totalUpdates: evidence.roomUpdates.length,
      validHostNames: validHostNames.length,
      validStarted: validStarted.length,
      withPlayerData: roomUpdatesWithPlayers.length,
      allValid: allFieldsValid
    };
    
    console.log('\n⏱️ Keeping browsers open for manual verification...');
    await hostPage.waitForTimeout(20000);
    
    return evidence.testResults;
    
  } catch (error) {
    console.error('❌ Validation test failed:', error);
  } finally {
    await browser.close();
  }
}

validateBroadcastFix().catch(console.error);