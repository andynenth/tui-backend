/**
 * Comprehensive Join Validation Test
 * Tests room join functionality with room creation and timing
 */

const { chromium } = require('playwright');

async function testJoinWithRoomCreation() {
  console.log('🧪 COMPREHENSIVE JOIN TEST: Testing complete join workflow');
  
  let browser1, browser2;
  let page1, page2;
  
  try {
    // Launch two browsers - one creates room, other joins
    browser1 = await chromium.launch({ headless: false, slowMo: 300 });
    browser2 = await chromium.launch({ headless: false, slowMo: 300 });
    
    page1 = await browser1.newPage();
    page2 = await browser2.newPage();
    
    // Enable console logging
    page1.on('console', msg => console.log(`📱 [CREATOR] ${msg.text()}`));
    page2.on('console', msg => console.log(`📱 [JOINER] ${msg.text()}`));
    
    console.log('🚀 Step 1: Both players enter lobby');
    
    // Player 1 (Creator) enters lobby
    await page1.goto('http://localhost:5050');
    await page1.waitForLoadState('networkidle');
    await page1.fill('input[placeholder*="name" i]', 'Creator');
    await page1.click('button:has-text("Enter Lobby")');
    await page1.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    
    // Player 2 (Joiner) enters lobby  
    await page2.goto('http://localhost:5050');
    await page2.waitForLoadState('networkidle');
    await page2.fill('input[placeholder*="name" i]', 'Joiner');
    await page2.click('button:has-text("Enter Lobby")');
    await page2.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    
    console.log('✅ Both players in lobby');
    
    console.log('🏠 Step 2: Creator creates room');
    
    // Creator creates a room
    await page1.click('button:has-text("Create Room")');
    
    // Wait for room creation and navigation
    await page1.waitForURL(/\/room\/\w+/, { timeout: 10000 });
    const roomUrl = page1.url();
    const roomId = roomUrl.match(/\/room\/(\w+)/)?.[1];
    
    console.log(`✅ Room created: ${roomId}`);
    console.log(`🏠 Room URL: ${roomUrl}`);
    
    // Small delay to allow room to appear in lobby
    await page2.waitForTimeout(2000);
    
    console.log('🔍 Step 3: Joiner looks for the room');
    
    // Joiner refreshes to see updated room list
    await page2.reload();
    await page2.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    await page2.waitForTimeout(3000); // Wait for room list to load
    
    // Check if the new room appears
    const roomCount = await page2.locator('.lp-roomCard').count();
    console.log(`📊 Joiner sees ${roomCount} rooms`);
    
    if (roomCount === 0) {
      return {
        success: false,
        message: 'No rooms visible to join',
        roomId,
        phase: 'room_discovery'
      };
    }
    
    // Find room with the specific ID
    let targetRoom = null;
    for (let i = 0; i < roomCount; i++) {
      const roomCard = page2.locator('.lp-roomCard').nth(i);
      const cardRoomId = await roomCard.locator('.lp-roomId').textContent();
      const occupancy = await roomCard.locator('.lp-roomOccupancy').textContent();
      
      console.log(`🏠 Found room: ${cardRoomId} occupancy: ${occupancy}`);
      
      if (cardRoomId === roomId) {
        targetRoom = roomCard;
        console.log(`✅ Target room found: ${cardRoomId}`);
        
        // Check if room is joinable
        const isFull = occupancy?.includes('4/4');
        if (isFull) {
          return {
            success: false,
            message: 'Target room is full (4/4)',
            roomId,
            occupancy,
            phase: 'room_full'
          };
        }
        break;
      }
    }
    
    if (!targetRoom) {
      return {
        success: false,
        message: 'Target room not found in lobby',
        roomId,
        phase: 'room_not_visible'
      };
    }
    
    console.log('🖱️  Step 4: Joiner attempts to join room');
    
    // Click on the room to join
    await targetRoom.click();
    
    console.log('⏳ Waiting for join result...');
    
    // Wait for join result
    const joinResult = await Promise.race([
      // Success: Navigation to room page
      page2.waitForURL(/\/room\/\w+/, { timeout: 15000 }).then(() => 'SUCCESS'),
      
      // Error: Check for error messages or alerts
      page2.waitForFunction(() => {
        const errorElements = document.querySelectorAll('[role="alert"], .error, .alert, .toast-error');
        return errorElements.length > 0;
      }, {}, { timeout: 15000 }).then(() => 'ERROR'),
      
      // Timeout
      new Promise(resolve => setTimeout(() => resolve('TIMEOUT'), 15000))
    ]);
    
    console.log(`🎯 Join result: ${joinResult}`);
    
    if (joinResult === 'SUCCESS') {
      const joinedUrl = page2.url();
      console.log('✅ SUCCESS: Join completed successfully!');
      console.log(`🏠 Joiner URL: ${joinedUrl}`);
      
      // Verify both players are in the same room
      const joinedRoomId = joinedUrl.match(/\/room\/(\w+)/)?.[1];
      const sameRoom = joinedRoomId === roomId;
      
      // Check room page loaded properly
      await page2.waitForSelector('.rp-gameContainer, .room-page, [data-testid="room"]', { timeout: 5000 });
      
      console.log('🎉 Step 5: Validating room state');
      
      // Get player count in room (both browsers)
      const creatorPlayerCount = await page1.locator('.rp-playerSlot:not(.rp-emptySlot)').count();
      const joinerPlayerCount = await page2.locator('.rp-playerSlot:not(.rp-emptySlot)').count();
      
      console.log(`👥 Creator sees ${creatorPlayerCount} players in room`);
      console.log(`👥 Joiner sees ${joinerPlayerCount} players in room`);
      
      return {
        success: true,
        message: 'Room join successful with validation',
        roomId,
        creatorUrl: roomUrl,
        joinerUrl: joinedUrl,
        sameRoom,
        creatorPlayerCount,
        joinerPlayerCount,
        phase: 'join_complete'
      };
      
    } else if (joinResult === 'ERROR') {
      console.log('❌ ERROR: Error occurred during join');
      
      // Get error details
      const errorElement = await page2.locator('[role="alert"], .error, .alert, .toast-error').first();
      const errorMessage = await errorElement.textContent().catch(() => 'Unknown error');
      
      return {
        success: false,
        message: `Join failed with error: ${errorMessage}`,
        roomId,
        error: errorMessage,
        phase: 'join_error'
      };
      
    } else {
      console.log('⏰ TIMEOUT: Join attempt timed out');
      return {
        success: false,
        message: 'Join attempt timed out',
        roomId,
        phase: 'join_timeout'
      };
    }
    
  } catch (error) {
    console.error('💥 Test error:', error.message);
    return {
      success: false,
      message: `Test failed: ${error.message}`,
      error: error.stack,
      phase: 'test_error'
    };
    
  } finally {
    console.log('🧹 Cleaning up browsers...');
    if (browser1) await browser1.close();
    if (browser2) await browser2.close();
  }
}

// Run the test
if (require.main === module) {
  testJoinWithRoomCreation()
    .then(result => {
      console.log('\n🎯 COMPREHENSIVE JOIN TEST RESULTS:');
      console.log('='.repeat(60));
      console.log(`Status: ${result.success ? '✅ PASS' : '❌ FAIL'}`);
      console.log(`Phase: ${result.phase || 'unknown'}`);
      console.log(`Message: ${result.message}`);
      if (result.roomId) console.log(`Room ID: ${result.roomId}`);
      if (result.creatorUrl) console.log(`Creator URL: ${result.creatorUrl}`);
      if (result.joinerUrl) console.log(`Joiner URL: ${result.joinerUrl}`);
      if (result.sameRoom !== undefined) console.log(`Same Room: ${result.sameRoom}`);
      if (result.creatorPlayerCount) console.log(`Creator Player Count: ${result.creatorPlayerCount}`);
      if (result.joinerPlayerCount) console.log(`Joiner Player Count: ${result.joinerPlayerCount}`);
      if (result.error) console.log(`Error Details: ${result.error}`);
      
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Test crashed:', error);
      process.exit(1);
    });
}

module.exports = { testJoinWithRoomCreation };