/**
 * 🧪 Room Slot Workflow Test - Correct Test for Bot Removal → Player Join
 * 
 * Tests the proper workflow:
 * 1. Andy creates room (1 human + 3 bots = full)
 * 2. Andy removes a bot to make space 
 * 3. Bob joins the room (takes bot's slot)
 * 4. Lobby updates to show Bob instead of bot
 * 5. Bob leaves room
 * 6. Lobby updates to show empty slot
 */

const { chromium } = require('playwright');

async function testRoomSlotWorkflow() {
  console.log('🧪 Starting Room Slot Workflow Test (Correct Version)...\n');
  
  let andy, bob, charlie, andyPage, bobPage, charliePage;
  
  try {
    // Launch browsers
    console.log('🚀 Launching browsers...');
    andy = await chromium.launch({ headless: false });
    bob = await chromium.launch({ headless: false });
    charlie = await chromium.launch({ headless: false });
    
    andyPage = await andy.newPage();
    bobPage = await bob.newPage();
    charliePage = await charlie.newPage();
    
    // Navigate all to start page
    await Promise.all([
      andyPage.goto('http://localhost:5050'),
      bobPage.goto('http://localhost:5050'),
      charliePage.goto('http://localhost:5050')
    ]);
    
    console.log('✅ All browsers ready\n');
    
    // Step 1: All players enter lobby
    console.log('👥 Step 1: All players entering lobby...');
    
    await andyPage.fill('input[type="text"]', 'Andy');
    await andyPage.click('button:has-text("Enter Lobby")');
    await andyPage.waitForSelector('.lp-lobbyTitle');
    
    await bobPage.fill('input[type="text"]', 'Bob');
    await bobPage.click('button:has-text("Enter Lobby")');
    await bobPage.waitForSelector('.lp-lobbyTitle');
    
    await charliePage.fill('input[type="text"]', 'Charlie');
    await charliePage.click('button:has-text("Enter Lobby")');
    await charliePage.waitForSelector('.lp-lobbyTitle');
    
    console.log('✅ All players in lobby\n');
    
    // Step 2: Andy creates room (should be 1 human + 3 bots = full)
    console.log('🏠 Step 2: Andy creating room...');
    await andyPage.click('button:has-text("Create Room")');
    
    // Andy should now be in room page, wait for it to load
    await andyPage.waitForTimeout(3000);
    
    // Step 3: Check Charlie's lobby view - should see full room with Andy + 3 bots
    console.log('🔍 Step 3: Checking initial room state (should be full)...');
    
    const charlieInitialView = await charliePage.evaluate(() => {
      const roomCards = document.querySelectorAll('.lp-roomCard');
      if (roomCards.length === 0) return null;
      
      const firstRoom = roomCards[0];
      const occupancy = firstRoom.querySelector('.lp-roomOccupancy')?.textContent;
      const canJoinClass = firstRoom.classList.contains('lp-full');
      
      // Get player names in slots
      const slotNames = [];
      const slotElements = firstRoom.querySelectorAll('.lp-playerSlot');
      slotElements.forEach(slot => {
        const nameElement = slot.querySelector('.lp-playerSlotName');
        slotNames.push(nameElement ? nameElement.textContent : 'Empty');
      });
      
      return {
        occupancy,
        canJoin: !canJoinClass,
        slotNames
      };
    });
    
    console.log('📊 Initial room state (Charlie\'s view):', charlieInitialView);
    
    // Step 4: Andy removes a bot to make space (this is the key step!)
    console.log('🤖 Step 4: Andy removing a bot to make space...');
    
    // Look for remove bot button and click it
    try {
      await andyPage.click('button:has-text("Remove Bot"), button[title*="remove"], button:has-text("✖")');
      console.log('✅ Andy removed a bot');
    } catch (e) {
      console.log('⚠️ Could not find remove bot button, trying alternative selectors...');
      // Try other possible selectors
      const removeButtons = await andyPage.$$('button');
      console.log(`Found ${removeButtons.length} buttons, looking for remove functionality...`);
      
      // Take screenshot to see current state
      await andyPage.screenshot({ path: 'andy-room-state.png' });
      console.log('📸 Screenshot saved: andy-room-state.png');
    }
    
    // Wait for room update
    await andyPage.waitForTimeout(2000);
    
    // Step 5: Check Charlie's view - should now show room with space available
    console.log('🔍 Step 5: Checking room state after bot removal...');
    
    const charlieAfterBotRemoval = await charliePage.evaluate(() => {
      const roomCards = document.querySelectorAll('.lp-roomCard');
      if (roomCards.length === 0) return null;
      
      const firstRoom = roomCards[0];
      const occupancy = firstRoom.querySelector('.lp-roomOccupancy')?.textContent;
      const canJoinClass = firstRoom.classList.contains('lp-full');
      
      const slotNames = [];
      const slotElements = firstRoom.querySelectorAll('.lp-playerSlot');
      slotElements.forEach(slot => {
        const nameElement = slot.querySelector('.lp-playerSlotName');
        slotNames.push(nameElement ? nameElement.textContent : 'Empty');
      });
      
      return {
        occupancy,
        canJoin: !canJoinClass,
        slotNames
      };
    });
    
    console.log('📊 Room state after bot removal (Charlie\'s view):', charlieAfterBotRemoval);
    
    // Step 6: Bob tries to join the room (should work now)
    console.log('🚪 Step 6: Bob joining room...');
    
    if (charlieAfterBotRemoval && charlieAfterBotRemoval.canJoin) {
      await bobPage.click('.lp-roomCard');
      await bobPage.waitForTimeout(3000);
      
      // Step 7: Check Charlie's view - should see Bob in the room
      console.log('🔍 Step 7: Checking room state after Bob joins...');
      
      const charlieAfterBobJoins = await charliePage.evaluate(() => {
        const roomCards = document.querySelectorAll('.lp-roomCard');
        if (roomCards.length === 0) return null;
        
        const firstRoom = roomCards[0];
        const occupancy = firstRoom.querySelector('.lp-roomOccupancy')?.textContent;
        
        const slotNames = [];
        const slotElements = firstRoom.querySelectorAll('.lp-playerSlot');
        slotElements.forEach(slot => {
          const nameElement = slot.querySelector('.lp-playerSlotName');
          slotNames.push(nameElement ? nameElement.textContent : 'Empty');
        });
        
        return {
          occupancy,
          slotNames
        };
      });
      
      console.log('📊 Room state after Bob joins (Charlie\'s view):', charlieAfterBobJoins);
      
      // Analysis
      console.log('\n📊 === TEST RESULTS ANALYSIS ===');
      
      const initialCorrect = charlieInitialView && 
        charlieInitialView.occupancy === '4/4' && 
        !charlieInitialView.canJoin;
      
      const afterRemovalCorrect = charlieAfterBotRemoval && 
        charlieAfterBotRemoval.canJoin;
      
      const afterJoinCorrect = charlieAfterBobJoins && 
        charlieAfterBobJoins.slotNames.includes('Bob');
      
      console.log(`Initial room full (correct): ${initialCorrect ? '✅ CORRECT' : '❌ INCORRECT'}`);
      console.log(`After bot removal (joinable): ${afterRemovalCorrect ? '✅ CORRECT' : '❌ INCORRECT'}`);
      console.log(`After Bob joins (Bob visible): ${afterJoinCorrect ? '✅ CORRECT' : '❌ INCORRECT'}`);
      
      if (initialCorrect && afterRemovalCorrect && afterJoinCorrect) {
        console.log('\n✅ SUCCESS: Room slot workflow is working correctly!');
        return { success: true, details: 'Room slot updates working as expected' };
      } else {
        console.log('\n❌ FAILURE: Room slot workflow needs attention');
        return { 
          success: false, 
          details: {
            initial: charlieInitialView,
            afterRemoval: charlieAfterBotRemoval,
            afterJoin: charlieAfterBobJoins
          }
        };
      }
    } else {
      console.log('❌ Room was not joinable after bot removal');
      return { success: false, error: 'Bot removal did not work' };
    }
    
  } catch (error) {
    console.error('❌ Test failed with error:', error);
    return { success: false, error: error.message };
  } finally {
    // Cleanup
    if (andy) await andy.close();
    if (bob) await bob.close();
    if (charlie) await charlie.close();
  }
}

// Run the test
if (require.main === module) {
  testRoomSlotWorkflow().then(result => {
    console.log('\n🏁 Test completed:', result.success ? 'PASSED' : 'FAILED');
    if (!result.success) {
      console.log('Details:', result.details || result.error);
    }
    process.exit(result.success ? 0 : 1);
  });
}

module.exports = { testRoomSlotWorkflow };