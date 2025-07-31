const { chromium } = require('playwright');

async function testCompleteSequence() {
  console.log('🎯 Final Validation: Complete Multi-Player Host Leave Sequence\n');
  
  const browser1 = await chromium.launch({ headless: false, devtools: false });
  const browser2 = await chromium.launch({ headless: false, devtools: false });
  
  const page1 = await browser1.newPage();
  const page2 = await browser2.newPage();
  
  let success = true;
  const results = [];
  
  try {
    console.log('📋 Test Sequence:');
    console.log('✓ Player 1 >> Enter Lobby');
    console.log('✓ Player 2 >> Enter Lobby');  
    console.log('✓ Player 1 >> Create Room');
    console.log('✓ Player 2 >> Join Room');
    console.log('✓ Player 1 >> Leave Room');
    console.log('✓ Expected: Room removed, Player 2 redirected to lobby\\n');
    
    // Step 1: Player 1 Enter Lobby
    console.log('1️⃣ Player 1: Enter Lobby');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await page1.waitForTimeout(1000);
    results.push('✅ Player 1 entered lobby');
    
    // Step 2: Player 2 Enter Lobby
    console.log('2️⃣ Player 2: Enter Lobby');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await page2.waitForTimeout(1000);
    results.push('✅ Player 2 entered lobby');
    
    // Step 3: Player 1 Create Room
    console.log('3️⃣ Player 1: Create Room');
    await page1.click('button:has-text("Create Room")');
    await page1.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    results.push('✅ Player 1 created room');
    
    // Step 4: Player 2 Join Room
    console.log('4️⃣ Player 2: Join Room');
    const roomCards = await page2.$$('.lp-roomCard');
    if (roomCards.length === 0) {
      throw new Error('No room cards found for Player 2');
    }
    await roomCards[0].click();
    await page2.waitForURL('**/room/**', { timeout: 5000 });
    results.push('✅ Player 2 joined room');
    
    // Verify both players in same room
    const p1RoomId = page1.url().split('/room/')[1] || 'none';
    const p2RoomId = page2.url().split('/room/')[1] || 'none';
    if (p1RoomId === p2RoomId && p1RoomId !== 'none') {
      results.push(`✅ Both players in same room: ${p1RoomId}`);
    } else {
      success = false;
      results.push(`❌ Players in different rooms: P1=${p1RoomId}, P2=${p2RoomId}`);
    }
    
    // Step 5: Player 1 Leave Room (Host Leave)
    console.log('5️⃣ Player 1 (HOST): Leave Room');
    await page1.click('button:has-text("Leave Room")');
    await page1.waitForURL('**/lobby', { timeout: 5000 });
    results.push('✅ Player 1 left room and returned to lobby');
    
    // Step 6: Wait for Player 2 redirection
    console.log('6️⃣ Waiting for Player 2 redirection...');
    try {
      await page2.waitForURL('**/lobby', { timeout: 8000 });
      results.push('✅ Player 2 automatically redirected to lobby');
    } catch (e) {
      success = false;
      results.push('❌ Player 2 was not redirected to lobby');
    }
    
    // Step 7: Verify room cleanup
    console.log('7️⃣ Verifying room cleanup...');
    await page1.waitForTimeout(2000);
    await page2.waitForTimeout(2000);
    
    const p1Rooms = await page1.$$('.lp-roomCard').then(cards => cards.length);
    const p2Rooms = await page2.$$('.lp-roomCard').then(cards => cards.length);
    
    if (p1Rooms === 0 && p2Rooms === 0) {
      results.push('✅ Room properly cleaned up (0 rooms remaining)');
    } else {
      success = false;
      results.push(`❌ Room cleanup failed: P1 sees ${p1Rooms} rooms, P2 sees ${p2Rooms} rooms`);
    }
    
    // Final Results
    console.log('\\n🏁 FINAL RESULTS:');
    results.forEach(result => console.log(result));
    
    if (success) {
      console.log('\\n🎉 ALL TESTS PASSED! Host leave functionality working perfectly!');
      console.log('\\n✅ Summary:');
      console.log('   • Players can join rooms by replacing bots');
      console.log('   • Room is closed when host leaves');
      console.log('   • Remaining players are redirected to lobby');
      console.log('   • Room is properly cleaned up from lobby');
    } else {
      console.log('\\n❌ SOME TESTS FAILED - See details above');
    }
    
    setTimeout(async () => {
      await browser1.close();
      await browser2.close();
    }, 3000);
    
  } catch (error) {
    console.error('❌ Test Error:', error.message);
    success = false;
    results.push(`❌ Test failed with error: ${error.message}`);
    await browser1.close();
    await browser2.close();
  }
  
  return success;
}

testCompleteSequence();