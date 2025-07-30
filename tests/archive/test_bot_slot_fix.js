const { chromium } = require('playwright');

const TEST_CONFIG = {
  frontendUrl: 'http://localhost:5050',
  wsUrl: 'ws://localhost:5050',
  testTimeout: 30000,
  testUser: 'TestPlayer',
  headless: process.env.HEADED !== 'true'
};

async function testBotSlotFix() {
  console.log('🧪 Testing Bot Slot Fix...\n');
  const browser = await chromium.launch({ headless: TEST_CONFIG.headless });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Navigate to the app
    await page.goto(TEST_CONFIG.frontendUrl);
    console.log('📱 Navigated to frontend');
    
    // Enter player name and join lobby
    await page.fill('input[placeholder="Enter your name"]', TEST_CONFIG.testUser);
    await page.click('button:has-text("Enter Lobby")');
    console.log('✅ Entered lobby');
    
    // Wait for lobby to load
    await page.waitForTimeout(1000);
    
    // Create a room
    await page.click('button:has-text("Create Room")');
    console.log('🏠 Created room');
    
    // Wait for room to load
    await page.waitForTimeout(2000);
    
    // Now we should be in the room with 3 bots
    // Let's check the initial state
    console.log('\n📊 Initial Room State:');
    const slots = await page.locator('.player-slot').all();
    
    for (let i = 0; i < slots.length; i++) {
      const slotElement = slots[i];
      const playerName = await slotElement.locator('.player-name').textContent();
      const isBot = await slotElement.locator('.bot-indicator').count() > 0;
      console.log(`  Slot ${i}: ${playerName?.trim() || 'Empty'} ${isBot ? '(Bot)' : ''}`);
    }
    
    // Remove Bot 3 (in slot 2, zero-indexed)
    console.log('\n🗑️ Removing Bot 3 from slot 2...');
    const bot3Slot = slots[2];
    const removeButton = bot3Slot.locator('button[aria-label="Remove player"]');
    
    if (await removeButton.isVisible()) {
      await removeButton.click();
      await page.waitForTimeout(1000);
      console.log('✅ Bot 3 removed');
    } else {
      console.log('❌ Could not find remove button for Bot 3');
      return false;
    }
    
    // Check state after removal
    console.log('\n📊 After Bot Removal:');
    const slotsAfterRemoval = await page.locator('.player-slot').all();
    
    for (let i = 0; i < slotsAfterRemoval.length; i++) {
      const slotElement = slotsAfterRemoval[i];
      const playerName = await slotElement.locator('.player-name').textContent();
      const isBot = await slotElement.locator('.bot-indicator').count() > 0;
      const isEmpty = await slotElement.locator('.empty-slot').count() > 0;
      
      if (isEmpty) {
        console.log(`  Slot ${i}: Empty`);
      } else {
        console.log(`  Slot ${i}: ${playerName?.trim() || 'Unknown'} ${isBot ? '(Bot)' : ''}`);
      }
    }
    
    // Now click "Add Bot" on the empty slot (slot 2)
    console.log('\n🤖 Adding bot to slot 2...');
    const emptySlot = slotsAfterRemoval[2];
    const addBotButton = emptySlot.locator('button:has-text("Add Bot")');
    
    if (await addBotButton.isVisible()) {
      // Log the button's data attributes if any
      const slotId = await emptySlot.getAttribute('data-slot-id');
      console.log(`  Clicking Add Bot button for slot with data-slot-id: ${slotId}`);
      
      await addBotButton.click();
      await page.waitForTimeout(1000);
      console.log('✅ Add Bot clicked');
    } else {
      console.log('❌ Could not find Add Bot button');
      return false;
    }
    
    // Final check - where did the bot end up?
    console.log('\n📊 Final Room State:');
    const finalSlots = await page.locator('.player-slot').all();
    let botAddedToCorrectSlot = false;
    
    for (let i = 0; i < finalSlots.length; i++) {
      const slotElement = finalSlots[i];
      const playerName = await slotElement.locator('.player-name').textContent();
      const isBot = await slotElement.locator('.bot-indicator').count() > 0;
      const isEmpty = await slotElement.locator('.empty-slot').count() > 0;
      
      if (isEmpty) {
        console.log(`  Slot ${i}: Empty`);
      } else {
        console.log(`  Slot ${i}: ${playerName?.trim() || 'Unknown'} ${isBot ? '(Bot)' : ''}`);
        
        // Check if slot 2 now has a bot
        if (i === 2 && isBot && playerName?.includes('Bot')) {
          botAddedToCorrectSlot = true;
        }
      }
    }
    
    // Test results
    console.log('\n📋 Test Results:');
    if (botAddedToCorrectSlot) {
      console.log('✅ SUCCESS: Bot was added to the correct slot (slot 2)');
      return true;
    } else {
      console.log('❌ FAILURE: Bot was NOT added to the correct slot');
      return false;
    }
    
  } catch (error) {
    console.error('❌ Test error:', error);
    return false;
  } finally {
    await browser.close();
  }
}

// Run the test
testBotSlotFix().then(success => {
  if (success) {
    console.log('\n🎉 Bot slot fix test PASSED!');
    process.exit(0);
  } else {
    console.log('\n💥 Bot slot fix test FAILED!');
    process.exit(1);
  }
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});