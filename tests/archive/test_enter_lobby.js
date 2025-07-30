const { chromium } = require('playwright');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 500
};

async function captureWebSocketMessages(page, playerName) {
  const messages = [];
  
  page.on('websocket', ws => {
    console.log(`🔗 [${playerName}] WebSocket connected: ${ws.url()}`);
    
    ws.on('framesent', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      console.log(`📤 [${playerName}] Sent: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({
          type: 'sent',
          timestamp,
          player: playerName,
          message: parsed,
          raw: message
        });
      } catch (e) {
        console.error(`Parse error for ${playerName}:`, e);
      }
    });
    
    ws.on('framereceived', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      console.log(`📥 [${playerName}] Received: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({
          type: 'received',
          timestamp,
          player: playerName,
          message: parsed,
          raw: message
        });
      } catch (e) {
        console.error(`Parse error for ${playerName}:`, e);
      }
    });
  });
  
  return messages;
}

async function enterLobby(page, playerName) {
  console.log(`🚀 [${playerName}] Entering lobby...`);
  
  await page.goto(TEST_CONFIG.baseUrl);
  await page.waitForLoadState('networkidle');
  
  const nameInput = await page.locator('input[type="text"]').first();
  await nameInput.fill(playerName);
  
  const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
  await startButton.click();
  
  await page.waitForTimeout(2000);
  
  const lobbyTitle = await page.locator('h1, h2').filter({ hasText: /lobby/i }).first();
  if (!(await lobbyTitle.isVisible())) {
    throw new Error(`${playerName} failed to reach lobby`);
  }
  
  console.log(`✅ [${playerName}] Successfully entered lobby`);
}

async function testEnterLobby() {
  console.log('🚀 Starting Enter Lobby Test...');
  
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Set up message capture
    const messages = await captureWebSocketMessages(page, 'TestPlayer');
    
    console.log('\n=== PHASE 1: Enter lobby ===');
    
    // Enter lobby
    await enterLobby(page, 'TestPlayer');
    
    console.log('\n=== PHASE 2: Verify lobby state ===');
    
    // Check if we can see lobby elements
    const lobbyElements = await page.locator('h1, h2, .lobby, [class*="lobby"]').all();
    console.log(`📋 Found ${lobbyElements.length} lobby-related elements`);
    
    // Look for room list or create room button
    const createButton = await page.locator('button').filter({ hasText: /create/i }).first();
    const createButtonVisible = await createButton.isVisible();
    console.log(`➕ Create room button visible: ${createButtonVisible}`);
    
    // Wait a bit more to see all messages
    await page.waitForTimeout(3000);
    
    console.log('\n=== ANALYSIS ===');
    console.log(`📨 Total WebSocket messages: ${messages.length}`);
    console.log(`📤 Sent messages: ${messages.filter(m => m.type === 'sent').length}`);
    console.log(`📥 Received messages: ${messages.filter(m => m.type === 'received').length}`);
    
    // Show message timeline
    messages.forEach(msg => {
      const event = msg.message?.event || 'unknown';
      console.log(`  ${msg.timestamp} [${msg.type}]: ${event}`);
    });
    
    console.log('\n✅ Successfully entered lobby! Keeping browser open for inspection...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Run the test
if (require.main === module) {
  testEnterLobby().catch(console.error);
}

module.exports = { testEnterLobby };