#!/bin/bash
# Setup script for contract testing infrastructure

set -e

echo "Setting up Contract Testing Infrastructure"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "Creating test directories..."
mkdir -p backend/tests/contracts/golden_masters
mkdir -p backend/tests/behavioral/results
mkdir -p backend/shadow_mode_data

# Check if golden masters exist
if [ -z "$(ls -A backend/tests/contracts/golden_masters 2>/dev/null)" ]; then
    echo ""
    echo "⚠️  WARNING: No golden masters found!"
    echo ""
    echo "Before starting refactoring, you MUST capture the current system behavior:"
    echo "  cd backend"
    echo "  python tests/contracts/capture_golden_masters.py"
    echo ""
fi

# Run initial contract validation
echo "Validating contract definitions..."
cd backend
python -c "
from tests.contracts.websocket_contracts import get_all_contracts
contracts = get_all_contracts()
print(f'Found {len(contracts)} WebSocket contracts')

# Validate all contracts have required fields
issues = []
for name, contract in contracts.items():
    if contract.direction.value == 'client_to_server' and not contract.request_schema:
        issues.append(f'{name}: missing request_schema')
    if contract.direction.value == 'server_to_client' and not contract.response_schema:
        issues.append(f'{name}: missing response_schema')

if issues:
    print('❌ Contract validation failed:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('✅ All contracts valid')
"
cd ..

# Create a contract testing checklist
echo "Creating contract testing checklist..."
cat > CONTRACT_TESTING_CHECKLIST.md << 'EOF'
# Contract Testing Checklist

## Before Starting Refactoring

- [ ] Run golden master capture: `cd backend && python tests/contracts/capture_golden_masters.py`
- [ ] Verify all golden masters created: `ls backend/tests/contracts/golden_masters/`
- [ ] Run behavioral tests: `cd backend && python tests/behavioral/run_behavioral_tests.py`
- [ ] Commit golden masters to git

## During Refactoring

- [ ] Run contract tests after each change: `cd backend && pytest tests/contracts/`
- [ ] Check specific contract: `pytest tests/contracts/ -k "test_create_room"`
- [ ] Monitor shadow mode: `python api/shadow_mode_manager.py status`

## Before Merging

- [ ] All contract tests pass
- [ ] No performance regressions (< 20% overhead)
- [ ] Shadow mode shows 100% compatibility
- [ ] Update documentation if any contracts changed

## CI/CD Verification

- [ ] GitHub Actions contract tests pass
- [ ] Pre-commit hooks pass locally
- [ ] No warnings in golden master check

EOF

echo ""
echo "✅ Contract Testing Infrastructure Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Capture golden masters: cd backend && python tests/contracts/capture_golden_masters.py"
echo "2. Run behavioral tests: cd backend && python tests/behavioral/run_behavioral_tests.py"
echo "3. Commit the golden masters to version control"
echo "4. Begin refactoring with confidence!"
echo ""
echo "See CONTRACT_TESTING_CHECKLIST.md for detailed steps"