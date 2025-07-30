const { chromium } = require('playwright');

async function testRoomCreationAndDisplay() {
  console.log('🧪 Two-Player Room Creation and Display Test...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 800
  });
  
  try {
    // Create two browser contexts
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    
    // Enable console logging for both
    player1Page.on('console', msg => console.log(`[P1] ${msg.type()}: ${msg.text()}`));
    player2Page.on('console', msg => console.log(`[P2] ${msg.type()}: ${msg.text()}`));
    
    console.log('🔄 Both players entering lobby...');
    
    // Both players enter lobby
    await Promise.all([
      enterLobby(player1Page, 'Player1'),
      enterLobby(player2Page, 'Player2')
    ]);
    
    // Player 1 creates a room
    console.log('➕ Player 1 creating room...');
    await player1Page.click('button:has-text("Create")');
    await player1Page.waitForTimeout(2000);
    
    // Check Player 2's room list after creation
    console.log('👀 Checking Player 2 room display...');
    await checkRoomDisplay(player2Page, 'Player2');
    
    // Refresh Player 2's room list manually
    console.log('🔄 Manually refreshing Player 2...');
    const refreshBtn = player2Page.locator('button[title="Refresh room list"]');
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      await player2Page.waitForTimeout(1000);
      await checkRoomDisplay(player2Page, 'Player2');
    }
    
    // Keep browsers open for inspection
    console.log('⏳ Keeping browsers open for 10 seconds...');
    await player1Page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

async function enterLobby(page, playerName) {
  await page.goto('http://localhost:5050');
  await page.waitForLoadState('networkidle');
  
  await page.fill('input[type="text"]', playerName);
  await page.click('button');
  await page.waitForTimeout(2000);
  
  // Inject monitoring
  await page.evaluate((name) => {
    console.log(`🔧 [${name}] Setting up monitoring...`);
    
    // Monitor room_list_update events specifically
    const originalLog = console.log;
    console.log = function(...args) {
      if (args[0] && args[0].includes && args[0].includes('room_list_update')) {
        originalLog(`🎯 [${name}] ROOM_LIST_UPDATE:`, ...args);
      }
      originalLog(...args);
    };
    
    // Check for React state updates
    window.monitorRooms = () => {
      const roomCards = document.querySelectorAll('.lp-roomCard');
      const emptyState = document.querySelector('.lp-emptyState');
      const roomCount = document.querySelector('.lp-roomCount');
      
      return {
        roomCards: roomCards.length,
        emptyVisible: emptyState && window.getComputedStyle(emptyState).display !== 'none',
        roomCountText: roomCount?.textContent,
        hasRoomList: !!document.querySelector('.lp-roomList')
      };
    };
    
  }, playerName);
}

async function checkRoomDisplay(page, playerName) {
  const roomState = await page.evaluate(() => window.monitorRooms());
  console.log(`📊 [${playerName}] Room State:`, roomState);
  
  // Check WebSocket connection
  const connectionStatus = await page.locator('.connection-status').textContent();
  console.log(`🔗 [${playerName}] Connection:`, connectionStatus);
  
  // Check if room list container exists
  const roomListExists = await page.locator('.lp-roomList').isVisible();
  console.log(`📋 [${playerName}] Room list container:`, roomListExists);
  
  // Check empty state
  const emptyStateText = await page.locator('.lp-emptyState .lp-emptyText').textContent();
  console.log(`🚫 [${playerName}] Empty state:`, emptyStateText);
}

if (require.main === module) {
  testRoomCreationAndDisplay().catch(console.error);
}

module.exports = { testRoomCreationAndDisplay };