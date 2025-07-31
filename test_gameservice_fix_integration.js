/**
 * Integration test to verify GameService phase_change fix
 * Tests the actual flow that would cause the original error
 */

const { chromium } = require('playwright');

async function testGameServiceFix() {
  console.log('🎮 Testing GameService JavaScript Error Fix - Integration Test');
  console.log('=' .repeat(70));
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Listen for console errors
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log('🚫 Console Error:', msg.text());
    }
  });
  
  // Listen for uncaught exceptions
  const uncaughtErrors = [];
  page.on('pageerror', (error) => {
    uncaughtErrors.push(error.message);
    console.log('💥 Uncaught Error:', error.message);
  });
  
  try {
    console.log('🌐 Loading game application...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    console.log('🔍 Checking for initial errors...');
    await page.waitForTimeout(2000);
    
    if (consoleErrors.length > 0) {
      console.log('⚠️  Initial console errors detected:');
      consoleErrors.forEach(error => console.log('   -', error));
    } else {
      console.log('✅ No initial console errors');
    }
    
    console.log('\n🎯 Simulating game start flow...');
    
    // Navigate to lobby
    await page.click('a[href="/lobby"]');
    await page.waitForLoadState('networkidle');
    console.log('✅ Navigated to lobby');
    
    // Create room
    await page.fill('input[name="playerName"]', 'TestPlayer');
    await page.click('button:has-text("Create Room")');
    await page.waitForSelector('[data-testid="room-created"]', { timeout: 10000 });
    console.log('✅ Room created successfully');
    
    // Add bots
    for (let i = 0; i < 3; i++) {
      await page.click('button:has-text("Add Bot")');
      await page.waitForTimeout(500);
    }
    console.log('✅ Added 3 bots');
    
    // Monitor WebSocket events and GameService state changes
    await page.evaluate(() => {
      // Hook into GameService to monitor phase_change events
      window.phaseChangeEvents = [];
      window.gameServiceErrors = [];
      
      // If GameService is available, monitor it
      if (window.gameService || (window.GameService && window.GameService.getInstance)) {
        const gameService = window.gameService || window.GameService.getInstance();
        
        // Override the handlePhaseChange method to track calls
        const originalProcessGameEvent = gameService.processGameEvent;
        gameService.processGameEvent = function(eventType, data) {
          console.log('🔍 [Monitor] Processing game event:', eventType);
          
          if (eventType === 'phase_change') {
            window.phaseChangeEvents.push({
              timestamp: Date.now(),
              data: JSON.parse(JSON.stringify(data)),
              playersType: Array.isArray(data.players) ? 'array' : typeof data.players,
              phaseDataPlayersType: data.phase_data && data.phase_data.players ? 
                (Array.isArray(data.phase_data.players) ? 'array' : typeof data.phase_data.players) : 'none'
            });
          }
          
          try {
            return originalProcessGameEvent.call(this, eventType, data);
          } catch (error) {
            console.error('🚫 [Monitor] Error in processGameEvent:', error);
            window.gameServiceErrors.push({
              eventType,
              error: error.message,
              timestamp: Date.now()
            });
            throw error;
          }
        };
      }
    });
    
    console.log('🎯 Starting game and monitoring phase_change events...');
    
    // Start game - this should trigger phase_change events
    await page.click('button:has-text("Start Game")');
    
    // Wait for game to start and monitor for errors
    await page.waitForTimeout(5000);
    
    // Check for the specific error we're fixing
    const hasMapError = consoleErrors.some(error => 
      error.includes('map is not a function') || 
      error.includes('TypeError') && error.includes('players')
    );
    
    // Get monitored events
    const monitoringData = await page.evaluate(() => ({
      phaseChangeEvents: window.phaseChangeEvents || [],
      gameServiceErrors: window.gameServiceErrors || []
    }));
    
    console.log('\n📊 Test Results:');
    console.log('=' .repeat(50));
    
    // Results summary
    const totalErrors = consoleErrors.length + uncaughtErrors.length;
    const hasTargetError = hasMapError;
    const phaseChangeCount = monitoringData.phaseChangeEvents.length;
    const gameServiceErrorCount = monitoringData.gameServiceErrors.length;
    
    console.log(`🔢 Total Console Errors: ${totalErrors}`);
    console.log(`🎯 Target Error (players.map): ${hasTargetError ? '❌ FOUND' : '✅ NOT FOUND'}`);
    console.log(`📨 Phase Change Events: ${phaseChangeCount}`);
    console.log(`⚠️  GameService Errors: ${gameServiceErrorCount}`);
    
    if (monitoringData.phaseChangeEvents.length > 0) {
      console.log('\n📋 Phase Change Events Details:');
      monitoringData.phaseChangeEvents.forEach((event, index) => {
        console.log(`  ${index + 1}. Players Type: ${event.playersType}, Phase Data Players: ${event.phaseDataPlayersType}`);
      });
    }
    
    if (monitoringData.gameServiceErrors.length > 0) {
      console.log('\n🚫 GameService Errors:');
      monitoringData.gameServiceErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.eventType}: ${error.error}`);
      });
    }
    
    // Final verdict
    console.log('\n🏆 Fix Validation Result:');
    if (hasTargetError) {
      console.log('❌ FAILURE: The target error still occurs');
      console.log('   The "players.map is not a function" error was detected');
    } else if (gameServiceErrorCount > 0) {
      console.log('⚠️  PARTIAL: Other GameService errors detected, but target error fixed');
    } else if (phaseChangeCount > 0) {
      console.log('✅ SUCCESS: phase_change events processed without target error');
      console.log('   The "players.map is not a function" error has been resolved');
    } else {
      console.log('❓ INCONCLUSIVE: No phase_change events detected to test the fix');
    }
    
    return {
      success: !hasTargetError && gameServiceErrorCount === 0,
      totalErrors,
      hasTargetError,
      phaseChangeCount,
      gameServiceErrorCount,
      consoleErrors,
      monitoringData
    };
    
  } catch (error) {
    console.error('💥 Test execution error:', error);
    return {
      success: false,
      error: error.message,
      totalErrors: consoleErrors.length + uncaughtErrors.length + 1,
      consoleErrors,
      hasTargetError: true
    };
  } finally {
    await browser.close();
  }
}

// Run the test
if (require.main === module) {
  testGameServiceFix()
    .then(result => {
      console.log('\n' + '='.repeat(70));
      console.log('🎮 GameService Fix Integration Test Complete');
      console.log('✅ Success:', result.success);
      console.log('📊 Summary:', {
        totalErrors: result.totalErrors,
        targetErrorFixed: !result.hasTargetError,
        phaseEventsProcessed: result.phaseChangeCount
      });
      
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Test failed:', error);
      process.exit(1);
    });
}

module.exports = { testGameServiceFix };