const { chromium } = require('playwright');

// Constants
const BASE_URL = 'http://localhost:5050';
const TEST_TIMEOUT = 60000;

// Test data
const HOST_NAME = 'TestHost';
const GUEST_NAME = 'TestGuest';

// Utility functions
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const takeEvidence = async (page, name) => {
  await page.screenshot({ path: `evidence_${name}.png`, fullPage: true });
  console.log(`📸 Evidence captured: ${name}`);
};

const captureWebSocketMessages = (page, label) => {
  return page.evaluate((label) => {
    window.__wsMessages = window.__wsMessages || [];
    
    // Intercept WebSocket send
    const originalSend = WebSocket.prototype.send;
    WebSocket.prototype.send = function(data) {
      const message = JSON.parse(data);
      window.__wsMessages.push({
        direction: 'SENT',
        label,
        time: new Date().toISOString(),
        data: message
      });
      console.log(`🔵 [${label}] WS SENT:`, message);
      return originalSend.call(this, data);
    };
    
    // Intercept WebSocket receive
    const sockets = Array.from(window.__websockets || []);
    sockets.forEach(ws => {
      ws.addEventListener('message', (event) => {
        try {
          const message = JSON.parse(event.data);
          window.__wsMessages.push({
            direction: 'RECEIVED',
            label,
            time: new Date().toISOString(),
            data: message
          });
          console.log(`🟢 [${label}] WS RECEIVED:`, message);
        } catch (e) {}
      });
    });
  }, label);
};

const getWebSocketMessages = async (page) => {
  return await page.evaluate(() => window.__wsMessages || []);
};

const waitForRoomUpdate = async (page, expectedUpdate, timeout = 5000) => {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const players = await page.evaluate(() => {
      const playerCards = document.querySelectorAll('.rp-playerCard.rp-filled');
      return Array.from(playerCards).map(card => {
        const nameEl = card.querySelector('.rp-playerName');
        const isBot = card.querySelector('.rp-playerInfo img')?.alt?.includes('Bot') || 
                      nameEl?.textContent?.includes('Bot');
        return {
          name: nameEl?.textContent || '',
          isBot
        };
      });
    });
    
    if (expectedUpdate.playerCount !== undefined && players.length === expectedUpdate.playerCount) {
      return true;
    }
    if (expectedUpdate.hasBot !== undefined) {
      const hasBots = players.some(p => p.isBot);
      if (hasBots === expectedUpdate.hasBot) {
        return true;
      }
    }
    
    await delay(100);
  }
  return false;
};

const checkLobbyUpdate = async (lobbyPage, roomId, expectedState) => {
  // Navigate to lobby
  await lobbyPage.goto(`${BASE_URL}/lobby`);
  await lobbyPage.waitForSelector('.room-card', { timeout: 5000 });
  
  // Find our room in the lobby
  const roomCard = await lobbyPage.locator(`.room-card:has-text("${roomId}")`);
  if (await roomCard.count() === 0) {
    console.log('❌ Room not found in lobby');
    return false;
  }
  
  // Check player count
  const playerCount = await roomCard.locator('.player-count').textContent();
  console.log(`📊 Lobby shows: ${playerCount}`);
  
  // Check if it matches expected state
  const expectedCount = `${expectedState.playerCount}/4 Players`;
  const matches = playerCount === expectedCount;
  
  console.log(`${matches ? '✅' : '❌'} Lobby ${matches ? 'correctly' : 'incorrectly'} shows ${playerCount} (expected ${expectedCount})`);
  
  return matches;
};

async function runBotSlotTests() {
  console.log('🚀 Starting Bot Slot Management Tests v2\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  try {
    // Create host context
    const hostContext = await browser.newContext();
    const hostPage = await hostContext.newPage();
    
    // Create guest context for lobby monitoring
    const guestContext = await browser.newContext();
    const lobbyPage = await guestContext.newPage();
    
    // Setup WebSocket monitoring
    await hostContext.addInitScript(() => {
      window.__websockets = [];
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = function(...args) {
        const ws = new OriginalWebSocket(...args);
        window.__websockets.push(ws);
        return ws;
      };
    });
    
    // Step 1: Host creates room
    console.log('\n📝 Step 1: Host creates room');
    await hostPage.goto(BASE_URL);
    await hostPage.fill('input[placeholder="Enter your name..."]', HOST_NAME);
    await hostPage.click('button:has-text("Enter Lobby")');
    await delay(1000);
    await hostPage.click('button:has-text("Create Room")');
    await hostPage.waitForSelector('.rp-roomIdValue', { timeout: 10000 });
    
    const roomId = await hostPage.textContent('.rp-roomIdValue');
    console.log(`✅ Room created: ${roomId}`);
    
    // Setup WebSocket capture
    await captureWebSocketMessages(hostPage, 'HOST');
    
    // Step 2: Add 3 bots to fill slots 2, 3, 4
    console.log('\n📝 Step 2: Adding 3 bots to fill the room');
    
    for (let slot = 2; slot <= 4; slot++) {
      console.log(`\n🤖 Adding bot to slot ${slot}`);
      const addButton = await hostPage.waitForSelector(
        `.rp-position-${slot} .rp-addBotBtn`,
        { timeout: 5000 }
      );
      await addButton.click();
      
      // Wait for bot to appear
      await hostPage.waitForSelector(
        `.rp-position-${slot} .rp-playerCard.rp-filled`,
        { timeout: 5000 }
      );
      
      // Check lobby update
      const lobbyUpdated = await checkLobbyUpdate(lobbyPage, roomId, { playerCount: slot });
      console.log(`${lobbyUpdated ? '✅' : '❌'} Lobby update after adding bot to slot ${slot}`);
      
      await delay(1000);
    }
    
    await takeEvidence(hostPage, 'all_bots_added');
    
    // Step 3: Test Issue 1 - Remove a bot and check lobby update
    console.log('\n\n🧪 TESTING ISSUE 1: Lobby update on bot removal');
    console.log('================================');
    
    // Remove bot from slot 2
    const removeButton2 = await hostPage.waitForSelector(
      '.rp-position-2 .rp-removeBtn',
      { timeout: 5000 }
    );
    
    console.log('🗑️ Removing bot from slot 2...');
    await removeButton2.click();
    
    // Wait for bot to be removed from UI
    await hostPage.waitForSelector(
      '.rp-position-2 .rp-playerCard.rp-empty',
      { timeout: 5000 }
    );
    
    console.log('✅ Bot removed from room UI');
    await takeEvidence(hostPage, 'bot_2_removed');
    
    // Check if lobby updated
    await delay(2000); // Give time for lobby to update
    const issue1LobbyUpdated = await checkLobbyUpdate(lobbyPage, roomId, { playerCount: 3 });
    
    if (!issue1LobbyUpdated) {
      console.log('❌ ISSUE 1 CONFIRMED: Lobby did NOT update after bot removal!');
    } else {
      console.log('✅ ISSUE 1 NOT REPRODUCED: Lobby correctly updated');
    }
    
    // Step 4: Test Issue 2 - Add bot to specific slot
    console.log('\n\n🧪 TESTING ISSUE 2: Add bot to specific slot 3');
    console.log('================================');
    
    // First remove all bots except host
    console.log('🗑️ Removing all remaining bots...');
    for (let slot = 3; slot <= 4; slot++) {
      const removeBtn = await hostPage.$(`.rp-position-${slot} .rp-removeBtn`);
      if (removeBtn) {
        await removeBtn.click();
        await hostPage.waitForSelector(
          `.rp-position-${slot} .rp-playerCard.rp-empty`,
          { timeout: 5000 }
        );
      }
    }
    
    await delay(1000);
    await takeEvidence(hostPage, 'all_bots_removed');
    
    // Clear previous WebSocket messages
    await hostPage.evaluate(() => { window.__wsMessages = []; });
    
    // Now click add bot on slot 3 specifically
    console.log('\n🎯 Clicking "Add Bot" on slot 3...');
    const slot3AddButton = await hostPage.waitForSelector(
      '.rp-position-3 .rp-addBotBtn',
      { timeout: 5000 }
    );
    await slot3AddButton.click();
    
    // Check WebSocket messages
    await delay(1000);
    const wsMessages = await getWebSocketMessages(hostPage);
    const addBotMessage = wsMessages.find(msg => 
      msg.direction === 'SENT' && msg.data.message_type === 'add_bot'
    );
    
    if (addBotMessage) {
      console.log('📨 Add bot WebSocket message:', JSON.stringify(addBotMessage.data, null, 2));
    }
    
    // Wait and check where bot was added
    await delay(2000);
    
    // Check each slot to see where the bot was added
    let botAddedToSlot = null;
    for (let slot = 2; slot <= 4; slot++) {
      const hasBot = await hostPage.$(`.rp-position-${slot} .rp-playerCard.rp-filled`);
      if (hasBot) {
        const botName = await hostPage.textContent(`.rp-position-${slot} .rp-playerName`);
        if (botName.includes('Bot')) {
          botAddedToSlot = slot;
          break;
        }
      }
    }
    
    console.log(`🤖 Bot was added to slot: ${botAddedToSlot}`);
    await takeEvidence(hostPage, 'bot_added_slot_test');
    
    if (botAddedToSlot !== 3) {
      console.log(`❌ ISSUE 2 CONFIRMED: Bot added to slot ${botAddedToSlot} instead of slot 3!`);
    } else {
      console.log('✅ ISSUE 2 NOT REPRODUCED: Bot correctly added to slot 3');
    }
    
    // Step 5: Test Issue 3 - Remove specific bot
    console.log('\n\n🧪 TESTING ISSUE 3: Remove specific bot');
    console.log('================================');
    
    // Add bots to all empty slots
    console.log('🤖 Filling all slots with bots...');
    for (let slot = 2; slot <= 4; slot++) {
      const isEmpty = await hostPage.$(`.rp-position-${slot} .rp-playerCard.rp-empty`);
      if (isEmpty) {
        const addBtn = await hostPage.waitForSelector(
          `.rp-position-${slot} .rp-addBotBtn`,
          { timeout: 5000 }
        );
        await addBtn.click();
        await hostPage.waitForSelector(
          `.rp-position-${slot} .rp-playerCard.rp-filled`,
          { timeout: 5000 }
        );
      }
    }
    
    await delay(1000);
    await takeEvidence(hostPage, 'all_slots_filled_for_remove_test');
    
    // Clear WebSocket messages
    await hostPage.evaluate(() => { window.__wsMessages = []; });
    
    // Get bot info before removal
    const botsBeforeRemoval = {};
    for (let slot = 2; slot <= 4; slot++) {
      const name = await hostPage.textContent(`.rp-position-${slot} .rp-playerName`);
      botsBeforeRemoval[slot] = name;
      console.log(`Slot ${slot}: ${name}`);
    }
    
    // Now remove bot from slot 3
    console.log('\n🎯 Clicking "Remove" on slot 3 (Bot 3)...');
    const slot3RemoveButton = await hostPage.waitForSelector(
      '.rp-position-3 .rp-removeBtn',
      { timeout: 5000 }
    );
    await slot3RemoveButton.click();
    
    // Check WebSocket messages
    await delay(1000);
    const wsMessagesRemove = await getWebSocketMessages(hostPage);
    const removeMessage = wsMessagesRemove.find(msg => 
      msg.direction === 'SENT' && msg.data.message_type === 'remove_player'
    );
    
    if (removeMessage) {
      console.log('📨 Remove player WebSocket message:', JSON.stringify(removeMessage.data, null, 2));
    }
    
    // Wait for removal
    await delay(2000);
    
    // Check which slot is now empty
    let emptySlot = null;
    for (let slot = 2; slot <= 4; slot++) {
      const isEmpty = await hostPage.$(`.rp-position-${slot} .rp-playerCard.rp-empty`);
      if (isEmpty) {
        emptySlot = slot;
        break;
      }
    }
    
    console.log(`🗑️ Slot ${emptySlot} is now empty`);
    await takeEvidence(hostPage, 'bot_removed_slot_test');
    
    if (emptySlot !== 3) {
      console.log(`❌ ISSUE 3 CONFIRMED: Bot removed from slot ${emptySlot} instead of slot 3!`);
    } else {
      console.log('✅ ISSUE 3 NOT REPRODUCED: Bot correctly removed from slot 3');
    }
    
    // Final WebSocket message analysis
    console.log('\n\n📊 WebSocket Message Analysis');
    console.log('================================');
    const allMessages = await getWebSocketMessages(hostPage);
    
    console.log('\nAll add_bot messages:');
    allMessages
      .filter(msg => msg.data.message_type === 'add_bot')
      .forEach(msg => {
        console.log(`- ${msg.direction}: ${JSON.stringify(msg.data.data)}`);
      });
    
    console.log('\nAll remove_player messages:');
    allMessages
      .filter(msg => msg.data.message_type === 'remove_player')
      .forEach(msg => {
        console.log(`- ${msg.direction}: ${JSON.stringify(msg.data.data)}`);
      });
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Run the tests
runBotSlotTests()
  .then(() => {
    console.log('\n✅ Bot slot tests completed');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Bot slot tests failed:', error);
    process.exit(1);
  });