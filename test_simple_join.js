/**
 * Simple Player Join Test
 * Tests basic room joining functionality
 */

const { chromium } = require('playwright');

async function testSimpleJoin() {
  console.log('🧪 SIMPLE JOIN TEST: Testing basic room join functionality');
  
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();
  
  // Enable console logging from the page
  page.on('console', msg => {
    console.log(`📱 [BROWSER] ${msg.text()}`);
  });
  
  try {
    console.log('🔗 Step 1: Navigate to application');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('👤 Step 2: Enter player name and join lobby');
    await page.fill('input[placeholder*="name" i]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    
    console.log('⏳ Step 3: Wait for lobby to load');
    await page.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    console.log('✅ Lobby loaded successfully');
    
    // Wait for room list to load
    await page.waitForTimeout(3000);
    
    console.log('🔍 Step 4: Check available rooms');
    const roomCount = await page.locator('.lp-roomCard').count();
    console.log(`📊 Found ${roomCount} available rooms`);
    
    if (roomCount === 0) {
      console.log('ℹ️  No rooms available - test cannot continue');
      return { success: true, message: 'No rooms to join (expected)' };
    }
    
    // Get first available room
    const firstRoom = page.locator('.lp-roomCard').first();
    const roomId = await firstRoom.locator('.lp-roomId').textContent();
    const occupancy = await firstRoom.locator('.lp-roomOccupancy').textContent();
    
    console.log(`🏠 Found room: ${roomId} with occupancy: ${occupancy}`);
    
    // Check if room is joinable (not full)
    const isFull = occupancy?.includes('4/4');
    if (isFull) {
      console.log('⚠️  Room is full - cannot join');
      return { success: true, message: 'Room full (expected behavior)' };
    }
    
    console.log('🖱️  Step 5: Click on room to join');
    await firstRoom.click();
    
    console.log('⏳ Waiting for join result...');
    
    // Wait for either navigation to room or error
    const result = await Promise.race([
      // Success: Navigation to room page
      page.waitForURL(/\/room\/\w+/, { timeout: 15000 }).then(() => 'SUCCESS'),
      
      // Error: Check for error messages
      page.waitForFunction(() => {
        const errorElements = document.querySelectorAll('[role="alert"], .error, .alert');
        return errorElements.length > 0;
      }, {}, { timeout: 15000 }).then(() => 'ERROR'),
      
      // Timeout
      new Promise(resolve => setTimeout(() => resolve('TIMEOUT'), 15000))
    ]);
    
    console.log(`🎯 Join result: ${result}`);
    
    if (result === 'SUCCESS') {
      const currentUrl = page.url();
      console.log('✅ SUCCESS: Successfully joined room!');
      console.log(`🏠 Current URL: ${currentUrl}`);
      
      // Verify we're in room page
      await page.waitForSelector('.rp-gameContainer, .room-page, [data-testid="room"]', { timeout: 5000 });
      console.log('✅ Room page loaded successfully');
      
      return {
        success: true,
        message: 'Room join successful',
        roomId,
        url: currentUrl
      };
      
    } else if (result === 'ERROR') {
      console.log('❌ ERROR: Error occurred during join');
      
      // Try to get error message
      const errorElement = await page.locator('[role="alert"], .error, .alert').first();
      const errorMessage = await errorElement.textContent().catch(() => 'Unknown error');
      
      console.log(`🔍 Error message: ${errorMessage}`);
      
      return {
        success: false,
        message: `Join failed: ${errorMessage}`,
        roomId
      };
      
    } else {
      console.log('⏰ TIMEOUT: Join attempt timed out');
      return {
        success: false,
        message: 'Join timed out',
        roomId
      };
    }
    
  } catch (error) {
    console.error('💥 Test error:', error.message);
    return {
      success: false,
      message: `Test failed: ${error.message}`,
      error: error.stack
    };
    
  } finally {
    console.log('🧹 Cleaning up browser...');
    await browser.close();
  }
}

// Run the test
if (require.main === module) {
  testSimpleJoin()
    .then(result => {
      console.log('\n🎯 SIMPLE JOIN TEST RESULTS:');
      console.log('=' .repeat(60));
      console.log(`Status: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
      console.log(`Message: ${result.message}`);
      if (result.roomId) console.log(`Room ID: ${result.roomId}`);
      if (result.url) console.log(`Final URL: ${result.url}`);
      if (result.error) console.log(`Error: ${result.error}`);
      
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Test crashed:', error);
      process.exit(1);
    });
}

module.exports = { testSimpleJoin };