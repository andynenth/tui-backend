// Debug script to check redeal decision state
console.log('=== REDEAL DEBUG EVIDENCE ===');

// Check if dealing animation is still showing
const dealingContainer = document.querySelector('.dealing-container');
console.log('1. Dealing animation showing:', !!dealingContainer);

// Check if weak hand alert exists
const weakHandAlert = document.querySelector('.weak-hand-alert');
console.log('2. Weak hand alert exists:', !!weakHandAlert);

// Check if alert has "show" class
if (weakHandAlert) {
  console.log('3. Alert classes:', weakHandAlert.className);
  console.log('4. Alert visible (has show class):', weakHandAlert.classList.contains('show'));
}

// Check for redeal buttons
const redealButtons = document.querySelectorAll('.alert-button');
console.log('5. Redeal buttons found:', redealButtons.length);

// Log current phase
const phaseHeading = document.querySelector('h1');
console.log('6. Current phase:', phaseHeading ? phaseHeading.textContent : 'Not found');

// Try to access React state through debug info
const contentSection = document.querySelector('.content-section');
if (contentSection) {
  console.log('7. Content section innerHTML length:', contentSection.innerHTML.length);
  console.log('8. Content section classes:', contentSection.className);
}

console.log('=== END REDEAL DEBUG ===');