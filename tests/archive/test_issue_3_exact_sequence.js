const { chromium } = require('playwright');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function logRoomState(page, label) {
  console.log(`\n📊 ${label}:`);
  
  try {
    // Get all player cards
    const playerCards = await page.locator('.rp-playerCard').all();
    
    for (let i = 0; i < playerCards.length; i++) {
      const card = playerCards[i];
      const isEmpty = await card.locator('.rp-playerAction button:has-text("Add Bot")').count() > 0;
      
      if (isEmpty) {
        console.log(`  Slot ${i + 1}: [EMPTY]`);
      } else {
        const nameElement = await card.locator('.rp-playerName').first();
        const name = await nameElement.textContent();
        const isHost = await card.locator('.rp-hostBadge').count() > 0;
        const hasRemoveBtn = await card.locator('button:has-text("Remove")').count() > 0;
        
        console.log(`  Slot ${i + 1}: ${name.trim()} ${isHost ? '👑' : ''} ${hasRemoveBtn ? '(removable)' : ''}`);
      }
    }
  } catch (error) {
    console.log('  Error capturing room state:', error.message);
  }
}

async function testExactSequence() {
  console.log('🧪 Testing Issue 3: Remove Bot Wrong Slot - EXACT SEQUENCE\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 // Slow actions to observe
  });
  
  try {
    // Create two browser contexts for two players
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Enable detailed logging
    page1.on('console', msg => {
      if (msg.text().includes('REMOVE_PLAYER') || msg.text().includes('ADD_BOT')) {
        console.log(`[P1 Console]: ${msg.text()}`);
      }
    });
    
    // Step 1: Player 1 joins lobby
    console.log('=== Step 1: Player 1 >> join lobby ===');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await sleep(1500);
    console.log('✅ Player 1 in lobby');
    
    // Step 2: Player 1 creates room
    console.log('\n=== Step 2: Player 1 >> create room ===');
    await page1.click('button:has-text("Create Room")');
    await sleep(2000);
    
    await logRoomState(page1, 'Initial room state');
    
    // Step 3: Player 1 removes bot 2
    console.log('\n=== Step 3: Player 1 >> remove bot 2 ===');
    // Find the second player card (Bot 2 should be in slot 2, index 1)
    const playerCards3 = await page1.locator('.rp-playerCard').all();
    if (playerCards3.length > 1) {
      const bot2Card = playerCards3[1]; // Second slot (index 1)
      const removeBtn = bot2Card.locator('button:has-text("Remove")');
      if (await removeBtn.isVisible()) {
        await removeBtn.click();
        console.log('✅ Clicked Remove on slot 2 (Bot 2)');
      }
    }
    await sleep(1500);
    await logRoomState(page1, 'After removing Bot 2');
    
    // Step 4: Player 2 joins lobby
    console.log('\n=== Step 4: Player 2 >> join lobby ===');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await sleep(1500);
    console.log('✅ Player 2 in lobby');
    
    // Step 5: Player 1 removes bot 3
    console.log('\n=== Step 5: Player 1 >> remove bot 3 ===');
    const playerCards5 = await page1.locator('.rp-playerCard').all();
    // After removing Bot 2, Bot 3 might still be in slot 3 (index 2) or might have shifted
    for (let i = 0; i < playerCards5.length; i++) {
      const card = playerCards5[i];
      const name = await card.locator('.rp-playerName').textContent();
      if (name.includes('Bot 3')) {
        const removeBtn = card.locator('button:has-text("Remove")');
        if (await removeBtn.isVisible()) {
          await removeBtn.click();
          console.log(`✅ Clicked Remove on Bot 3 (found in slot ${i + 1})`);
          break;
        }
      }
    }
    await sleep(1500);
    await logRoomState(page1, 'After removing Bot 3');
    
    // Step 6: Player 1 removes bot 4
    console.log('\n=== Step 6: Player 1 >> remove bot 4 ===');
    const playerCards6 = await page1.locator('.rp-playerCard').all();
    for (let i = 0; i < playerCards6.length; i++) {
      const card = playerCards6[i];
      const name = await card.locator('.rp-playerName').textContent();
      if (name.includes('Bot 4')) {
        const removeBtn = card.locator('button:has-text("Remove")');
        if (await removeBtn.isVisible()) {
          await removeBtn.click();
          console.log(`✅ Clicked Remove on Bot 4 (found in slot ${i + 1})`);
          break;
        }
      }
    }
    await sleep(1500);
    await logRoomState(page1, 'After removing Bot 4');
    
    // Step 7: Player 1 adds bot to slot 3
    console.log('\n=== Step 7: Player 1 >> add bot 3 ===');
    const playerCards7 = await page1.locator('.rp-playerCard').all();
    if (playerCards7.length > 2) {
      const slot3 = playerCards7[2]; // Third slot (index 2)
      const addBotBtn = slot3.locator('button:has-text("Add Bot")');
      if (await addBotBtn.isVisible()) {
        await addBotBtn.click();
        console.log('✅ Clicked Add Bot on slot 3');
      }
    }
    await sleep(1500);
    await logRoomState(page1, 'After adding bot to slot 3');
    
    // Step 8: Player 2 joins room
    console.log('\n=== Step 8: Player 2 >> join room ===');
    // Get the room list in Player 2's lobby
    const roomCards = await page2.locator('.room-card').all();
    if (roomCards.length > 0) {
      await roomCards[0].click();
      console.log('✅ Player 2 clicked on room');
    }
    await sleep(2000);
    await logRoomState(page1, 'After Player 2 joined (from P1 view)');
    
    // Step 9: Player 1 removes Player 2
    console.log('\n=== Step 9: Player 1 >> remove Player 2 ===');
    const playerCards9 = await page1.locator('.rp-playerCard').all();
    for (let i = 0; i < playerCards9.length; i++) {
      const card = playerCards9[i];
      const name = await card.locator('.rp-playerName').textContent();
      if (name.includes('Player2')) {
        const removeBtn = card.locator('button:has-text("Remove")');
        if (await removeBtn.isVisible()) {
          await removeBtn.click();
          console.log(`✅ Clicked Remove on Player2 (found in slot ${i + 1})`);
          break;
        }
      }
    }
    await sleep(1500);
    await logRoomState(page1, 'After removing Player 2');
    
    // Continue with remaining steps...
    console.log('\n=== Test sequence partially complete ===');
    console.log('Review the logs above to see if bots were removed from the correct slots.');
    
    // Keep browser open for manual inspection
    console.log('\n⏸️ Browser will stay open for 30 seconds for inspection...');
    await sleep(30000);
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

// Run the test
testExactSequence().then(() => {
  console.log('\n✅ Test execution complete');
  process.exit(0);
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});