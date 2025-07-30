/**
 * 🤖 SWARM-COORDINATED ROOM CREATION TEST
 * 
 * Tests room creation functionality using Claude Flow swarm intelligence.
 * This test verifies if clicking "Create Room" works properly in current lobby.
 */

const { chromium } = require('playwright');

async function testRoomCreationSwarm() {
  console.log('🐝 SWARM TEST: Room Creation Functionality');
  console.log('=' .repeat(60));
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500  // Slow down to observe behavior
  });
  
  const page = await browser.newPage();
  
  // Enable console logging from the page
  page.on('console', msg => {
    console.log(`📱 [BROWSER] ${msg.text()}`);
  });
  
  try {
    console.log('🔗 Step 1: Navigate to application');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('👤 Step 2: Enter player name');
    await page.fill('input[placeholder*="name" i]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    
    console.log('⏳ Step 3: Wait for lobby to load');
    await page.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    console.log('✅ Lobby loaded successfully');
    
    console.log('🏠 Step 4: Test room creation');
    
    // Check initial state
    const initialRoomCount = await page.locator('.lp-roomCard').count();
    console.log(`📊 Initial room count: ${initialRoomCount}`);
    
    // Click Create Room button
    console.log('🖱️  Clicking Create Room button...');
    const createButton = page.locator('button:has-text("Create Room")');
    await createButton.click();
    
    console.log('⏳ Waiting for room creation...');
    
    // Wait for either:
    // 1. Navigation to room page (success)
    // 2. Loading spinner to disappear (potential failure)
    // 3. Error message (failure)
    
    const result = await Promise.race([
      // Success: Navigation to room page
      page.waitForURL(/\/room\/\w+/, { timeout: 15000 }).then(() => 'SUCCESS_NAVIGATION'),
      
      // Check if still stuck on loading
      page.waitForSelector('.lp-loadingOverlay:not(.show)', { timeout: 15000 }).then(() => 'LOADING_CLEARED'),
      
      // Check for error
      page.waitForSelector('[role="alert"], .error', { timeout: 15000 }).then(() => 'ERROR_DETECTED')
    ]).catch(() => 'TIMEOUT');
    
    console.log(`🎯 Room creation result: ${result}`);
    
    if (result === 'SUCCESS_NAVIGATION') {
      const currentUrl = page.url();
      console.log('✅ SUCCESS: Room creation worked!');
      console.log(`🏠 Navigated to: ${currentUrl}`);
      
      // Verify we're in a room
      await page.waitForSelector('.room-page, [data-testid="room"], .rp-gameContainer', { timeout: 5000 });
      console.log('✅ Room page loaded successfully');
      
      return {
        success: true,
        message: 'Room creation works perfectly',
        url: currentUrl
      };
      
    } else if (result === 'LOADING_CLEARED') {
      console.log('⚠️  Loading cleared but no navigation - checking current state...');
      
      const currentUrl = page.url();
      const isStillInLobby = currentUrl.includes('/lobby') || !currentUrl.includes('/room/');
      
      if (isStillInLobby) {
        console.log('❌ FAILED: Still in lobby, room creation did not work');
        
        // Check for any error indicators
        const buttonText = await createButton.textContent();
        console.log(`🔍 Create button text: "${buttonText}"`);
        
        return {
          success: false,
          message: 'Room creation failed - remained in lobby',
          url: currentUrl,
          buttonState: buttonText
        };
      } else {
        console.log('✅ Actually navigated successfully');
        return {
          success: true,
          message: 'Room creation worked (delayed navigation)',
          url: currentUrl
        };
      }
      
    } else if (result === 'ERROR_DETECTED') {
      console.log('❌ FAILED: Error detected during room creation');
      return {
        success: false,
        message: 'Room creation failed with error',
        url: page.url()
      };
      
    } else {
      console.log('⏰ TIMEOUT: Room creation took too long');
      const currentUrl = page.url();
      const buttonText = await createButton.textContent();
      
      return {
        success: false,
        message: 'Room creation timed out',
        url: currentUrl,
        buttonState: buttonText
      };
    }
    
  } catch (error) {
    console.error('💥 Test error:', error.message);
    return {
      success: false,
      message: `Test failed with error: ${error.message}`,
      error: error.stack
    };
    
  } finally {
    console.log('🧹 Cleaning up browser...');
    await browser.close();
  }
}

// Run the test
if (require.main === module) {
  testRoomCreationSwarm()
    .then(result => {
      console.log('\n🎯 SWARM TEST RESULTS:');
      console.log('=' .repeat(60));
      console.log(`Status: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
      console.log(`Message: ${result.message}`);
      if (result.url) console.log(`URL: ${result.url}`);
      if (result.buttonState) console.log(`Button State: ${result.buttonState}`);
      if (result.error) console.log(`Error: ${result.error}`);
      
      // Exit with appropriate code for swarm coordination
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Swarm test crashed:', error);
      process.exit(1);
    });
}

module.exports = { testRoomCreationSwarm };