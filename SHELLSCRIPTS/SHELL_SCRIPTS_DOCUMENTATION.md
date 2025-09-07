# Shell Scripts Documentation - Liap Tui Project

This document provides a comprehensive overview of all shell scripts (.sh files) in the project root directory.

## Overview

The project contains 38 shell scripts organized by function:
- **Development & Building**: Local development and Docker builds
- **AWS Deployment**: EC2 and ECS deployment scripts
- **Server Management**: Monitoring, backup, and maintenance
- **Tokyo Migration**: Scripts for migrating to Tokyo region
- **AWS Billing & Setup**: Cost monitoring and initial setup

---

## 1. Development & Local Environment

### `start.sh` (1,218 bytes)
**Purpose**: Main development launcher for local environment
- Loads environment variables from `.env`
- Creates static directory and copies `index.html`
- Starts FastAPI backend with hot reload on configured host/port
- Installs frontend dependencies if needed
- Runs esbuild in watch mode for frontend development
- Gracefully shuts down backend when frontend exits

### `version-and-deploy.sh` (410 bytes)
**Purpose**: Placeholder/template script for version management and deployment
- Appears to be a template for automated versioning and deployment workflow

### `update-version-local.sh` (1,218 bytes)
**Purpose**: Updates version locally (likely similar to version-and-deploy.sh)
- Used for local version management before deployment

---

## 2. AWS ECS Deployment (Original)

### `deploy-to-aws.sh` (3,497 bytes)
**Purpose**: Full AWS ECS deployment pipeline
- Builds Docker image with production Dockerfile
- Tags image with version from `frontend/package.json`
- Logs into AWS ECR (Elastic Container Registry)
- Pushes image to ECR repository
- Updates ECS task definition with new image
- Forces ECS service update with new task
- Waits for deployment stabilization
- Verifies deployment health via ALB endpoint
- Includes maintenance system check for v1.1.0+

---

## 3. EC2 Instance Deployment

### `connect-to-ec2.sh` (105 bytes)
**Purpose**: Quick SSH connection to EC2 instance
- Simple SSH command with pre-configured key and IP address (34.233.7.20)

### `deploy-ec2.sh` (2,677 bytes)
**Purpose**: Simplified EC2 deployment using Docker Compose
- Builds production Docker image locally
- Saves image as compressed tarball
- Transfers image and docker-compose.yml to EC2 via SCP
- Loads image on EC2 and starts container
- Creates necessary directories (/home/ubuntu/liap-tui-data, /home/ubuntu/logs)
- Verifies deployment version matches local version
- Provides monitoring command examples

### `deploy-ec2-ssl.sh` (4,074 bytes)
**Purpose**: EC2 deployment with SSL/HTTPS support
- Similar to deploy-ec2.sh but with SSL configuration
- Checks for nginx installation and SSL certificates
- Configures nginx with proper SSL settings
- Validates Let's Encrypt certificate exists
- Sets up nginx reverse proxy configuration
- Health checks after deployment
- Used for production deployment with HTTPS

### `deploy-ec2-ssl-no-rebuild.sh` (4,395 bytes)
**Purpose**: SSL deployment without rebuilding Docker image
- Skips Docker build step, uses existing image
- Useful for quick redeployments or configuration changes
- Otherwise identical to deploy-ec2-ssl.sh

---

## 4. Server Monitoring & Maintenance

### `monitor-ec2.sh` (7,178 bytes)
**Purpose**: Comprehensive EC2 monitoring dashboard
- Checks SSH connectivity to EC2
- System resources: CPU, memory, disk usage, load average
- Docker container status and resource usage
- API health check and response times
- Database status and recent game activity
- Backup status and count
- Container logs and health check failures
- Network connections and uptime
- Provides overall health status with suggestions

### `quick-monitor.sh` (1,321 bytes)
**Purpose**: Lightweight monitoring script for quick status checks
- Simplified version of monitor-ec2.sh
- Basic health and status information

### `auto-monitor.sh` (1,121 bytes)
**Purpose**: Automated monitoring, likely for cron jobs
- Designed to run periodically without user interaction
- Sends alerts or logs status automatically

### `maintain-ec2.sh` (15,048 bytes)
**Purpose**: Interactive maintenance menu for EC2 operations
- 15 different maintenance options including:
  - View container status and logs
  - Restart containers and Docker service
  - Create and manage backups
  - Database statistics and cleanup
  - Disk usage monitoring
  - Game room management
  - System resource viewing
  - Emergency container rebuild

### `verify-deployment.sh` (5,039 bytes)
**Purpose**: Post-deployment verification script
- Tests all API endpoints for proper response
- Validates JSON responses
- Tests WebSocket connectivity
- Checks telemetry system
- Performance quick check
- Provides deployment verification summary
- Lists manual checks needed

### `monitor_debug_logs.sh` (439 bytes)
**Purpose**: Monitors debug logs in real-time
- Watches debug log files for troubleshooting
- Useful during development and debugging sessions

---

## 5. Backup & Recovery

### `backup-ec2.sh` (776 bytes)
**Purpose**: Creates backup of game database from EC2
- Creates local backup directory
- Runs alpine container to create tarball of game data
- Downloads backup to local machine
- Cleans up remote backup file
- Names backups with timestamp

### `backup-game-ec2.sh` (4,485 bytes)
**Purpose**: Enhanced game backup script
- More comprehensive than backup-ec2.sh
- Includes additional game state and configuration
- Handles larger data volumes
- Includes verification steps

### `restore-ec2.sh` (4,514 bytes)
**Purpose**: Restores game data from backup
- Uploads backup file to EC2
- Stops running containers
- Restores data from backup tarball
- Restarts containers
- Verifies restoration success

### `restore-backup.sh` (1,316 bytes)
**Purpose**: Simplified backup restoration
- Lightweight version of restore-ec2.sh
- For quick restorations

### `emergency_cleanup.sh` (890 bytes)
**Purpose**: Emergency disk space cleanup
- Removes events older than 24 hours
- Deletes archives older than 7 days
- Vacuums SQLite database
- Shows disk usage before and after
- Checks maintenance status

---

## 6. Tokyo Region Migration

### `deploy-ec2-tokyo.sh` (3,799 bytes)
**Purpose**: Deploy to Tokyo EC2 instance
- Configured for ap-northeast-1 region
- Similar to deploy-ec2.sh but for Tokyo instance
- Includes latency benefit information
- Requires Tokyo instance IP and key configuration

### `deploy-ec2-ssl-tokyo-no-rebuild.sh` (5,804 bytes)
**Purpose**: Tokyo SSL deployment without rebuild
- Combines Tokyo deployment with SSL support
- No Docker rebuild, uses existing image
- For quick Tokyo deployments

### `tokyo-server-setup.sh` (3,013 bytes)
**Purpose**: Initial setup for Tokyo EC2 instance
- Installs Docker and required packages
- Sets up directory structure
- Configures firewall rules
- Prepares server for deployments

### `launch-tokyo-ec2.sh` (5,091 bytes)
**Purpose**: Launch new EC2 instance in Tokyo
- AWS CLI commands to create Tokyo instance
- Configures security groups
- Sets up networking
- Returns instance details

### `migrate-server-to-tokyo.sh` (4,140 bytes)
**Purpose**: Migrate data from current server to Tokyo
- Backs up data from current instance
- Transfers to Tokyo instance
- Restores data
- Updates DNS/configuration

### `clone-to-tokyo.sh` (3,046 bytes)
**Purpose**: Clone current setup to Tokyo
- Creates exact replica in Tokyo region
- Includes all configurations and data
- Useful for testing before migration

### `fix-tokyo-nginx.sh` (3,876 bytes)
**Purpose**: Fix nginx configuration for Tokyo instance
- Resolves SSL/nginx issues specific to Tokyo setup
- Updates configuration files
- Restarts nginx service

---

## 7. AWS Setup & Billing

### `launch-ec2-instance.sh` (8,195 bytes)
**Purpose**: Launch new EC2 instance with proper configuration
- Creates EC2 instance with specified parameters
- Configures security groups
- Sets up elastic IP
- Installs initial software
- Returns instance access details

### `ec2-setup.sh` (4,104 bytes)
**Purpose**: Initial EC2 instance configuration
- Installs Docker and Docker Compose
- Sets up user permissions
- Configures firewall
- Prepares for application deployment

### `aws-free-tier-check.sh` (4,357 bytes)
**Purpose**: Check AWS Free Tier eligibility and usage
- Shows free tier resources and limits
- Calculates monthly cost estimates
- Provides warnings about free tier expiration
- Creates billing alert setup script
- Shows cost optimization tips

### `setup-billing-alerts.sh` (992 bytes)
**Purpose**: Set up AWS billing alerts
- Creates SNS topic for billing notifications
- Sets up CloudWatch alarms at $1, $5, $10
- Configures email notifications

### `setup-billing-alerts-auto.sh` (4,102 bytes)
**Purpose**: Automated billing alert setup
- Non-interactive version of billing alerts
- Uses pre-configured thresholds
- Suitable for scripted deployments

### `setup-billing-alerts-interactive.sh` (6,227 bytes)
**Purpose**: Interactive billing alert configuration
- Guides user through alert setup
- Customizable thresholds
- Multiple notification options

### `monitor-aws-costs.sh` (1,634 bytes)
**Purpose**: Monitor current AWS costs
- Shows current month's charges
- Breaks down by service
- Compares to free tier limits

### `phase2-checklist.sh` (3,817 bytes)
**Purpose**: Deployment phase 2 checklist
- Verification steps for production deployment
- Security checks
- Performance validation
- Go-live checklist

---

## 8. Utility Scripts

### `clear-ec2-telemetry.sh` (1,082 bytes)
**Purpose**: Clear telemetry data on EC2
- Removes old telemetry logs
- Frees up disk space
- Maintains recent data only

### `rollback.sh` (865 bytes)
**Purpose**: Rollback deployment to previous version
- Reverts to previous Docker image
- Restores previous configuration
- Emergency recovery tool

### `check-deployed-version.sh` (1,544 bytes)
**Purpose**: Check currently deployed version
- Queries health endpoint for version
- Compares with expected version
- Useful for deployment verification

### `purge-cloudflare-cache.sh` (2,690 bytes)
**Purpose**: Clear Cloudflare CDN cache
- Forces cache refresh
- Useful after deployments
- Ensures users get latest version

---

## Usage Notes

1. **Environment Variables**: Many scripts use these defaults:
   - `EC2_HOST`: Your EC2 instance IP
   - `EC2_USER`: Usually "ubuntu"
   - `KEY_PATH`: Path to your SSH key

2. **Prerequisites**:
   - AWS CLI configured with proper credentials
   - Docker installed locally for build scripts
   - SSH key permissions set to 400

3. **Script Permissions**: All scripts should be executable:
   ```bash
   chmod +x *.sh
   ```

4. **Safety**: Scripts include error handling with `set -e` to stop on errors

5. **Color Coding**: Scripts use consistent colors:
   - 🟢 Green: Success
   - 🟡 Yellow: Warning/Info
   - 🔴 Red: Error
   - 🔵 Blue: Headers/Sections
