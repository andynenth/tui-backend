#!/bin/bash
#
# build-prod.sh - Local Production Build & Deployment Script
#
# This script automates the deployment process for local production testing.
# It performs version bumping, frontend building, and Docker container deployment.
#
# Usage: ./build-prod.sh [version_type]
#
# Version types:
#   - patch (default): 1.5.17 → 1.5.18
#   - minor: 1.5.17 → 1.6.0
#   - major: 1.5.17 → 2.0.0
#   - x.y.z: Set specific version (e.g., 2.1.0)
#
# Examples:
#   ./build-prod.sh              # Bump patch version
#   ./build-prod.sh patch        # Same as above
#   ./build-prod.sh minor        # Bump minor version
#   ./build-prod.sh major        # Bump major version
#   ./build-prod.sh 2.0.0        # Set to version 2.0.0
#
# Author: Liap Tui Development Team
# Date: September 2025

# ============================================================================
# BASH SCRIPT SETTINGS
# ============================================================================

# Exit immediately if any command fails (error handling)
# This prevents the script from continuing after an error occurs
set -e

# Exit if any command in a pipeline fails (not just the last one)
# Example: false | echo "test" would fail with this setting
set -o pipefail

# Treat unset variables as an error and exit immediately
# This helps catch typos in variable names
set -u

# ============================================================================
# COLOR DEFINITIONS (for better visual feedback)
# ============================================================================

# ANSI color codes for terminal output
# Usage: echo -e "${GREEN}Success!${NC}"
GREEN='\033[0;32m'   # Green text for success messages
BLUE='\033[0;34m'    # Blue text for information
YELLOW='\033[1;33m'  # Yellow text for warnings
RED='\033[0;31m'     # Red text for errors
NC='\033[0m'         # No Color - reset to default

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Function to print colored messages with timestamps
# Usage: print_message "INFO" "Building frontend..." "$BLUE"
print_message() {
    local level=$1      # Message level (INFO, SUCCESS, ERROR, etc.)
    local message=$2    # The actual message
    local color=$3      # Color code to use

    # Get current timestamp in readable format
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Print formatted message with color
    echo -e "${color}[${timestamp}] [${level}] ${message}${NC}"
}

# Function to handle errors and provide helpful information
# This function is automatically called when any command fails (due to set -e)
error_handler() {
    local line_number=$1
    local error_code=$2

    print_message "ERROR" "Script failed at line ${line_number} with exit code ${error_code}" "$RED"
    print_message "ERROR" "Check the output above for details" "$RED"

    # Cleanup actions could go here if needed
    # For example: stopping partially started services

    exit $error_code
}

# Set up error handling to call our error_handler function
# $LINENO is a special variable containing the current line number
# $? contains the exit code of the last command
trap 'error_handler $LINENO $?' ERR

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

print_message "INFO" "Starting local deployment process..." "$BLUE"

# Check if we're in the correct directory
# The script should be run from the project root
if [ ! -f "docker-compose.prod-local.yml" ]; then
    print_message "ERROR" "docker-compose.prod-local.yml not found!" "$RED"
    print_message "ERROR" "Please run this script from the project root directory" "$RED"
    exit 1
fi

# Check if required commands are available
# command -v returns the path of the command if it exists
for cmd in npm node docker docker-compose; do
    if ! command -v $cmd &> /dev/null; then
        print_message "ERROR" "Required command '${cmd}' is not installed!" "$RED"
        exit 1
    fi
done

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    print_message "ERROR" "frontend directory not found!" "$RED"
    exit 1
fi

# ============================================================================
# PARAMETER HANDLING
# ============================================================================

# Default version bump type is 'patch'
# Can be overridden by passing: major, minor, patch, or a specific version
VERSION_TYPE="${1:-patch}"

# Validate version parameter
if [[ ! "$VERSION_TYPE" =~ ^(major|minor|patch|[0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    print_message "ERROR" "Invalid version parameter: ${VERSION_TYPE}" "$RED"
    print_message "INFO" "Valid options are: major, minor, patch, or specific version (e.g., 2.0.0)" "$BLUE"
    print_message "INFO" "Usage: ./build-prod.sh [major|minor|patch|x.y.z]" "$BLUE"
    exit 1
fi

# ============================================================================
# STORE INITIAL DIRECTORY
# ============================================================================

# Save the current directory so we can return to it later
# This is useful if the script fails partway through
INITIAL_DIR=$(pwd)
print_message "INFO" "Working directory: ${INITIAL_DIR}" "$BLUE"

# ============================================================================
# STEP 1: VERSION BUMP
# ============================================================================

print_message "INFO" "Step 1/4: Bumping version number..." "$BLUE"

# Change to frontend directory
cd frontend

# Get current version before bumping
# This reads the version field from package.json using Node.js
CURRENT_VERSION=$(node -p "require('./package.json').version")
print_message "INFO" "Current version: ${CURRENT_VERSION}" "$BLUE"

# Bump the version based on parameter
# npm version accepts: major, minor, patch, or specific version
print_message "INFO" "Version bump type: ${VERSION_TYPE}" "$BLUE"
npm version "$VERSION_TYPE"

# Get new version after bumping
NEW_VERSION=$(node -p "require('./package.json').version")
print_message "SUCCESS" "Version bumped to: ${NEW_VERSION}" "$GREEN"

# ============================================================================
# STEP 2: BUILD FRONTEND
# ============================================================================

print_message "INFO" "Step 2/4: Building frontend..." "$BLUE"

# Run the build script defined in package.json
# This typically:
# - Bundles JavaScript/CSS with esbuild
# - Copies index.html to ../backend/static/
# - Creates ../VERSION file with new version number
npm run build

# Check if build artifacts were created
if [ -f "../backend/static/bundle.js" ]; then
    print_message "SUCCESS" "Frontend build completed successfully" "$GREEN"

    # Show build artifact sizes for information
    BUNDLE_SIZE=$(ls -lh ../backend/static/bundle.js | awk '{print $5}')
    print_message "INFO" "Bundle size: ${BUNDLE_SIZE}" "$BLUE"
else
    print_message "ERROR" "Frontend build failed - bundle.js not found!" "$RED"
    exit 1
fi

# ============================================================================
# STEP 3: RETURN TO PROJECT ROOT
# ============================================================================

print_message "INFO" "Step 3/4: Returning to project root..." "$BLUE"

# Go back to the initial directory
# Using the stored path is more reliable than 'cd ..'
cd "${INITIAL_DIR}"

# ============================================================================
# STEP 4: BUILD AND START DOCKER CONTAINER
# ============================================================================

print_message "INFO" "Step 4/4: Building and starting Docker container..." "$BLUE"

# Stop any existing container to avoid port conflicts
# The || true ensures the script continues even if no container is running
print_message "INFO" "Stopping any existing containers..." "$BLUE"
docker-compose -f docker-compose.prod-local.yml down || true

# Build and start the container
# --build flag forces Docker to rebuild the image even if it exists
# This ensures our new frontend build is included in the image
print_message "INFO" "Building Docker image with new version ${NEW_VERSION}..." "$BLUE"
docker-compose -f docker-compose.prod-local.yml up --build -d

# ============================================================================
# WAIT FOR CONTAINER TO BE HEALTHY
# ============================================================================

print_message "INFO" "Waiting for container to become healthy..." "$BLUE"

# Maximum time to wait (in seconds)
MAX_WAIT=60
WAITED=0

# Check container health status every 2 seconds
while [ $WAITED -lt $MAX_WAIT ]; do
    # Get health status of the container
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' liap-tui-game 2>/dev/null || echo "not-found")

    if [ "$HEALTH_STATUS" = "healthy" ]; then
        print_message "SUCCESS" "Container is healthy!" "$GREEN"
        break
    elif [ "$HEALTH_STATUS" = "unhealthy" ]; then
        print_message "ERROR" "Container is unhealthy!" "$RED"
        docker logs liap-tui-game --tail 50
        exit 1
    fi

    # Wait 2 seconds before checking again
    sleep 2
    WAITED=$((WAITED + 2))

    # Show progress
    echo -ne "\rWaited ${WAITED}s / ${MAX_WAIT}s..."
done

echo "" # New line after progress indicator

# Check if we timed out
if [ $WAITED -ge $MAX_WAIT ]; then
    print_message "ERROR" "Container failed to become healthy within ${MAX_WAIT} seconds" "$RED"
    docker logs liap-tui-game --tail 50
    exit 1
fi

# ============================================================================
# VERIFY DEPLOYMENT
# ============================================================================

print_message "INFO" "Verifying deployment..." "$BLUE"

# Test the health endpoint
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/api/health || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    print_message "SUCCESS" "API health check passed!" "$GREEN"

    # Get and display health information
    HEALTH_INFO=$(curl -s http://localhost:80/api/health | python3 -m json.tool 2>/dev/null || echo "{}")
    print_message "INFO" "Health check response:" "$BLUE"
    echo "$HEALTH_INFO"
else
    print_message "ERROR" "API health check failed with status: ${HTTP_STATUS}" "$RED"
    exit 1
fi

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

print_message "SUCCESS" "Deployment completed successfully! 🎉" "$GREEN"
echo ""
print_message "INFO" "Deployment Summary:" "$BLUE"
print_message "INFO" "  - Version: ${NEW_VERSION}" "$BLUE"
print_message "INFO" "  - URL: http://localhost:80" "$BLUE"
print_message "INFO" "  - API Health: http://localhost:80/api/health" "$BLUE"
print_message "INFO" "  - Container: liap-tui-game" "$BLUE"
echo ""
print_message "INFO" "To view logs: docker logs -f liap-tui-game" "$BLUE"
print_message "INFO" "To stop: docker-compose -f docker-compose.prod-local.yml down" "$BLUE"

# ============================================================================
# OPTIONAL: OPEN BROWSER
# ============================================================================

# Uncomment the following lines to automatically open the browser
# This works on macOS. For Linux, use 'xdg-open' instead of 'open'
# print_message "INFO" "Opening browser..." "$BLUE"
# open http://localhost:80

# Script completed successfully
exit 0
