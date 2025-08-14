#!/bin/bash
# Test version detection locally

echo "🔍 Testing version detection system..."
echo ""

# Get version from package.json
PACKAGE_VERSION=$(cd frontend && node -p "require('./package.json').version")
echo "📦 Package.json version: $PACKAGE_VERSION"

# Test frontend build creates VERSION file
echo ""
echo "🏗️  Testing frontend build..."
cd frontend && npm run build > /dev/null 2>&1
cd ..

if [ -f "VERSION" ]; then
    VERSION_FILE_CONTENT=$(cat VERSION)
    echo "✅ VERSION file created: $VERSION_FILE_CONTENT"
else
    echo "❌ VERSION file not created"
fi

# Test backend version detection
echo ""
echo "🐍 Testing backend version detection..."
cd backend
python3 -c "
import sys
sys.path.insert(0, '..')
from backend.config.version import APP_VERSION
print(f'Backend detected version: {APP_VERSION}')
"

echo ""
echo "🔧 Testing with environment variable..."
APP_VERSION=2.0.0-test python3 -c "
import sys
sys.path.insert(0, '..')
from backend.config.version import get_app_version
version = get_app_version()
print(f'Version with env var: {version}')
"

cd ..

# Cleanup
[ -f "VERSION" ] && rm VERSION

echo ""
echo "✅ Version system test complete!"