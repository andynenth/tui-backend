const { chromium } = require('playwright');

async function testBotSlotIssues() {
  console.log('🚀 Testing Bot Slot Management Issues\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable console and request logging
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('ADD_BOT') || text.includes('REMOVE_PLAYER') || text.includes('WebSocket')) {
        console.log('🖥️ Console:', text);
      }
    });
    
    // Log WebSocket frames
    page.on('websocket', ws => {
      console.log('🔌 WebSocket created:', ws.url());
      ws.on('framesent', event => {
        try {
          const data = JSON.parse(event.payload);
          if (data.message_type === 'add_bot' || data.message_type === 'remove_player') {
            console.log('📤 WS SENT:', JSON.stringify(data));
          }
        } catch (e) {}
      });
      ws.on('framereceived', event => {
        try {
          const data = JSON.parse(event.payload);
          if (data.event === 'room_update' || data.event === 'room_list_update') {
            console.log('📥 WS RECEIVED:', data.event);
          }
        } catch (e) {}
      });
    });
    
    // Navigate to home page
    console.log('1️⃣ Navigating to home page...');
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(1000);
    
    // Enter player name
    console.log('2️⃣ Entering player name...');
    await page.fill('input.sp-glowing-input', 'TestHost');
    await page.waitForTimeout(500);
    
    // Enter lobby
    console.log('3️⃣ Entering lobby...');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    
    // Create room
    console.log('4️⃣ Creating room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    // Get room ID
    const roomId = await page.textContent('.rp-roomIdValue').catch(() => 'unknown');
    console.log(`✅ Room created: ${roomId}\n`);
    
    // === TEST ISSUE 2: Add bot to specific slot ===
    console.log('🧪 TESTING ISSUE 2: Add bot to slot 3');
    console.log('Expected: Bot should appear in slot 3\n');
    
    // Click add bot on slot 3
    const slot3AddBtn = await page.locator('.rp-position-3 .rp-addBotBtn').first();
    console.log('Clicking "Add Bot" on slot 3...');
    await slot3AddBtn.click();
    await page.waitForTimeout(2000);
    
    // Check where bot was added
    let botAddedToSlot = null;
    for (let slot = 2; slot <= 4; slot++) {
      const slotHasBot = await page.locator(`.rp-position-${slot} .rp-playerCard.rp-filled`).count() > 0;
      if (slotHasBot) {
        const playerName = await page.textContent(`.rp-position-${slot} .rp-playerName`);
        if (playerName && playerName.includes('Bot')) {
          botAddedToSlot = slot;
          break;
        }
      }
    }
    
    if (botAddedToSlot === 3) {
      console.log('✅ SUCCESS: Bot was added to slot 3');
    } else if (botAddedToSlot) {
      console.log(`❌ ISSUE 2 CONFIRMED: Bot was added to slot ${botAddedToSlot} instead of slot 3`);
    } else {
      console.log('❌ ISSUE 2: No bot was added');
    }
    
    // Take screenshot
    await page.screenshot({ path: 'issue2_add_bot_slot3.png' });
    console.log('📸 Screenshot saved: issue2_add_bot_slot3.png\n');
    
    // === TEST ISSUE 3: Remove specific bot ===
    console.log('🧪 TESTING ISSUE 3: Remove specific bot');
    
    // First, add bots to all empty slots
    console.log('Adding bots to fill all slots...');
    for (let slot = 2; slot <= 4; slot++) {
      const isEmpty = await page.locator(`.rp-position-${slot} .rp-addBotBtn`).count() > 0;
      if (isEmpty) {
        await page.click(`.rp-position-${slot} .rp-addBotBtn`);
        await page.waitForTimeout(1000);
      }
    }
    
    // Record which bot is in slot 3
    const bot3Name = await page.textContent('.rp-position-3 .rp-playerName');
    console.log(`Bot in slot 3: ${bot3Name}`);
    
    // Remove bot from slot 3
    console.log('Clicking "Remove" on slot 3...');
    await page.click('.rp-position-3 .rp-removeBtn');
    await page.waitForTimeout(2000);
    
    // Check if slot 3 is empty
    const slot3IsEmpty = await page.locator('.rp-position-3 .rp-playerCard.rp-empty').count() > 0;
    
    if (slot3IsEmpty) {
      console.log('✅ SUCCESS: Bot was removed from slot 3');
    } else {
      console.log('❌ ISSUE 3 CONFIRMED: Bot was NOT removed from slot 3');
    }
    
    await page.screenshot({ path: 'issue3_remove_bot_slot3.png' });
    console.log('📸 Screenshot saved: issue3_remove_bot_slot3.png\n');
    
    // === TEST ISSUE 1: Lobby update on bot removal ===
    console.log('🧪 TESTING ISSUE 1: Lobby update on bot removal');
    
    // Open lobby in new page
    const lobbyPage = await context.newPage();
    await lobbyPage.goto('http://localhost:5050/lobby');
    await lobbyPage.waitForTimeout(2000);
    
    // Find our room in lobby
    const roomCards = await lobbyPage.locator('.room-card');
    const roomCount = await roomCards.count();
    console.log(`Found ${roomCount} rooms in lobby`);
    
    // Get current player count
    let initialPlayerCount = null;
    for (let i = 0; i < roomCount; i++) {
      const card = roomCards.nth(i);
      const cardText = await card.textContent();
      if (cardText && cardText.includes(roomId)) {
        const playerCountText = await card.locator('.player-count').textContent();
        initialPlayerCount = playerCountText;
        console.log(`Initial lobby shows: ${playerCountText}`);
        break;
      }
    }
    
    // Remove a bot from room
    await page.bringToFront();
    const removeBtn = await page.locator('.rp-removeBtn').first();
    if (await removeBtn.count() > 0) {
      console.log('Removing a bot...');
      await removeBtn.click();
      await page.waitForTimeout(3000);
      
      // Check lobby again
      await lobbyPage.bringToFront();
      await lobbyPage.reload();
      await lobbyPage.waitForTimeout(1000);
      
      // Find updated player count
      let updatedPlayerCount = null;
      const updatedRoomCards = await lobbyPage.locator('.room-card');
      const updatedRoomCount = await updatedRoomCards.count();
      
      for (let i = 0; i < updatedRoomCount; i++) {
        const card = updatedRoomCards.nth(i);
        const cardText = await card.textContent();
        if (cardText && cardText.includes(roomId)) {
          const playerCountText = await card.locator('.player-count').textContent();
          updatedPlayerCount = playerCountText;
          console.log(`After removal, lobby shows: ${playerCountText}`);
          break;
        }
      }
      
      if (initialPlayerCount !== updatedPlayerCount) {
        console.log('✅ SUCCESS: Lobby updated after bot removal');
      } else {
        console.log('❌ ISSUE 1 CONFIRMED: Lobby did NOT update after bot removal');
      }
    }
    
    await lobbyPage.screenshot({ path: 'issue1_lobby_update.png' });
    console.log('📸 Screenshot saved: issue1_lobby_update.png\n');
    
    console.log('✅ All tests completed!');
    console.log('\nPress Enter to close browser...');
    await new Promise(resolve => process.stdin.once('data', resolve));
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

// Run tests
testBotSlotIssues().catch(console.error);