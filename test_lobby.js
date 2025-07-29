const { chromium } = require('playwright');

async function testLobby() {
  console.log('🚀 Starting lobby test...');
  
  // Launch browser
  const browser = await chromium.launch({ 
    headless: false,  // Show browser window
    slowMo: 1000     // Slow down actions for visibility
  });
  
  try {
    // Create new page
    const page = await browser.newPage();
    
    // Set viewport size
    await page.setViewportSize({ width: 1280, height: 720 });
    
    console.log('🌐 Navigating to http://localhost:5050/...');
    
    // Navigate to the application
    await page.goto('http://localhost:5050/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    console.log('📝 Page loaded. Looking for player name input...');
    
    // Look for player name input (assuming there's a start page)
    const playerNameInput = await page.locator('input[type="text"]').first();
    
    if (await playerNameInput.isVisible()) {
      console.log('✏️ Entering player name...');
      await playerNameInput.fill('TestPlayer');
      
      // Look for a button to proceed (Play, Start, Enter Lobby, etc.)
      const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
      
      if (await startButton.isVisible()) {
        console.log('🎮 Clicking start button...');
        await startButton.click();
      }
    }
    
    // Wait for lobby to load
    await page.waitForTimeout(2000);
    
    console.log('🏢 Looking for lobby elements...');
    
    // Check if we're in the lobby
    const lobbyTitle = await page.locator('h1, h2').filter({ hasText: /lobby/i }).first();
    
    if (await lobbyTitle.isVisible()) {
      console.log('✅ Successfully reached the lobby!');
      console.log('📋 Lobby title:', await lobbyTitle.textContent());
      
      // Look for room list
      const roomList = await page.locator('.lp-roomList, [class*="room"], [class*="Room"]').first();
      if (await roomList.isVisible()) {
        console.log('📋 Room list found');
      }
      
      // Look for create room button
      const createRoomBtn = await page.locator('button').filter({ hasText: /create/i }).first();
      if (await createRoomBtn.isVisible()) {
        console.log('➕ Create room button found');
      }
      
    } else {
      console.log('❌ Could not find lobby. Current page title:', await page.title());
      console.log('🔍 Available text on page:');
      const bodyText = await page.locator('body').textContent();
      console.log(bodyText.substring(0, 500) + '...');
    }
    
    // Keep browser open for 10 seconds to observe
    console.log('⏱️ Keeping browser open for 10 seconds...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Error during test:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Run the test
testLobby().catch(console.error);