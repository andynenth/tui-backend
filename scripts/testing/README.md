# Testing Scripts

This directory contains manual testing scripts and utilities for the Liap Tui project.

## Scripts

### **`test_endpoints_manual.sh`** - Manual REST API Testing
**Purpose**: Interactive script to test all REST API endpoints with curl

**Usage**:
```bash
# Make script executable
chmod +x scripts/testing/test_endpoints_manual.sh

# Run the test script
./scripts/testing/test_endpoints_manual.sh
```

**Features**:
- Tests all REST API endpoints (`/api/health`, `/api/debug/*`, etc.)
- Color-coded output (✅ success, ❌ failure)
- Displays response times and status codes
- Shows actual response data for verification
- Automatically detects if backend server is running

**Requirements**:
- Backend server must be running on `localhost:5050`
- `curl` command must be available
- Bash shell environment

**Example Output**:
```
======================================
Testing Liap Tui REST API Endpoints
======================================

✅ Health Check - 200 OK (45ms)
✅ Detailed Health - 200 OK (32ms)
✅ Health Metrics - 200 OK (28ms)
❌ Debug Room Stats - 500 Error (Connection refused)
```

## Adding New Testing Scripts

When adding new testing scripts:

1. **Use descriptive names**: `test_[feature]_[type].sh`
2. **Include help text**: Add usage instructions and examples
3. **Add error handling**: Check prerequisites and provide helpful error messages
4. **Use consistent output**: Follow the emoji-based status indicators
5. **Document in README**: Update this file with new script descriptions

## Running Tests

### Prerequisites
```bash
# Ensure backend is running
./start.sh

# Wait for services to be ready
sleep 5
```

### Run All Testing Scripts
```bash
# Make all scripts executable
chmod +x scripts/testing/*.sh

# Run each script
for script in scripts/testing/test_*.sh; do
    echo "Running $script..."
    "$script"
    echo "---"
done
```

## Integration with Development Workflow

These scripts are designed for:
- **Manual verification** during development
- **Quick smoke tests** after changes
- **Debugging** when automated tests fail
- **Documentation** of expected API behavior

## CI/CD Integration

Scripts can be integrated into continuous integration:
```bash
# Example GitHub Actions step
- name: Run manual API tests
  run: |
    ./start.sh &
    sleep 10
    ./scripts/testing/test_endpoints_manual.sh
```

## Troubleshooting

Common issues:
- **Permission denied**: Run `chmod +x script_name.sh`
- **Command not found**: Ensure `curl` and `jq` are installed
- **Connection refused**: Verify backend server is running
- **Port conflicts**: Check if port 5050 is available