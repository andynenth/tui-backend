const { chromium } = require('playwright');

async function debugRoomDisplay() {
  console.log('🔍 Starting Room Display Debug Test...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable console logging from the browser
    page.on('console', msg => {
      console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
    });
    
    // Capture errors
    page.on('pageerror', error => {
      console.error(`[PAGE ERROR] ${error.message}`);
    });
    
    // Go to the lobby
    await page.goto('http://localhost:5050');
    
    // Enter player name
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button');
    await page.waitForTimeout(2000);
    
    // Inject debugging script to monitor room list updates
    await page.evaluate(() => {
      console.log('🔧 Setting up debug monitoring...');
      
      // Monitor room state
      let roomUpdateCount = 0;
      
      // Check if the room list container exists
      const roomList = document.querySelector('.lp-roomList');
      console.log('📋 Room list container found:', !!roomList);
      
      // Monitor DOM changes
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' && mutation.target.classList.contains('lp-roomList')) {
            console.log('📈 Room list DOM changed:', mutation.addedNodes.length, 'added,', mutation.removedNodes.length, 'removed');
            console.log('📊 Current room count in DOM:', document.querySelectorAll('.lp-roomCard').length);
          }
        });
      });
      
      if (roomList) {
        observer.observe(roomList, { childList: true, subtree: true });
      }
      
      // Monitor WebSocket messages 
      window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'room_list_update') {
          roomUpdateCount++;
          console.log(`🔔 Room list update #${roomUpdateCount}:`, event.data);
        }
      });
      
      // Check for NetworkService events
      if (window.networkService) {
        console.log('🌐 NetworkService found, adding event listener');
        window.networkService.addEventListener('room_list_update', (event) => {
          console.log('📥 NetworkService room_list_update:', event.detail);
          console.log('📊 Rooms data:', event.detail.data);
        });
      } else {
        console.log('❌ NetworkService not found in window');
      }
      
      // Monitor React state changes
      setInterval(() => {
        const roomCountDisplay = document.querySelector('.lp-roomCount');
        const roomCards = document.querySelectorAll('.lp-roomCard');
        const emptyState = document.querySelector('.lp-emptyState');
        
        console.log('📈 UI State Check:', {
          roomCountText: roomCountDisplay?.textContent,
          roomCardsInDOM: roomCards.length,
          emptyStateVisible: emptyState && !emptyState.hidden,
          roomListExists: !!document.querySelector('.lp-roomList')
        });
      }, 5000);
    });
    
    console.log('✅ Debug monitoring set up. Waiting for events...');
    await page.waitForTimeout(30000); // Wait 30 seconds to observe
    
  } catch (error) {
    console.error('❌ Debug test failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  debugRoomDisplay().catch(console.error);
}

module.exports = { debugRoomDisplay };