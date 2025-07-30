const { chromium } = require('playwright');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 500
};

async function testFrontendRoomDisplay() {
  console.log('🚀 Testing Frontend Room Display...');
  
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    // Create TWO separate contexts
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    
    console.log('\n=== STEP 1: Both players enter lobby ===');
    
    // Helper function to enter lobby
    async function enterLobby(page, playerName) {
      console.log(`🚀 [${playerName}] Entering lobby...`);
      
      await page.goto(TEST_CONFIG.baseUrl);
      await page.waitForLoadState('networkidle');
      
      const nameInput = await page.locator('input[type="text"]').first();
      await nameInput.fill(playerName);
      
      const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
      await startButton.click();
      
      await page.waitForTimeout(2000);
      
      console.log(`✅ [${playerName}] Entered lobby`);
    }
    
    // Both players enter lobby
    await enterLobby(player1Page, 'Player1');
    await enterLobby(player2Page, 'Player2');
    
    console.log('\n=== STEP 2: Check initial room count in UI ===');
    
    // Check UI room count for both players
    const player1InitialCount = await player1Page.locator('.lp-roomCount').textContent();
    const player2InitialCount = await player2Page.locator('.lp-roomCount').textContent();
    
    console.log(`Player 1 UI shows: ${player1InitialCount}`);
    console.log(`Player 2 UI shows: ${player2InitialCount}`);
    
    console.log('\n=== STEP 3: Player 1 creates room ===');
    
    // Player 1 creates room
    const createBtn = await player1Page.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    
    // Wait for room creation
    await player1Page.waitForTimeout(3000);
    
    console.log('\n=== STEP 4: Check room count in UI after creation ===');
    
    // Check UI room count after creation
    const player1PostCreateCount = await player1Page.locator('.lp-roomCount').textContent();
    const player2PostCreateCount = await player2Page.locator('.lp-roomCount').textContent();
    
    console.log(`Player 1 UI now shows: ${player1PostCreateCount}`);
    console.log(`Player 2 UI now shows: ${player2PostCreateCount}`);
    
    console.log('\n=== STEP 5: Check console logs for errors ===');
    
    // Capture console messages
    const player1Console = [];
    const player2Console = [];
    
    player1Page.on('console', msg => {
      if (msg.text().includes('room') || msg.text().includes('🎯') || msg.text().includes('error')) {
        player1Console.push(`[Player1] ${msg.text()}`);
      }
    });
    
    player2Page.on('console', msg => {
      if (msg.text().includes('room') || msg.text().includes('🎯') || msg.text().includes('error')) {
        player2Console.push(`[Player2] ${msg.text()}`);
      }
    });
    
    // Manual refresh to see console logs
    await player2Page.locator('button[title="Refresh room list"]').click();
    await player2Page.waitForTimeout(2000);
    
    console.log('\n=== CONSOLE LOG ANALYSIS ===');
    console.log('Player 1 relevant console logs:');
    player1Console.forEach(log => console.log(log));
    
    console.log('\nPlayer 2 relevant console logs:');
    player2Console.forEach(log => console.log(log));
    
    console.log('\n=== STEP 6: Check actual room cards in DOM ===');
    
    // Count actual room cards in DOM
    const player1RoomCards = await player1Page.locator('.lp-roomCard').count();
    const player2RoomCards = await player2Page.locator('.lp-roomCard').count();
    
    console.log(`Player 1 actual room cards in DOM: ${player1RoomCards}`);
    console.log(`Player 2 actual room cards in DOM: ${player2RoomCards}`);
    
    console.log('\n=== FINAL ANALYSIS ===');
    
    if (player1RoomCards > 0 && player2RoomCards === 0) {
      console.log('❌ ISSUE CONFIRMED: Player 2 UI is not showing rooms');
      console.log('   - Backend sends room_list_update to Player 2 ✅');
      console.log('   - Player 2 frontend is not rendering rooms ❌');
    } else if (player1RoomCards > 0 && player2RoomCards > 0) {
      console.log('✅ SUCCESS: Both players see rooms in UI');
    } else {
      console.log('❓ UNCLEAR: Neither player sees rooms');
    }
    
    // Keep browsers open for manual inspection
    console.log('\n⏱️ Keeping browsers open for 30 seconds for manual inspection...');
    await player1Page.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Run the test
if (require.main === module) {
  testFrontendRoomDisplay().catch(console.error);
}

module.exports = { testFrontendRoomDisplay };