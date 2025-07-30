const { chromium } = require('playwright');

async function testCancelSimple() {
  console.log('🔍 Testing Cancel Navigation Issue\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Intercept navigation to catch the problematic URL
  page.on('request', request => {
    const url = request.url();
    console.log(`📤 Request: ${request.method()} ${url}`);
    
    // Check if this is the problematic request
    if (url.includes('/cancel') || url.includes('/leave') || request.failure()) {
      console.log(`  ⚠️  Potentially problematic URL!`);
    }
  });
  
  page.on('response', response => {
    if (response.status() === 404) {
      console.log(`❌ 404 Error: ${response.url()}`);
      response.text().then(text => {
        console.log(`  Response body: ${text}`);
        
        // Check if it's the FastAPI 404 error
        if (text.includes('"detail":"Not Found"')) {
          console.log('  🐛 This is the bug! FastAPI is returning 404 for this URL');
          console.log('  The URL is not handled by any route in the backend');
        }
      });
    }
  });
  
  // Monitor navigation events
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const url = frame.url();
      console.log(`🧭 Navigated to: ${url}`);
      
      // Check if this is an API URL that shouldn't be navigated to
      if (url.includes('/api/') || url.includes(':5050/') && !url.includes('/lobby') && !url.includes('/room/') && !url.includes('/game/')) {
        console.log('  ⚠️  WARNING: Navigated to a non-frontend URL!');
      }
    }
  });

  try {
    // Quick flow to get to game state
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'TestUser');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    await page.click('button:has-text("Start")');
    await page.waitForTimeout(3000);
    
    // Handle room error if it occurs
    const pageText = await page.textContent('body');
    if (pageText.includes('room no longer exists')) {
      console.log('⏳ Waiting for auto-redirect...');
      await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
      
      // Try again
      await page.fill('input[type="text"]', 'TestUser2');
      await page.click('button:has-text("Enter Lobby")');
      await page.waitForTimeout(1500);
      await page.click('button:has-text("Create Room")');
      await page.waitForTimeout(2000);
      await page.click('button:has-text("Start")');
      await page.waitForTimeout(3000);
    }
    
    // Now click cancel
    console.log('\n📍 Looking for Cancel button...');
    const cancelButton = await page.$('button:has-text("Cancel")');
    
    if (cancelButton) {
      console.log('✓ Found Cancel button');
      
      // Get button properties
      const buttonInfo = await cancelButton.evaluate(el => {
        const rect = el.getBoundingClientRect();
        return {
          text: el.textContent,
          visible: rect.width > 0 && rect.height > 0,
          onclick: el.onclick ? 'has onclick' : null,
          href: el.href || null,
          parent: el.parentElement?.tagName
        };
      });
      console.log('Button info:', buttonInfo);
      
      const beforeUrl = page.url();
      console.log(`Current URL before click: ${beforeUrl}`);
      
      console.log('\n🖱️ Clicking Cancel...');
      await cancelButton.click();
      
      // Wait a moment to see what happens
      await page.waitForTimeout(3000);
      
      const afterUrl = page.url();
      console.log(`\nURL after click: ${afterUrl}`);
      
      // Check page content
      const content = await page.textContent('body');
      if (content.includes('"detail":"Not Found"')) {
        console.log('\n❌ BUG CONFIRMED!');
        console.log('The page shows: {"detail":"Not Found"}');
        console.log('This is a FastAPI 404 error response');
        
        // Try to understand what URL it tried to access
        if (afterUrl !== beforeUrl) {
          console.log(`\nThe cancel button navigated to: ${afterUrl}`);
          console.log('This URL is not handled by the backend');
        }
      }
      
    } else {
      console.log('❌ No Cancel button found');
    }
    
    console.log('\n✅ Test complete. Browser remains open.');
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testCancelSimple().catch(console.error);