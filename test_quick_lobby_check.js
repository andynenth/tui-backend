const { test, expect } = require('@playwright/test');

test('Quick lobby to game check', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('Console error:', msg.text());
    }
  });
  
  // Go to lobby
  await page.goto('http://localhost:5050');
  
  // Create room
  await page.fill('input[placeholder="Enter your name"]', 'TestPlayer');
  await page.click('button:has-text("Create Room")');
  
  // Wait for room page
  await page.waitForURL(/\/room\/.+/);
  console.log('Room created:', page.url());
  
  // Add 3 bots quickly
  for (let i = 0; i < 3; i++) {
    await page.click('button:has-text("Add Bot")');
    await page.waitForTimeout(200);
  }
  
  // Check if start button is enabled
  const startButton = page.locator('button:has-text("Start Game")');
  await expect(startButton).toBeVisible();
  const isEnabled = await startButton.isEnabled();
  console.log('Start button enabled:', isEnabled);
  
  if (!isEnabled) {
    console.log('Start button is disabled! This is the issue.');
    
    // Check player count
    const playerElements = await page.locator('[class*="player"]').all();
    console.log('Number of player elements found:', playerElements.length);
    
    // Take screenshot
    await page.screenshot({ path: 'start-button-disabled.png', fullPage: true });
    return;
  }
  
  // Try to start game
  console.log('Clicking start button...');
  await startButton.click();
  
  // Wait and check what happens
  console.log('Waiting for transition...');
  
  // Set up a race between URL change and timeout
  const result = await Promise.race([
    page.waitForURL(/\/game\/.+/, { timeout: 10000 }).then(() => 'success'),
    page.waitForTimeout(10000).then(() => 'timeout')
  ]);
  
  if (result === 'success') {
    console.log('SUCCESS! Reached game page:', page.url());
  } else {
    console.log('FAILED! Still on:', page.url());
    
    // Check for any visible errors or waiting indicators
    const pageText = await page.textContent('body');
    if (pageText.includes('waiting') || pageText.includes('Waiting')) {
      console.log('Found waiting indicator - stuck in waiting state');
    }
    
    await page.screenshot({ path: 'stuck-after-start.png', fullPage: true });
  }
});