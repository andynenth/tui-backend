#!/bin/bash
# backend/run_preparation_tests.sh

echo "🧪 Running ALL Preparation State Tests..."
echo "========================================"
echo ""

echo "📋 1. Basic Preparation State Tests"
echo "-----------------------------------"
pytest tests/test_preparation_state.py -v

echo ""
echo "📋 2. Complex Weak Hand Scenario Tests"
echo "-------------------------------------"
pytest tests/test_weak_hand_scenarios.py -v

echo ""
echo "📋 3. All State Machine Tests (including Preparation)"
echo "---------------------------------------------------"
pytest tests/test_state_machine.py tests/test_preparation_state.py tests/test_weak_hand_scenarios.py -v

echo ""
echo "📊 Test Summary"
echo "---------------"
pytest tests/test_preparation_state.py tests/test_weak_hand_scenarios.py --tb=no -q

echo ""
echo "✅ Test run complete!"