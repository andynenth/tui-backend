#!/bin/bash
#
# dev.sh - Full-stack development environment
#
# This script manages both frontend and backend development:
# - Frontend: File watcher that rebuilds on changes (no dev server)
# - Backend: Docker container with hot reload
# - Everything served through http://localhost:5050
#
# Architecture Overview:
# Unlike typical React apps with separate dev servers (e.g., port 3000/5173),
# this project uses a unified approach where the backend serves everything:
#   1. Frontend builds static files to backend/static/
#   2. Backend serves both API and static files on port 5050
#   3. No CORS issues, no proxy configuration needed
#   4. Simpler deployment (same architecture in dev and prod)
#
# Usage: ./dev.sh

# Shell Options Explained:
# set -e: Exit immediately if any command returns non-zero status
# This ensures the script stops on errors rather than continuing
# with potentially broken state
set -e

# ANSI Color Codes for Terminal Output
# These escape sequences change text color in compatible terminals
# Format: \033[style;colorcode
# Common codes: 0=reset, 1=bold, 30-37=foreground colors
GREEN='\033[0;32m'   # Success messages
YELLOW='\033[1;33m'  # Warnings (1; makes it bold)
RED='\033[0;31m'     # Errors
BLUE='\033[0;34m'    # Information
NC='\033[0m'         # No Color (reset to default)

# Function to print timestamped, colored messages
# Parameters:
#   $1: Log level (INFO, WARNING, ERROR, SUCCESS)
#   $2: Message text
#   $3: Color code variable
# Example: print_message "INFO" "Starting server" "$BLUE"
print_message() {
    local level=$1
    local message=$2
    local color=$3
    # -e flag enables escape sequence interpretation
    echo -e "${color}[$(date '+%H:%M:%S')] [${level}] ${message}${NC}"
}

# Function to check if a port is in use
# This is important because binding to an already-used port will fail
# Parameters:
#   $1: Port number to check
# Returns:
#   0 if port is free, 1 if in use
check_port() {
    local port=$1

    # lsof = List Open Files (on Unix, everything is a file, including network connections)
    # -i :$port = Internet address matching :port
    # -P = Don't convert port numbers to service names
    # -n = Don't convert IP addresses to hostnames (faster)
    # -t = Terse output (just PIDs)
    # 2>/dev/null = Redirect stderr to null (hide error if no process found)

    if lsof -i :$port -P -n -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is free
    fi
}

# Function to clear a port by killing the process using it
# This allows the script to recover from previous runs that didn't clean up
# Parameters:
#   $1: Port number to clear
clear_port() {
    local port=$1

    print_message "WARNING" "Port $port is already in use" "$YELLOW"

    # Find the process using the port
    # lsof shows all processes, we need to parse the output
    local process_info=$(lsof -i :$port -P -n 2>/dev/null | grep LISTEN | head -1)

    if [ -n "$process_info" ]; then
        # Extract process details using awk
        # awk splits the line into fields: $1=command, $2=PID, etc.
        local pid=$(echo "$process_info" | awk '{print $2}')
        local process_name=$(echo "$process_info" | awk '{print $1}')

        print_message "INFO" "Process '$process_name' (PID: $pid) is using port $port" "$BLUE"
        echo -n "Do you want to kill this process? (y/n): "
        read -r response

        # Check user response (case-insensitive)
        if [[ "$response" =~ ^[Yy]$ ]]; then
            # kill -9 sends SIGKILL (force kill)
            # Regular kill sends SIGTERM (graceful shutdown)
            # We try graceful first
            if kill $pid 2>/dev/null; then
                print_message "SUCCESS" "Process killed successfully" "$GREEN"
                # Give it a moment to release the port
                sleep 1
            else
                # If graceful kill failed, try force kill
                print_message "WARNING" "Graceful shutdown failed, forcing..." "$YELLOW"
                kill -9 $pid 2>/dev/null || {
                    print_message "ERROR" "Failed to kill process. Try: sudo kill -9 $pid" "$RED"
                    return 1
                }
            fi
        else
            print_message "INFO" "Skipping port cleanup" "$BLUE"
            return 1
        fi
    fi

    return 0
}

# Global variable to store frontend watcher PID
# This needs to be global so the cleanup function can access it
FRONTEND_PID=""

# Main function - orchestrates the entire development environment
main() {
    print_message "INFO" "Starting Full-Stack Development Environment" "$BLUE"
    echo "=============================================="

    # Step 1: Check if port 5050 is available
    # This prevents "bind: address already in use" errors
    if ! check_port 5050; then
        print_message "WARNING" "Port 5050 is not available" "$YELLOW"
        if ! clear_port 5050; then
            print_message "ERROR" "Cannot proceed without port 5050" "$RED"
            exit 1
        fi
    else
        print_message "SUCCESS" "Port 5050 is available" "$GREEN"
    fi

    # Step 2: Frontend dependency check
    # node_modules contains all npm packages. If missing, we need npm install
    if [ ! -d "frontend/node_modules" ]; then
        print_message "INFO" "Frontend dependencies not found" "$YELLOW"
        print_message "INFO" "Installing frontend dependencies..." "$BLUE"

        # Subshell execution with ()
        # This ensures we return to original directory even if npm fails
        (cd frontend && npm install) || {
            print_message "ERROR" "Failed to install frontend dependencies" "$RED"
            exit 1
        }

        print_message "SUCCESS" "Frontend dependencies installed" "$GREEN"
    fi

    # Step 3: Initial frontend build check
    # The backend serves static files, so we need at least one build
    if [ ! -f "backend/static/index.html" ]; then
        print_message "WARNING" "Frontend static files not found!" "$YELLOW"
        print_message "INFO" "Building frontend for the first time..." "$BLUE"

        (cd frontend && npm run build) || {
            print_message "ERROR" "Failed to build frontend" "$RED"
            exit 1
        }

        print_message "SUCCESS" "Frontend built successfully" "$GREEN"
    else
        print_message "INFO" "Frontend static files found" "$GREEN"
    fi

    # Step 4: Start frontend file watcher in background
    print_message "INFO" "Starting frontend file watcher..." "$BLUE"

    # The & at the end runs the command in the background
    # $! captures the PID of the last background process
    # We use a subshell to ensure clean directory handling
    (
        cd frontend
        # Redirect output to show it's from frontend
        # The file descriptor manipulation here allows us to prefix output
        npm run dev 2>&1 | sed 's/^/[FRONTEND] /'
    ) &

    # Capture the PID immediately after starting background process
    FRONTEND_PID=$!

    print_message "SUCCESS" "Frontend watcher started (PID: $FRONTEND_PID)" "$GREEN"
    print_message "INFO" "Frontend will auto-rebuild on file changes" "$BLUE"

    # Give frontend watcher a moment to start
    sleep 2

    # Step 5: Docker cleanup and preparation
    print_message "INFO" "Preparing Docker environment..." "$BLUE"

    # docker-compose down ensures clean state
    # 2>/dev/null suppresses errors if nothing to stop
    # || true ensures script continues even if command "fails"
    docker-compose -f docker-compose.backend-dev.yml down 2>/dev/null || true

    # Step 6: Build backend Docker image if needed
    print_message "INFO" "Building backend development image..." "$BLUE"

    # Docker will use cache if nothing changed, so this is usually fast
    docker-compose -f docker-compose.backend-dev.yml build || {
        print_message "ERROR" "Failed to build backend image" "$RED"
        # Clean up frontend watcher before exiting
        [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
        exit 1
    }

    # Step 7: Display helpful information
    echo ""
    print_message "INFO" "🚀 Development Environment Ready!" "$GREEN"
    echo "=============================================="
    print_message "INFO" "Architecture Overview:" "$BLUE"
    echo "  - Frontend watcher: Rebuilds JS/CSS to backend/static/"
    echo "  - Backend server: Serves API + static files on port 5050"
    echo "  - Hot reload: Both frontend and backend auto-reload on changes"
    echo ""
    print_message "INFO" "Access your application at:" "$BLUE"
    echo "  🌐 Main App: http://localhost:5050"
    echo "  🔌 WebSocket: ws://localhost:5050/ws/{room_id}"
    echo "  💊 Health: http://localhost:5050/api/health"
    echo "  🐛 Debug: http://localhost:5050/api/debug/*"
    echo ""
    print_message "INFO" "Development features:" "$GREEN"
    echo "  ✓ Frontend auto-rebuild (esbuild watching)"
    echo "  ✓ Backend hot reload (uvicorn --reload)"
    echo "  ✓ DEBUG=true for detailed logging"
    echo "  ✓ Dev tools: ipython, ipdb, pytest, black, pylint"
    echo "  ✓ Shared database with production structure"
    echo ""
    print_message "INFO" "File watching:" "$BLUE"
    echo "  - Frontend: ./frontend/src/**/* → ./backend/static/"
    echo "  - Backend: ./backend/**/*.py, ./shared/**/*.py"
    echo ""
    print_message "WARNING" "Press Ctrl+C to stop both frontend and backend" "$YELLOW"
    echo "=============================================="
    echo ""

    # Step 8: Start backend container in foreground
    # This keeps the script running and shows backend logs
    print_message "INFO" "Starting backend container..." "$BLUE"

    # Run in foreground so we see the logs
    # When this exits (Ctrl+C), our cleanup function runs
    docker-compose -f docker-compose.backend-dev.yml up
}

# Enhanced cleanup function - handles both frontend and backend
# This function is called when:
#   - Script exits normally
#   - User presses Ctrl+C (SIGINT)
#   - Script is terminated (SIGTERM)
#   - Script exits due to error (because of trap on EXIT)
cleanup() {
    echo ""
    print_message "INFO" "Shutting down development environment..." "$YELLOW"

    # Step 1: Kill frontend watcher if it's running
    # The frontend process runs in background, so we need to stop it explicitly
    if [ -n "$FRONTEND_PID" ]; then
        print_message "INFO" "Stopping frontend watcher (PID: $FRONTEND_PID)..." "$BLUE"

        # Check if process is still running before trying to kill
        # kill -0 sends no signal but checks if process exists
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            # Process exists, kill it
            kill $FRONTEND_PID 2>/dev/null

            # Wait a moment for graceful shutdown
            sleep 1

            # Check again and force kill if needed
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                print_message "WARNING" "Frontend still running, force killing..." "$YELLOW"
                kill -9 $FRONTEND_PID 2>/dev/null
            fi

            print_message "SUCCESS" "Frontend watcher stopped" "$GREEN"
        else
            print_message "INFO" "Frontend watcher already stopped" "$BLUE"
        fi
    fi

    # Step 2: Stop Docker containers
    print_message "INFO" "Stopping backend Docker container..." "$BLUE"

    # docker-compose down stops and removes containers
    # It also removes networks created by docker-compose
    docker-compose -f docker-compose.backend-dev.yml down 2>/dev/null || {
        print_message "WARNING" "Some Docker resources may not have been cleaned up" "$YELLOW"
    }

    print_message "SUCCESS" "Backend container stopped" "$GREEN"

    # Final message
    echo ""
    print_message "SUCCESS" "Development environment shut down successfully! 👋" "$GREEN"
    echo "=============================================="
}

# Signal Handling with trap
#
# The trap command sets up signal handlers. When the shell receives
# these signals, it executes the cleanup function before exiting.
#
# Signals explained:
#   EXIT - Triggered when script exits for any reason (normal or error)
#   INT  - Interrupt signal (Ctrl+C)
#   TERM - Terminate signal (kill command without -9)
#
# This ensures cleanup happens no matter how the script ends
trap cleanup EXIT INT TERM

# Process Management Concepts:
#
# 1. Foreground vs Background Processes:
#    - Foreground: Script waits for completion (docker-compose up)
#    - Background: Script continues immediately (npm run dev &)
#
# 2. Process Groups:
#    - When you Ctrl+C, signal goes to entire process group
#    - Background processes need explicit handling
#
# 3. Signal Propagation:
#    - Parent process (this script) receives signals
#    - Must manually propagate to child processes
#
# 4. PID Management:
#    - $! gives PID of last background process
#    - Store immediately after starting background process
#    - PIDs can be reused by OS, so check before killing

# Start the application by calling main function
# Everything begins here!
main
