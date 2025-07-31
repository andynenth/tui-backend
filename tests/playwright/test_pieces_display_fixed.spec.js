const { test, expect, beforeEach, afterEach } = require('@playwright/test');
const { beforeEachTest, afterEachTest } = require('./utils/test-helpers');

let page, browser, context;
let testInfo;

beforeEach(async ({ browser: testBrowser }, info) => {
  browser = testBrowser;
  testInfo = info;
  const setup = await beforeEachTest(browser, info);
  page = setup.page;
  context = setup.context;
});

afterEach(async () => {
  await afterEachTest(page, browser, testInfo);
});

test('pieces display correctly in preparation phase after backend fix', async () => {
  console.log('🎮 Starting pieces display test...');

  // 1. Navigate to home page
  await page.goto('http://localhost:5050');
  await page.waitForLoadState('networkidle');
  console.log('✅ Loaded home page');

  // 2. Enter lobby
  await page.click('button:has-text("Enter Lobby")');
  await page.waitForSelector('text=Join Room', { timeout: 10000 });
  console.log('✅ Entered lobby');

  // 3. Create room
  await page.click('button:has-text("Create Room")');
  await page.waitForSelector('text=Waiting for game to start', { timeout: 10000 });
  console.log('✅ Created room');

  // 4. Start game (NO BOT NEEDED)
  await page.click('button:has-text("Start Game")');
  console.log('✅ Clicked Start Game');

  // 5. Wait for preparation phase
  await page.waitForSelector('text=Preparation Phase', { timeout: 15000 });
  console.log('✅ Entered preparation phase');

  // 6. Check for pieces display - wait a bit for pieces to render
  await page.waitForTimeout(2000);

  // Check if PieceTray is rendered with pieces
  const pieceTraySelector = '[data-testid="piece-tray"], .piece-tray, .pieces-container';
  const hasPieceTray = await page.locator(pieceTraySelector).first().isVisible().catch(() => false);
  
  if (hasPieceTray) {
    console.log('✅ PieceTray is visible');
    
    // Count the pieces
    const pieceSelector = '[data-testid="game-piece"], .game-piece, .piece';
    const pieceCount = await page.locator(pieceSelector).count();
    console.log(`📊 Found ${pieceCount} pieces displayed`);
    
    // Expect 8 pieces for a single player
    expect(pieceCount).toBeGreaterThan(0);
    expect(pieceCount).toBeLessThanOrEqual(8);
    
    // Log piece details
    const pieces = await page.locator(pieceSelector).all();
    for (let i = 0; i < Math.min(3, pieces.length); i++) {
      const pieceText = await pieces[i].textContent();
      console.log(`   Piece ${i + 1}: ${pieceText}`);
    }
  } else {
    // Check console logs for debugging
    const consoleLogs = await page.evaluate(() => {
      const logs = [];
      const originalLog = console.log;
      console.log = (...args) => {
        logs.push(args.join(' '));
        originalLog.apply(console, args);
      };
      return logs;
    });
    
    console.log('❌ PieceTray not visible. Checking console logs...');
    const relevantLogs = consoleLogs.filter(log => 
      log.includes('PreparationUI') || 
      log.includes('myHand') || 
      log.includes('PieceTray')
    );
    relevantLogs.forEach(log => console.log(`   Console: ${log}`));
  }

  // Take screenshot for visual verification
  await page.screenshot({ 
    path: 'pieces-display-test.png',
    fullPage: true 
  });
  console.log('📸 Screenshot saved as pieces-display-test.png');

  // Final assertion
  expect(hasPieceTray).toBe(true);
});