/**
 * 🧪 Lobby State Fix Verification Test 
 * 
 * This test specifically validates that the React state update fix works correctly
 * by monitoring both WebSocket events AND React component state changes.
 */

const { chromium } = require('playwright');

async function runStateFixVerificationTest() {
  console.log('🧪 Starting Lobby State Fix Verification Test...\n');
  
  let andy, alexanderium, andyPage, alexanderiumPage;
  
  try {
    // Launch browsers
    console.log('🚀 Launching browsers...');
    andy = await chromium.launch({ headless: false });
    alexanderium = await chromium.launch({ headless: false });
    
    andyPage = await andy.newPage();
    alexanderiumPage = await alexanderium.newPage();
    
    // Navigate both to start page
    await Promise.all([
      andyPage.goto('http://localhost:5050'),
      alexanderiumPage.goto('http://localhost:5050')
    ]);
    
    console.log('✅ Both browsers ready\n');
    
    // Set up React state monitoring for Alexanderium
    await alexanderiumPage.addInitScript(() => {
      window.reactStateMonitor = {
        roomsHistory: [],
        stateUpdates: [],
        renderCount: 0
      };
      
      // Monitor React state changes
      const originalSetState = React.Component.prototype.setState;
      React.Component.prototype.setState = function(updater, callback) {
        window.reactStateMonitor.stateUpdates.push({
          timestamp: Date.now(),
          component: this.constructor.name,
          state: typeof updater === 'function' ? 'functional_update' : updater
        });
        return originalSetState.call(this, updater, callback);
      };
    });
    
    // Step 1: Both players enter lobby
    console.log('👥 Step 1: Both players entering lobby...');
    
    // Andy enters lobby
    await andyPage.fill('input[type="text"]', 'Andy');
    await andyPage.click('button:has-text("Enter Lobby")');
    await andyPage.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    
    // Alexanderium enters lobby  
    await alexanderiumPage.fill('input[type="text"]', 'Alexanderium');
    await alexanderiumPage.click('button:has-text("Enter Lobby")');
    await alexanderiumPage.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    
    console.log('✅ Both players in lobby\n');
    
    // Step 2: Get initial room count for Alexanderium
    await alexanderiumPage.waitForTimeout(2000); // Let initial load settle
    
    const initialRoomCount = await alexanderiumPage.evaluate(() => {
      const roomCountElement = document.querySelector('.lp-roomCount');
      if (roomCountElement) {
        const match = roomCountElement.textContent.match(/Available Rooms \((\d+)\)/);
        return match ? parseInt(match[1]) : 0;
      }
      return 0;
    });
    
    console.log(`📊 Initial room count for Alexanderium: ${initialRoomCount}`);
    
    // Step 3: Monitor WebSocket and React state for Alexanderium
    const stateMonitoringPromise = alexanderiumPage.evaluate(() => {
      return new Promise((resolve) => {
        let roomListUpdatesReceived = 0;
        let lastRoomCount = null;
        
        // Monitor console logs for our new debug messages
        const originalConsoleLog = console.log;
        console.log = function(...args) {
          const message = args.join(' ');
          
          if (message.includes('🔄 [LOBBY UPDATE] State update')) {
            const newCountMatch = message.match(/new count: (\d+)/);
            if (newCountMatch) {
              lastRoomCount = parseInt(newCountMatch[1]);
              roomListUpdatesReceived++;
              
              // Check if we got the expected update
              if (roomListUpdatesReceived >= 1) {
                resolve({
                  success: true,
                  roomListUpdatesReceived,
                  finalRoomCount: lastRoomCount,
                  reactStateHistory: window.reactStateMonitor?.stateUpdates || []
                });
              }
            }
          }
          
          return originalConsoleLog.apply(console, args);
        };
        
        // Timeout after 10 seconds
        setTimeout(() => {
          resolve({
            success: false,
            roomListUpdatesReceived,
            finalRoomCount: lastRoomCount,
            reactStateHistory: window.reactStateMonitor?.stateUpdates || [],
            error: 'Timeout waiting for state updates'
          });
        }, 10000);
      });
    });
    
    // Step 4: Andy creates a room (trigger the update)
    console.log('🏠 Step 3: Andy creating room...');
    await andyPage.click('button:has-text("Create Room")');
    
    // Wait for room creation - look for room page or confirmation
    try {
      await andyPage.waitForSelector('.rp-roomCode', { timeout: 5000 });
      const roomCode = await andyPage.textContent('.rp-roomCode');
      console.log(`✅ Andy created room: ${roomCode}\n`);
    } catch (e) {
      // If room code selector not found, check if we're still in lobby or got error
      const currentUrl = andyPage.url();
      console.log(`⚠️ Room creation may have failed or different flow. Current URL: ${currentUrl}`);
      
      // Take screenshot for debugging
      await andyPage.screenshot({ path: 'andy-after-create-attempt.png' });
      console.log('📸 Screenshot saved: andy-after-create-attempt.png');
    }
    
    // Step 5: Wait for Alexanderium's state monitoring to complete
    console.log('🔍 Step 4: Monitoring Alexanderium\'s state updates...');
    const stateResult = await stateMonitoringPromise;
    
    // Step 6: Verify final room count in UI
    await alexanderiumPage.waitForTimeout(2000); // Let UI settle
    
    const finalRoomCount = await alexanderiumPage.evaluate(() => {
      const roomCountElement = document.querySelector('.lp-roomCount');
      if (roomCountElement) {
        const match = roomCountElement.textContent.match(/Available Rooms \((\d+)\)/);
        return match ? parseInt(match[1]) : 0;
      }
      return 0;
    });
    
    // Step 7: Results analysis
    console.log('\n📊 === STATE UPDATE VERIFICATION RESULTS ===');
    console.log(`Initial room count: ${initialRoomCount}`);
    console.log(`Final room count in UI: ${finalRoomCount}`);
    console.log(`Room list updates received: ${stateResult.roomListUpdatesReceived}`);
    console.log(`Final room count from state: ${stateResult.finalRoomCount}`);
    console.log(`React state updates: ${stateResult.reactStateHistory.length}`);
    
    // Determine if fix worked
    const expectedRoomCount = initialRoomCount + 1;
    const fixWorked = finalRoomCount === expectedRoomCount && 
                      stateResult.roomListUpdatesReceived > 0 &&
                      stateResult.finalRoomCount === 1; // New room should show 1 room
    
    if (fixWorked) {
      console.log('\n✅ SUCCESS: Lobby state fix is working correctly!');
      console.log(`   - UI room count updated correctly: ${initialRoomCount} → ${finalRoomCount}`);
      console.log(`   - WebSocket events processed: ${stateResult.roomListUpdatesReceived}`);
      console.log(`   - React state pipeline functional`);
    } else {
      console.log('\n❌ FAILURE: Lobby state fix needs more work');
      console.log(`   - Expected room count: ${expectedRoomCount}, got: ${finalRoomCount}`);
      console.log(`   - WebSocket updates: ${stateResult.roomListUpdatesReceived}`);
      console.log(`   - State result:`, stateResult);
    }
    
    // Step 8: Take screenshots for visual verification
    await Promise.all([
      andyPage.screenshot({ path: 'andy-final-state.png' }),
      alexanderiumPage.screenshot({ path: 'alexanderium-final-state.png' })
    ]);
    
    console.log('\n📸 Screenshots saved: andy-final-state.png, alexanderium-final-state.png');
    
    return {
      success: fixWorked,
      initialRoomCount,
      finalRoomCount,
      expectedRoomCount,
      stateUpdates: stateResult.roomListUpdatesReceived,
      details: stateResult
    };
    
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    return { success: false, error: error.message };
  } finally {
    // Cleanup
    if (andy) await andy.close();
    if (alexanderium) await alexanderium.close();
  }
}

// Run the test
if (require.main === module) {
  runStateFixVerificationTest().then(result => {
    console.log('\n🏁 Test completed:', result.success ? 'PASSED' : 'FAILED');
    process.exit(result.success ? 0 : 1);
  });
}

module.exports = { runStateFixVerificationTest };