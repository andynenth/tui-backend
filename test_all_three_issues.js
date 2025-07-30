const { chromium } = require('playwright');

// Test configuration
const BASE_URL = 'http://localhost:5050';
const PLAYER1_NAME = 'Player1Host';
const PLAYER2_NAME = 'Player2Guest';

// Utility functions
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Store WebSocket messages
const wsMessages = {
  player1: [],
  player2: []
};

async function setupPlayer(page, playerName) {
  console.log(`Setting up ${playerName}...`);
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  const nameInput = await page.locator('input[type="text"]').first();
  await nameInput.fill(playerName);
  
  const enterBtn = await page.locator('button').filter({ hasText: /enter|lobby|play/i }).first();
  await enterBtn.click();
  
  await delay(1500);
  console.log(`✅ ${playerName} entered lobby`);
}

async function getRoomInLobby(page, roomId) {
  try {
    // Check WebSocket messages for room data
    const playerName = await page.evaluate(() => window.playerName);
    const messages = playerName === PLAYER1_NAME ? wsMessages.player1 : wsMessages.player2;
    
    const lastRoomUpdate = messages.filter(m => 
      m.type === 'received' && 
      m.data.event === 'room_list_update'
    ).pop();
    
    if (lastRoomUpdate && lastRoomUpdate.data.data.rooms) {
      const room = lastRoomUpdate.data.data.rooms.find(r => r.room_id === roomId);
      if (room) {
        return `${room.player_count}/${room.max_players} Players`;
      }
    }
    
    return null;
  } catch (e) {
    return null;
  }
}

async function logSlots(page, message) {
  console.log(`\n${message}`);
  for (let slot = 1; slot <= 4; slot++) {
    try {
      const hasPlayer = await page.locator(`.rp-position-${slot} .rp-playerCard.rp-filled`).count() > 0;
      if (hasPlayer) {
        const name = await page.locator(`.rp-position-${slot} .rp-playerName`).textContent();
        console.log(`  Slot ${slot}: ${name}`);
      } else {
        console.log(`  Slot ${slot}: [empty]`);
      }
    } catch (e) {
      console.log(`  Slot ${slot}: [error]`);
    }
  }
}

async function clickRemoveBot(page, slot) {
  const btn = await page.locator(`.rp-position-${slot} .rp-removeBtn`).first();
  if (await btn.count() > 0) {
    await btn.click();
    return true;
  }
  return false;
}

async function clickAddBot(page, slot) {
  const btn = await page.locator(`.rp-position-${slot} .rp-addBotBtn`).first();
  if (await btn.count() > 0) {
    await btn.click();
    return true;
  }
  return false;
}

async function testAllThreeIssues() {
  console.log('🚀 Testing All Three Bot Slot Management Issues\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  try {
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const player1Page = await context1.newPage();
    const player2Page = await context2.newPage();
    
    // Store player names in page context
    await player1Page.evaluate((name) => { window.playerName = name; }, PLAYER1_NAME);
    await player2Page.evaluate((name) => { window.playerName = name; }, PLAYER2_NAME);
    
    // Setup WebSocket monitoring
    [player1Page, player2Page].forEach((page, index) => {
      const playerName = index === 0 ? 'Player1' : 'Player2';
      const messageStore = index === 0 ? wsMessages.player1 : wsMessages.player2;
      
      page.on('websocket', ws => {
        ws.on('framesent', event => {
          try {
            const data = JSON.parse(event.payload);
            messageStore.push({ type: 'sent', data, timestamp: new Date().toISOString() });
            
            if (data.event === 'add_bot' || data.event === 'remove_player') {
              console.log(`📤 [${playerName}] ${data.event}:`, JSON.stringify(data.data));
            }
          } catch (e) {}
        });
        
        ws.on('framereceived', event => {
          try {
            const data = JSON.parse(event.payload);
            messageStore.push({ type: 'received', data, timestamp: new Date().toISOString() });
            
            if (data.event === 'room_list_update') {
              const rooms = data.data.rooms || [];
              console.log(`📥 [${playerName}] room_list_update: ${rooms.length} rooms`);
              rooms.forEach(room => {
                console.log(`   - ${room.room_id}: ${room.player_count}/${room.max_players}`);
              });
            }
          } catch (e) {}
        });
      });
    });
    
    // ========== ISSUE 1: Lobby Update Test ==========
    console.log('═══════════════════════════════════════════════');
    console.log('🧪 ISSUE 1: Lobby update when removing bot');
    console.log('═══════════════════════════════════════════════\n');
    
    // Step 1: Player 1 >> join lobby
    console.log('1. Player 1 >> join lobby');
    await setupPlayer(player1Page, PLAYER1_NAME);
    
    // Step 2: Player 1 >> create room
    console.log('\n2. Player 1 >> create room');
    await player1Page.locator('button').filter({ hasText: /create/i }).first().click();
    await delay(2000);
    
    const roomId = await player1Page.locator('.rp-roomIdValue').textContent();
    console.log(`   Room created: ${roomId}`);
    await logSlots(player1Page, '   Initial state (should be 4/4):');
    
    // Step 3: Player 2 >> join lobby
    console.log('\n3. Player 2 >> join lobby');
    await setupPlayer(player2Page, PLAYER2_NAME);
    await delay(2000);
    
    const initial = await getRoomInLobby(player2Page, roomId);
    console.log(`   Player 2 sees: ${initial || 'Room not visible'}`);
    
    // Step 4: Player 1 >> remove bot 3
    console.log('\n4. Player 1 >> remove bot 3');
    await clickRemoveBot(player1Page, 3);
    await delay(2000);
    await logSlots(player1Page, '   After removal:');
    
    // Step 5: Check lobby update
    console.log('\n5. Checking Player 2 lobby (no refresh)...');
    await delay(3000);
    const updated = await getRoomInLobby(player2Page, roomId);
    console.log(`   Player 2 sees: ${updated || 'Room not visible'}`);
    
    if (initial === '4/4 Players' && updated === '3/4 Players') {
      console.log('✅ Issue 1: Lobby updated correctly');
    } else {
      console.log('❌ Issue 1 CONFIRMED: Lobby did NOT update');
    }
    
    // ========== ISSUE 2: Add Bot Slot Targeting ==========
    console.log('\n\n═══════════════════════════════════════════════');
    console.log('🧪 ISSUE 2: Add bot to specific slot');
    console.log('═══════════════════════════════════════════════\n');
    
    // Navigate back to lobby and create new room for Issue 2
    console.log('Navigating to start fresh for Issue 2...');
    await player1Page.goto(BASE_URL);
    await delay(1500);
    
    // Steps 1-2: Create new room
    console.log('1. Player 1 >> join lobby');
    await setupPlayer(player1Page, PLAYER1_NAME);
    
    console.log('2. Player 1 >> create room');
    await player1Page.locator('button').filter({ hasText: /create/i }).first().click();
    await delay(2000);
    
    const roomId2 = await player1Page.locator('.rp-roomIdValue').textContent();
    console.log(`   New room created: ${roomId2}`);
    
    // Step 3: Player 1 >> remove bot 2
    console.log('\n3. Player 1 >> remove bot 2');
    await clickRemoveBot(player1Page, 2);
    await delay(1000);
    
    // Step 4: Player 2 >> join lobby (already done)
    console.log('4. Player 2 >> join lobby ✓');
    
    // Step 5: Player 1 >> remove bot 3
    console.log('\n5. Player 1 >> remove bot 3');
    await clickRemoveBot(player1Page, 3);
    await delay(1000);
    
    // Step 6: Player 1 >> remove bot 4
    console.log('6. Player 1 >> remove bot 4');
    await clickRemoveBot(player1Page, 4);
    await delay(1000);
    await logSlots(player1Page, 'All bots removed:');
    
    // Step 7: Player 1 >> add bot 3
    console.log('\n7. Player 1 >> add bot 3 (CRITICAL TEST)');
    await clickAddBot(player1Page, 3);
    await delay(2000);
    await logSlots(player1Page, 'After clicking Add Bot on slot 3:');
    
    // Check if bot was added to slot 3
    const slot3HasBot = await player1Page.locator('.rp-position-3 .rp-playerCard.rp-filled').count() > 0;
    if (slot3HasBot) {
      const botName = await player1Page.locator('.rp-position-3 .rp-playerName').textContent();
      if (botName.includes('Bot')) {
        console.log('✅ Bot correctly added to slot 3');
      }
    } else {
      console.log('❌ Issue 2 CONFIRMED: Bot NOT added to slot 3');
      // Check other slots
      for (let s = 2; s <= 4; s++) {
        if (s !== 3) {
          const hasBot = await player1Page.locator(`.rp-position-${s} .rp-playerCard.rp-filled`).count() > 0;
          if (hasBot) {
            console.log(`   Bot was added to slot ${s} instead!`);
          }
        }
      }
    }
    
    // Continue with remaining steps...
    console.log('\n8. Player 2 >> join room');
    await player2Page.goto(`${BASE_URL}/room/${roomId2}`);
    await delay(2000);
    
    console.log('9. Player 1 >> remove Player 2');
    // Find and remove Player 2
    for (let slot = 2; slot <= 4; slot++) {
      const name = await player1Page.locator(`.rp-position-${slot} .rp-playerName`).textContent().catch(() => '');
      if (name === PLAYER2_NAME) {
        await clickRemoveBot(player1Page, slot);
        break;
      }
    }
    await delay(1000);
    
    console.log('10. Player 1 >> remove bot 3');
    await clickRemoveBot(player1Page, 3);
    await delay(1000);
    
    console.log('11. Player 1 >> add bot 4');
    await clickAddBot(player1Page, 4);
    await delay(1000);
    
    console.log('12. Player 1 >> add bot 3');
    await clickAddBot(player1Page, 3);
    await delay(1000);
    
    console.log('13. Player 1 >> add bot 2');
    await clickAddBot(player1Page, 2);
    await delay(1000);
    
    await logSlots(player1Page, 'Final state for Issue 2:');
    
    // ========== ISSUE 3: Remove Bot Slot Targeting ==========
    console.log('\n\n═══════════════════════════════════════════════');
    console.log('🧪 ISSUE 3: Remove bot from specific slot');
    console.log('═══════════════════════════════════════════════\n');
    
    console.log('Testing removal of bot from slot 3...');
    const beforeRemoval = await player1Page.locator('.rp-position-3 .rp-playerName').textContent();
    console.log(`Bot in slot 3 before: ${beforeRemoval}`);
    
    await clickRemoveBot(player1Page, 3);
    await delay(1500);
    
    const slot3Empty = await player1Page.locator('.rp-position-3 .rp-playerCard.rp-empty').count() > 0;
    if (slot3Empty) {
      console.log('✅ Bot correctly removed from slot 3');
    } else {
      console.log('❌ Issue 3 CONFIRMED: Bot NOT removed from slot 3');
      // Check which slot became empty
      for (let s = 1; s <= 4; s++) {
        const isEmpty = await player1Page.locator(`.rp-position-${s} .rp-playerCard.rp-empty`).count() > 0;
        if (isEmpty) {
          console.log(`   Slot ${s} became empty instead!`);
        }
      }
    }
    
    await logSlots(player1Page, 'Final state:');
    
    // Save screenshots
    await player1Page.screenshot({ path: 'all_issues_player1.png' });
    await player2Page.screenshot({ path: 'all_issues_player2.png' });
    
    console.log('\n✅ All tests completed!');
    console.log('\nPress Enter to close browsers...');
    await new Promise(resolve => process.stdin.once('data', resolve));
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

// Run test
testAllThreeIssues().catch(console.error);