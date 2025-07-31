#!/bin/bash

# 🧪 **PlaywrightTester Agent - Test Runner Script**
#
# Comprehensive test execution for game start flow bug reproduction and validation

set -e

echo "🧪 === PLAYWRIGHT GAME START FLOW TESTING ==="
echo "🤖 PlaywrightTester Agent - Comprehensive Test Suite"
echo ""

# Check if server is running
echo "🔍 Checking if game server is running on localhost:5050..."
if ! curl -s http://localhost:5050 > /dev/null 2>&1; then
    echo "❌ Game server is not running on localhost:5050"
    echo "💡 Please start the server first:"
    echo "   cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 5050"
    echo ""
    exit 1
fi

echo "✅ Server is running on localhost:5050"
echo ""

# Ensure Playwright is installed
echo "🔧 Ensuring Playwright is installed..."
if ! npx playwright --version > /dev/null 2>&1; then
    echo "📦 Installing Playwright..."
    npm install @playwright/test
    npx playwright install
fi

echo "✅ Playwright is ready"
echo ""

# Create test results directory
mkdir -p test-results
mkdir -p test-screenshots

# Run coordination protocol
echo "🤖 Executing swarm coordination protocol..."
npx claude-flow@alpha hooks pre-task --description "Comprehensive Playwright testing suite execution" --auto-spawn-agents false || echo "⚠️  Coordination hook failed (continuing)"

echo ""
echo "🎯 === EXECUTING TEST SUITES ==="
echo ""

# Test execution with different strategies
TEST_EXIT_CODE=0

# 1. Primary Bug Reproduction Tests
echo "🚨 Running PRIMARY BUG REPRODUCTION tests..."
echo "   Target: Reproduce game start stuck on waiting page bug"
if npx playwright test --project=chromium-game-tests game-start-flow.spec.js --reporter=list; then
    echo "✅ Bug reproduction tests completed"
else
    echo "⚠️  Bug reproduction tests had issues (may be expected if bug exists)"
    TEST_EXIT_CODE=1
fi
echo ""

# 2. WebSocket Validation Tests  
echo "🌐 Running WEBSOCKET VALIDATION tests..."
echo "   Target: Validate WebSocket connection stability and events"
if npx playwright test --project=chromium-game-tests websocket-validation.spec.js --reporter=list; then
    echo "✅ WebSocket validation tests completed"
else
    echo "❌ WebSocket validation tests failed"
    TEST_EXIT_CODE=1
fi
echo ""

# 3. Regression Tests
echo "🔄 Running REGRESSION PREVENTION tests..."
echo "   Target: Ensure fixes remain stable and prevent future regressions"
if npx playwright test --project=regression-tests regression-tests.spec.js --reporter=list; then
    echo "✅ Regression tests completed"
else
    echo "⚠️  Regression tests had issues"
    TEST_EXIT_CODE=1
fi
echo ""

# 4. Legacy Test Compatibility (if exists)
if [ -f "test_lobby_game_transition.spec.js" ]; then
    echo "🔗 Running LEGACY COMPATIBILITY tests..."
    if npx playwright test --project=legacy-compatibility test_lobby_game_transition.spec.js --reporter=list; then
        echo "✅ Legacy compatibility tests completed"
    else
        echo "⚠️  Legacy compatibility tests had issues"
    fi
    echo ""
fi

# Generate comprehensive HTML report
echo "📋 Generating comprehensive test report..."
npx playwright show-report --host=127.0.0.1 --port=0 > /dev/null 2>&1 &
REPORT_PID=$!

# Wait a moment for report to generate
sleep 2

echo ""
echo "📊 === TEST EXECUTION SUMMARY ==="

# Count test results
if [ -d "test-results" ]; then
    RESULT_FILES=$(find test-results -name "*.json" | wc -l)
    SCREENSHOT_FILES=$(find test-screenshots -name "*.png" 2>/dev/null | wc -l || echo "0")
    echo "📁 Test result files generated: $RESULT_FILES"
    echo "📸 Screenshots captured: $SCREENSHOT_FILES"
fi

# Show key result locations
echo ""
echo "📂 Key Results Locations:"
echo "   🧪 Test results: ./test-results/"
echo "   📸 Screenshots: ./test-screenshots/"
echo "   📋 HTML report: ./playwright-report/index.html"
echo "   🤖 Swarm data: ./test-results/swarm-coordination-report.json"

# Execute post-task coordination
echo ""
echo "🤖 Executing post-task coordination..."
npx claude-flow@alpha hooks post-task --task-id "playwright-comprehensive-testing" --analyze-performance true || echo "⚠️  Post-task hook failed (continuing)"

# Store results in swarm memory
echo "💾 Storing results in swarm memory..."
npx claude-flow@alpha hooks notify --message "PlaywrightTester: Comprehensive test suite completed. Bug reproduction, WebSocket validation, and regression tests executed. Results available for other agents." --telemetry true || echo "⚠️  Memory storage failed (continuing)"

echo ""
echo "🎯 === PLAYWRIGHT TESTING COMPLETE ==="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All test suites executed successfully"
    echo "📋 Review test results to understand bug status and validation outcomes"
else
    echo "⚠️  Some tests had issues (may be expected for bug reproduction)"
    echo "📋 Check individual test reports for detailed analysis"
fi

echo ""
echo "🔄 Next Steps:"
echo "   1. Review bug reproduction results in test-results/game-start-flow/"
echo "   2. Analyze WebSocket validation in test-results/websocket-validation/"
echo "   3. Check regression test outcomes in test-results/regression-tests/"
echo "   4. Coordinate with other agents for fix implementation"
echo "   5. Re-run fix validation tests after fixes are implemented"
echo ""

# Keep report server running for a bit
if [ ! -z "$REPORT_PID" ]; then
    echo "📊 HTML report server running temporarily (PID: $REPORT_PID)"
    echo "💡 View report at: http://127.0.0.1:9323 (auto-port)"
    sleep 5
    kill $REPORT_PID 2>/dev/null || true
fi

exit $TEST_EXIT_CODE