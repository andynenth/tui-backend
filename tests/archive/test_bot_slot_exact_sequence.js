const { chromium } = require('playwright');

// Test configuration
const BASE_URL = 'http://localhost:5050';
const PLAYER1_NAME = 'Player1Host';
const PLAYER2_NAME = 'Player2Guest';

// Utility functions
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function setupPlayer(page, playerName) {
  console.log(`Setting up ${playerName}...`);
  await page.goto(BASE_URL);
  await page.fill('input.sp-glowing-input', playerName);
  await page.click('button:has-text("Enter Lobby")');
  await delay(1500);
}

async function getRoomPlayerCount(lobbyPage, roomId) {
  const roomCards = await lobbyPage.locator('.room-card');
  const count = await roomCards.count();
  
  for (let i = 0; i < count; i++) {
    const card = roomCards.nth(i);
    const text = await card.textContent();
    if (text && text.includes(roomId)) {
      const playerCount = await card.locator('.player-count').textContent();
      return playerCount;
    }
  }
  return null;
}

async function logBotPositions(page, message) {
  console.log(`\n📍 ${message}`);
  for (let slot = 1; slot <= 4; slot++) {
    const hasPlayer = await page.locator(`.rp-position-${slot} .rp-playerCard.rp-filled`).count() > 0;
    if (hasPlayer) {
      const name = await page.textContent(`.rp-position-${slot} .rp-playerName`);
      console.log(`  Slot ${slot}: ${name}`);
    } else {
      console.log(`  Slot ${slot}: [empty]`);
    }
  }
}

async function testBotSlotIssues() {
  console.log('🚀 Testing Bot Slot Management Issues - EXACT SEQUENCES\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  try {
    // Create two browser contexts
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const player1Page = await context1.newPage();
    const player2Page = await context2.newPage();
    
    // Setup WebSocket logging for both players
    [player1Page, player2Page].forEach((page, index) => {
      const playerName = index === 0 ? 'Player1' : 'Player2';
      
      page.on('websocket', ws => {
        ws.on('framesent', event => {
          try {
            const data = JSON.parse(event.payload);
            if (data.message_type === 'add_bot' || data.message_type === 'remove_player') {
              console.log(`📤 [${playerName}] WS SENT:`, JSON.stringify(data));
            }
          } catch (e) {}
        });
        
        ws.on('framereceived', event => {
          try {
            const data = JSON.parse(event.payload);
            if (data.event === 'room_update' || data.event === 'room_list_update') {
              console.log(`📥 [${playerName}] WS RECEIVED: ${data.event}`);
            }
          } catch (e) {}
        });
      });
    });
    
    // ========== TEST ISSUE 1 ==========
    console.log('🧪 TEST ISSUE 1: Lobby update when removing bot\n');
    console.log('Expected: Player 2 should see room update from 4/4 to 3/4\n');
    
    // Step 1: Player 1 >> join lobby
    console.log('1. Player 1 >> join lobby');
    await setupPlayer(player1Page, PLAYER1_NAME);
    
    // Step 2: Player 1 >> create room
    console.log('2. Player 1 >> create room');
    await player1Page.click('button:has-text("Create Room")');
    await delay(2000);
    
    const roomId = await player1Page.textContent('.rp-roomIdValue');
    console.log(`   Room created: ${roomId}`);
    await logBotPositions(player1Page, 'Initial room state (should be 4/4)');
    
    // Step 3: Player 2 >> join lobby
    console.log('\n3. Player 2 >> join lobby');
    await setupPlayer(player2Page, PLAYER2_NAME);
    
    const initialCount = await getRoomPlayerCount(player2Page, roomId);
    console.log(`   Player 2 sees in lobby: ${initialCount}`);
    
    // Step 4: Player 1 >> remove bot 3
    console.log('\n4. Player 1 >> remove bot 3');
    await player1Page.click('.rp-position-3 .rp-removeBtn');
    await delay(2000);
    await logBotPositions(player1Page, 'After removing bot 3');
    
    // Step 5: Check if Player 2 sees update
    console.log('\n5. Checking if Player 2 sees the update...');
    await delay(2000); // Give time for update to propagate
    await player2Page.reload(); // Reload to check for updates
    await delay(1000);
    
    const updatedCount = await getRoomPlayerCount(player2Page, roomId);
    console.log(`   Player 2 now sees in lobby: ${updatedCount}`);
    
    if (initialCount === '4/4 Players' && updatedCount === '3/4 Players') {
      console.log('✅ ISSUE 1: NOT CONFIRMED - Lobby correctly updated from 4/4 to 3/4');
    } else {
      console.log('❌ ISSUE 1: CONFIRMED - Lobby did NOT update correctly');
      console.log(`   Expected: 4/4 → 3/4, Actual: ${initialCount} → ${updatedCount}`);
    }
    
    await player1Page.screenshot({ path: 'issue1_player1_room.png' });
    await player2Page.screenshot({ path: 'issue1_player2_lobby.png' });
    
    // ========== TEST ISSUE 2 ==========
    console.log('\n\n🧪 TEST ISSUE 2: Add bot to specific slot\n');
    console.log('Following exact 13-step sequence...\n');
    
    // Reset for Issue 2 test
    await player1Page.reload();
    await delay(1500);
    
    // Steps 1-2 already done (Player 1 in room)
    
    // Step 3: Player 1 >> remove bot 2
    console.log('3. Player 1 >> remove bot 2');
    const bot2RemoveBtn = await player1Page.locator('.rp-position-2 .rp-removeBtn');
    if (await bot2RemoveBtn.count() > 0) {
      await bot2RemoveBtn.click();
      await delay(1000);
    } else {
      console.log('   No remove button in slot 2 - continuing...');
    }
    
    // Step 4: Player 2 >> join lobby (already done)
    console.log('4. Player 2 >> join lobby (already in lobby)');
    
    // Step 5: Player 1 >> remove bot 3
    console.log('5. Player 1 >> remove bot 3');
    const bot3RemoveBtn = await player1Page.locator('.rp-position-3 .rp-removeBtn');
    if (await bot3RemoveBtn.count() > 0) {
      await bot3RemoveBtn.click();
      await delay(1000);
    }
    
    // Step 6: Player 1 >> remove bot 4
    console.log('6. Player 1 >> remove bot 4');
    await player1Page.click('.rp-position-4 .rp-removeBtn');
    await delay(1000);
    await logBotPositions(player1Page, 'After removing all bots');
    
    // Step 7: Player 1 >> add bot 3
    console.log('\n7. Player 1 >> add bot 3 (CRITICAL TEST)');
    await player1Page.click('.rp-position-3 .rp-addBotBtn');
    await delay(1500);
    await logBotPositions(player1Page, 'After clicking Add Bot on slot 3');
    
    // Check if bot was added to correct slot
    const bot3Added = await player1Page.locator('.rp-position-3 .rp-playerCard.rp-filled').count() > 0;
    if (bot3Added) {
      const botName = await player1Page.textContent('.rp-position-3 .rp-playerName');
      if (botName.includes('Bot')) {
        console.log('✅ Bot correctly added to slot 3');
      }
    } else {
      console.log('❌ ISSUE 2: CONFIRMED - Bot was NOT added to slot 3');
      // Check other slots
      for (let slot = 2; slot <= 4; slot++) {
        if (slot !== 3) {
          const hasBot = await player1Page.locator(`.rp-position-${slot} .rp-playerCard.rp-filled`).count() > 0;
          if (hasBot) {
            console.log(`   Bot was incorrectly added to slot ${slot}`);
          }
        }
      }
    }
    
    // Step 8: Player 2 >> join room
    console.log('\n8. Player 2 >> join room');
    await player2Page.goto(`${BASE_URL}/room/${roomId}`);
    await delay(2000);
    
    // Step 9: Player 1 >> remove Player 2
    console.log('9. Player 1 >> remove Player 2');
    // Find Player 2's slot
    for (let slot = 2; slot <= 4; slot++) {
      const playerName = await player1Page.textContent(`.rp-position-${slot} .rp-playerName`).catch(() => '');
      if (playerName === PLAYER2_NAME) {
        await player1Page.click(`.rp-position-${slot} .rp-removeBtn`);
        break;
      }
    }
    await delay(1000);
    
    // Step 10: Player 1 >> remove bot 3
    console.log('10. Player 1 >> remove bot 3');
    const removeBot3Again = await player1Page.locator('.rp-position-3 .rp-removeBtn');
    if (await removeBot3Again.count() > 0) {
      await removeBot3Again.click();
      await delay(1000);
    }
    
    // Step 11: Player 1 >> add bot 4
    console.log('11. Player 1 >> add bot 4');
    await player1Page.click('.rp-position-4 .rp-addBotBtn');
    await delay(1000);
    
    // Step 12: Player 1 >> add bot 3
    console.log('12. Player 1 >> add bot 3');
    await player1Page.click('.rp-position-3 .rp-addBotBtn');
    await delay(1000);
    
    // Step 13: Player 1 >> add bot 2
    console.log('13. Player 1 >> add bot 2');
    await player1Page.click('.rp-position-2 .rp-addBotBtn');
    await delay(1000);
    
    await logBotPositions(player1Page, 'Final state for Issue 2 test');
    await player1Page.screenshot({ path: 'issue2_final_state.png' });
    
    // ========== TEST ISSUE 3 ==========
    console.log('\n\n🧪 TEST ISSUE 3: Remove bot from specific slot\n');
    console.log('Using same sequence, verifying correct bot removal...\n');
    
    // The setup is already done from Issue 2 test
    // Now we verify that removing bot 3 removes the correct bot
    
    console.log('Testing: Remove bot from slot 3');
    const bot3Name = await player1Page.textContent('.rp-position-3 .rp-playerName');
    console.log(`Bot in slot 3 before removal: ${bot3Name}`);
    
    await player1Page.click('.rp-position-3 .rp-removeBtn');
    await delay(1500);
    
    // Check if slot 3 is now empty
    const slot3Empty = await player1Page.locator('.rp-position-3 .rp-playerCard.rp-empty').count() > 0;
    
    if (slot3Empty) {
      console.log('✅ ISSUE 3: NOT CONFIRMED - Correct bot was removed from slot 3');
    } else {
      console.log('❌ ISSUE 3: CONFIRMED - Bot was NOT removed from slot 3');
    }
    
    await logBotPositions(player1Page, 'After removing bot from slot 3');
    await player1Page.screenshot({ path: 'issue3_after_removal.png' });
    
    console.log('\n✅ All tests completed following exact sequences!');
    console.log('\nPress Enter to close browsers...');
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