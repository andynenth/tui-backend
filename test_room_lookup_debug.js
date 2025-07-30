const { chromium } = require('playwright');

/**
 * ROOM LOOKUP DEBUG TEST
 * 
 * Tests the exact room lookup mechanism to identify why join_room fails.
 * Focus on capturing the room_id that gets created vs the room_id being looked up.
 */

async function debugRoomLookup() {
  console.log('🔍 ROOM LOOKUP DEBUG TEST');
  console.log('=========================');
  console.log('🎯 Objective: Identify exact room lookup failure cause');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 2000
  });
  
  try {
    const evidence = {
      roomCreation: {},
      roomLookup: {},
      websocketMessages: []
    };
    
    // === STEP 1: Create room and capture exact room_id ===
    console.log('\n=== STEP 1: Create room and capture details ===');
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    // Capture WebSocket messages to get exact room_id
    creatorPage.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          evidence.websocketMessages.push({
            timestamp: new Date().toISOString(),
            player: 'Creator',
            direction: 'received',
            event: parsed.event,
            data: parsed.data
          });
          
          if (parsed.event === 'room_created') {
            evidence.roomCreation = {
              room_id: parsed.data?.room_id,
              room_code: parsed.data?.room_code,
              host_name: parsed.data?.host_name,
              success: parsed.data?.success,
              room_info: parsed.data?.room_info
            };
            console.log('📋 ROOM CREATED:', evidence.roomCreation);
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
    
    // Capture room ID from URL as well
    const creatorUrl = creatorPage.url();
    const urlRoomId = creatorUrl.match(/\/room\/([^/?]+)/)?.[1];
    console.log('🔗 URL Room ID:', urlRoomId);
    
    if (!evidence.roomCreation.room_id) {
      console.log('❌ Failed to capture room creation details');
      return;
    }
    
    // === STEP 2: Remove bot to create joining opportunity ===
    console.log('\n=== STEP 2: Remove bot ===');
    const removeBtns = await creatorPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeBtns.length > 0) {
      await removeBtns[0].click();
      await creatorPage.waitForTimeout(3000);
      console.log('✅ Bot removed');
    }
    
    // === STEP 3: Set up joiner and capture join attempt details ===
    console.log('\n=== STEP 3: Setup joiner and attempt join ===');
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    
    // Capture joiner's WebSocket messages
    joinerPage.on('websocket', ws => {
      ws.on('framesent', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'join_room') {
            evidence.roomLookup = {
              sent_room_id: parsed.data?.room_id,
              sent_player_name: parsed.data?.player_name,
              sent_player_id: parsed.data?.player_id,
              timestamp: new Date().toISOString()
            };
            console.log('📤 JOIN ROOM SENT:', evidence.roomLookup);
          }
        } catch (e) {}
      });
      
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'error' && parsed.data?.message?.includes('join_room')) {
            evidence.joinError = {
              message: parsed.data?.message,
              type: parsed.data?.type,
              details: parsed.data?.details,
              timestamp: new Date().toISOString()
            };
            console.log('❌ JOIN ERROR:', evidence.joinError);
          }
        } catch (e) {}
      });
    });
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('Joiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // === STEP 4: Detailed room card analysis before join ===
    console.log('\n=== STEP 4: Analyze room cards before join ===');
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    
    if (roomCards.length > 0) {
      const cardText = await roomCards[0].textContent();
      console.log('🏠 Room card text:', cardText);
      
      // Try to extract room_id from card if visible
      const roomIdMatch = cardText.match(/([A-Z0-9]{6})/);
      const cardRoomId = roomIdMatch?.[1];
      console.log('🔍 Room ID from card:', cardRoomId);
      
      evidence.cardAnalysis = {
        cardText,
        extractedRoomId: cardRoomId,
        visibleRoomCount: roomCards.length
      };
    }
    
    // === STEP 5: Attempt join and capture results ===
    console.log('\n=== STEP 5: Attempt join ===');
    if (roomCards.length > 0) {
      await roomCards[0].click();
      await joinerPage.waitForTimeout(5000);
      
      const finalUrl = joinerPage.url();
      console.log('🔗 Final URL after join attempt:', finalUrl);
    }
    
    // === STEP 6: Comprehensive analysis ===
    console.log('\n=== STEP 6: ROOT CAUSE ANALYSIS ===');
    
    console.log('\n📊 ROOM CREATION EVIDENCE:');
    console.log('   WebSocket room_id:', evidence.roomCreation.room_id);
    console.log('   URL room_id:', urlRoomId);
    console.log('   Room code:', evidence.roomCreation.room_code);
    console.log('   Success:', evidence.roomCreation.success);
    
    console.log('\n🔍 ROOM LOOKUP EVIDENCE:');
    if (evidence.roomLookup.sent_room_id) {
      console.log('   Sent room_id:', evidence.roomLookup.sent_room_id);
      console.log('   Sent player_name:', evidence.roomLookup.sent_player_name);
      console.log('   Sent player_id:', evidence.roomLookup.sent_player_id);
    } else {
      console.log('   ❌ No join_room message captured');
    }
    
    console.log('\n🚫 ERROR ANALYSIS:');
    if (evidence.joinError) {
      console.log('   Error message:', evidence.joinError.message);
      console.log('   Error type:', evidence.joinError.type);
      console.log('   Error details:', evidence.joinError.details);
    } else {
      console.log('   ❌ No error message captured');
    }
    
    console.log('\n🃏 CARD ANALYSIS:');
    if (evidence.cardAnalysis) {
      console.log('   Card room_id:', evidence.cardAnalysis.extractedRoomId);
      console.log('   Visible rooms:', evidence.cardAnalysis.visibleRoomCount);
    }
    
    // === STEP 7: ID Comparison ===
    console.log('\n🎯 ID COMPARISON ANALYSIS:');
    
    const createdRoomId = evidence.roomCreation.room_id;
    const lookupRoomId = evidence.roomLookup?.sent_room_id;
    const cardRoomId = evidence.cardAnalysis?.extractedRoomId;
    const urlRoomId2 = urlRoomId;
    
    console.log(`   Created room_id: "${createdRoomId}"`);
    console.log(`   Lookup room_id:  "${lookupRoomId}"`);
    console.log(`   Card room_id:    "${cardRoomId}"`);
    console.log(`   URL room_id:     "${urlRoomId2}"`);
    
    if (createdRoomId === lookupRoomId) {
      console.log('✅ Room IDs MATCH - issue is elsewhere');
    } else {
      console.log('❌ Room IDs MISMATCH - this is the root cause!');
      console.log('   The frontend is sending a different room_id than what was created');
    }
    
    // === STEP 8: Player ID Analysis ===
    console.log('\n👤 PLAYER ID ANALYSIS:');
    
    if (evidence.roomLookup?.sent_player_id) {
      console.log('   Join attempt player_id:', evidence.roomLookup.sent_player_id);
      console.log('   Player_id format matches expected pattern?', /^[A-Z0-9]+_p\d+$/.test(evidence.roomLookup.sent_player_id));
    }
    
    // Final verdict
    console.log('\n🏆 FINAL VERDICT:');
    
    if (!evidence.roomLookup?.sent_room_id) {
      console.log('❌ FRONTEND ISSUE: join_room message not sent properly');
    } else if (createdRoomId !== lookupRoomId) {
      console.log('❌ ID MISMATCH ISSUE: Frontend sending wrong room_id');  
    } else if (evidence.joinError?.details) {
      console.log('❌ BACKEND ISSUE: Room lookup failed in database');
      console.log(`   Specific error: ${evidence.joinError.details}`);
    } else {
      console.log('❓ UNKNOWN ISSUE: Need to check server logs for detailed error');
    }
    
    // Keep browsers open for inspection
    console.log('\n⏱️ Keeping browsers open for manual inspection...');
    await joinerPage.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Debug test failed:', error);
  } finally {
    await browser.close();
  }
}

debugRoomLookup().catch(console.error);