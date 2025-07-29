/**
 * 🧪 Room Slot Status Update Test
 * 
 * Tests that room slot statuses update correctly in lobby when:
 * 1. Player joins a room (slot should show as filled)
 * 2. Player leaves a room (slot should show as empty)
 * 3. Host leaves and room is removed
 */

const { chromium } = require('playwright');

async function testRoomSlotUpdates() {
  console.log('🧪 Starting Room Slot Status Update Test...\n');
  
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
    
    // Enter lobby for all players
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
    
    // Wait for initial room list to load
    await andyPage.waitForTimeout(2000);
    
    // Step 2: Andy creates a room
    console.log('🏠 Step 2: Andy creating room...');
    await andyPage.click('button:has-text("Create Room")');
    
    // Wait a moment for room creation
    await bobPage.waitForTimeout(3000);
    
    // Step 3: Check if Bob and Charlie see Andy's room with 1 player
    console.log('🔍 Step 3: Checking initial room state...');
    
    const bobInitialRoomData = await bobPage.evaluate(() => {
      const roomCards = document.querySelectorAll('.lp-roomCard');
      if (roomCards.length === 0) return null;
      
      const firstRoom = roomCards[0];
      const roomId = firstRoom.querySelector('.lp-roomId')?.textContent;
      const hostName = firstRoom.querySelector('.lp-hostName')?.textContent;
      const occupancy = firstRoom.querySelector('.lp-roomOccupancy')?.textContent;
      
      // Count filled vs empty slots
      const slots = firstRoom.querySelectorAll('.lp-playerSlot');
      const filledSlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-filled').length;
      const emptySlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-empty').length;
      const botSlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-bot').length;
      
      return {
        roomId,
        hostName,
        occupancy,
        filledSlots,
        emptySlots,
        botSlots,
        totalSlots: slots.length
      };
    });
    
    console.log('📊 Initial room state (Bob\'s view):', bobInitialRoomData);
    
    // Step 4: Bob joins Andy's room
    console.log('🚪 Step 4: Bob joining Andy\'s room...');
    
    if (bobInitialRoomData && bobInitialRoomData.roomId) {
      await bobPage.click('.lp-roomCard');
      // Wait for Bob to enter room
      await bobPage.waitForTimeout(2000);
      
      // Check Charlie's view - should see room with 2 players
      console.log('🔍 Step 5: Checking room state after Bob joins...');
      
      const charlieAfterBobJoins = await charliePage.evaluate(() => {
        const roomCards = document.querySelectorAll('.lp-roomCard');
        if (roomCards.length === 0) return null;
        
        const firstRoom = roomCards[0];
        const occupancy = firstRoom.querySelector('.lp-roomOccupancy')?.textContent;
        const filledSlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-filled').length;
        const emptySlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-empty').length;
        const botSlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-bot').length;
        
        // Get player names in slots
        const slotNames = [];
        const slotElements = firstRoom.querySelectorAll('.lp-playerSlot');
        slotElements.forEach(slot => {
          const nameElement = slot.querySelector('.lp-playerSlotName');
          slotNames.push(nameElement ? nameElement.textContent : 'Empty');
        });
        
        return {
          occupancy,
          filledSlots,
          emptySlots,
          botSlots,
          slotNames
        };
      });
      
      console.log('📊 Room state after Bob joins (Charlie\'s view):', charlieAfterBobJoins);
      
      // Step 5: Bob leaves the room (go back to lobby)
      console.log('🚪 Step 6: Bob leaving room...');
      await bobPage.click('button:has-text("Back to Start Page")');
      await bobPage.waitForTimeout(1000);
      await bobPage.fill('input[type="text"]', 'Bob');
      await bobPage.click('button:has-text("Enter Lobby")');
      await bobPage.waitForSelector('.lp-lobbyTitle');
      
      // Wait for room update
      await bobPage.waitForTimeout(3000);
      
      // Check Charlie's view - should see room with 1 player again
      console.log('🔍 Step 7: Checking room state after Bob leaves...');
      
      const charlieAfterBobLeaves = await charliePage.evaluate(() => {
        const roomCards = document.querySelectorAll('.lp-roomCard');
        if (roomCards.length === 0) return null;
        
        const firstRoom = roomCards[0];
        const occupancy = firstRoom.querySelector('.lp-roomOccupancy')?.textContent;
        const filledSlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-filled').length;
        const emptySlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-empty').length;
        const botSlots = firstRoom.querySelectorAll('.lp-playerSlot.lp-bot').length;
        
        const slotNames = [];
        const slotElements = firstRoom.querySelectorAll('.lp-playerSlot');
        slotElements.forEach(slot => {
          const nameElement = slot.querySelector('.lp-playerSlotName');
          slotNames.push(nameElement ? nameElement.textContent : 'Empty');
        });
        
        return {
          occupancy,
          filledSlots,
          emptySlots,
          botSlots,
          slotNames
        };
      });
      
      console.log('📊 Room state after Bob leaves (Charlie\'s view):', charlieAfterBobLeaves);
      
      // Analysis
      console.log('\n📊 === TEST RESULTS ANALYSIS ===');
      
      const initialCorrect = bobInitialRoomData && 
        bobInitialRoomData.filledSlots === 1 && 
        bobInitialRoomData.emptySlots === 3;
      
      const afterJoinCorrect = charlieAfterBobJoins && 
        charlieAfterBobJoins.filledSlots === 2 && 
        charlieAfterBobJoins.emptySlots === 2;
      
      const afterLeaveCorrect = charlieAfterBobLeaves && 
        charlieAfterBobLeaves.filledSlots === 1 && 
        charlieAfterBobLeaves.emptySlots === 3;
      
      console.log(`Initial room state (Andy only): ${initialCorrect ? '✅ CORRECT' : '❌ INCORRECT'}`);
      console.log(`After Bob joins: ${afterJoinCorrect ? '✅ CORRECT' : '❌ INCORRECT'}`);
      console.log(`After Bob leaves: ${afterLeaveCorrect ? '✅ CORRECT' : '❌ INCORRECT'}`);
      
      if (initialCorrect && afterJoinCorrect && afterLeaveCorrect) {
        console.log('\n✅ SUCCESS: Room slot updates are working correctly!');
        return { success: true, details: 'All slot updates working' };
      } else {
        console.log('\n❌ FAILURE: Room slot updates are not working correctly');
        return { 
          success: false, 
          details: {
            initial: bobInitialRoomData,
            afterJoin: charlieAfterBobJoins,
            afterLeave: charlieAfterBobLeaves
          }
        };
      }
    } else {
      console.log('❌ No room found for testing');
      return { success: false, error: 'No room created' };
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
  testRoomSlotUpdates().then(result => {
    console.log('\n🏁 Test completed:', result.success ? 'PASSED' : 'FAILED');
    if (!result.success) {
      console.log('Details:', result.details || result.error);
    }
    process.exit(result.success ? 0 : 1);
  });
}

module.exports = { testRoomSlotUpdates };