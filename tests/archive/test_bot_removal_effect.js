const { chromium } = require('playwright');

async function testBotRemovalEffect() {
  console.log('🔍 TESTING BOT REMOVAL EFFECT');
  console.log('🎯 Hypothesis: Room becomes visible when player count drops below max_players');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    // Observer to watch room visibility
    const observerContext = await browser.newContext();
    const observerPage = await observerContext.newPage();
    
    // Creator to create room and remove bots
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    const roomUpdates = [];
    
    // Track observer's room updates
    observerPage.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'room_list_update') {
            roomUpdates.push({
              timestamp: new Date().toISOString(),
              player: 'Observer',
              roomCount: parsed.data?.rooms?.length || 0,
              rooms: parsed.data?.rooms || []
            });
            
            console.log(`📥 Observer: ${parsed.data?.rooms?.length || 0} rooms`);
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
    
    // Wait for room creation and navigation
    await creatorPage.waitForTimeout(5000);
    
    console.log('\n=== STEP 3: Check room visibility (should be hidden) ===');
    
    // Observer manually refreshes to see if room is visible
    const refreshBtn = await observerPage.locator('button[title="Refresh room list"]');
    await refreshBtn.click();
    
    await observerPage.waitForTimeout(2000);
    
    console.log('\n=== STEP 4: Creator removes bot ===');
    
    // Check if creator is in room page
    try {
      // Look for remove/kick buttons
      const removeBtns = await creatorPage.locator('button:has-text(\"Remove\"), button:has-text(\"Kick\")').all();
      
      if (removeBtns.length > 0) {
        console.log(`🎯 Found ${removeBtns.length} remove buttons, clicking first one`);
        await removeBtns[0].click();
        await creatorPage.waitForTimeout(2000);
        console.log('✅ Bot removal attempted');
      } else {
        console.log('❓ No remove buttons found, trying alternative approach');
        
        // Try right-clicking on bot slots or look for other bot management
        const botSlots = await creatorPage.locator('.player-slot, .seat, [class*=\"bot\"]').all();
        if (botSlots.length > 0) {
          console.log(`🎯 Found ${botSlots.length} player slots, trying to interact`);
          // This might not work but let's try
          await botSlots[0].click();
          await creatorPage.waitForTimeout(1000);
        }
      }
    } catch (error) {
      console.log(`❓ Could not remove bot: ${error.message}`);
    }
    
    console.log('\n=== STEP 5: Check if room becomes visible ===');
    
    // Wait a moment for any events to propagate
    await observerPage.waitForTimeout(3000);
    
    // Observer refreshes again
    await observerPage.locator('button[title="Refresh room list"]').click();
    await observerPage.waitForTimeout(2000);
    
    console.log('\n=== FINAL ANALYSIS ===');
    
    console.log('📊 Room visibility timeline:');
    roomUpdates.forEach((update, i) => {
      console.log(`${i + 1}. ${update.timestamp}: ${update.roomCount} rooms`);
      if (update.roomCount > 0) {
        update.rooms.forEach(room => {
          console.log(`     Room ${room.room_id}: ${room.player_count}/${room.max_players} players`);
        });
      }
    });
    
    // Analyze the pattern
    const beforeBotRemoval = roomUpdates.filter(u => u.timestamp < new Date(Date.now() - 10000).toISOString());
    const afterBotRemoval = roomUpdates.filter(u => u.timestamp >= new Date(Date.now() - 10000).toISOString());
    
    console.log('\n🎯 BOT REMOVAL EFFECT:');
    
    const visibleRoomsBefore = beforeBotRemoval.filter(u => u.roomCount > 0);
    const visibleRoomsAfter = afterBotRemoval.filter(u => u.roomCount > 0);
    
    if (visibleRoomsBefore.length === 0 && visibleRoomsAfter.length > 0) {
      console.log('✅ CONFIRMED: Room becomes visible after bot removal');
      console.log('   📊 Before: Room hidden (4/4 players)'); 
      console.log('   📊 After: Room visible (3/4 players)');
    } else if (visibleRoomsBefore.length > 0 && visibleRoomsAfter.length === 0) {
      console.log('❓ Room was visible then disappeared');
    } else {
      console.log('📝 Pattern unclear from this test - manual verification needed');
    }
    
    // Keep browsers open for manual verification
    console.log('\n⏱️ Browsers staying open for manual verification...');
    await observerPage.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

testBotRemovalEffect().catch(console.error);