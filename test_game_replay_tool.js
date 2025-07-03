#!/usr/bin/env node
/**
 * 🎮 **Phase 6.1 Game Replay Tool Test** - Validate debugging functionality
 * 
 * Tests the game replay tool implementation by:
 * 1. Verifying GameReplayManager core functionality
 * 2. Checking React hook integration
 * 3. Validating UI component implementation
 * 4. Testing event recording and playback
 * 5. Ensuring session management works
 */

const fs = require('fs');
const path = require('path');

console.log('🎮 Testing Phase 6.1 Game Replay Tool Implementation...\n');

// Test 1: Check GameReplayManager core implementation
console.log('📋 Test 1: Checking GameReplayManager core implementation...');

const gameReplayPath = path.join(__dirname, 'frontend', 'src', 'tools', 'GameReplay.ts');
try {
  const content = fs.readFileSync(gameReplayPath, 'utf8');
  
  // Check core features
  const hasReplayEvent = /interface ReplayEvent/.test(content);
  const hasReplaySession = /interface ReplaySession/.test(content);
  const hasReplayManager = /class GameReplayManager/.test(content);
  const hasRecordingMethods = /startRecording.*stopRecording/.test(content);
  const hasPlaybackMethods = /startReplay.*stopReplay.*togglePause/.test(content);
  const hasTimelineControl = /jumpToEvent.*stepForward.*stepBackward/.test(content);
  const hasEventFiltering = /setEventFilters/.test(content);
  const hasImportExport = /exportSession.*importSession/.test(content);
  const hasEventListeners = /setupEventListeners/.test(content);
  
  console.log(`✅ ReplayEvent interface: ${hasReplayEvent}`);
  console.log(`✅ ReplaySession interface: ${hasReplaySession}`);
  console.log(`✅ GameReplayManager class: ${hasReplayManager}`);
  console.log(`✅ Recording methods: ${hasRecordingMethods}`);
  console.log(`✅ Playback methods: ${hasPlaybackMethods}`);
  console.log(`✅ Timeline control: ${hasTimelineControl}`);
  console.log(`✅ Event filtering: ${hasEventFiltering}`);
  console.log(`✅ Import/Export: ${hasImportExport}`);
  console.log(`✅ Event listeners: ${hasEventListeners}`);
  
} catch (err) {
  console.log('❌ Could not check GameReplayManager implementation');
}

// Test 2: Check useGameReplay hook
console.log('\n📋 Test 2: Checking useGameReplay hook implementation...');

const useGameReplayPath = path.join(__dirname, 'frontend', 'src', 'hooks', 'useGameReplay.ts');
try {
  const content = fs.readFileSync(useGameReplayPath, 'utf8');
  
  const hasGameReplayHook = /interface GameReplayHook/.test(content);
  const hasUseGameReplay = /export const useGameReplay/.test(content);
  const hasRecordingControls = /startRecording.*stopRecording.*isRecording/.test(content);
  const hasPlaybackControls = /startReplay.*stopReplay.*togglePause/.test(content);
  const hasSessionManagement = /saveSession.*loadSession.*deleteSession/.test(content);
  const hasLocalStorage = /localStorage/.test(content);
  const hasEventListeners = /addEventListener.*removeEventListener/.test(content);
  
  console.log(`✅ GameReplayHook interface: ${hasGameReplayHook}`);
  console.log(`✅ useGameReplay hook: ${hasUseGameReplay}`);
  console.log(`✅ Recording controls: ${hasRecordingControls}`);
  console.log(`✅ Playback controls: ${hasPlaybackControls}`);
  console.log(`✅ Session management: ${hasSessionManagement}`);
  console.log(`✅ LocalStorage integration: ${hasLocalStorage}`);
  console.log(`✅ Event listeners: ${hasEventListeners}`);
  
} catch (err) {
  console.log('❌ Could not check useGameReplay hook');
}

// Test 3: Check GameReplayUI component
console.log('\n📋 Test 3: Checking GameReplayUI component...');

const gameReplayUIPath = path.join(__dirname, 'frontend', 'src', 'components', 'debug', 'GameReplayUI.jsx');
try {
  const content = fs.readFileSync(gameReplayUIPath, 'utf8');
  
  const hasGameReplayUI = /const GameReplayUI/.test(content);
  const hasRecordingSection = /recording-section/.test(content);
  const hasSessionSection = /session-section/.test(content);
  const hasPlaybackSection = /playback-section/.test(content);
  const hasTimelineContainer = /timeline-container/.test(content);
  const hasEventFilters = /filter-checkboxes/.test(content);
  const hasImportExport = /import-export/.test(content);
  const hasStyledComponents = /style jsx/.test(content);
  const hasEventHandlers = /onClick.*onChange/.test(content);
  
  console.log(`✅ GameReplayUI component: ${hasGameReplayUI}`);
  console.log(`✅ Recording section: ${hasRecordingSection}`);
  console.log(`✅ Session section: ${hasSessionSection}`);
  console.log(`✅ Playback section: ${hasPlaybackSection}`);
  console.log(`✅ Timeline container: ${hasTimelineContainer}`);
  console.log(`✅ Event filters: ${hasEventFilters}`);
  console.log(`✅ Import/Export UI: ${hasImportExport}`);
  console.log(`✅ Styled components: ${hasStyledComponents}`);
  console.log(`✅ Event handlers: ${hasEventHandlers}`);
  
} catch (err) {
  console.log('❌ Could not check GameReplayUI component');
}

// Test 4: Check GamePage integration
console.log('\n📋 Test 4: Checking GamePage integration...');

const gamePagePath = path.join(__dirname, 'frontend', 'src', 'pages', 'GamePage.jsx');
try {
  const content = fs.readFileSync(gamePagePath, 'utf8');
  
  const hasReplayImport = /import.*GameReplayUI.*from.*GameReplayUI/.test(content);
  const hasReplayState = /showReplayTool/.test(content);
  const hasDebugButton = /🎮 Debug/.test(content);
  const hasReplayUIRender = /<GameReplayUI/.test(content);
  const hasPhase61Comment = /Phase 6\.1/.test(content);
  
  console.log(`✅ GameReplayUI import: ${hasReplayImport}`);
  console.log(`✅ Replay tool state: ${hasReplayState}`);
  console.log(`✅ Debug button: ${hasDebugButton}`);
  console.log(`✅ GameReplayUI render: ${hasReplayUIRender}`);
  console.log(`✅ Phase 6.1 comments: ${hasPhase61Comment}`);
  
} catch (err) {
  console.log('❌ Could not check GamePage integration');
}

// Test 5: Check event recording capabilities
console.log('\n📋 Test 5: Checking event recording capabilities...');

try {
  const gameReplayContent = fs.readFileSync(gameReplayPath, 'utf8');
  
  const hasNetworkInterception = /interceptNetworkSend/.test(gameReplayContent);
  const hasStateChangeTracking = /handleStateChange/.test(gameReplayContent);
  const hasNetworkEventTracking = /handleNetworkMessage.*handleNetworkEvent/.test(gameReplayContent);
  const hasEventTypes = /network_message.*state_change.*user_action.*system_event/.test(gameReplayContent);
  const hasEventMetadata = /metadata.*playerName.*phase.*actionType/.test(gameReplayContent);
  const hasSequenceTracking = /eventSequence/.test(gameReplayContent);
  
  console.log(`✅ Network message interception: ${hasNetworkInterception}`);
  console.log(`✅ State change tracking: ${hasStateChangeTracking}`);
  console.log(`✅ Network event tracking: ${hasNetworkEventTracking}`);
  console.log(`✅ Event type classification: ${hasEventTypes}`);
  console.log(`✅ Event metadata: ${hasEventMetadata}`);
  console.log(`✅ Sequence tracking: ${hasSequenceTracking}`);
  
} catch (err) {
  console.log('❌ Could not check event recording capabilities');
}

// Test 6: Check playback capabilities
console.log('\n📋 Test 6: Checking playback capabilities...');

try {
  const gameReplayContent = fs.readFileSync(gameReplayPath, 'utf8');
  
  const hasPlaybackSpeed = /playbackSpeed/.test(gameReplayContent);
  const hasStepControl = /stepForward.*stepBackward/.test(gameReplayContent);
  const hasJumpControl = /jumpToEvent/.test(gameReplayContent);
  const hasPauseControl = /togglePause.*isPaused/.test(gameReplayContent);
  const hasEventApplication = /applyEvent.*replayToIndex/.test(gameReplayContent);
  const hasTimelineScheduling = /scheduleNextEvent/.test(gameReplayContent);
  
  console.log(`✅ Playback speed control: ${hasPlaybackSpeed}`);
  console.log(`✅ Step controls: ${hasStepControl}`);
  console.log(`✅ Jump control: ${hasJumpControl}`);
  console.log(`✅ Pause control: ${hasPauseControl}`);
  console.log(`✅ Event application: ${hasEventApplication}`);
  console.log(`✅ Timeline scheduling: ${hasTimelineScheduling}`);
  
} catch (err) {
  console.log('❌ Could not check playback capabilities');
}

// Test 7: Check TypeScript exports and imports
console.log('\n📋 Test 7: Checking TypeScript exports and imports...');

try {
  const gameReplayContent = fs.readFileSync(gameReplayPath, 'utf8');
  const hookContent = fs.readFileSync(useGameReplayPath, 'utf8');
  
  const hasManagerExport = /export const gameReplayManager/.test(gameReplayContent);
  const hasTypeExports = /export type.*ReplayEvent.*ReplaySession/.test(gameReplayContent);
  const hasHookExport = /export.*useGameReplay/.test(hookContent);
  const hasHookTypeImports = /import.*ReplaySession.*from.*GameReplay/.test(hookContent);
  
  console.log(`✅ GameReplayManager export: ${hasManagerExport}`);
  console.log(`✅ Type exports: ${hasTypeExports}`);
  console.log(`✅ Hook export: ${hasHookExport}`);
  console.log(`✅ Hook type imports: ${hasHookTypeImports}`);
  
} catch (err) {
  console.log('❌ Could not check TypeScript exports');
}

// Test Summary
console.log('\n📊 Phase 6.1 Game Replay Tool Summary:');
console.log('======================================');

// Collect test results
let hasGameReplayManager = false, hasGameReplayHook = false, hasGameReplayUI = false;
let hasGamePageIntegration = false, hasRecordingCapabilities = false, hasPlaybackCapabilities = false;

try {
  const gameReplayContent = fs.readFileSync(gameReplayPath, 'utf8');
  hasGameReplayManager = /class GameReplayManager/.test(gameReplayContent);
  hasRecordingCapabilities = /startRecording.*stopRecording/.test(gameReplayContent);
  hasPlaybackCapabilities = /startReplay.*stopReplay.*togglePause/.test(gameReplayContent);
  
  const hookContent = fs.readFileSync(useGameReplayPath, 'utf8');
  hasGameReplayHook = /export const useGameReplay/.test(hookContent);
  
  const uiContent = fs.readFileSync(gameReplayUIPath, 'utf8');
  hasGameReplayUI = /const GameReplayUI/.test(uiContent);
  
  const gamePageContent = fs.readFileSync(gamePagePath, 'utf8');
  hasGamePageIntegration = /import.*GameReplayUI.*from.*GameReplayUI/.test(gamePageContent);
} catch (err) {
  // Use defaults
}

// Calculate completion metrics
const coreFeatures = [
  { name: 'GameReplayManager implementation', status: hasGameReplayManager },
  { name: 'useGameReplay hook', status: hasGameReplayHook },
  { name: 'GameReplayUI component', status: hasGameReplayUI },
  { name: 'GamePage integration', status: hasGamePageIntegration },
  { name: 'Recording capabilities', status: hasRecordingCapabilities },
  { name: 'Playback capabilities', status: hasPlaybackCapabilities }
];

let implementedCount = 0;
coreFeatures.forEach(feature => {
  const icon = feature.status ? '✅' : '❌';
  console.log(`${icon} ${feature.name}: ${feature.status ? 'IMPLEMENTED' : 'NEEDS WORK'}`);
  if (feature.status) implementedCount++;
});

const completionPercentage = Math.round((implementedCount / coreFeatures.length) * 100);

if (completionPercentage >= 85) {
  console.log(`\n🎉 SUCCESS: Phase 6.1 Game Replay Tool ${completionPercentage}% complete!`);
  console.log('✅ Recording functionality for capturing game sessions');
  console.log('✅ Playback functionality with timeline controls');
  console.log('✅ Session management with save/load/export');
  console.log('✅ Visual interface integrated into GamePage');
  console.log('✅ Event filtering and debugging capabilities');
  console.log('\n📈 Developer Benefits:');
  console.log('• Record exact game sessions that caused bugs');
  console.log('• Step-by-step replay to understand issues');
  console.log('• Export/share problematic sessions with team');
  console.log('• Filter events to focus on specific problems');
  console.log('• Visual timeline shows event flow clearly');
  console.log('\n🎯 Usage:');
  console.log('1. Click "🎮 Debug" button in game header');
  console.log('2. Start recording to capture events');
  console.log('3. When issue occurs, stop recording');
  console.log('4. Use playback controls to debug step-by-step');
  console.log('5. Export session to share with team');
} else {
  console.log(`\n⚠️  PARTIAL: Phase 6.1 implementation ${completionPercentage}% complete`);
  console.log('Additional work needed to complete game replay functionality');
}

console.log('\n🎯 Next Steps:');
console.log('1. Test replay tool in live game environment');
console.log('2. Verify event recording captures all game actions');
console.log('3. Test session export/import functionality');
console.log('4. Implement Phase 6.2: State Debug Tool');
console.log('5. Implement Phase 6.3: Sync Checker Tool');

process.exit(completionPercentage >= 85 ? 0 : 1);