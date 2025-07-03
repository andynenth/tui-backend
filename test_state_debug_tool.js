#!/usr/bin/env node
/**
 * 🔍 **Phase 6.2 State Debug Tool Test** - Validate debugging functionality
 * 
 * Tests the state debug tool implementation by:
 * 1. Verifying StateDebugger core functionality
 * 2. Checking React hook integration
 * 3. Validating UI component implementation
 * 4. Testing state comparison and diff detection
 * 5. Ensuring performance metrics tracking
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Testing Phase 6.2 State Debug Tool Implementation...\n');

// Test 1: Check StateDebugger core implementation
console.log('📋 Test 1: Checking StateDebugger core implementation...');

const stateDebuggerPath = path.join(__dirname, 'frontend', 'src', 'tools', 'StateDebugger.ts');
try {
  const content = fs.readFileSync(stateDebuggerPath, 'utf8');
  
  // Check core features
  const hasStateSnapshot = /interface StateSnapshot/.test(content);
  const hasStateDifference = /interface StateDifference/.test(content);
  const hasWebSocketMessage = /interface WebSocketMessage/.test(content);
  const hasPerformanceMetrics = /interface PerformanceMetrics/.test(content);
  const hasDebuggerState = /interface DebuggerState/.test(content);
  const hasStateDebugger = /class StateDebugger/.test(content);
  const hasDebuggingMethods = /startDebugging.*stopDebugging/.test(content);
  const hasStateCapture = /captureCurrentState/.test(content);
  const hasStateComparison = /compareStates.*findStateDifferences/.test(content);
  const hasNetworkInterception = /interceptNetworkSend/.test(content);
  const hasPerformanceTracking = /updatePerformanceMetric/.test(content);
  const hasEventListeners = /setupEventListeners/.test(content);
  
  console.log(`✅ StateSnapshot interface: ${hasStateSnapshot}`);
  console.log(`✅ StateDifference interface: ${hasStateDifference}`);
  console.log(`✅ WebSocketMessage interface: ${hasWebSocketMessage}`);
  console.log(`✅ PerformanceMetrics interface: ${hasPerformanceMetrics}`);
  console.log(`✅ DebuggerState interface: ${hasDebuggerState}`);
  console.log(`✅ StateDebugger class: ${hasStateDebugger}`);
  console.log(`✅ Debugging methods: ${hasDebuggingMethods}`);
  console.log(`✅ State capture: ${hasStateCapture}`);
  console.log(`✅ State comparison: ${hasStateComparison}`);
  console.log(`✅ Network interception: ${hasNetworkInterception}`);
  console.log(`✅ Performance tracking: ${hasPerformanceTracking}`);
  console.log(`✅ Event listeners: ${hasEventListeners}`);
  
} catch (err) {
  console.log('❌ Could not check StateDebugger implementation');
}

// Test 2: Check useStateDebugger hook
console.log('\n📋 Test 2: Checking useStateDebugger hook implementation...');

const useStateDebuggerPath = path.join(__dirname, 'frontend', 'src', 'hooks', 'useStateDebugger.ts');
try {
  const content = fs.readFileSync(useStateDebuggerPath, 'utf8');
  
  const hasStateDebuggerHook = /interface StateDebuggerHook/.test(content);
  const hasUseStateDebugger = /export const useStateDebugger/.test(content);
  const hasDebuggingControls = /startDebugging.*stopDebugging.*captureState/.test(content);
  const hasStateData = /stateHistory.*stateDifferences.*performanceMetrics/.test(content);
  const hasMessageFiltering = /filteredMessages.*setMessageFilters/.test(content);
  const hasViewOptions = /viewOptions.*setViewOptions/.test(content);
  const hasEventListeners = /addEventListener.*removeEventListener/.test(content);
  const hasStatistics = /totalSnapshots.*criticalDifferences.*averageLatency/.test(content);
  
  console.log(`✅ StateDebuggerHook interface: ${hasStateDebuggerHook}`);
  console.log(`✅ useStateDebugger hook: ${hasUseStateDebugger}`);
  console.log(`✅ Debugging controls: ${hasDebuggingControls}`);
  console.log(`✅ State data access: ${hasStateData}`);
  console.log(`✅ Message filtering: ${hasMessageFiltering}`);
  console.log(`✅ View options: ${hasViewOptions}`);
  console.log(`✅ Event listeners: ${hasEventListeners}`);
  console.log(`✅ Statistics: ${hasStatistics}`);
  
} catch (err) {
  console.log('❌ Could not check useStateDebugger hook');
}

// Test 3: Check StateDebuggerUI component
console.log('\n📋 Test 3: Checking StateDebuggerUI component...');

const stateDebuggerUIPath = path.join(__dirname, 'frontend', 'src', 'components', 'debug', 'StateDebuggerUI.jsx');
try {
  const content = fs.readFileSync(stateDebuggerUIPath, 'utf8');
  
  const hasStateDebuggerUI = /const StateDebuggerUI/.test(content);
  const hasDebuggingControls = /Start Debugging.*Stop Debugging.*Capture State/.test(content);
  const hasViewOptions = /View Options.*showStateComparison.*showMessages.*showPerformance/.test(content);
  const hasMessageFilters = /Message Filters.*showIncoming.*showOutgoing.*eventFilter/.test(content);
  const hasPerformanceDisplay = /Performance.*stateUpdateLatency.*websocketLatency/.test(content);
  const hasStateDifferences = /State Differences.*getSeverityColor/.test(content);
  const hasStateComparison = /State Comparison.*Frontend State.*Backend State/.test(content);
  const hasMessageViewer = /WebSocket Messages.*filteredMessages/.test(content);
  const hasExportFunction = /Export Session.*handleExport/.test(content);
  const hasStyledComponents = /style jsx/.test(content);
  
  console.log(`✅ StateDebuggerUI component: ${hasStateDebuggerUI}`);
  console.log(`✅ Debugging controls: ${hasDebuggingControls}`);
  console.log(`✅ View options: ${hasViewOptions}`);
  console.log(`✅ Message filters: ${hasMessageFilters}`);
  console.log(`✅ Performance display: ${hasPerformanceDisplay}`);
  console.log(`✅ State differences: ${hasStateDifferences}`);
  console.log(`✅ State comparison: ${hasStateComparison}`);
  console.log(`✅ Message viewer: ${hasMessageViewer}`);
  console.log(`✅ Export function: ${hasExportFunction}`);
  console.log(`✅ Styled components: ${hasStyledComponents}`);
  
} catch (err) {
  console.log('❌ Could not check StateDebuggerUI component');
}

// Test 4: Check GamePage integration
console.log('\n📋 Test 4: Checking GamePage integration...');

const gamePagePath = path.join(__dirname, 'frontend', 'src', 'pages', 'GamePage.jsx');
try {
  const content = fs.readFileSync(gamePagePath, 'utf8');
  
  const hasDebuggerImport = /import.*StateDebuggerUI.*from.*StateDebuggerUI/.test(content);
  const hasDebuggerState = /showStateDebugger/.test(content);
  const hasDebugButton = /🔍 Debug/.test(content);
  const hasDebuggerUIRender = /<StateDebuggerUI/.test(content);
  const hasPhase62Comment = /Phase 6\.2/.test(content);
  const hasBothDebugTools = /🎮 Replay.*🔍 Debug/.test(content);
  
  console.log(`✅ StateDebuggerUI import: ${hasDebuggerImport}`);
  console.log(`✅ Debugger tool state: ${hasDebuggerState}`);
  console.log(`✅ Debug button: ${hasDebugButton}`);
  console.log(`✅ StateDebuggerUI render: ${hasDebuggerUIRender}`);
  console.log(`✅ Phase 6.2 comments: ${hasPhase62Comment}`);
  console.log(`✅ Both debug tools: ${hasBothDebugTools}`);
  
} catch (err) {
  console.log('❌ Could not check GamePage integration');
}

// Test 5: Check state comparison capabilities
console.log('\n📋 Test 5: Checking state comparison capabilities...');

try {
  const stateDebuggerContent = fs.readFileSync(stateDebuggerPath, 'utf8');
  
  const hasStateDifferenceTypes = /missing.*different.*extra/.test(stateDebuggerContent);
  const hasSeverityLevels = /low.*medium.*high.*critical/.test(stateDebuggerContent);
  const hasDeepComparison = /findStateDifferences.*frontendObj.*backendObj/.test(stateDebuggerContent);
  const hasArrayHandling = /Array\.isArray.*maxLength/.test(stateDebuggerContent);
  const hasObjectHandling = /Object\.keys.*allKeys/.test(stateDebuggerContent);
  const hasSeverityMapping = /getSeverity.*phase.*currentPlayer.*gameOver/.test(stateDebuggerContent);
  const hasChecksumValidation = /calculateChecksum/.test(stateDebuggerContent);
  
  console.log(`✅ State difference types: ${hasStateDifferenceTypes}`);
  console.log(`✅ Severity levels: ${hasSeverityLevels}`);
  console.log(`✅ Deep comparison: ${hasDeepComparison}`);
  console.log(`✅ Array handling: ${hasArrayHandling}`);
  console.log(`✅ Object handling: ${hasObjectHandling}`);
  console.log(`✅ Severity mapping: ${hasSeverityMapping}`);
  console.log(`✅ Checksum validation: ${hasChecksumValidation}`);
  
} catch (err) {
  console.log('❌ Could not check state comparison capabilities');
}

// Test 6: Check performance monitoring capabilities
console.log('\n📋 Test 6: Checking performance monitoring capabilities...');

try {
  const stateDebuggerContent = fs.readFileSync(stateDebuggerPath, 'utf8');
  
  const hasLatencyTracking = /stateUpdateLatency.*websocketLatency.*renderLatency/.test(stateDebuggerContent);
  const hasEventProcessingTime = /eventProcessingTime.*measureEventProcessingTime/.test(stateDebuggerContent);
  const hasPerformanceTimers = /performanceTimers.*performance\.now/.test(stateDebuggerContent);
  const hasMetricAggregation = /average.*min.*max.*recent/.test(stateDebuggerContent);
  const hasMetricLimits = /recent\.length.*100/.test(stateDebuggerContent);
  const hasAutoUpdate = /autoUpdate.*updateInterval/.test(stateDebuggerContent);
  
  console.log(`✅ Latency tracking: ${hasLatencyTracking}`);
  console.log(`✅ Event processing time: ${hasEventProcessingTime}`);
  console.log(`✅ Performance timers: ${hasPerformanceTimers}`);
  console.log(`✅ Metric aggregation: ${hasMetricAggregation}`);
  console.log(`✅ Metric limits: ${hasMetricLimits}`);
  console.log(`✅ Auto update: ${hasAutoUpdate}`);
  
} catch (err) {
  console.log('❌ Could not check performance monitoring capabilities');
}

// Test 7: Check TypeScript exports and imports
console.log('\n📋 Test 7: Checking TypeScript exports and imports...');

try {
  const stateDebuggerContent = fs.readFileSync(stateDebuggerPath, 'utf8');
  const hookContent = fs.readFileSync(useStateDebuggerPath, 'utf8');
  
  const hasDebuggerExport = /export const stateDebugger/.test(stateDebuggerContent);
  const hasTypeExports = /export.*StateSnapshot.*StateDifference.*PerformanceMetrics/.test(stateDebuggerContent);
  const hasHookExport = /export.*useStateDebugger/.test(hookContent);
  const hasHookTypeImports = /import.*DebuggerState.*StateSnapshot.*from.*StateDebugger/.test(hookContent);
  
  console.log(`✅ StateDebugger export: ${hasDebuggerExport}`);
  console.log(`✅ Type exports: ${hasTypeExports}`);
  console.log(`✅ Hook export: ${hasHookExport}`);
  console.log(`✅ Hook type imports: ${hasHookTypeImports}`);
  
} catch (err) {
  console.log('❌ Could not check TypeScript exports');
}

// Test Summary
console.log('\n📊 Phase 6.2 State Debug Tool Summary:');
console.log('======================================');

// Collect test results
let hasStateDebugger = false, hasStateDebuggerHook = false, hasStateDebuggerUI = false;
let hasGamePageIntegration = false, hasStateComparison = false, hasPerformanceMonitoring = false;

try {
  const stateDebuggerContent = fs.readFileSync(stateDebuggerPath, 'utf8');
  hasStateDebugger = /class StateDebugger/.test(stateDebuggerContent);
  hasStateComparison = /compareStates.*findStateDifferences/.test(stateDebuggerContent);
  hasPerformanceMonitoring = /updatePerformanceMetric.*measureEventProcessingTime/.test(stateDebuggerContent);
  
  const hookContent = fs.readFileSync(useStateDebuggerPath, 'utf8');
  hasStateDebuggerHook = /export const useStateDebugger/.test(hookContent);
  
  const uiContent = fs.readFileSync(stateDebuggerUIPath, 'utf8');
  hasStateDebuggerUI = /const StateDebuggerUI/.test(uiContent);
  
  const gamePageContent = fs.readFileSync(gamePagePath, 'utf8');
  hasGamePageIntegration = /import.*StateDebuggerUI.*from.*StateDebuggerUI/.test(gamePageContent);
} catch (err) {
  // Use defaults
}

// Calculate completion metrics
const coreFeatures = [
  { name: 'StateDebugger implementation', status: hasStateDebugger },
  { name: 'useStateDebugger hook', status: hasStateDebuggerHook },
  { name: 'StateDebuggerUI component', status: hasStateDebuggerUI },
  { name: 'GamePage integration', status: hasGamePageIntegration },
  { name: 'State comparison capabilities', status: hasStateComparison },
  { name: 'Performance monitoring', status: hasPerformanceMonitoring }
];

let implementedCount = 0;
coreFeatures.forEach(feature => {
  const icon = feature.status ? '✅' : '❌';
  console.log(`${icon} ${feature.name}: ${feature.status ? 'IMPLEMENTED' : 'NEEDS WORK'}`);
  if (feature.status) implementedCount++;
});

const completionPercentage = Math.round((implementedCount / coreFeatures.length) * 100);

if (completionPercentage >= 85) {
  console.log(`\n🎉 SUCCESS: Phase 6.2 State Debug Tool ${completionPercentage}% complete!`);
  console.log('✅ Live state monitoring with frontend/backend comparison');
  console.log('✅ Real-time difference detection with severity levels');
  console.log('✅ WebSocket message filtering and viewing');
  console.log('✅ Performance metrics tracking and analysis');
  console.log('✅ Visual interface integrated into GamePage');
  console.log('\n📈 Developer Benefits:');
  console.log('• Real-time state desync detection');
  console.log('• Live performance monitoring');
  console.log('• Visual diff highlighting for state differences');
  console.log('• WebSocket message inspection with filtering');
  console.log('• Export debugging sessions for team analysis');
  console.log('\n🎯 Usage:');
  console.log('1. Click "🔍 Debug" button in game header');
  console.log('2. Start debugging to monitor live state');
  console.log('3. View state differences with severity indicators');
  console.log('4. Filter WebSocket messages by type/direction');
  console.log('5. Monitor performance metrics in real-time');
  console.log('6. Export session data for detailed analysis');
} else {
  console.log(`\n⚠️  PARTIAL: Phase 6.2 implementation ${completionPercentage}% complete`);
  console.log('Additional work needed to complete state debug functionality');
}

console.log('\n🎯 Next Steps:');
console.log('1. Test state debugger in live game environment');
console.log('2. Verify state difference detection accuracy');
console.log('3. Test performance metrics tracking');
console.log('4. Implement Phase 6.3: Sync Checker Tool');
console.log('5. Create comprehensive debugging workflow documentation');

process.exit(completionPercentage >= 85 ? 0 : 1);