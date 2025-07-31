/**
 * Playwright Test: UI Update Fix Verification
 * 
 * This test verifies that the UI properly updates during the game start flow
 * and transitions from waiting page to preparation/game page correctly.
 */

const { chromium } = require('playwright');

async function testUIUpdateFix() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging to capture debug messages
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('🎮') || text.includes('GameService') || text.includes('useGameState') || text.includes('GameContainer')) {
      console.log(`BROWSER: ${text}`);
    }
  });

  // Capture JavaScript errors
  const jsErrors = [];
  page.on('pageerror', error => {
    jsErrors.push(error.message);
    console.error('JS ERROR:', error.message);
  });

  try {
    console.log('🧪 Starting UI update fix verification test...');
    
    // Step 1: Navigate to start page
    console.log('🧪 Step 1: Navigating to start page');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');

    // Step 2: Enter player name and go to lobby
    console.log('🧪 Step 2: Setting player name and entering lobby');
    await page.fill('input[placeholder="Enter your name..."]', 'TestPlayer1');
    await page.click('button:has-text("ENTER LOBBY")');
    await page.waitForURL('**/lobby');
    console.log('✅ Successfully navigated to lobby');

    // Step 3: Create a room
    console.log('🧪 Step 3: Creating room');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL('**/room/**');
    
    // Extract room ID from URL
    const url = page.url();
    const roomId = url.split('/room/')[1];
    console.log(`✅ Room created with ID: ${roomId}`);

    // Step 4: Start the game and monitor UI transitions
    console.log('🧪 Step 4: Starting game and monitoring UI transitions');
    
    // Record the start time
    const startTime = Date.now();
    
    // Add logs to track state changes
    await page.evaluate(() => {
      // Override console.log temporarily to capture our debug logs
      const originalLog = console.log;
      window.uiUpdateLogs = [];
      console.log = function(...args) {
        const message = args.join(' ');
        if (message.includes('🎮') && (
          message.includes('GameService.handleGameStarted') ||
          message.includes('useGameState') ||
          message.includes('GameContainer')
        )) {
          window.uiUpdateLogs.push(`${Date.now()}: ${message}`);
        }
        originalLog.apply(console, args);
      };
    });

    // Click start game button
    await page.click('button:has-text("Start Game")');
    console.log('🧪 Start Game button clicked');

    // Wait for navigation to game page - this should happen quickly now
    console.log('🧪 Waiting for navigation to game page...');
    
    try {
      // Wait for URL change with a reasonable timeout
      await page.waitForURL(`**/game/${roomId}`, { timeout: 5000 });
      const navigationTime = Date.now() - startTime;
      console.log(`✅ Navigated to game page in ${navigationTime}ms`);
      
      // Wait a moment for the game to initialize and UI to update
      await page.waitForTimeout(2000);
      
      // Check that we're not stuck on waiting page
      const waitingElements = await page.locator('text="Waiting for game to start"').count();
      const preparationElements = await page.locator('text="Starting game"').count() + 
                                  await page.locator('text="Preparing"').count() + 
                                  await page.locator('text="preparation"').count();
      
      console.log(`🧪 UI State Check:`);
      console.log(`   - Waiting elements found: ${waitingElements}`);
      console.log(`   - Preparation/Game elements found: ${preparationElements}`);
      
      // Get debug logs from the page
      const uiLogs = await page.evaluate(() => window.uiUpdateLogs || []);
      console.log('🧪 UI Update Debug Logs:');
      uiLogs.forEach(log => console.log(`   ${log}`));
      
      // Check final state
      const currentUrl = page.url();
      const pageTitle = await page.title();
      console.log(`🧪 Final state: URL=${currentUrl}, Title=${pageTitle}`);
      
      // Verify we successfully transitioned
      if (currentUrl.includes('/game/') && (waitingElements === 0 || preparationElements > 0)) {
        console.log('✅ SUCCESS: UI properly updated and transitioned from waiting to game state');
        console.log(`✅ Navigation completed successfully in ${navigationTime}ms`);
      } else {
        console.log('❌ FAILURE: UI appears to be stuck on waiting state');
        // Take a screenshot for debugging
        await page.screenshot({ path: 'ui_update_failure.png' });
      }
      
    } catch (timeoutError) {
      console.log('❌ TIMEOUT: Failed to navigate to game page within 5 seconds');
      console.log('Current URL:', page.url());
      
      // Take a screenshot for debugging
      await page.screenshot({ path: 'navigation_timeout.png' });
      
      // Get debug logs anyway
      const uiLogs = await page.evaluate(() => window.uiUpdateLogs || []);
      console.log('🧪 Debug logs at timeout:');
      uiLogs.forEach(log => console.log(`   ${log}`));
    }

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
    await page.screenshot({ path: 'test_error.png' });
  } finally {
    // Report JavaScript errors
    if (jsErrors.length > 0) {
      console.log('❌ JavaScript errors detected:');
      jsErrors.forEach(error => console.log(`   ${error}`));
    } else {
      console.log('✅ No JavaScript errors detected');
    }

    await browser.close();
    console.log('🧪 Test completed');
  }
}

// Run the test
testUIUpdateFix().catch(console.error);