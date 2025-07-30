const { chromium } = require('playwright');

async function debugEventHandler() {
  console.log('🔍 Debugging Event Handler...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('room_list_update') || text.includes('setRooms') || text.includes('Received room_list_update')) {
        console.log(`[BROWSER] 🎯 ${msg.type()}: ${text}`);
      } else {
        console.log(`[BROWSER] ${msg.type()}: ${text}`);
      }
    });
    
    // Go to lobby
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'DebugPlayer');
    await page.click('button');
    await page.waitForTimeout(3000);
    
    // Inject debugging to intercept the event handler
    await page.evaluate(() => {
      console.log('🔧 Intercepting room_list_update handler...');
      
      // Find the original handler and wrap it
      const originalAddEventListener = EventTarget.prototype.addEventListener;
      EventTarget.prototype.addEventListener = function(type, listener, options) {
        if (type === 'room_list_update') {
          console.log('🎯 room_list_update listener registered!');
          
          // Wrap the listener to log when it's called
          const wrappedListener = function(event) {
            console.log('📥 room_list_update event triggered!');
            console.log('📊 Event detail:', event.detail);
            console.log('🏠 Rooms data:', event.detail?.data?.rooms);
            console.log('🔢 Rooms count:', event.detail?.data?.rooms?.length);
            
            // Call original listener
            const result = listener.call(this, event);
            
            // Check React state after handler
            setTimeout(() => {
              const roomCards = document.querySelectorAll('.lp-roomCard');
              const emptyState = document.querySelector('.lp-emptyState');
              const roomCount = document.querySelector('.lp-roomCount');
              
              console.log('📈 Post-handler UI state:', {
                roomCardsInDOM: roomCards.length,
                emptyStateVisible: emptyState && window.getComputedStyle(emptyState).display !== 'none',
                roomCountText: roomCount?.textContent
              });
            }, 100);
            
            return result;
          };
          
          originalAddEventListener.call(this, type, wrappedListener, options);
        } else {
          originalAddEventListener.call(this, type, listener, options);
        }
      };
      
      // Also monitor manual setRooms calls if we can access React
      window.debugRooms = function() {
        const roomCards = document.querySelectorAll('.lp-roomCard');
        const emptyState = document.querySelector('.lp-emptyState');
        const roomCount = document.querySelector('.lp-roomCount');
        const roomList = document.querySelector('.lp-roomList');
        
        return {
          roomCards: roomCards.length,
          emptyVisible: emptyState && window.getComputedStyle(emptyState).display !== 'none',
          roomCountText: roomCount?.textContent,
          roomListExists: !!roomList,
          timestamp: new Date().toISOString()
        };
      };
    });
    
    console.log('⏳ Waiting for room_list_update events...');
    await page.waitForTimeout(20000);
    
  } catch (error) {
    console.error('❌ Debug failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  debugEventHandler().catch(console.error);
}

module.exports = { debugEventHandler };