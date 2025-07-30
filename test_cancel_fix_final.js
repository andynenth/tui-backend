const { chromium } = require('playwright');

async function testCancelFixFinal() {
  console.log('✅ Final Cancel Button Fix Verification\n');
  console.log('Expected flow: Cancel → /lobby → / (if no playerName)\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor for 404 errors
  let found404 = false;
  page.on('response', response => {
    if (response.status() === 404) {
      found404 = true;
      console.log(`❌ 404 Error: ${response.url()}`);
      response.text().then(text => {
        if (text.includes('"detail":"Not Found"')) {
          console.log('  🐛 BUG STILL EXISTS: {"detail":"Not Found"} error');
        }
      });
    }
  });

  // Monitor navigation
  const navigationLog = [];
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const url = frame.url();
      const path = new URL(url).pathname;
      navigationLog.push(path);
      console.log(`🧭 Navigated to: ${path}`);
    }
  });

  try {
    // Setup: Get to game state
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    await page.click('button:has-text("Start")');
    await page.waitForTimeout(3000);
    
    // Handle room error
    const pageText = await page.textContent('body');
    if (pageText.includes('room no longer exists')) {
      console.log('⏳ Room error - waiting for redirect...');
      await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
      
      // Try again
      await page.fill('input[type="text"]', 'TestPlayer2');
      await page.click('button:has-text("Enter Lobby")');
      await page.waitForTimeout(1500);
      await page.click('button:has-text("Create Room")');
      await page.waitForTimeout(2000);
      await page.click('button:has-text("Start")');
      await page.waitForTimeout(3000);
    }
    
    // Clear navigation log for cancel test
    navigationLog.length = 0;
    found404 = false;
    
    // Test cancel button
    console.log('\n📍 Testing Cancel Button...');
    const cancelButton = await page.$('button:has-text("Cancel")');
    
    if (cancelButton) {
      console.log('✓ Found Cancel button');
      
      // Check localStorage before click
      const playerNameBefore = await page.evaluate(() => localStorage.getItem('playerName'));
      console.log(`PlayerName in localStorage: ${playerNameBefore}`);
      
      await cancelButton.click();
      console.log('✓ Clicked Cancel button');
      
      // Wait for navigation to complete
      await page.waitForTimeout(2000);
      
      // Check final state
      const finalUrl = page.url();
      const finalPath = new URL(finalUrl).pathname;
      const finalContent = await page.textContent('body');
      
      console.log('\n📊 Results:');
      console.log(`Navigation path: ${navigationLog.join(' → ')}`);
      console.log(`Final URL: ${finalPath}`);
      console.log(`404 Error: ${found404 ? '❌ Yes (BUG!)' : '✅ No'}`);
      console.log(`Shows "Not Found": ${finalContent.includes('"detail":"Not Found"') ? '❌ Yes (BUG!)' : '✅ No'}`);
      
      // Analyze the result
      if (!found404 && !finalContent.includes('"detail":"Not Found"')) {
        console.log('\n✅ FIX CONFIRMED!');
        console.log('The cancel button works correctly:');
        
        if (navigationLog.includes('/lobby') && finalPath === '/') {
          console.log('  - Navigated to /lobby');
          console.log('  - Redirected to / (start page) due to missing playerName');
          console.log('  - This is the expected behavior!');
        } else if (finalPath === '/lobby') {
          console.log('  - Successfully stayed in /lobby');
          console.log('  - PlayerName was preserved');
        } else if (finalPath === '/') {
          console.log('  - Navigated directly to start page');
          console.log('  - This is also acceptable');
        }
        
        console.log('\n✅ No more {"detail":"Not Found"} error!');
      } else {
        console.log('\n❌ Bug still present');
      }
      
    } else {
      console.log('❌ No Cancel button found');
    }
    
    console.log('\n✅ Test complete.');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
  
  await browser.close();
}

testCancelFixFinal().catch(console.error);