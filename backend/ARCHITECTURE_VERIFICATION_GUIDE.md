# Architecture Verification Guide

**How to Determine if Your Project is Running Clean Architecture or Legacy Code**

This guide provides multiple methods to definitively verify whether your Liap TUI project is running on clean architecture or legacy code. Use these tools and techniques to get reliable answers about your system's current state.

## 🎯 Quick Answer Methods

### Method 1: Quick Command-Line Check ⚡ (Fastest)

```bash
# Instant status check
python quick_architecture_check.py

# Check specific method
python quick_architecture_check.py --method endpoint
python quick_architecture_check.py --method flags  
python quick_architecture_check.py --method reports

# JSON output
python quick_architecture_check.py --json
```

**What this tells you:**
- ✅ Clean Architecture: System is fully migrated
- ⚠️ Partial Migration: System is in hybrid state
- ❌ Legacy Code: System is running legacy implementation

### Method 2: HTTP Health Endpoint 🌐 (Most Reliable)

```bash
# Architecture status endpoint
curl http://localhost:8000/api/health/architecture-status

# Basic health check
curl http://localhost:8000/api/health

# Detailed health with components
curl http://localhost:8000/api/health/detailed
```

**Architecture Status Response:**
```json
{
  "architecture_status": "clean_architecture",
  "message": "System is running on Clean Architecture", 
  "confidence_percentage": 95,
  "feature_flags": {
    "clean_architecture": {
      "use_clean_architecture": true,
      "use_domain_events": true,
      "use_application_layer": true,
      "use_new_repositories": true
    },
    "adapters": {
      "use_connection_adapters": true,
      "use_room_adapters": true, 
      "use_game_adapters": true,
      "use_lobby_adapters": true
    }
  },
  "migration_evidence": [
    "Phase 6 completion report found",
    "Final performance validation report found"
  ]
}
```

### Method 3: Real-Time Dashboard 📊 (Most Visual)

```bash
# Start real-time monitoring dashboard
python architecture_status_dashboard.py

# Custom refresh interval
python architecture_status_dashboard.py --refresh-interval 5

# Different server
python architecture_status_dashboard.py --server-url http://production:8000
```

**Dashboard Features:**
- 🎯 Architecture status with confidence meter
- 🏁 Feature flag status (enabled/disabled)
- 📋 Migration evidence tracking
- 💡 Specific recommendations
- 📊 Status history timeline
- 💚 System health indicators

## 🔍 Comprehensive Verification

### Method 4: Full Verification Suite 🔬 (Most Thorough)

```bash
# Complete verification analysis
python verify_architecture_status.py

# Save detailed report
python verify_architecture_status.py --output-file architecture_report.json

# Minimal output
python verify_architecture_status.py --quiet
```

**Verification Methods Used:**
1. **Feature Flags Analysis** (30% weight) - Checks configuration
2. **Migration Reports Analysis** (25% weight) - Checks completion evidence  
3. **Environment Variables** (20% weight) - Checks runtime config
4. **Health Endpoints** (15% weight) - Checks server status
5. **Code Structure** (10% weight) - Checks file organization

**Exit Codes:**
- `0`: Clean Architecture confirmed
- `1`: Partial migration (hybrid state)
- `2`: Legacy code confirmed  
- `3`: Unknown/indeterminate
- `4`: Verification error

## 📋 Manual Verification Methods

### Check Feature Flags Directly

```python
# In Python console
from infrastructure.feature_flags import get_feature_flags
flags = get_feature_flags()
print(flags.get_all_flags())
```

### Check Environment Variables

```bash
# Check feature flag environment variables
echo $FF_USE_CLEAN_ARCHITECTURE
echo $FF_USE_DOMAIN_EVENTS
echo $FF_USE_APPLICATION_LAYER  
echo $FF_USE_NEW_REPOSITORIES

# Check adapter flags
echo $FF_USE_CONNECTION_ADAPTERS
echo $FF_USE_ROOM_ADAPTERS
echo $FF_USE_GAME_ADAPTERS
echo $FF_USE_LOBBY_ADAPTERS
```

### Check Migration Reports

```bash
# Phase 6 completion report
cat PHASE_6_COMPLETION_REPORT.md | grep "COMPLETE"

# Final validation report
cat tests/phase6/reports/final_performance_validation_report.json | jq '.summary'

# Regression test report  
cat tests/phase6/reports/regression_test_report.json | jq '.summary'
```

### Check Code Structure

```bash
# Clean architecture directories should exist and contain files
ls -la domain/
ls -la application/
ls -la infrastructure/

# Count clean architecture files
find domain/ application/ infrastructure/ -name "*.py" | wc -l

# Legacy directories should be empty or non-existent
ls -la legacy/ 2>/dev/null || echo "No legacy directory (good!)"
```

## 🏗️ Architecture Indicators

### ✅ Clean Architecture Indicators

**Strong Evidence (95%+ confidence):**
- All 8 feature flags enabled (`use_clean_architecture`, `use_domain_events`, etc.)
- Phase 6 completion report present and marked complete
- Final performance validation passed with Grade A
- Regression tests passed with 0 regressions
- Architecture status endpoint returns "clean_architecture"

**Medium Evidence (70-94% confidence):**
- Most feature flags enabled (6-7 out of 8)
- Some migration reports present
- Health endpoints show clean components
- Clean architecture directories present with files

### ⚠️ Partial Migration Indicators

**Evidence:**
- Some feature flags enabled (2-5 out of 8)
- Partial migration reports present
- Health endpoints show mixed components
- Both clean and legacy patterns present

### ❌ Legacy Code Indicators

**Strong Evidence:**
- No feature flags enabled (0-1 out of 8)
- No migration reports found
- Architecture status endpoint returns "legacy_code"
- Only legacy directories present

## 🚀 Usage Examples

### Continuous Integration Check

```bash
#!/bin/bash
# CI/CD architecture verification
python quick_architecture_check.py --method endpoint
if [ $? -eq 0 ]; then
    echo "✅ Clean Architecture confirmed - deployment approved"
else
    echo "❌ Architecture verification failed - blocking deployment"
    exit 1
fi
```

### Development Workflow

```bash
# Before making changes
python quick_architecture_check.py

# After deployment
curl http://localhost:8000/api/health/architecture-status | jq '.architecture_status'

# Continuous monitoring
python architecture_status_dashboard.py
```

### Production Monitoring

```bash
# Production status check
python verify_architecture_status.py --server-url http://production:8000 --output-file prod_status.json

# Alert if not clean architecture
if ! python quick_architecture_check.py --method endpoint | grep "✅"; then
    echo "ALERT: Production not running clean architecture!"
fi
```

## 🎛️ Configuration Management

### Enable Clean Architecture

If verification shows legacy code and you want to enable clean architecture:

```python
# Enable all clean architecture features
from infrastructure.feature_flags import get_feature_flags
flags = get_feature_flags()
flags.enable_clean_architecture(100)  # 100% rollout
```

### Environment Variable Method

```bash
# Set environment variables for clean architecture
export FF_USE_CLEAN_ARCHITECTURE=true
export FF_USE_DOMAIN_EVENTS=true
export FF_USE_APPLICATION_LAYER=true
export FF_USE_NEW_REPOSITORIES=true
export FF_USE_CONNECTION_ADAPTERS=true
export FF_USE_ROOM_ADAPTERS=true
export FF_USE_GAME_ADAPTERS=true
export FF_USE_LOBBY_ADAPTERS=true

# Restart application for changes to take effect
```

### Gradual Rollout

```python
# Enable clean architecture for 50% of traffic
flags.enable_clean_architecture(50)

# Enable for specific users/rooms
flags.override("use_clean_architecture", True)
```

## 🔧 Troubleshooting

### Common Issues

**Q: Verification tools show "connection error"**
A: Make sure the backend server is running on `http://localhost:8000`

**Q: Feature flags show "import error"**  
A: Ensure you're running the script from the backend directory

**Q: Dashboard shows "unknown status"**
A: Check if the architecture status endpoint is available in your routes

**Q: Mixed signals from different verification methods**
A: This indicates partial migration - some components migrated, others not

### Getting Help

1. **Check server logs** for feature flag and adapter initialization
2. **Use the comprehensive verification** tool for detailed analysis
3. **Check the Phase 6 completion report** for migration status
4. **Review the architecture documentation** for expected configuration

## 📊 Confidence Levels

| Confidence | Meaning | Action |
|------------|---------|---------|
| 90-100% | Definitive | Trust the result completely |
| 70-89% | High confidence | Result is very likely correct |
| 50-69% | Medium confidence | Additional verification recommended |
| 30-49% | Low confidence | Multiple verification methods needed |
| 0-29% | Uncertain | Manual investigation required |

## 🎉 Success Confirmation

**When verification shows Clean Architecture:**
- ✅ All feature flags enabled
- ✅ Migration reports confirm completion  
- ✅ Health endpoints show clean components
- ✅ Performance tests passed with Grade A
- ✅ Zero regressions in functionality

**This means:**
- Your system has successfully migrated to clean architecture
- Legacy code has been removed or disabled
- All new requests use clean architecture patterns
- Performance is equal or better than legacy
- The system is production-ready

---

**Quick Reference:**
- 🚀 **Fastest**: `python quick_architecture_check.py`
- 🌐 **Most Reliable**: `curl /api/health/architecture-status`
- 📊 **Most Visual**: `python architecture_status_dashboard.py`
- 🔬 **Most Thorough**: `python verify_architecture_status.py`