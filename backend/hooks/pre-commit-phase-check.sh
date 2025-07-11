#!/bin/bash
# Pre-commit hook to check phase transitions
# 
# To use this hook, copy it to .git/hooks/pre-commit:
#   cp backend/hooks/pre-commit-phase-check.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit

echo "🔍 Checking phase transitions..."

# Check if any state machine files were modified
if git diff --cached --name-only | grep -qE "(state_machine|bot_manager)"; then
    echo "📋 State machine files modified - running phase validation tests..."
    
    # Run quick validation
    cd backend
    python run_phase_tests.py --quick
    
    if [ $? -ne 0 ]; then
        echo "❌ Phase transition tests failed!"
        echo "Please fix the issues before committing."
        exit 1
    fi
    
    echo "✅ Phase transition tests passed!"
fi

exit 0