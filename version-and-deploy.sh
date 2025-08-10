#!/bin/bash
# version-and-deploy.sh - Update version and deploy

set -e

# Check if version type is provided
if [ -z "$1" ]; then
    echo "Usage: ./version-and-deploy.sh [major|minor|patch]"
    echo "Example: ./version-and-deploy.sh minor"
    exit 1
fi

# Update version
echo "📦 Updating version..."
cd frontend
npm version $1
cd ..

# Run deployment
echo "🚀 Starting deployment..."
./deploy-to-aws.sh