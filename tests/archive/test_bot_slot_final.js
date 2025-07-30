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
  console.log(`\n🚀 Setting up ${playerName}...`);
  await page.goto(BASE_URL);
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Enter player name
  const nameInput = await page.locator('input[type="text"]').first();
  await nameInput.fill(playerName);
  
  // Click enter lobby button
  const enterBtn = await page.locator('button').filter({ hasText: /enter|lobby|play/i }).first();
  await enterBtn.click();
  
  await delay(1500);
  console.log(`✅ ${playerName} entered lobby`);
}

async function getRoomInLobby(page, roomId) {
  try {
    // Check WebSocket messages first
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
    
    // Fallback to UI check
    const roomCards = await page.locator('.room-card, .room-item, [class*="room"]').all();
    for (const card of roomCards) {
      const text = await card.textContent();
      if (text && text.includes(roomId)) {
        const playerCount = await card.locator('.player-count, [class*="player"]').textContent();
        return playerCount;
      }
    }
    
    return null;
  } catch (e) {
    console.log('Error getting room:', e.message);
    return null;
  }
}

async function logBotPositions(page, message) {
  console.log(`\n📍 ${message}`);
  for (let slot = 1; slot <= 4; slot++) {
    try {
      // Check for filled slots using various selectors
      const filledSelectors = [
        `.rp-position-${slot} .rp-playerCard.rp-filled`,
        `.seat-${slot}.filled`,
        `.slot-${slot}.occupied`,
        `[data-slot="${slot}"].filled`
      ];
      
      let hasPlayer = false;
      let playerName = '';
      
      for (const selector of filledSelectors) {
        if (await page.locator(selector).count() > 0) {
          hasPlayer = true;
          // Try to get player name
          const nameElement = await page.locator(`${selector} .rp-playerName, ${selector} .player-name`).first();
          if (await nameElement.count() > 0) {
            playerName = await nameElement.textContent();
          }
          break;
        }
      }
      
      if (!hasPlayer) {
        // Check for empty slots
        const emptySelectors = [
          `.rp-position-${slot} .rp-playerCard.rp-empty`,
          `.seat-${slot}.empty`,
          `.slot-${slot}.empty`
        ];
        
        for (const selector of emptySelectors) {
          if (await page.locator(selector).count() > 0) {
            console.log(`  Slot ${slot}: [empty]`);
            break;
          }
        }
      } else {
        console.log(`  Slot ${slot}: ${playerName || '[occupied]'}`);
      }
    } catch (e) {
      console.log(`  Slot ${slot}: [error reading]`);
    }
  }
}

async function testBotSlotIssues() {
  console.log('🚀 Testing Bot Slot Management Issues - FINAL VERSION\n');
  console.log('This test will NOT refresh pages and will track WebSocket messages\n');
  
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
    
    // Store player name in page context
    await player1Page.evaluate((name) => { window.playerName = name; }, PLAYER1_NAME);
    await player2Page.evaluate((name) => { window.playerName = name; }, PLAYER2_NAME);
    
    // Setup WebSocket monitoring
    [player1Page, player2Page].forEach((page, index) => {
      const playerName = index === 0 ? 'Player1' : 'Player2';
      const messageStore = index === 0 ? wsMessages.player1 : wsMessages.player2;
      
      page.on('websocket', ws => {
        console.log(`🔌 [${playerName}] WebSocket connected: ${ws.url()}`);
        
        ws.on('framesent', event => {
          try {
            const data = JSON.parse(event.payload);
            messageStore.push({ type: 'sent', data, timestamp: new Date().toISOString() });
            
            if (data.event === 'add_bot' || data.event === 'remove_player') {
              console.log(`📤 [${playerName}] SENT ${data.event}:`, JSON.stringify(data.data));
            }
          } catch (e) {}
        });
        
        ws.on('framereceived', event => {
          try {
            const data = JSON.parse(event.payload);
            messageStore.push({ type: 'received', data, timestamp: new Date().toISOString() });
            
            if (data.event === 'room_list_update') {
              const rooms = data.data.rooms || [];
              console.log(`📥 [${playerName}] Room list update: ${rooms.length} rooms`);
              rooms.forEach(room => {
                console.log(`   - ${room.room_id}: ${room.player_count}/${room.max_players} players`);
              });
            } else if (data.event === 'room_update') {
              console.log(`📥 [${playerName}] Room update received`);
            }
          } catch (e) {}
        });
      });
    });
    
    // ========== TEST ISSUE 1 ==========
    console.log('🧪 TEST ISSUE 1: Lobby update when removing bot\n');
    
    // Step 1-2: Player 1 joins lobby and creates room
    await setupPlayer(player1Page, PLAYER1_NAME);
    
    console.log('\n📝 Player 1 creating room...');
    const createBtn = await player1Page.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await delay(2000);
    
    // Get room ID
    const roomIdElement = await player1Page.locator('.rp-roomIdValue, .room-id, [class*="room-id"]').first();
    const roomId = await roomIdElement.textContent();
    console.log(`✅ Room created: ${roomId}`);
    
    await logBotPositions(player1Page, 'Initial room state');
    
    // Step 3: Player 2 joins lobby
    await setupPlayer(player2Page, PLAYER2_NAME);
    
    // Wait for lobby update
    await delay(2000);
    
    const initialLobbyView = await getRoomInLobby(player2Page, roomId);
    console.log(`\n📊 Player 2 sees in lobby: ${initialLobbyView || 'Room not visible'}`);
    
    // Step 4: Player 1 removes bot from slot 3
    console.log('\n🎯 Player 1 clicking remove on slot 3...');
    
    // Try multiple selectors for remove button
    const removeSelectors = [
      '.rp-position-3 .rp-removeBtn',
      '.seat-3 .remove-btn',
      '.slot-3 button.remove',
      '[data-slot="3"] .remove'
    ];
    
    let removeClicked = false;
    for (const selector of removeSelectors) {
      const btn = await player1Page.locator(selector).first();
      if (await btn.count() > 0) {
        console.log(`  Found remove button with selector: ${selector}`);
        await btn.click();
        removeClicked = true;
        break;
      }
    }
    
    if (!removeClicked) {
      console.log('  ❌ Could not find remove button for slot 3');
    }
    
    await delay(2000);
    await logBotPositions(player1Page, 'After clicking remove on slot 3');
    
    // Step 5: Check lobby update WITHOUT refreshing
    console.log('\n⏳ Waiting for lobby update (no refresh)...');
    await delay(3000);
    
    const updatedLobbyView = await getRoomInLobby(player2Page, roomId);
    console.log(`\n📊 Player 2 now sees in lobby: ${updatedLobbyView || 'Room not visible'}`);
    
    // Analyze WebSocket messages
    console.log('\n📨 WebSocket Analysis:');
    const p2RoomUpdates = wsMessages.player2.filter(m => 
      m.type === 'received' && m.data.event === 'room_list_update'
    );
    console.log(`Player 2 received ${p2RoomUpdates.length} room_list_update messages`);
    
    if (initialLobbyView !== updatedLobbyView) {
      console.log('✅ Lobby updated automatically!');
    } else {
      console.log('❌ ISSUE 1 CONFIRMED: Lobby did not update');
    }
    
    // Take screenshots
    await player1Page.screenshot({ path: 'final_test_player1_room.png' });
    await player2Page.screenshot({ path: 'final_test_player2_lobby.png' });
    
    console.log('\n✅ Test completed!');
    console.log('Screenshots saved: final_test_player1_room.png, final_test_player2_lobby.png');
    console.log('\nPress Enter to close browsers...');
    await new Promise(resolve => process.stdin.once('data', resolve));
    
  } catch (error) {
    console.error('❌ Test error:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Run test
testBotSlotIssues().catch(console.error);