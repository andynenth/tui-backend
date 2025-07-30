const { chromium } = require('playwright');

async function testLobbyNavigation() {
  console.log('🧪 Testing Lobby Navigation...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
      console.error(`[PAGE ERROR] ${error.message}`);
    });
    
    // Go to the start page
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('🏠 On start page, checking for elements...');
    
    // Check what elements are available
    const playerInput = page.locator('input[type="text"]').first();
    const playButton = page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    
    console.log('👤 Player input visible:', await playerInput.isVisible());
    console.log('🎮 Play button visible:', await playButton.isVisible());
    
    // Enter player name and navigate to lobby
    await playerInput.fill('TestPlayer');
    await playButton.click();
    
    console.log('🔄 Clicked play button, waiting for navigation...');
    
    // Wait for navigation and check URL
    await page.waitForTimeout(3000);
    const currentUrl = page.url();
    console.log('🌐 Current URL:', currentUrl);
    
    // Check if we're in the lobby
    const lobbyTitle = page.locator('h1, h2').filter({ hasText: /lobby/i }).first();
    console.log('🏛️ Lobby title visible:', await lobbyTitle.isVisible());
    
    // Wait for lobby to fully load
    await page.waitForTimeout(2000);
    
    // Check lobby elements
    const roomList = page.locator('.lp-roomList').first();
    const emptyState = page.locator('.lp-emptyState').first();
    const roomCount = page.locator('.lp-roomCount').first();
    const createButton = page.locator('button').filter({ hasText: /create/i }).first();
    
    console.log('📋 Room list container exists:', await roomList.isVisible());
    console.log('🚫 Empty state visible:', await emptyState.isVisible());
    console.log('📊 Room count element exists:', await roomCount.isVisible());
    console.log('➕ Create button visible:', await createButton.isVisible());
    
    if (await roomCount.isVisible()) {
      console.log('📊 Room count text:', await roomCount.textContent());
    }
    
    // Check connection status
    const connectionStatus = page.locator('.connection-status').first();
    if (await connectionStatus.isVisible()) {
      console.log('🔗 Connection status:', await connectionStatus.textContent());
    }
    
    // Inject debug script to monitor network events
    await page.evaluate(() => {
      console.log('🔧 Injecting network monitoring...');
      
      // Check if networkService exists
      const services = [
        'networkService',
        'serviceIntegration',
        'gameService'
      ];
      
      services.forEach(serviceName => {
        if (window[serviceName]) {
          console.log(`✅ ${serviceName} found in window`);
          
          if (serviceName === 'networkService') {
            // Add listener for room_list_update
            window[serviceName].addEventListener('room_list_update', (event) => {
              console.log('📥 room_list_update received:', event.detail);
              console.log('🏠 Rooms in data:', event.detail?.data?.rooms?.length || 0);
            });
            
            // Check connection status
            const status = window[serviceName].getStatus();
            console.log('🌐 NetworkService status:', status);
          }
        } else {
          console.log(`❌ ${serviceName} not found in window`);
        }
      });
      
      // Monitor React components
      const checkReactState = () => {
        const roomCards = document.querySelectorAll('.lp-roomCard');
        const emptyState = document.querySelector('.lp-emptyState');
        const roomCount = document.querySelector('.lp-roomCount');
        
        console.log('📈 React State:', {
          roomCards: roomCards.length,
          emptyStateVisible: emptyState && window.getComputedStyle(emptyState).display !== 'none',
          roomCountText: roomCount?.textContent,
          timestamp: new Date().toISOString()
        });
      };
      
      // Check state every 3 seconds
      setInterval(checkReactState, 3000);
      checkReactState(); // Initial check
    });
    
    console.log('⏳ Monitoring for 15 seconds...');
    await page.waitForTimeout(15000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  testLobbyNavigation().catch(console.error);
}

module.exports = { testLobbyNavigation };