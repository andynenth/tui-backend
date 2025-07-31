const { chromium } = require('playwright');

async function testManualFlow() {
  console.log('🔍 Manual Game Flow Test with Longer Waits\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: false
  });

  const page = await browser.newPage();
  
  try {
    console.log('📍 Step 1: Navigate to application');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    console.log('  ✓ Page loaded');
    
    console.log('\n📍 Step 2: Enter player name');
    await page.fill('input[type="text"]', 'ManualTestPlayer');
    console.log('  ✓ Filled player name');
    
    console.log('\n📍 Step 3: Click Enter Lobby');
    await page.click('button:has-text("Enter Lobby")');
    console.log('  ✓ Clicked Enter Lobby');
    
    // Wait longer for lobby load
    await page.waitForTimeout(5000);
    
    let currentUrl = page.url();
    console.log(`  URL after lobby: ${currentUrl}`);
    
    let pageText = await page.textContent('body');
    console.log(`  Contains "Create Room": ${pageText.includes('Create Room')}`);
    
    if (pageText.includes('Create Room')) {
      console.log('\n📍 Step 4: Create room');
      await page.click('button:has-text("Create Room")');
      console.log('  ✓ Clicked Create Room');
      
      // Wait much longer for room creation
      await page.waitForTimeout(8000);
      
      currentUrl = page.url();
      pageText = await page.textContent('body');
      
      console.log(`  URL after room creation: ${currentUrl}`);
      console.log(`  Contains "Start": ${pageText.includes('Start')}`);
      console.log(`  URL includes /room/: ${currentUrl.includes('/room/')}`);
      
      if (currentUrl.includes('/room/') && pageText.includes('Start')) {
        console.log('✅ Successfully in room page with Start button available');
        
        console.log('\n📍 Step 5: Start game');
        await page.click('button:has-text("Start")');
        console.log('  ✓ Clicked Start button');
        
        // Wait for game start
        await page.waitForTimeout(5000);
        
        const finalUrl = page.url();
        const finalText = await page.textContent('body');
        
        console.log(`  Final URL: ${finalUrl}`);
        console.log(`  Contains "Waiting for game to start": ${finalText.includes('Waiting for game to start')}`);
        console.log(`  Contains "Declaration": ${finalText.includes('Declaration')}`);
        
        if (finalUrl.includes('/game/')) {
          console.log('✅ Successfully navigated to game page');
          
          if (finalText.includes('Waiting for game to start')) {
            console.log('⚠️ Still on waiting page - this was the original issue');
          } else if (finalText.includes('Declaration') || finalText.includes('Choose')) {
            console.log('🎉 SUCCESS: Game progressed beyond waiting page!');
          } else {
            console.log('🤔 Unknown game state');
            console.log('  Page content:', finalText.substring(0, 300));
          }
        } else {
          console.log('❌ Did not navigate to game page');
        }
        
      } else {
        console.log('❌ Room creation failed or Start button not available');
      }
    } else {
      console.log('❌ Not in lobby - Create Room button not found');
    }
    
    console.log('\n✅ Test complete. Leaving browser open for manual inspection...');
    console.log('You can now manually test the flow in the browser.');
    await page.waitForTimeout(60000); // Wait 60 seconds for manual inspection
    await browser.close();
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await browser.close();
  }
}

testManualFlow();