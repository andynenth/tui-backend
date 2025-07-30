const { chromium } = require('playwright');

async function validateFix() {
  console.log('🧪 VALIDATING FIX');
  console.log('🎯 Expected: Room should be visible immediately after creation (4/4 players)');
  console.log('🔧 Fix applied: include_full=True in broadcast handlers');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    // Observer to watch room visibility
    const observerContext = await browser.newContext();
    const observerPage = await observerContext.newPage();
    
    // Creator to create room
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    const roomUpdates = [];
    
    // Track observer's room updates
    observerPage.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'room_list_update') {
            const roomCount = parsed.data?.rooms?.length || 0;
            roomUpdates.push({
              timestamp: new Date().toISOString(),
              roomCount,
              rooms: parsed.data?.rooms || []
            });
            
            console.log(`📥 Observer received: ${roomCount} rooms`);
            if (roomCount > 0) {
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
    
    console.log('\n=== STEP 1: Setup observer ===');
    
    await observerPage.goto('http://localhost:5050');
    await observerPage.waitForLoadState('networkidle');
    
    const observerNameInput = await observerPage.locator('input[type="text"]').first();
    await observerNameInput.fill('Observer');
    
    const observerStartButton = await observerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await observerStartButton.click();
    
    await observerPage.waitForTimeout(2000);
    console.log('✅ Observer in lobby');
    
    console.log('\n=== STEP 2: Creator creates room ===');
    
    await creatorPage.goto('http://localhost:5050');
    await creatorPage.waitForLoadState('networkidle');
    
    const creatorNameInput = await creatorPage.locator('input[type="text"]').first();
    await creatorNameInput.fill('Creator');
    
    const creatorStartButton = await creatorPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await creatorStartButton.click();
    
    await creatorPage.waitForTimeout(2000);
    
    // Create room
    const createBtn = await creatorPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    
    console.log('🏗️ Room being created...');
    
    // Wait for room creation broadcast
    await observerPage.waitForTimeout(4000);
    
    console.log('\n=== STEP 3: Test manual refresh (the critical test) ===');
    
    // This is the key test - manual refresh should now show the room
    const refreshBtn = await observerPage.locator('button[title="Refresh room list"]');
    await refreshBtn.click();
    
    console.log('🔄 Manual refresh triggered - this should now show the room!');
    
    // Wait for response
    await observerPage.waitForTimeout(3000);
    
    console.log('\n=== STEP 4: Validate UI shows room ===');
    
    try {
      const roomCountText = await observerPage.locator('.lp-roomCount').textContent({ timeout: 5000 });
      const roomCards = await observerPage.locator('.lp-roomCard').count();
      
      console.log(`📊 UI State: ${roomCountText}`);
      console.log(`📊 Actual room cards: ${roomCards}`);
      
      const match = roomCountText.match(/Available Rooms \\((\\d+)\\)/);
      const displayedCount = match ? parseInt(match[1]) : 0;
      
      if (displayedCount > 0 && roomCards > 0) {
        console.log('✅ SUCCESS: Room is visible in UI after manual refresh!');
      } else {
        console.log('❌ FAILURE: Room still not visible in UI');
      }
    } catch (error) {
      console.log(`❌ ERROR: Could not check UI state: ${error.message}`);
    }
    
    console.log('\n=== FINAL VALIDATION ===');
    
    console.log('📊 WebSocket Message Timeline:');
    roomUpdates.forEach((update, i) => {
      console.log(`${i + 1}. ${update.timestamp}: ${update.roomCount} rooms`);
      if (update.roomCount > 0) {
        update.rooms.forEach(room => {
          console.log(`     Room ${room.room_id}: ${room.player_count}/${room.max_players} players`);
        });
      }
    });
    
    // Check if manual refresh returns rooms
    const manualRefreshUpdates = roomUpdates.slice(-2); // Last 2 updates should include the manual refresh
    const hasRoomsAfterRefresh = manualRefreshUpdates.some(update => update.roomCount > 0);
    
    console.log('\\n🎯 FIX VALIDATION RESULT:');
    
    if (hasRoomsAfterRefresh) {
      console.log('✅ FIX SUCCESSFUL!');
      console.log('   📡 Manual refresh now returns rooms');
      console.log('   🏠 Rooms with 4/4 players are no longer filtered');
      console.log('   🎉 Player 2 can now see newly created rooms');
    } else {
      console.log('❌ FIX UNSUCCESSFUL');
      console.log('   📡 Manual refresh still returns empty list');
      console.log('   🔍 Need to investigate further');
    }
    
    // Keep open for visual confirmation
    console.log('\\n⏱️ Keeping browsers open for visual confirmation...');
    await observerPage.waitForTimeout(20000);
    
  } catch (error) {
    console.error('❌ Validation test failed:', error);
  } finally {
    await browser.close();
  }
}

validateFix().catch(console.error);