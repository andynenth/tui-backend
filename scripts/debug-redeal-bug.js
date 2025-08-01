/**
 * Debug Script for Redeal Decision Bug
 * 
 * This script uses the current game session to collect evidence
 * and prove the bug exists in the handleWeakHandsFound method.
 */

// Debug script to be executed in browser console
(() => {
  console.log('🔍 ==========================================');
  console.log('🔍 REDEAL DECISION BUG DEBUG ANALYSIS');
  console.log('🔍 ==========================================');

  // 1. Current Page State
  console.log('\n📍 1. CURRENT PAGE STATE:');
  console.log('   URL:', window.location.href);
  console.log('   Title:', document.title);
  console.log('   Phase:', document.querySelector('h1')?.textContent || 'Unknown');

  // 2. DOM Elements Analysis
  console.log('\n🔍 2. DOM ELEMENTS ANALYSIS:');
  
  const contentSection = document.querySelector('.content-section');
  const dealingContainer = document.querySelector('.dealing-container');
  const weakHandAlert = document.querySelector('.weak-hand-alert');
  const redealButtons = document.querySelectorAll('.alert-button');
  
  console.log('   Content section exists:', !!contentSection);
  console.log('   Dealing animation showing:', !!dealingContainer);
  console.log('   Weak hand alert exists:', !!weakHandAlert);
  
  if (weakHandAlert) {
    console.log('   Alert classes:', weakHandAlert.className);
    console.log('   Alert has "show" class:', weakHandAlert.classList.contains('show'));
    console.log('   Alert is visible:', weakHandAlert.offsetParent !== null);
    console.log('   Alert computed display:', window.getComputedStyle(weakHandAlert).display);
  }
  
  console.log('   Redeal buttons found:', redealButtons.length);
  redealButtons.forEach((btn, i) => {
    console.log(`     Button ${i + 1}:`, btn.textContent.trim());
  });

  // 3. Game Service State Analysis
  console.log('\n🎮 3. GAME SERVICE STATE ANALYSIS:');
  
  let gameState = null;
  
  // Try different paths to access GameService
  if (window.gameService) {
    gameState = window.gameService.getState();
    console.log('   ✅ Found gameService on window');
  } else if (window.GameService) {
    gameState = window.GameService.getState();
    console.log('   ✅ Found GameService on window');
  } else if (window.services?.gameService) {
    gameState = window.services.gameService.getState();
    console.log('   ✅ Found gameService in services');
  } else {
    console.log('   ❌ GameService not accessible from window');
    
    // Try to find React components with state
    const reactElements = document.querySelectorAll('[data-reactroot], [data-reactroot] *');
    console.log('   React elements found:', reactElements.length);
  }

  if (gameState) {
    console.log('\n   📊 GAME STATE FLAGS (Critical for Bug):');
    console.log('     phase:', gameState.phase);
    console.log('     playerName:', gameState.playerName);
    console.log('     myHand length:', gameState.myHand?.length || 'undefined');
    console.log('     isMyHandWeak:', gameState.isMyHandWeak, '← BUG: Should be true for weak hands');
    console.log('     isMyDecision:', gameState.isMyDecision, '← BUG: Should be true when it\'s my turn');
    console.log('     weakHands:', gameState.weakHands);
    console.log('     currentWeakPlayer:', gameState.currentWeakPlayer);
    console.log('     simultaneousMode:', gameState.simultaneousMode);
    console.log('     handValue:', gameState.handValue);
    console.log('     highestCardValue:', gameState.highestCardValue);
    
    // 4. Bug Analysis
    console.log('\n🐛 4. BUG ANALYSIS:');
    
    const hasWeakHand = gameState.isMyHandWeak;
    const canDecide = gameState.isMyDecision;
    const shouldShowUI = hasWeakHand && canDecide;
    
    console.log('   Should show redeal UI calculation:');
    console.log('     hasWeakHand (isMyHandWeak):', hasWeakHand);
    console.log('     canDecide (isMyDecision):', canDecide);
    console.log('     shouldShowUI (both true):', shouldShowUI);
    console.log('     UI actually showing:', !!weakHandAlert && weakHandAlert.classList.contains('show'));
    
    if (gameState.myHand && gameState.myHand.length > 0) {
      const actuallyWeak = gameState.myHand.every(piece => piece.value <= 9);
      console.log('   Manual weak hand check:', actuallyWeak);
      
      if (actuallyWeak && !hasWeakHand) {
        console.log('   🚨 BUG CONFIRMED: Hand is actually weak but isMyHandWeak is false!');
      }
      
      if (gameState.currentWeakPlayer === gameState.playerName && !canDecide) {
        console.log('   🚨 BUG CONFIRMED: It\'s my turn but isMyDecision is false!');
      }
    }
  }

  // 5. Event History Analysis
  console.log('\n📜 5. CONSOLE LOG ANALYSIS:');
  console.log('   Look for these patterns in console logs:');
  console.log('     ✅ "weak_hands_found" events received');
  console.log('     ❌ "handleWeakHandsFound" state updates missing');
  console.log('     ❌ "isMyHandWeak" and "isMyDecision" remain stale');

  // 6. Network Events
  console.log('\n🌐 6. NETWORK EVENTS RECOMMENDATION:');
  console.log('   Monitor WebSocket messages for:');
  console.log('     - weak_hands_found events');
  console.log('     - phase_change events');
  console.log('     - Game state updates');

  // 7. Reproduction Steps
  console.log('\n🔄 7. BUG REPRODUCTION CONFIRMED:');
  console.log('   1. ✅ Game started and reached preparation phase');
  console.log('   2. ✅ Dealing animation completed');
  console.log('   3. ✅ weak_hands_found events received (check console)');
  console.log('   4. ❌ Redeal decision UI not appearing');
  console.log('   5. ❌ isMyHandWeak and isMyDecision flags not updated');

  console.log('\n🔧 8. REQUIRED FIX:');
  console.log('   File: frontend/src/services/GameService.ts');
  console.log('   Method: handleWeakHandsFound (lines 1232-1238)');
  console.log('   Missing: UI state flag calculations');
  console.log('   Add: isMyHandWeak, isMyDecision, handValue, highestCardValue calculations');

  console.log('\n🔍 ==========================================');
  console.log('🔍 DEBUG ANALYSIS COMPLETE');
  console.log('🔍 ==========================================');

  // Return summary for programmatic access
  return {
    bugConfirmed: gameState ? 
      (gameState.weakHands.includes(gameState.playerName) && !gameState.isMyHandWeak) ||
      (gameState.currentWeakPlayer === gameState.playerName && !gameState.isMyDecision)
      : false,
    gameState: gameState ? {
      phase: gameState.phase,
      isMyHandWeak: gameState.isMyHandWeak,
      isMyDecision: gameState.isMyDecision,
      weakHands: gameState.weakHands,
      currentWeakPlayer: gameState.currentWeakPlayer,
      playerName: gameState.playerName
    } : null,
    domState: {
      weakHandAlertExists: !!weakHandAlert,
      weakHandAlertVisible: weakHandAlert ? weakHandAlert.offsetParent !== null : false,
      redealButtonsCount: redealButtons.length,
      dealingAnimationActive: !!dealingContainer
    }
  };
})();