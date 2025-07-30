const { test, expect } = require('@playwright/test');

test('Debug start button issue - exact reproduction', async ({ page, context }) => {
  console.log('🧪 Starting start button debug test...');
  
  try {
    // Step 1: Navigate to lobby
    console.log('📍 Step 1: Enter lobby');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Check if we're on the lobby page
    const lobbyTitle = await page.locator('h1').textContent();
    console.log(`✅ Lobby loaded: "${lobbyTitle}"`);
    
    // Step 2: Create room
    console.log('📍 Step 2: Create room');
    const createRoomButton = page.locator('button:has-text("Create Room")');
    await expect(createRoomButton).toBeVisible();
    await createRoomButton.click();
    
    // Wait for room creation and navigation
    await page.waitForURL('**/room/**');
    console.log('✅ Room created and navigated to room page');
    
    // Wait for room to load completely
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Allow WebSocket connections to establish
    
    // Check room state
    const roomTitle = await page.locator('h2').first().textContent();
    console.log(`✅ Room page loaded: "${roomTitle}"`);
    
    // Step 3: Press start button
    console.log('📍 Step 3: Attempting to press start button');
    
    // Check if start button exists and is visible
    const startButton = page.locator('button:has-text("Start Game")');
    
    console.log('🔍 Checking start button state...');
    const isStartButtonVisible = await startButton.isVisible();
    console.log(`Start button visible: ${isStartButtonVisible}`);
    
    if (isStartButtonVisible) {
      const isStartButtonEnabled = await startButton.isEnabled();
      console.log(`Start button enabled: ${isStartButtonEnabled}`);
      
      if (!isStartButtonEnabled) {
        // Check why button is disabled
        const buttonText = await startButton.textContent();
        const isDisabled = await startButton.getAttribute('disabled');
        console.log(`❌ Start button is DISABLED: text="${buttonText}", disabled="${isDisabled}"`);
        
        // Check room state that might affect button
        const playersInRoom = await page.locator('[class*="player"], [class*="slot"]').count();
        console.log(`Players/slots found: ${playersInRoom}`);
      } else {
        console.log('✅ Start button is enabled, clicking...');
        
        // Monitor for navigation or changes
        const currentURL = page.url();
        console.log(`Current URL before click: ${currentURL}`);
        
        // Click the start button
        await startButton.click();
        console.log('🖱️ Start button clicked');
        
        // Wait for potential navigation or state change
        await page.waitForTimeout(3000);
        
        // Check what happened
        const newURL = page.url();
        console.log(`URL after click: ${newURL}`);
        
        if (newURL === currentURL) {
          console.log('❌ NO NAVIGATION OCCURRED - Button click had no effect');
          
          // Check for any error messages or state changes
          const errorMessages = await page.locator('.error, [class*="error"]').allTextContents();
          if (errorMessages.length > 0) {
            console.log(`❌ Error messages found: ${errorMessages.join(', ')}`);
          }
          
          // Check button state after click
          const buttonTextAfter = await startButton.textContent();
          console.log(`Button text after click: "${buttonTextAfter}"`);
          
        } else {
          console.log('✅ Navigation occurred - checking if game started');
          // Additional checks for game page could go here
        }
      }
    } else {
      console.log('❌ Start button NOT VISIBLE');
      
      // Check what buttons ARE visible
      const visibleButtons = await page.locator('button').allTextContents();
      console.log(`Visible buttons: ${visibleButtons.join(', ')}`);
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    
    // Capture current page state for debugging
    const currentURL = page.url();
    const pageTitle = await page.title();
    console.log(`Debug info - URL: ${currentURL}, Title: ${pageTitle}`);
  }
});