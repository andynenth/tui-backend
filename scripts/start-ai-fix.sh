#!/bin/bash

# Script to start AI bug fix workflow
# This ensures the checklist is followed

echo "==================================="
echo "Starting AI Bug Fix Workflow"
echo "==================================="

# Check if room ID provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/start-ai-fix.sh <ROOM_ID>"
    echo "Example: ./scripts/start-ai-fix.sh B5AE3B"
    exit 1
fi

ROOM_ID=$1
DATE=$(date +%Y-%m-%d)

# Create bug directory
BUG_DIR="ai-bugs/bug-$ROOM_ID-$DATE"
mkdir -p "$BUG_DIR"

# Copy checklist
cp AI_BUG_FIX_CHECKLIST.md "$BUG_DIR/checklist.md"

# Extract game data
echo "Extracting game data for room $ROOM_ID..."
curl -s "http://localhost:5050/api/rooms/$ROOM_ID/play-history" | python3 -m json.tool > "$BUG_DIR/game-data.json"

if [ $? -eq 0 ]; then
    echo "✓ Game data saved to $BUG_DIR/game-data.json"
else
    echo "✗ Failed to extract game data. Is the server running?"
    exit 1
fi

# Create initial test file
cat > "$BUG_DIR/test_reproduction.py" << 'EOF'
#!/usr/bin/env python3
"""Reproduce bug from room $ROOM_ID"""

import sys
from pathlib import Path

# Add to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.ai_regression.ai_decision_framework import AIDecisionTester

def test_bug():
    """Test the bug scenario"""
    tester = AIDecisionTester()

    # TODO: Add exact scenario from game data
    tester.add_scenario(
        name="Bug from Room $ROOM_ID",
        description="TODO: Describe what went wrong",
        bot_name="TODO",
        hand_specs=[
            # TODO: Add hand
        ],
        declared=0,
        captured=0,
        required_pieces=1,
        turn_number=1
    )

    tester.run_all_scenarios()

if __name__ == "__main__":
    test_bug()
EOF

# Update room ID in test file
sed -i '' "s/\$ROOM_ID/$ROOM_ID/g" "$BUG_DIR/test_reproduction.py"

echo ""
echo "Bug fix workspace created: $BUG_DIR"
echo ""
echo "Next steps:"
echo "1. Open $BUG_DIR/checklist.md and follow it"
echo "2. Analyze $BUG_DIR/game-data.json to identify the bug"
echo "3. Update $BUG_DIR/test_reproduction.py with exact scenario"
echo "4. Run: python $BUG_DIR/test_reproduction.py"
echo ""
echo "Remember: NO ASSUMPTIONS - trace actual execution!"