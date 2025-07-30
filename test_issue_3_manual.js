const { chromium } = require('playwright');

async function captureRoomState(page, label) {
  console.log(`\n📊 ${label}:`);
  
  try {
    // Wait for room content to be visible
    await page.waitForSelector('.game-room', { timeout: 5000 });
    
    // Get all player slots - they might be in different containers
    const slots = await page.locator('.player-info, .player-slot').all();
    
    console.log(`  Found ${slots.length} player slots`);
    
    for (let i = 0; i < slots.length; i++) {
      const slot = slots[i];
      const text = await slot.textContent();
      console.log(`  Slot ${i}: ${text.replace(/\s+/g, ' ').trim()}`);
    }
  } catch (error) {
    console.log('  Could not capture room state:', error.message);
  }
}

async function performTestSequence() {
  console.log('🧪 Testing Issue 3: Remove Bot Wrong Slot\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 // Slow down to observe
  });
  
  try {
    const page = await browser.newPage();
    
    // Step 1: Player 1 joins lobby
    console.log('=== Step 1: Player 1 >> join lobby ===');
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'Player1');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1000);
    console.log('✅ Player 1 in lobby');
    
    // Step 2: Player 1 creates room
    console.log('\n=== Step 2: Player 1 >> create room ===');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    console.log('✅ Room created');
    
    await captureRoomState(page, 'Initial room state');
    await page.screenshot({ path: 'issue3_2_room_created.png' });
    
    // Step 3: Player 1 removes bot 2
    console.log('\n=== Step 3: Player 1 >> remove bot 2 ===');
    console.log('⏸️ Manually remove Bot 2 in the browser...');
    await page.waitForTimeout(10000); // Wait for manual action
    
    await captureRoomState(page, 'After removing Bot 2');
    await page.screenshot({ path: 'issue3_3_bot2_removed.png' });
    
    // Step 5: Player 1 removes bot 3
    console.log('\n=== Step 5: Player 1 >> remove bot 3 ===');
    console.log('⏸️ Manually remove Bot 3 in the browser...');
    await page.waitForTimeout(10000); // Wait for manual action
    
    await captureRoomState(page, 'After removing Bot 3');
    await page.screenshot({ path: 'issue3_5_bot3_removed.png' });
    
    // Step 6: Player 1 removes bot 4
    console.log('\n=== Step 6: Player 1 >> remove bot 4 ===');
    console.log('⏸️ Manually remove Bot 4 in the browser...');
    await page.waitForTimeout(10000); // Wait for manual action
    
    await captureRoomState(page, 'After removing Bot 4');
    await page.screenshot({ path: 'issue3_6_bot4_removed.png' });
    
    // Step 7: Player 1 adds bot to slot 3
    console.log('\n=== Step 7: Player 1 >> add bot 3 ===');
    console.log('⏸️ Manually add bot to slot 3 in the browser...');
    await page.waitForTimeout(10000); // Wait for manual action
    
    await captureRoomState(page, 'After adding bot to slot 3');
    await page.screenshot({ path: 'issue3_7_bot_added_slot3.png' });
    
    console.log('\n=== Test Complete ===');
    console.log('Screenshots saved. Review them to see if bots were removed from wrong slots.');
    
    // Keep browser open for final inspection
    console.log('\n⏸️ Browser will stay open for 10 more seconds...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

performTestSequence();