const { chromium } = require('playwright');

// Test configuration
const BASE_URL = 'http://localhost:5050';
const PLAYER1_NAME = 'DebugHost';

// Utility functions
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function testBotSlotDebug() {
  console.log('🔍 Debugging Bot Slot Issue\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 300 
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Monitor WebSocket messages
    const wsMessages = [];
    page.on('websocket', ws => {
      ws.on('framesent', event => {
        try {
          const data = JSON.parse(event.payload);
          wsMessages.push({ type: 'sent', data });
          if (data.event === 'add_bot') {
            console.log('📤 WebSocket SENT:', JSON.stringify(data));
          }
        } catch (e) {}
      });
      
      ws.on('framereceived', event => {
        try {
          const data = JSON.parse(event.payload);
          wsMessages.push({ type: 'received', data });
          if (data.event === 'room_update') {
            console.log('\n📥 Room Update Received:');
            const players = data.data.players || [];
            players.forEach((player, index) => {
              if (player) {
                console.log(`   Array Index ${index}: ${player.name} (seat_position: ${player.seat_position})`);
              }
            });
          }
        } catch (e) {}
      });
    });
    
    // Enter lobby
    console.log('1. Entering lobby...');
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.fill(PLAYER1_NAME);
    
    const enterBtn = await page.locator('button').filter({ hasText: /enter|lobby|play/i }).first();
    await enterBtn.click();
    await delay(1500);
    
    // Create room
    console.log('\n2. Creating room...');
    await page.locator('button').filter({ hasText: /create/i }).first().click();
    await delay(2000);
    
    const roomId = await page.locator('.rp-roomIdValue').textContent();
    console.log(`   Room created: ${roomId}`);
    
    // Log initial state
    console.log('\n3. Initial room state:');
    for (let pos = 1; pos <= 4; pos++) {
      const hasPlayer = await page.locator(`.rp-position-${pos} .rp-playerCard.rp-filled`).count() > 0;
      if (hasPlayer) {
        const name = await page.locator(`.rp-position-${pos} .rp-playerName`).textContent();
        console.log(`   Visual Position ${pos}: ${name}`);
      } else {
        console.log(`   Visual Position ${pos}: [empty]`);
      }
    }
    
    // Remove all bots
    console.log('\n4. Removing all bots...');
    for (let pos = 2; pos <= 4; pos++) {
      const removeBtn = await page.locator(`.rp-position-${pos} .rp-removeBtn`).first();
      if (await removeBtn.count() > 0) {
        await removeBtn.click();
        await delay(1000);
      }
    }
    
    // Log empty state
    console.log('\n5. After removing all bots:');
    for (let pos = 1; pos <= 4; pos++) {
      const hasPlayer = await page.locator(`.rp-position-${pos} .rp-playerCard.rp-filled`).count() > 0;
      if (hasPlayer) {
        const name = await page.locator(`.rp-position-${pos} .rp-playerName`).textContent();
        console.log(`   Visual Position ${pos}: ${name}`);
      } else {
        console.log(`   Visual Position ${pos}: [empty]`);
      }
    }
    
    // Test adding bot to position 3
    console.log('\n6. CRITICAL TEST: Clicking Add Bot on Visual Position 3...');
    console.log('   This should send slot_id=3 to backend');
    console.log('   Backend should convert to seat_position=2');
    console.log('   Bot should appear in visual position 3\n');
    
    const addBotBtn3 = await page.locator('.rp-position-3 .rp-addBotBtn').first();
    await addBotBtn3.click();
    await delay(2000);
    
    // Log result
    console.log('\n7. Result after clicking Add Bot on position 3:');
    for (let pos = 1; pos <= 4; pos++) {
      const hasPlayer = await page.locator(`.rp-position-${pos} .rp-playerCard.rp-filled`).count() > 0;
      if (hasPlayer) {
        const name = await page.locator(`.rp-position-${pos} .rp-playerName`).textContent();
        console.log(`   Visual Position ${pos}: ${name} ${pos === 3 ? '← EXPECTED HERE' : ''}`);
      } else {
        console.log(`   Visual Position ${pos}: [empty]`);
      }
    }
    
    // Check the WebSocket data
    console.log('\n8. Checking WebSocket data...');
    const addBotMessage = wsMessages.find(m => m.type === 'sent' && m.data.event === 'add_bot');
    if (addBotMessage) {
      console.log('   Add bot message found:', JSON.stringify(addBotMessage.data.data));
    }
    
    const lastRoomUpdate = wsMessages.filter(m => 
      m.type === 'received' && m.data.event === 'room_update'
    ).pop();
    
    if (lastRoomUpdate && lastRoomUpdate.data.data.players) {
      console.log('\n   Last room update players array:');
      lastRoomUpdate.data.data.players.forEach((player, index) => {
        if (player) {
          console.log(`   [${index}] = ${player.name} (is_bot: ${player.is_bot})`);
        } else {
          console.log(`   [${index}] = null`);
        }
      });
    }
    
    console.log('\n✅ Debug test completed!');
    console.log('\nPress Enter to close browser...');
    await new Promise(resolve => process.stdin.once('data', resolve));
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

// Run test
testBotSlotDebug().catch(console.error);