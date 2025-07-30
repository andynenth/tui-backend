const { chromium } = require('playwright');

// Test configuration
const BASE_URL = 'http://localhost:5050';
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function testBotSlotManagement() {
  console.log('🚀 Starting Simple Bot Slot Test\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 // Slower to see what's happening
  });
  
  try {
    // Create browser context
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('ADD_BOT')) {
        console.log('🖥️ Frontend:', msg.text());
      }
    });
    
    // Log all network requests
    page.on('request', request => {
      if (request.url().includes('ws://')) {
        console.log('📡 WebSocket URL:', request.url());
      }
    });
    
    // Step 1: Navigate and create room
    console.log('📝 Step 1: Creating room...');
    await page.goto(BASE_URL);
    
    // Set player name
    await page.fill('input[placeholder="Enter your name"]', 'TestHost');
    await page.click('button:has-text("Set Name")');
    await delay(500);
    
    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForSelector('.rp-roomIdValue', { timeout: 10000 });
    
    const roomId = await page.textContent('.rp-roomIdValue');
    console.log(`✅ Room created: ${roomId}\n`);
    
    // Step 2: Test adding bot to specific slot
    console.log('🧪 TEST: Add bot to slot 3');
    console.log('Expected: Bot should appear in slot 3');
    console.log('Clicking Add Bot button on slot 3...\n');
    
    // Intercept WebSocket messages
    await page.evaluate(() => {
      const originalSend = WebSocket.prototype.send;
      WebSocket.prototype.send = function(data) {
        const parsed = JSON.parse(data);
        if (parsed.message_type === 'add_bot') {
          console.log('🔵 WebSocket SEND add_bot:', JSON.stringify(parsed.data));
        }
        return originalSend.call(this, data);
      };
    });
    
    // Click add bot on slot 3
    const slot3AddBtn = await page.waitForSelector('.rp-position-3 .rp-addBotBtn');
    await slot3AddBtn.click();
    
    // Wait for bot to appear
    await delay(2000);
    
    // Check where bot was added
    let botLocation = null;
    for (let slot = 2; slot <= 4; slot++) {
      const hasPlayer = await page.$eval(`.rp-position-${slot}`, el => {
        const playerCard = el.querySelector('.rp-playerCard');
        return playerCard && playerCard.classList.contains('rp-filled');
      }).catch(() => false);
      
      if (hasPlayer) {
        const playerName = await page.textContent(`.rp-position-${slot} .rp-playerName`);
        if (playerName.includes('Bot')) {
          botLocation = slot;
          break;
        }
      }
    }
    
    if (botLocation === 3) {
      console.log(`✅ SUCCESS: Bot was correctly added to slot 3\n`);
    } else if (botLocation) {
      console.log(`❌ FAIL: Bot was added to slot ${botLocation} instead of slot 3\n`);
    } else {
      console.log(`❌ FAIL: No bot was added\n`);
    }
    
    // Take screenshot
    await page.screenshot({ path: 'bot_slot_3_test.png', fullPage: true });
    
    // Step 3: Test removing specific bot
    console.log('🧪 TEST: Remove bot from slot 3');
    
    if (botLocation) {
      // Add more bots first
      for (let slot = 2; slot <= 4; slot++) {
        if (slot !== botLocation) {
          const addBtn = await page.$(`.rp-position-${slot} .rp-addBotBtn`);
          if (addBtn) {
            await addBtn.click();
            await delay(1000);
          }
        }
      }
      
      // Now remove bot from original location
      const removeBtn = await page.$(`.rp-position-${botLocation} .rp-removeBtn`);
      if (removeBtn) {
        console.log(`Clicking Remove on slot ${botLocation}...`);
        await removeBtn.click();
        await delay(2000);
        
        // Check if correct bot was removed
        const isEmpty = await page.$eval(`.rp-position-${botLocation}`, el => {
          const playerCard = el.querySelector('.rp-playerCard');
          return playerCard && playerCard.classList.contains('rp-empty');
        }).catch(() => false);
        
        if (isEmpty) {
          console.log(`✅ Bot was removed from slot ${botLocation}\n`);
        } else {
          console.log(`❌ Bot was NOT removed from slot ${botLocation}\n`);
        }
      }
    }
    
    // Step 4: Test lobby update
    console.log('🧪 TEST: Lobby update on bot removal');
    
    // Open lobby in new tab
    const lobbyPage = await context.newPage();
    await lobbyPage.goto(`${BASE_URL}/lobby`);
    await lobbyPage.waitForSelector('.room-card', { timeout: 5000 });
    
    // Find room and check player count
    const roomCard = await lobbyPage.$(`text=${roomId}`);
    if (roomCard) {
      const playerCount = await lobbyPage.textContent('.player-count');
      console.log(`Lobby shows: ${playerCount}`);
      
      // Remove a bot and check if lobby updates
      await page.bringToFront();
      const removeBtn = await page.$('.rp-removeBtn');
      if (removeBtn) {
        await removeBtn.click();
        await delay(3000); // Wait for potential update
        
        await lobbyPage.bringToFront();
        await lobbyPage.reload();
        const newPlayerCount = await lobbyPage.textContent('.player-count');
        console.log(`After removal, lobby shows: ${newPlayerCount}`);
        
        if (playerCount !== newPlayerCount) {
          console.log('✅ Lobby updated after bot removal');
        } else {
          console.log('❌ Lobby did NOT update after bot removal');
        }
      }
    }
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    console.log('\nPress Enter to close browser...');
    await new Promise(resolve => process.stdin.once('data', resolve));
    await browser.close();
  }
}

// Run test
testBotSlotManagement();