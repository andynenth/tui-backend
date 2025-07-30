const { chromium } = require('playwright');

const TEST_CONFIG = {
  frontendUrl: 'http://localhost:5050',
  wsUrl: 'ws://localhost:5050',
  testTimeout: 60000,
  player1Name: 'Player1',
  player2Name: 'Player2',
  headless: process.env.HEADED !== 'true'
};

async function captureRoomState(page, label) {
  console.log(`\n📊 ${label}:`);
  
  // Get all player slots
  const slots = await page.locator('.player-slot').all();
  
  for (let i = 0; i < slots.length; i++) {
    const slotElement = slots[i];
    
    // Check if slot is empty
    const isEmpty = await slotElement.locator('.empty-slot').count() > 0;
    
    if (isEmpty) {
      console.log(`  Slot ${i}: [EMPTY]`);
    } else {
      // Get player info
      const playerName = await slotElement.locator('.player-name').textContent();
      const isBot = await slotElement.locator('.bot-indicator').count() > 0;
      const isHost = await slotElement.locator('.host-indicator').count() > 0;
      
      console.log(`  Slot ${i}: ${playerName?.trim() || 'Unknown'} ${isBot ? '🤖' : '👤'} ${isHost ? '👑' : ''}`);
    }
  }
}

async function removePlayerByName(page, playerName, expectedSlot) {
  console.log(`\n🗑️ Attempting to remove "${playerName}" (expected in slot ${expectedSlot})...`);
  
  const slots = await page.locator('.player-slot').all();
  let removed = false;
  
  for (let i = 0; i < slots.length; i++) {
    const slotElement = slots[i];
    const nameElement = await slotElement.locator('.player-name').textContent();
    
    if (nameElement?.trim() === playerName) {
      console.log(`  Found "${playerName}" in slot ${i}`);
      
      if (i !== expectedSlot) {
        console.log(`  ⚠️ WARNING: Player is in slot ${i}, but expected in slot ${expectedSlot}`);
      }
      
      // Click remove button
      const removeButton = slotElement.locator('button[aria-label="Remove player"]');
      if (await removeButton.isVisible()) {
        await removeButton.click();
        console.log(`  ✅ Clicked remove button for "${playerName}" in slot ${i}`);
        removed = true;
        break;
      }
    }
  }
  
  if (!removed) {
    console.log(`  ❌ Could not find or remove "${playerName}"`);
  }
  
  // Wait for update
  await page.waitForTimeout(1000);
}

async function addBotToSlot(page, slotIndex) {
  console.log(`\n🤖 Adding bot to slot ${slotIndex}...`);
  
  const slots = await page.locator('.player-slot').all();
  
  if (slotIndex < slots.length) {
    const slotElement = slots[slotIndex];
    const isEmpty = await slotElement.locator('.empty-slot').count() > 0;
    
    if (isEmpty) {
      const addBotButton = slotElement.locator('button:has-text("Add Bot")');
      if (await addBotButton.isVisible()) {
        await addBotButton.click();
        console.log(`  ✅ Clicked "Add Bot" button in slot ${slotIndex}`);
      } else {
        console.log(`  ❌ No "Add Bot" button found in slot ${slotIndex}`);
      }
    } else {
      const playerName = await slotElement.locator('.player-name').textContent();
      console.log(`  ❌ Slot ${slotIndex} is not empty (contains: ${playerName?.trim()})`);
    }
  }
  
  // Wait for update
  await page.waitForTimeout(1000);
}

async function testRemoveBotIssue() {
  console.log('🧪 Testing Issue 3: Remove Bot Wrong Slot Targeting\n');
  console.log('Test sequence:');
  console.log('1. Player 1 >> join lobby');
  console.log('2. Player 1 >> create room');
  console.log('3. Player 1 >> remove bot 2');
  console.log('4. Player 2 >> join lobby');
  console.log('5. Player 1 >> remove bot 3');
  console.log('6. Player 1 >> remove bot 4');
  console.log('7. Player 1 >> add bot 3');
  console.log('8. Player 2 >> join room');
  console.log('9. Player 1 >> remove Player 2');
  console.log('10. Player 1 >> remove bot 3');
  console.log('11. Player 1 >> add bot 4');
  console.log('12. Player 1 >> add bot 3');
  console.log('13. Player 1 >> add bot 2');
  
  const browser = await chromium.launch({ headless: TEST_CONFIG.headless });
  
  try {
    // Create contexts for both players
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Enable console logging for debugging
    page1.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`[P1 Console Error]: ${msg.text()}`);
      }
    });
    
    page2.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`[P2 Console Error]: ${msg.text()}`);
      }
    });
    
    // Step 1: Player 1 joins lobby
    console.log('\n=== Step 1: Player 1 >> join lobby ===');
    await page1.goto(TEST_CONFIG.frontendUrl);
    
    // Try multiple selectors for the name input
    const nameInput = await page1.locator('input[type="text"]').first();
    if (await nameInput.isVisible()) {
      await nameInput.fill(TEST_CONFIG.player1Name);
    } else {
      console.error('❌ Could not find name input field');
      return;
    }
    
    // Try to find the enter button
    const enterButton = page1.locator('button').filter({ hasText: /enter|join|lobby/i }).first();
    if (await enterButton.isVisible()) {
      await enterButton.click();
    } else {
      console.error('❌ Could not find enter lobby button');
      return;
    }
    
    await page1.waitForTimeout(1000);
    console.log('✅ Player 1 in lobby');
    
    // Step 2: Player 1 creates room
    console.log('\n=== Step 2: Player 1 >> create room ===');
    await page1.click('button:has-text("Create Room")');
    await page1.waitForTimeout(2000);
    console.log('✅ Room created');
    
    await captureRoomState(page1, 'Initial room state');
    
    // Step 3: Player 1 removes bot 2
    console.log('\n=== Step 3: Player 1 >> remove bot 2 ===');
    await removePlayerByName(page1, 'Bot 2', 1);
    await captureRoomState(page1, 'After removing Bot 2');
    
    // Step 4: Player 2 joins lobby
    console.log('\n=== Step 4: Player 2 >> join lobby ===');
    await page2.goto(TEST_CONFIG.frontendUrl);
    
    // Try multiple selectors for the name input
    const nameInput2 = await page2.locator('input[type="text"]').first();
    if (await nameInput2.isVisible()) {
      await nameInput2.fill(TEST_CONFIG.player2Name);
    } else {
      console.error('❌ Could not find name input field for Player 2');
      return;
    }
    
    // Try to find the enter button
    const enterButton2 = page2.locator('button').filter({ hasText: /enter|join|lobby/i }).first();
    if (await enterButton2.isVisible()) {
      await enterButton2.click();
    } else {
      console.error('❌ Could not find enter lobby button for Player 2');
      return;
    }
    
    await page2.waitForTimeout(1000);
    console.log('✅ Player 2 in lobby');
    
    // Step 5: Player 1 removes bot 3
    console.log('\n=== Step 5: Player 1 >> remove bot 3 ===');
    await removePlayerByName(page1, 'Bot 3', 2);
    await captureRoomState(page1, 'After removing Bot 3');
    
    // Step 6: Player 1 removes bot 4
    console.log('\n=== Step 6: Player 1 >> remove bot 4 ===');
    await removePlayerByName(page1, 'Bot 4', 3);
    await captureRoomState(page1, 'After removing Bot 4');
    
    // Step 7: Player 1 adds bot to slot 3
    console.log('\n=== Step 7: Player 1 >> add bot 3 ===');
    await addBotToSlot(page1, 2); // Slot 3 is index 2
    await captureRoomState(page1, 'After adding bot to slot 3');
    
    // Step 8: Player 2 joins room
    console.log('\n=== Step 8: Player 2 >> join room ===');
    // First, Player 2 needs to see the room in lobby
    await page2.waitForTimeout(1000);
    
    // Click on the room to join
    const roomCard = page2.locator('.room-card').first();
    if (await roomCard.isVisible()) {
      await roomCard.click();
      await page2.waitForTimeout(2000);
      console.log('✅ Player 2 joined room');
    } else {
      console.log('❌ No room visible for Player 2');
    }
    
    await captureRoomState(page1, 'After Player 2 joined');
    
    // Step 9: Player 1 removes Player 2
    console.log('\n=== Step 9: Player 1 >> remove Player 2 ===');
    await removePlayerByName(page1, TEST_CONFIG.player2Name, -1); // Unknown slot
    await captureRoomState(page1, 'After removing Player 2');
    
    // Step 10: Player 1 removes bot 3
    console.log('\n=== Step 10: Player 1 >> remove bot 3 ===');
    await removePlayerByName(page1, 'Bot 3', 2);
    await captureRoomState(page1, 'After removing Bot 3 again');
    
    // Step 11: Player 1 adds bot to slot 4
    console.log('\n=== Step 11: Player 1 >> add bot 4 ===');
    await addBotToSlot(page1, 3); // Slot 4 is index 3
    await captureRoomState(page1, 'After adding bot to slot 4');
    
    // Step 12: Player 1 adds bot to slot 3
    console.log('\n=== Step 12: Player 1 >> add bot 3 ===');
    await addBotToSlot(page1, 2); // Slot 3 is index 2
    await captureRoomState(page1, 'After adding bot to slot 3');
    
    // Step 13: Player 1 adds bot to slot 2
    console.log('\n=== Step 13: Player 1 >> add bot 2 ===');
    await addBotToSlot(page1, 1); // Slot 2 is index 1
    await captureRoomState(page1, 'Final room state');
    
    console.log('\n=== Test Complete ===');
    console.log('Review the output above to identify where bots are being removed from the wrong slots.');
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

// Run the test
testRemoveBotIssue().then(() => {
  console.log('\n✅ Test execution complete');
  process.exit(0);
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});