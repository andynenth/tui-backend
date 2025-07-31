/**
 * Simple Manual Flow Test - Validate Game Start Fix
 * Test Order: Player 1 >> Enter Lobby >> Create Room >> Start Game
 */

const { test, expect } = require('@playwright/test');

test('Manual Game Start Flow Validation', async ({ page }) => {
  console.log('🎯 Starting manual game start flow validation...');
  
  // Step 1: Navigate to app
  console.log('📍 Step 1: Loading application...');
  await page.goto('http://localhost:5050');
  await page.waitForLoadState('networkidle');
  
  // Take a screenshot to see what we have
  await page.screenshot({ path: 'manual-test-1-loaded.png', fullPage: true });
  console.log('📸 Screenshot taken: manual-test-1-loaded.png');
  
  // Step 2: Enter player name - let's check the actual placeholder
  console.log('📍 Step 2: Looking for name input field...');
  const nameInput = page.locator('input[placeholder*="name"]').first();
  await expect(nameInput).toBeVisible({ timeout: 10000 });
  
  await nameInput.fill('TestPlayer');
  console.log('✅ Name entered: TestPlayer');
  
  // Take screenshot after name entry
  await page.screenshot({ path: 'manual-test-2-name-entered.png' });
  
  // Step 3: Enter lobby (create room)
  console.log('📍 Step 3: Clicking Enter Lobby...');
  const enterLobbyButton = page.locator('button:has-text("ENTER LOBBY")');
  await expect(enterLobbyButton).toBeVisible();
  await enterLobbyButton.click();
  
  // Wait for lobby/room creation
  await page.waitForURL(/\/lobby|\/room/, { timeout: 10000 });
  console.log('✅ Entered lobby, current URL:', page.url());
  
  await page.screenshot({ path: 'manual-test-3-in-lobby.png' });
  
  // Step 4: If we're in lobby, create a room
  if (page.url().includes('/lobby')) {
    console.log('📍 Step 4: Creating room from lobby...');
    const createRoomButton = page.locator('button:has-text("Create Room")');
    await expect(createRoomButton).toBeVisible({ timeout: 5000 });
    await createRoomButton.click();
    
    await page.waitForURL(/\/room/, { timeout: 10000 });
    console.log('✅ Room created, current URL:', page.url());
  }
  
  await page.screenshot({ path: 'manual-test-4-room-created.png' });
  
  // Step 5: Add bots and start game
  console.log('📍 Step 5: Adding bots...');
  
  // Add 3 bots for a full game
  for (let i = 0; i < 3; i++) {
    const addBotButton = page.locator('button:has-text("Add Bot")').first();
    if (await addBotButton.isVisible({ timeout: 2000 })) {
      await addBotButton.click();
      await page.waitForTimeout(1000);
      console.log(`✅ Bot ${i + 1} added`);
    }
  }
  
  await page.screenshot({ path: 'manual-test-5-bots-added.png' });
  
  // Step 6: Start the game - THIS IS THE CRITICAL TEST
  console.log('📍 Step 6: Looking for Start Game button...');
  const startButton = page.locator('button:has-text("Start Game")');
  await expect(startButton).toBeVisible({ timeout: 10000 });
  
  const isEnabled = await startButton.isEnabled();
  console.log(`🔍 Start Game button enabled: ${isEnabled}`);
  
  if (isEnabled) {
    console.log('🚨 CRITICAL: Clicking Start Game button...');
    
    // Set up monitoring for the navigation
    page.on('console', msg => {
      if (msg.text().includes('game_started') || msg.text().includes('phase_change')) {
        console.log(`🎮 WebSocket Event: ${msg.text()}`);
      }
    });
    
    await startButton.click();
    console.log('⏱️  Start Game clicked, waiting for navigation...');
    
    // Wait for either game page or timeout
    try {
      await page.waitForURL(/\/game\//, { timeout: 30000 });
      console.log('✅ SUCCESS: Navigated to game page!');
      console.log('🎯 Final URL:', page.url());
      
      await page.screenshot({ path: 'manual-test-6-SUCCESS-game-page.png' });
      
    } catch (error) {
      console.log('❌ TIMEOUT: Did not navigate to game page');
      console.log('🔍 Current URL:', page.url());
      
      await page.screenshot({ path: 'manual-test-6-FAILED-stuck.png' });
      
      // Check if we're still on waiting page
      const waitingElements = await page.locator('text=waiting').count();
      console.log(`🔍 Waiting elements found: ${waitingElements}`);
      
      throw new Error('Game start navigation failed - stuck on waiting page');
    }
  } else {
    throw new Error('Start Game button is not enabled');
  }
});