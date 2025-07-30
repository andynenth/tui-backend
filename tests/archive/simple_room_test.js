/**
 * 🧪 Simple Room Creation Manual Test
 * 
 * Just opens a browser for manual testing
 */

const { chromium } = require('playwright');

async function simpleRoomTest() {
  console.log('🧪 Opening browser for manual room creation test...');
  console.log('👉 Please manually test room creation and report back');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000  // Slow down to see what happens
  });
  
  const page = await browser.newPage();
  
  // Navigate to the app
  await page.goto('http://localhost:5050');
  
  console.log('✅ Browser opened - please manually:');
  console.log('1. Enter your name');
  console.log('2. Click "Enter Lobby"');
  console.log('3. Click "Create Room"');
  console.log('4. Report what happens');
  
  // Keep browser open for manual testing
  console.log('\n⏸️  Browser will stay open for manual testing...');
  console.log('Press Ctrl+C to close when done');
  
  // Wait for user to close manually
  try {
    await page.waitForTimeout(300000); // 5 minutes max
  } catch (e) {
    // User closed or timeout
  }
  
  await browser.close();
  console.log('🏁 Manual test session ended');
}

// Run the test
if (require.main === module) {
  simpleRoomTest().catch(console.error);
}

module.exports = { simpleRoomTest };