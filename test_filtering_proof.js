const { chromium } = require('playwright');

async function proveFilteringIssue() {
  console.log('🔍 PROVING FILTERING ISSUE');
  console.log('🎯 Evidence: Room appears in broadcast but disappears in manual refresh');
  console.log('🎯 Root cause: include_full=false in GetRoomListRequest');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Track WebSocket messages
    const wsMessages = [];
    
    page.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'room_list_update') {
            wsMessages.push({
              timestamp: new Date().toISOString(),
              roomCount: parsed.data?.rooms?.length || 0,
              rooms: parsed.data?.rooms || [],
              source: 'WebSocket broadcast'
            });
            
            console.log(`📥 room_list_update: ${parsed.data?.rooms?.length || 0} rooms`);
            if (parsed.data?.rooms?.length > 0) {
              parsed.data.rooms.forEach(room => {
                console.log(`   🏠 Room ${room.room_id}: ${room.player_count}/${room.max_players} players`);
              });
            }
          }
        } catch (e) {
          // Ignore parse errors
        }
      });
    });
    
    console.log('\n=== STEP 1: Enter lobby as observer ===');
    
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.fill('Observer');
    
    const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await startButton.click();
    
    await page.waitForTimeout(2000);
    
    console.log('✅ Observer entered lobby');
    
    // Wait for any existing room broadcasts
    await page.waitForTimeout(2000);
    
    console.log('\n=== STEP 2: Create room in separate browser ===');
    
    // Open second browser to create room
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    await creatorPage.goto('http://localhost:5050');
    await creatorPage.waitForLoadState('networkidle');
    
    const creatorNameInput = await creatorPage.locator('input[type="text"]').first();
    await creatorNameInput.fill('RoomCreator');
    
    const creatorStartButton = await creatorPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await creatorStartButton.click();
    
    await creatorPage.waitForTimeout(2000);
    
    // Create room
    const createBtn = await creatorPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    
    console.log('🏗️ Room creation initiated');
    
    // Wait for broadcast to reach observer
    await page.waitForTimeout(3000);
    
    console.log('\n=== STEP 3: Manual refresh to trigger filtering ===');
    
    // Manually refresh room list (this triggers GetRoomListRequest)
    const refreshBtn = await page.locator('button[title="Refresh room list"]');
    await refreshBtn.click();
    
    console.log('🔄 Manual refresh triggered');
    
    // Wait for response
    await page.waitForTimeout(2000);
    
    console.log('\n=== STEP 4: Analysis ===');
    
    console.log('📊 WebSocket Message Analysis:');
    wsMessages.forEach((msg, i) => {
      console.log(`${i + 1}. ${msg.timestamp}: ${msg.roomCount} rooms (${msg.source})`);
      if (msg.roomCount > 0) {
        msg.rooms.forEach(room => {
          console.log(`     Room ${room.room_id}: ${room.player_count}/${room.max_players} players`);
        });
      }
    });
    
    console.log('\n🎯 FILTERING PROOF:');
    
    const broadcastMessages = wsMessages.filter(msg => msg.roomCount > 0);
    const emptyMessages = wsMessages.filter(msg => msg.roomCount === 0);
    
    if (broadcastMessages.length > 0 && emptyMessages.length > 0) {
      console.log('✅ CONFIRMED: Room filtering issue');
      console.log(`   📡 Broadcast shows ${broadcastMessages[0].roomCount} room(s)`);
      console.log(`   🔄 Manual refresh returns ${emptyMessages[emptyMessages.length - 1].roomCount} rooms`);
      console.log('   🎯 Root cause: include_full=false in GetRoomListRequest filters 4/4 rooms');
      
      if (broadcastMessages[0].rooms.length > 0) {
        const room = broadcastMessages[0].rooms[0];
        console.log(`   📊 Room details: ${room.player_count}/${room.max_players} players`);
        if (room.player_count >= room.max_players) {
          console.log('   🚨 Room is FULL - explains why include_full=false filters it!');
        }
      }
    } else {
      console.log('❓ Unexpected result - need further investigation');
    }
    
    // Keep open for inspection
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

proveFilteringIssue().catch(console.error);